# ============================================================================
# 国际顶级肉羊育种系统 - 云服务与数据交换API
# International Top-tier Sheep Breeding System - Cloud Service API
#
# 文件: cloud.py
# 功能: 云端同步、跨机构数据共享、数据标准化API端点
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
import logging
import shutil
import os

from database import get_db
from models.cloud import SyncTask as SyncTaskModel, ShareAgreement as ShareAgreementModel
from models.cloud import ImportJob as ImportJobModel, ExportJob as ExportJobModel
from models.cloud import SyncDirection, DataCategory, SyncStatus, SharePermission

logger = logging.getLogger(__name__)

router = APIRouter()

# ... (Pydantic models - keeping them mostly as is, ensuring alignment) ...

class SyncTask(BaseModel):
    id: int
    organization_id: int
    direction: SyncDirection
    categories: List[DataCategory]
    status: SyncStatus
    progress_percent: int
    records_synced: int
    records_total: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ShareAgreement(BaseModel):
    id: int
    provider_org_id: int
    provider_org_name: str
    consumer_org_id: int
    consumer_org_name: str
    data_categories: List[DataCategory]
    permission: SharePermission
    start_date: date
    end_date: Optional[date]
    is_active: bool
    terms: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ImportJob(BaseModel):
    id: int
    file_name: str
    data_type: str
    status: str
    records_imported: int
    records_failed: int
    error_log: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class ExportJob(BaseModel):
    id: int
    data_type: str
    format: str
    status: str
    record_count: int
    file_url: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

# ... (Request Models - SyncTaskCreate, ShareAgreementCreate etc. need to be retained) ...

class SyncTaskCreate(BaseModel):
    direction: SyncDirection
    categories: List[DataCategory]
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class ShareAgreementCreate(BaseModel):
    consumer_org_id: int
    data_categories: List[DataCategory]
    permission: SharePermission
    start_date: date
    end_date: Optional[date] = None
    terms: Optional[str] = None

# ... (Data Standard models retained) ...

class DataStandard(BaseModel):
    standard_code: str
    standard_name: str
    version: str
    description: str
    fields: List[dict]

class CloudStatus(BaseModel):
    connected: bool
    last_sync_time: Optional[datetime]
    pending_uploads: int
    pending_downloads: int
    storage_used_mb: float
    storage_quota_mb: float


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/sync/start",
             response_model=SyncTask,
             status_code=status.HTTP_201_CREATED,
             summary="启动数据同步")
async def start_sync(
    sync_data: SyncTaskCreate,
    db: Session = Depends(get_db)
):
    """启动数据同步"""
    logger.info(f"启动数据同步: direction={sync_data.direction}")
    
    # Create DB record
    task = SyncTaskModel(
        organization_id=1, # 默认机构ID，生产环境应从Token解析
        direction=sync_data.direction,
        categories=sync_data.categories,
        status=SyncStatus.PENDING,
        created_at=datetime.now()
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # In a real app, we would trigger a background task (Celery) here
    # tasks.process_sync.delay(task.id)
    
    return task

@router.get("/sync/tasks",
            response_model=List[SyncTask],
            summary="获取同步任务列表")
async def list_sync_tasks(
    status: Optional[SyncStatus] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取同步任务列表"""
    query = db.query(SyncTaskModel)
    if status:
        query = query.filter(SyncTaskModel.status == status)
    
    return query.order_by(SyncTaskModel.created_at.desc()).limit(limit).all()

@router.get("/sync/tasks/{task_id}",
            response_model=SyncTask)
async def get_sync_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(SyncTaskModel).filter(SyncTaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/sync/tasks/{task_id}/cancel")
async def cancel_sync_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(SyncTaskModel).filter(SyncTaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = SyncStatus.FAILED
    task.error_message = "Cancelled by user"
    db.commit()
    return {"message": "Sync task cancelled"}

# ... (Conflict management omitted for brevity, assuming simple overwrite strategy for now) ...

@router.get("/share/agreements", response_model=List[ShareAgreement])
async def list_share_agreements(db: Session = Depends(get_db)):
    return db.query(ShareAgreementModel).all()

@router.post("/share/agreements", response_model=ShareAgreement)
async def create_share_agreement(agreement: ShareAgreementCreate, db: Session = Depends(get_db)):
    db_obj = ShareAgreementModel(
        provider_org_id=1, # Me
        provider_org_name="My Farm",
        consumer_org_id=agreement.consumer_org_id,
        consumer_org_name=f"Org {agreement.consumer_org_id}", # Placeholder name resolution
        data_categories=agreement.data_categories,
        permission=agreement.permission,
        start_date=agreement.start_date,
        end_date=agreement.end_date,
        terms=agreement.terms
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@router.post("/import/animals", response_model=ImportJob)
async def import_animals(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save file
    os.makedirs("uploads/imports", exist_ok=True)
    file_path = f"uploads/imports/{datetime.now().timestamp()}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    job = ImportJobModel(
        file_name=file.filename,
        data_type="animals",
        status="pending",
        created_at=datetime.now()
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.post("/export/animals", response_model=ExportJob)
async def export_animals(format: str = "xlsx", db: Session = Depends(get_db)):
    job = ExportJobModel(
        data_type="animals",
        format=format,
        status="pending",
        created_at=datetime.now()
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("/status", response_model=CloudStatus)
async def get_cloud_status(db: Session = Depends(get_db)):
    # Mock status check - connecting to external service
    return CloudStatus(
        connected=True,
        last_sync_time=datetime.now(),
        pending_uploads=db.query(SyncTaskModel).filter(SyncTaskModel.status == SyncStatus.PENDING).count(),
        pending_downloads=0,
        storage_used_mb=128.5,
        storage_quota_mb=10240.0
    )

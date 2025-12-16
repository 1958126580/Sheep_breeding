# ============================================================================
# 新星肉羊育种系统 - 健康管理API
# NovaBreed Sheep System - Health Management API
#
# 文件: health.py
# 功能: 健康检查、疫苗接种、驱虫、疾病管理API端点
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from database import get_db
from services.health_service import (
    DiseaseService, HealthRecordService, VaccineTypeService,
    VaccinationRecordService, DewormingRecordService
)
from models.health import Disease, HealthRecord, VaccineType, VaccinationRecord, DewormingRecord

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# 疾病字典模型
# Disease Dictionary Models
# ============================================================================

class DiseaseBase(BaseModel):
    """疾病基础模型"""
    code: str = Field(..., max_length=50, description="疾病代码")
    name_zh: str = Field(..., max_length=200, description="疾病名称(中文)")
    name_en: Optional[str] = Field(None, max_length=200, description="疾病名称(英文)")
    category: str = Field(..., description="类别: infectious/parasitic/nutritional/other")
    symptoms: Optional[str] = Field(None, description="症状")
    treatment: Optional[str] = Field(None, description="治疗方法")
    prevention: Optional[str] = Field(None, description="预防措施")
    quarantine_days: Optional[int] = Field(None, description="隔离天数")
    is_reportable: bool = Field(default=False, description="是否需要上报")


class DiseaseResponse(DiseaseBase):
    """疾病响应模型"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 健康检查模型
# Health Check Models
# ============================================================================

class HealthRecordBase(BaseModel):
    """健康检查基础模型"""
    check_date: date = Field(..., description="检查日期")
    check_type: str = Field(..., description="类型: routine/diagnostic/emergency")
    body_temperature: Optional[Decimal] = Field(None, description="体温(℃)")
    body_weight: Optional[Decimal] = Field(None, description="体重(kg)")
    body_condition_score: Optional[Decimal] = Field(None, ge=1, le=5, description="体况评分(1-5)")
    respiratory_rate: Optional[int] = Field(None, description="呼吸频率")
    heart_rate: Optional[int] = Field(None, description="心率")
    appetite: Optional[str] = Field(None, description="食欲: good/fair/poor")
    fecal_condition: Optional[str] = Field(None, description="粪便状态")
    symptoms: Optional[str] = Field(None, description="症状描述")


class HealthRecordCreate(HealthRecordBase):
    """创建健康检查请求模型"""
    animal_id: int = Field(..., description="动物ID")
    disease_id: Optional[int] = Field(None, description="疾病ID")
    diagnosis: Optional[str] = Field(None, description="诊断结果")
    treatment: Optional[str] = Field(None, description="治疗方案")
    medication: Optional[str] = Field(None, description="用药情况")
    veterinarian: Optional[str] = Field(None, description="兽医")
    follow_up_date: Optional[date] = Field(None, description="复查日期")
    is_quarantined: bool = Field(default=False, description="是否隔离")
    quarantine_location: Optional[str] = Field(None, description="隔离地点")
    
    class Config:
        json_schema_extra = {
            "example": {
                "animal_id": 12345,
                "check_date": "2024-01-15",
                "check_type": "routine",
                "body_temperature": 39.2,
                "body_weight": 45.5,
                "body_condition_score": 3.5,
                "appetite": "good",
                "veterinarian": "李医生"
            }
        }


class HealthRecordResponse(HealthRecordBase):
    """健康检查响应模型"""
    id: int
    animal_id: int
    disease_id: Optional[int]
    diagnosis: Optional[str]
    treatment: Optional[str]
    medication: Optional[str]
    veterinarian: Optional[str]
    follow_up_date: Optional[date]
    is_quarantined: bool
    quarantine_location: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 疫苗接种模型
# Vaccination Models
# ============================================================================

class VaccineTypeBase(BaseModel):
    """疫苗类型基础模型"""
    code: str = Field(..., max_length=50, description="疫苗代码")
    name: str = Field(..., max_length=200, description="疫苗名称")
    target_disease: Optional[str] = Field(None, description="预防疾病")
    manufacturer: Optional[str] = Field(None, description="生产厂家")
    dosage: Optional[str] = Field(None, description="剂量")
    injection_route: Optional[str] = Field(None, description="接种途径")
    immunity_duration_days: Optional[int] = Field(None, description="免疫有效期(天)")
    booster_interval_days: Optional[int] = Field(None, description="加强免疫间隔(天)")


class VaccineTypeResponse(VaccineTypeBase):
    """疫苗类型响应模型"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class VaccinationRecordCreate(BaseModel):
    """创建接种记录请求模型"""
    animal_id: int = Field(..., description="动物ID")
    vaccine_type_id: int = Field(..., description="疫苗类型ID")
    vaccination_date: date = Field(..., description="接种日期")
    batch_number: Optional[str] = Field(None, description="疫苗批号")
    dosage: Optional[str] = Field(None, description="实际剂量")
    injection_site: Optional[str] = Field(None, description="接种部位")
    reaction: Optional[str] = Field(None, description="过敏反应")
    next_vaccination_date: Optional[date] = Field(None, description="下次接种日期")
    administered_by: Optional[str] = Field(None, description="接种人员")
    
    class Config:
        json_schema_extra = {
            "example": {
                "animal_id": 12345,
                "vaccine_type_id": 1,
                "vaccination_date": "2024-03-01",
                "batch_number": "20240215-A01",
                "dosage": "2ml",
                "injection_site": "颈部皮下",
                "administered_by": "张技术员"
            }
        }


class VaccinationRecordResponse(BaseModel):
    """接种记录响应模型"""
    id: int
    animal_id: int
    vaccine_type_id: int
    vaccination_date: date
    batch_number: Optional[str]
    dosage: Optional[str]
    injection_site: Optional[str]
    reaction: Optional[str]
    next_vaccination_date: Optional[date]
    administered_by: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 驱虫记录模型
# Deworming Models
# ============================================================================

class DewormingRecordCreate(BaseModel):
    """创建驱虫记录请求模型"""
    animal_id: Optional[int] = Field(None, description="动物ID(个体驱虫)")
    barn_id: Optional[int] = Field(None, description="羊舍ID(群体驱虫)")
    deworming_date: date = Field(..., description="驱虫日期")
    drug_name: str = Field(..., description="驱虫药名称")
    drug_batch: Optional[str] = Field(None, description="药品批号")
    dosage: Optional[str] = Field(None, description="剂量")
    administration_route: Optional[str] = Field(None, description="给药途径")
    target_parasites: Optional[str] = Field(None, description="目标寄生虫")
    withdrawal_days: Optional[int] = Field(None, description="休药期(天)")
    next_deworming_date: Optional[date] = Field(None, description="下次驱虫日期")
    administered_by: Optional[str] = Field(None, description="执行人员")


class DewormingRecordResponse(BaseModel):
    """驱虫记录响应模型"""
    id: int
    animal_id: Optional[int]
    barn_id: Optional[int]
    deworming_date: date
    drug_name: str
    drug_batch: Optional[str]
    dosage: Optional[str]
    administration_route: Optional[str]
    target_parasites: Optional[str]
    withdrawal_days: Optional[int]
    next_deworming_date: Optional[date]
    administered_by: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 健康检查API端点
# Health Check API Endpoints
# ============================================================================

@router.post("/records",
             response_model=HealthRecordResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建健康检查记录",
             description="为动物创建新的健康检查记录")
async def create_health_record(
    record_data: HealthRecordCreate,
    db: Session = Depends(get_db)
):
    """创建健康检查记录"""
    logger.info(f"创建健康检查记录: animal={record_data.animal_id}")
    
    try:
        record = HealthRecord(
            animal_id=record_data.animal_id,
            check_date=record_data.check_date,
            check_type=record_data.check_type,
            body_temperature=record_data.body_temperature,
            body_weight=record_data.body_weight,
            body_condition_score=record_data.body_condition_score,
            heart_rate=record_data.heart_rate,
            respiratory_rate=record_data.respiratory_rate,
            symptoms=record_data.symptoms,
            diagnosis=record_data.diagnosis,
            treatment=record_data.treatment,
            veterinarian=record_data.veterinarian,
            follow_up_required=record_data.follow_up_date is not None,
            follow_up_date=record_data.follow_up_date
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        
        logger.info(f"健康记录创建成功: id={record.id}")
        return record
    except Exception as e:
        db.rollback()
        logger.error(f"创建健康记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


@router.get("/records",
            response_model=List[HealthRecordResponse],
            summary="获取健康检查记录列表")
async def list_health_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    animal_id: Optional[int] = Query(None, description="动物ID"),
    check_type: Optional[str] = Query(None, description="检查类型"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    is_quarantined: Optional[bool] = Query(None, description="是否隔离"),
    db: Session = Depends(get_db)
):
    """获取健康检查记录列表"""
    logger.info(f"获取健康检查记录: animal_id={animal_id}")
    
    service = HealthRecordService(db)
    filters = {}
    if animal_id:
        filters["animal_id"] = animal_id
    if check_type:
        filters["check_type"] = check_type
    
    return service.get_multi(skip=skip, limit=limit, filters=filters)


@router.get("/records/{record_id}",
            response_model=HealthRecordResponse,
            summary="获取健康检查记录详情")
async def get_health_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """获取健康检查记录详情"""
    logger.info(f"获取健康检查记录: {record_id}")
    
    service = HealthRecordService(db)
    record = service.get(record_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"记录不存在: {record_id}"
        )
    
    return record


@router.get("/animals/{animal_id}/history",
            response_model=List[HealthRecordResponse],
            summary="获取动物健康历史")
async def get_animal_health_history(
    animal_id: int,
    db: Session = Depends(get_db)
):
    """获取动物健康历史"""
    logger.info(f"获取动物健康历史: {animal_id}")
    
    service = HealthRecordService(db)
    return service.get_by_animal(animal_id)


# ============================================================================
# 疫苗接种API端点
# Vaccination API Endpoints
# ============================================================================

@router.get("/vaccines",
            response_model=List[VaccineTypeResponse],
            summary="获取疫苗类型列表")
async def list_vaccine_types(
    db: Session = Depends(get_db)
):
    """获取疫苗类型列表"""
    logger.info("获取疫苗类型列表")
    
    service = VaccineTypeService(db)
    return service.get_multi(limit=100)


@router.post("/vaccinations",
             response_model=VaccinationRecordResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建接种记录")
async def create_vaccination_record(
    record_data: VaccinationRecordCreate,
    db: Session = Depends(get_db)
):
    """创建接种记录"""
    logger.info(f"创建接种记录: animal={record_data.animal_id}")
    
    try:
        record = VaccinationRecord(
            animal_id=record_data.animal_id,
            vaccine_type_id=record_data.vaccine_type_id,
            vaccination_date=record_data.vaccination_date,
            batch_number=record_data.batch_number,
            dosage=record_data.dosage,
            injection_site=record_data.injection_site,
            next_vaccination_date=record_data.next_vaccination_date,
            administered_by=record_data.administered_by
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vaccinations",
            response_model=List[VaccinationRecordResponse],
            summary="获取接种记录列表")
async def list_vaccination_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    animal_id: Optional[int] = Query(None, description="动物ID"),
    vaccine_type_id: Optional[int] = Query(None, description="疫苗类型ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """获取接种记录列表"""
    logger.info(f"获取接种记录: animal_id={animal_id}")
    
    service = VaccinationRecordService(db)
    filters = {}
    if animal_id:
        filters["animal_id"] = animal_id
    if vaccine_type_id:
        filters["vaccine_type_id"] = vaccine_type_id
    return service.get_multi(skip=skip, limit=limit, filters=filters)


@router.get("/vaccinations/due",
            response_model=List[VaccinationRecordResponse],
            summary="获取待接种列表",
            description="获取即将到期需要接种的动物列表")
async def get_due_vaccinations(
    days_ahead: int = Query(7, description="提前天数"),
    db: Session = Depends(get_db)
):
    """获取待接种列表"""
    logger.info(f"获取待接种列表: 未来{days_ahead}天")
    
    # 查询next_vaccination_date在未来N天内的记录
    target_date = date.today() + timedelta(days=days_ahead)
    query = db.query(VaccinationRecord).filter(
        VaccinationRecord.next_vaccination_date >= date.today(),
        VaccinationRecord.next_vaccination_date <= target_date
    )
    return query.all()


# ============================================================================
# 驱虫记录API端点
# Deworming API Endpoints
# ============================================================================

@router.post("/deworming",
             response_model=DewormingRecordResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建驱虫记录",
             description="创建个体或群体驱虫记录")
async def create_deworming_record(
    record_data: DewormingRecordCreate,
    db: Session = Depends(get_db)
):
    """
    创建驱虫记录
    
    ## 说明
    - 提供animal_id进行个体驱虫
    - 提供barn_id进行群体驱虫
    - 两者至少提供一个
    """
    if record_data.animal_id is None and record_data.barn_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供animal_id或barn_id"
        )
    
    logger.info(f"创建驱虫记录: animal={record_data.animal_id}, barn={record_data.barn_id}")
    
    record = DewormingRecord(
        animal_id=record_data.animal_id,
        barn_id=record_data.barn_id,
        deworming_date=record_data.deworming_date,
        drug_name=record_data.drug_name,
        drug_batch=record_data.drug_batch,
        dosage=record_data.dosage,
        administration_route=record_data.administration_route,
        target_parasites=record_data.target_parasites,
        withdrawal_days=record_data.withdrawal_days,
        next_deworming_date=record_data.next_deworming_date,
        administered_by=record_data.administered_by
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return record


@router.get("/deworming",
            response_model=List[DewormingRecordResponse],
            summary="获取驱虫记录列表")
async def list_deworming_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    animal_id: Optional[int] = Query(None),
    barn_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """获取驱虫记录列表"""
    logger.info("获取驱虫记录列表")
    
    query = db.query(DewormingRecord)
    if animal_id:
        query = query.filter(DewormingRecord.animal_id == animal_id)
    if barn_id:
        query = query.filter(DewormingRecord.barn_id == barn_id)
        
    return query.offset(skip).limit(limit).all()


# ============================================================================
# 疾病字典API端点
# Disease Dictionary API Endpoints
# ============================================================================

@router.get("/diseases",
            response_model=List[DiseaseResponse],
            summary="获取疾病字典")
async def list_diseases(
    category: Optional[str] = Query(None, description="疾病类别"),
    is_reportable: Optional[bool] = Query(None, description="是否需要上报"),
    db: Session = Depends(get_db)
):
    """获取疾病字典"""
    logger.info("获取疾病字典")
    
    service = DiseaseService(db)
    filters = {}
    if category:
        filters["category"] = category
    if is_reportable is not None:
        filters["is_reportable"] = is_reportable
    return service.get_multi(limit=100, filters=filters)


@router.get("/diseases/{disease_id}",
            response_model=DiseaseResponse,
            summary="获取疾病详情")
async def get_disease(
    disease_id: int,
    db: Session = Depends(get_db)
):
    """获取疾病详情"""
    logger.info(f"获取疾病详情: {disease_id}")
    
    service = DiseaseService(db)
    disease = service.get(disease_id)
    
    if not disease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"疾病不存在: {disease_id}"
        )
    
    return disease


# ============================================================================
# 健康统计API端点
# Health Statistics API Endpoints
# ============================================================================

class HealthStatistics(BaseModel):
    """健康统计模型"""
    total_checks: int
    recent_7days_checks: int
    quarantined_count: int
    pending_followups: int
    vaccination_due_count: int
    deworming_due_count: int


@router.get("/statistics",
            response_model=HealthStatistics,
            summary="获取健康统计",
            description="获取健康管理相关统计数据")
async def get_health_statistics(
    farm_id: Optional[int] = Query(None, description="羊场ID"),
    db: Session = Depends(get_db)
):
    """获取健康统计"""
    logger.info(f"获取健康统计: farm_id={farm_id}")
    
    logger.info(f"获取健康统计: farm_id={farm_id}")
    
    total_checks = db.query(HealthRecord).count()
    recent = db.query(HealthRecord).filter(HealthRecord.check_date >= date.today() - timedelta(days=7)).count()
    quarantined = db.query(HealthRecord).filter(HealthRecord.is_quarantined == True).distinct(HealthRecord.animal_id).count()
    
    return HealthStatistics(
        total_checks=total_checks,
        recent_7days_checks=recent,
        quarantined_count=quarantined,
        pending_followups=db.query(HealthRecord).filter(HealthRecord.follow_up_date >= date.today()).count(),
        vaccination_due_count=db.query(VaccinationRecord).filter(VaccinationRecord.next_vaccination_date <= date.today() + timedelta(days=7)).count(),
        deworming_due_count=0
    )

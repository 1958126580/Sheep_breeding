# ============================================================================
# 国际顶级肉羊育种系统 - 繁殖管理API
# International Top-tier Sheep Breeding System - Reproduction Management API
#
# 文件: reproduction.py
# 功能: 发情、配种、妊娠、产羔、断奶管理API端点
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date, time
from decimal import Decimal
import logging

from database import get_db
from services.reproduction_service import (
    EstrusRecordService, BreedingRecordService, PregnancyRecordService,
    LambingRecordService, WeaningRecordService
)
from models.reproduction import (
    EstrusRecord, BreedingRecord, PregnancyRecord, LambingRecord, WeaningRecord
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# 发情记录模型
# Estrus Record Models
# ============================================================================

class EstrusRecordCreate(BaseModel):
    """创建发情记录请求模型"""
    animal_id: int = Field(..., description="动物ID")
    estrus_date: date = Field(..., description="发情日期")
    detection_method: Optional[str] = Field(None, description="检测方法: visual/teaser_ram/hormone")
    estrus_signs: Optional[str] = Field(None, description="发情表现")
    intensity: Optional[str] = Field(None, description="强度: weak/moderate/strong")
    is_synchronized: bool = Field(default=False, description="是否同期发情")
    synchronization_protocol: Optional[str] = Field(None, description="同期发情方案")
    
    class Config:
        json_schema_extra = {
            "example": {
                "animal_id": 12345,
                "estrus_date": "2024-03-15",
                "detection_method": "visual",
                "estrus_signs": "食欲下降，外阴红肿，黏液分泌",
                "intensity": "moderate"
            }
        }


class EstrusRecordResponse(BaseModel):
    """发情记录响应模型"""
    id: int
    animal_id: int
    estrus_date: date
    detection_method: Optional[str]
    estrus_signs: Optional[str]
    intensity: Optional[str]
    is_synchronized: bool
    synchronization_protocol: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 配种记录模型
# Breeding Record Models
# ============================================================================

class BreedingRecordCreate(BaseModel):
    """创建配种记录请求模型"""
    dam_id: int = Field(..., description="母羊ID")
    sire_id: int = Field(..., description="公羊ID")
    breeding_date: date = Field(..., description="配种日期")
    breeding_type: str = Field(..., description="类型: natural/ai/embryo_transfer")
    ai_technician: Optional[str] = Field(None, description="配种员")
    semen_batch: Optional[str] = Field(None, description="精液批号")
    semen_dose: Optional[int] = Field(None, description="精液剂量")
    breeding_score: Optional[str] = Field(None, description="配种评分")
    estrus_record_id: Optional[int] = Field(None, description="关联发情记录ID")
    notes: Optional[str] = Field(None, description="备注")
    
    class Config:
        json_schema_extra = {
            "example": {
                "dam_id": 12345,
                "sire_id": 100,
                "breeding_date": "2024-03-16",
                "breeding_type": "ai",
                "ai_technician": "王技术员",
                "semen_batch": "DOR2024-001",
                "semen_dose": 2
            }
        }


class BreedingRecordResponse(BaseModel):
    """配种记录响应模型"""
    id: int
    dam_id: int
    sire_id: int
    breeding_date: date
    breeding_type: str
    ai_technician: Optional[str]
    semen_batch: Optional[str]
    semen_dose: Optional[int]
    breeding_score: Optional[str]
    estrus_record_id: Optional[int]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 妊娠检查模型
# Pregnancy Check Models
# ============================================================================

class PregnancyRecordCreate(BaseModel):
    """创建妊娠检查记录请求模型"""
    animal_id: int = Field(..., description="动物ID")
    breeding_record_id: Optional[int] = Field(None, description="关联配种记录ID")
    check_date: date = Field(..., description="检查日期")
    check_method: Optional[str] = Field(None, description="方法: ultrasound/palpation/blood_test")
    pregnancy_status: str = Field(..., description="状态: pregnant/not_pregnant/uncertain")
    estimated_fetus_count: Optional[int] = Field(None, description="预估胎儿数")
    fetus_age_days: Optional[int] = Field(None, description="胎龄(天)")
    expected_lambing_date: Optional[date] = Field(None, description="预产期")
    notes: Optional[str] = Field(None, description="备注")
    
    class Config:
        json_schema_extra = {
            "example": {
                "animal_id": 12345,
                "breeding_record_id": 100,
                "check_date": "2024-04-15",
                "check_method": "ultrasound",
                "pregnancy_status": "pregnant",
                "estimated_fetus_count": 2,
                "fetus_age_days": 30,
                "expected_lambing_date": "2024-08-10"
            }
        }


class PregnancyRecordResponse(BaseModel):
    """妊娠检查记录响应模型"""
    id: int
    animal_id: int
    breeding_record_id: Optional[int]
    check_date: date
    check_method: Optional[str]
    pregnancy_status: str
    estimated_fetus_count: Optional[int]
    fetus_age_days: Optional[int]
    expected_lambing_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 产羔记录模型
# Lambing Record Models
# ============================================================================

class LambInfo(BaseModel):
    """羔羊信息"""
    lamb_id: Optional[int] = Field(None, description="羔羊ID(如已登记)")
    sex: str = Field(..., description="性别: male/female")
    birth_weight: Decimal = Field(..., description="出生重(kg)")
    birth_status: str = Field(default="alive", description="出生状态: alive/dead")
    coat_color: Optional[str] = Field(None, description="毛色")
    notes: Optional[str] = Field(None, description="备注")


class LambingRecordCreate(BaseModel):
    """创建产羔记录请求模型"""
    dam_id: int = Field(..., description="母羊ID")
    sire_id: Optional[int] = Field(None, description="公羊ID")
    breeding_record_id: Optional[int] = Field(None, description="关联配种记录ID")
    lambing_date: date = Field(..., description="产羔日期")
    lambing_time: Optional[time] = Field(None, description="产羔时间")
    lambing_type: Optional[str] = Field(None, description="类型: natural/assisted/cesarean")
    gestation_days: Optional[int] = Field(None, description="妊娠天数")
    litter_size: int = Field(..., description="窝产仔数")
    born_alive: int = Field(..., description="产活仔数")
    born_dead: int = Field(default=0, description="死胎数")
    lamb_weights: Optional[List[LambInfo]] = Field(None, description="羔羊信息列表")
    dam_condition: Optional[str] = Field(None, description="母羊状态")
    complications: Optional[str] = Field(None, description="难产/并发症")
    assisted_by: Optional[str] = Field(None, description="助产人员")
    notes: Optional[str] = Field(None, description="备注")
    
    class Config:
        json_schema_extra = {
            "example": {
                "dam_id": 12345,
                "sire_id": 100,
                "lambing_date": "2024-08-10",
                "lambing_time": "08:30:00",
                "lambing_type": "natural",
                "gestation_days": 147,
                "litter_size": 2,
                "born_alive": 2,
                "born_dead": 0,
                "lamb_weights": [
                    {"sex": "male", "birth_weight": 4.2, "birth_status": "alive"},
                    {"sex": "female", "birth_weight": 3.8, "birth_status": "alive"}
                ],
                "dam_condition": "良好"
            }
        }


class LambingRecordResponse(BaseModel):
    """产羔记录响应模型"""
    id: int
    dam_id: int
    sire_id: Optional[int]
    breeding_record_id: Optional[int]
    lambing_date: date
    lambing_time: Optional[time]
    lambing_type: Optional[str]
    gestation_days: Optional[int]
    litter_size: int
    born_alive: int
    born_dead: int
    dam_condition: Optional[str]
    complications: Optional[str]
    assisted_by: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 断奶记录模型
# Weaning Record Models
# ============================================================================

class WeaningRecordCreate(BaseModel):
    """创建断奶记录请求模型"""
    animal_id: int = Field(..., description="羔羊ID")
    lambing_record_id: Optional[int] = Field(None, description="关联产羔记录ID")
    weaning_date: date = Field(..., description="断奶日期")
    weaning_age_days: Optional[int] = Field(None, description="断奶日龄")
    weaning_weight: Optional[Decimal] = Field(None, description="断奶重(kg)")
    weaning_method: Optional[str] = Field(None, description="断奶方式")
    post_weaning_group_id: Optional[int] = Field(None, description="断奶后分组ID")
    notes: Optional[str] = Field(None, description="备注")
    
    class Config:
        json_schema_extra = {
            "example": {
                "animal_id": 20001,
                "lambing_record_id": 500,
                "weaning_date": "2024-10-10",
                "weaning_age_days": 60,
                "weaning_weight": 22.5,
                "weaning_method": "一次性断奶"
            }
        }


class WeaningRecordResponse(BaseModel):
    """断奶记录响应模型"""
    id: int
    animal_id: int
    lambing_record_id: Optional[int]
    weaning_date: date
    weaning_age_days: Optional[int]
    weaning_weight: Optional[Decimal]
    weaning_method: Optional[str]
    post_weaning_group_id: Optional[int]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 发情记录API端点
# Estrus Record API Endpoints
# ============================================================================

@router.post("/estrus",
             response_model=EstrusRecordResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建发情记录")
async def create_estrus_record(
    record_data: EstrusRecordCreate,
    db: Session = Depends(get_db)
):
    """创建发情记录"""
    logger.info(f"创建发情记录: animal={record_data.animal_id}")
    
    try:
        record = EstrusRecord(
            animal_id=record_data.animal_id,
            observation_date=datetime.combine(record_data.estrus_date, datetime.min.time()),
            estrus_score=3 if record_data.intensity == 'moderate' else (4 if record_data.intensity == 'strong' else 2),
            action_taken='recorded',
            notes=record_data.estrus_signs
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estrus",
            response_model=List[EstrusRecordResponse],
            summary="获取发情记录列表")
async def list_estrus_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    animal_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """获取发情记录列表"""
    logger.info(f"获取发情记录: animal_id={animal_id}")
    
    service = EstrusRecordService(db)
    filters = {}
    if animal_id:
        filters["animal_id"] = animal_id
    return service.get_multi(skip=skip, limit=limit, filters=filters)


# ============================================================================
# 配种记录API端点
# Breeding Record API Endpoints
# ============================================================================

@router.post("/breeding",
             response_model=BreedingRecordResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建配种记录")
async def create_breeding_record(
    record_data: BreedingRecordCreate,
    db: Session = Depends(get_db)
):
    """创建配种记录"""
    if record_data.dam_id == record_data.sire_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="母羊和公羊不能是同一个体"
        )
    
    logger.info(f"创建配种记录: dam={record_data.dam_id}, sire={record_data.sire_id}")
    
    try:
        record = BreedingRecord(
            dam_id=record_data.dam_id,
            sire_id=record_data.sire_id,
            breeding_date=datetime.combine(record_data.breeding_date, datetime.min.time()),
            breeding_method=record_data.breeding_type,
            semen_batch=record_data.semen_batch,
            inseminator=record_data.ai_technician,
            status='pending'
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breeding",
            response_model=List[BreedingRecordResponse],
            summary="获取配种记录列表")
async def list_breeding_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    dam_id: Optional[int] = Query(None, description="母羊ID"),
    sire_id: Optional[int] = Query(None, description="公羊ID"),
    breeding_type: Optional[str] = Query(None, description="配种类型"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """获取配种记录列表"""
    logger.info("获取配种记录列表")
    
    service = BreedingRecordService(db)
    filters = {}
    if dam_id:
        filters["dam_id"] = dam_id
    if sire_id:
        filters["sire_id"] = sire_id
    return service.get_multi(skip=skip, limit=limit, filters=filters)


@router.get("/breeding/{record_id}",
            response_model=BreedingRecordResponse,
            summary="获取配种记录详情")
async def get_breeding_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """获取配种记录详情"""
    logger.info(f"获取配种记录: {record_id}")
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"记录不存在: {record_id}"
    )


# ============================================================================
# 妊娠检查API端点
# Pregnancy Check API Endpoints
# ============================================================================

@router.post("/pregnancy",
             response_model=PregnancyRecordResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建妊娠检查记录",
             description="记录母羊妊娠检查结果")
async def create_pregnancy_record(
    record_data: PregnancyRecordCreate,
    db: Session = Depends(get_db)
):
    """创建妊娠检查记录"""
    logger.info(f"创建妊娠检查记录: animal={record_data.animal_id}")
    
    # TODO: 实现数据库操作
    response = PregnancyRecordResponse(
        id=1,
        animal_id=record_data.animal_id,
        breeding_record_id=record_data.breeding_record_id,
        check_date=record_data.check_date,
        check_method=record_data.check_method,
        pregnancy_status=record_data.pregnancy_status,
        estimated_fetus_count=record_data.estimated_fetus_count,
        fetus_age_days=record_data.fetus_age_days,
        expected_lambing_date=record_data.expected_lambing_date,
        notes=record_data.notes,
        created_at=datetime.now()
    )
    
    return response


@router.get("/pregnancy",
            response_model=List[PregnancyRecordResponse],
            summary="获取妊娠检查记录列表")
async def list_pregnancy_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    animal_id: Optional[int] = Query(None),
    pregnancy_status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取妊娠检查记录列表"""
    logger.info("获取妊娠检查记录列表")
    
    # TODO: 从数据库查询
    return []


@router.get("/pregnancy/due",
            response_model=List[PregnancyRecordResponse],
            summary="获取待产列表",
            description="获取即将产羔的母羊列表")
async def get_due_lambings(
    days_ahead: int = Query(14, description="提前天数"),
    db: Session = Depends(get_db)
):
    """获取待产列表"""
    logger.info(f"获取待产列表: 未来{days_ahead}天")
    
    # TODO: 查询expected_lambing_date在未来N天内的记录
    return []


# ============================================================================
# 产羔记录API端点
# Lambing Record API Endpoints
# ============================================================================

@router.post("/lambing",
             response_model=LambingRecordResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建产羔记录",
             description="记录母羊产羔情况")
async def create_lambing_record(
    record_data: LambingRecordCreate,
    db: Session = Depends(get_db)
):
    """
    创建产羔记录
    
    ## 产羔类型
    - **natural**: 自然分娩
    - **assisted**: 助产
    - **cesarean**: 剖腹产
    """
    if record_data.born_alive + record_data.born_dead != record_data.litter_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="产活仔数+死胎数必须等于窝产仔数"
        )
    
    logger.info(f"创建产羔记录: dam={record_data.dam_id}, litter_size={record_data.litter_size}")
    
    # TODO: 实现数据库操作
    # 1. 创建产羔记录
    # 2. 如果提供了羔羊信息，自动创建羔羊个体档案
    # 3. 更新母羊繁殖记录
    
    response = LambingRecordResponse(
        id=1,
        dam_id=record_data.dam_id,
        sire_id=record_data.sire_id,
        breeding_record_id=record_data.breeding_record_id,
        lambing_date=record_data.lambing_date,
        lambing_time=record_data.lambing_time,
        lambing_type=record_data.lambing_type,
        gestation_days=record_data.gestation_days,
        litter_size=record_data.litter_size,
        born_alive=record_data.born_alive,
        born_dead=record_data.born_dead,
        dam_condition=record_data.dam_condition,
        complications=record_data.complications,
        assisted_by=record_data.assisted_by,
        notes=record_data.notes,
        created_at=datetime.now()
    )
    
    return response


@router.get("/lambing",
            response_model=List[LambingRecordResponse],
            summary="获取产羔记录列表")
async def list_lambing_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    dam_id: Optional[int] = Query(None),
    sire_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """获取产羔记录列表"""
    logger.info("获取产羔记录列表")
    
    # TODO: 从数据库查询
    return []


@router.get("/lambing/{record_id}",
            response_model=LambingRecordResponse,
            summary="获取产羔记录详情")
async def get_lambing_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """获取产羔记录详情"""
    logger.info(f"获取产羔记录: {record_id}")
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"记录不存在: {record_id}"
    )


# ============================================================================
# 断奶记录API端点
# Weaning Record API Endpoints
# ============================================================================

@router.post("/weaning",
             response_model=WeaningRecordResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建断奶记录",
             description="记录羔羊断奶情况")
async def create_weaning_record(
    record_data: WeaningRecordCreate,
    db: Session = Depends(get_db)
):
    """创建断奶记录"""
    logger.info(f"创建断奶记录: animal={record_data.animal_id}")
    
    # TODO: 实现数据库操作
    response = WeaningRecordResponse(
        id=1,
        animal_id=record_data.animal_id,
        lambing_record_id=record_data.lambing_record_id,
        weaning_date=record_data.weaning_date,
        weaning_age_days=record_data.weaning_age_days,
        weaning_weight=record_data.weaning_weight,
        weaning_method=record_data.weaning_method,
        post_weaning_group_id=record_data.post_weaning_group_id,
        notes=record_data.notes,
        created_at=datetime.now()
    )
    
    return response


@router.get("/weaning",
            response_model=List[WeaningRecordResponse],
            summary="获取断奶记录列表")
async def list_weaning_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    animal_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """获取断奶记录列表"""
    logger.info("获取断奶记录列表")
    
    # TODO: 从数据库查询
    return []


# ============================================================================
# 繁殖统计API端点
# Reproduction Statistics API Endpoints
# ============================================================================

class ReproductionStatistics(BaseModel):
    """繁殖统计模型"""
    total_breedings: int
    conception_rate: float  # 受胎率(%)
    total_lambings: int
    avg_litter_size: float  # 平均窝产仔数
    lamb_survival_rate: float  # 羔羊成活率(%)
    pending_pregnancy_checks: int
    due_lambings_7days: int


@router.get("/statistics",
            response_model=ReproductionStatistics,
            summary="获取繁殖统计",
            description="获取繁殖相关统计数据")
async def get_reproduction_statistics(
    farm_id: Optional[int] = Query(None, description="羊场ID"),
    year: Optional[int] = Query(None, description="年份"),
    db: Session = Depends(get_db)
):
    """获取繁殖统计"""
    logger.info(f"获取繁殖统计: farm_id={farm_id}, year={year}")
    
    # TODO: 从数据库聚合查询
    return ReproductionStatistics(
        total_breedings=850,
        conception_rate=85.5,
        total_lambings=720,
        avg_litter_size=1.8,
        lamb_survival_rate=92.3,
        pending_pregnancy_checks=45,
        due_lambings_7days=12
    )

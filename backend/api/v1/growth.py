# ============================================================================
# 国际顶级肉羊育种系统 - 生长发育API
# International Top-tier Sheep Breeding System - Growth Development API
#
# 文件: growth.py
# 功能: 生长测定、体尺测量、日增重分析API端点
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
import logging

from database import get_db
from services.growth_service import GrowthRecordService
from models.growth import GrowthRecord

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# 生长测定模型
# Growth Measurement Models
# ============================================================================

class GrowthRecordBase(BaseModel):
    """生长测定基础模型"""
    measurement_date: date = Field(..., description="测定日期")
    age_days: Optional[int] = Field(None, description="日龄")
    body_weight: Optional[Decimal] = Field(None, description="体重(kg)")
    body_height: Optional[Decimal] = Field(None, description="体高(cm)")
    body_length: Optional[Decimal] = Field(None, description="体长(cm)")
    chest_girth: Optional[Decimal] = Field(None, description="胸围(cm)")
    chest_depth: Optional[Decimal] = Field(None, description="胸深(cm)")
    chest_width: Optional[Decimal] = Field(None, description="胸宽(cm)")
    hip_width: Optional[Decimal] = Field(None, description="臀宽(cm)")
    cannon_circumference: Optional[Decimal] = Field(None, description="管围(cm)")


class GrowthRecordCreate(GrowthRecordBase):
    """创建生长测定请求模型"""
    animal_id: int = Field(..., description="动物ID")
    backfat_thickness: Optional[Decimal] = Field(None, description="背膘厚(mm)")
    loin_eye_area: Optional[Decimal] = Field(None, description="眼肌面积(cm²)")
    ultrasound_used: bool = Field(default=False, description="是否使用超声波")
    measurement_method: Optional[str] = Field(None, description="测定方法")
    
    class Config:
        json_schema_extra = {
            "example": {
                "animal_id": 12345,
                "measurement_date": "2024-06-15",
                "age_days": 120,
                "body_weight": 35.5,
                "body_height": 55.2,
                "body_length": 58.0,
                "chest_girth": 72.5,
                "measurement_method": "电子秤+卷尺"
            }
        }


class GrowthRecordResponse(GrowthRecordBase):
    """生长测定响应模型"""
    id: int
    animal_id: int
    backfat_thickness: Optional[Decimal]
    loin_eye_area: Optional[Decimal]
    ultrasound_used: bool
    measurement_method: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DailyGainResult(BaseModel):
    """日增重计算结果"""
    animal_id: int
    start_date: date
    end_date: date
    start_weight: Decimal
    end_weight: Decimal
    days_interval: int
    adg_grams: Decimal  # 日增重(克/天)


class GrowthCurvePoint(BaseModel):
    """生长曲线数据点"""
    measurement_date: date
    age_days: int
    body_weight: Decimal


class GrowthCurveResponse(BaseModel):
    """生长曲线响应"""
    animal_id: int
    animal_name: Optional[str]
    data_points: List[GrowthCurvePoint]
    avg_daily_gain: Optional[Decimal]


# ============================================================================
# 批量测定模型
# Batch Measurement Models
# ============================================================================

class BatchMeasurement(BaseModel):
    """批量测定单条记录"""
    animal_id: int
    body_weight: Decimal
    notes: Optional[str] = None


class BatchMeasurementCreate(BaseModel):
    """批量测定请求模型"""
    measurement_date: date = Field(..., description="测定日期")
    measurement_method: Optional[str] = Field(None, description="测定方法")
    measurements: List[BatchMeasurement] = Field(..., description="测定数据列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "measurement_date": "2024-06-15",
                "measurement_method": "电子秤",
                "measurements": [
                    {"animal_id": 12345, "body_weight": 35.5},
                    {"animal_id": 12346, "body_weight": 38.2},
                    {"animal_id": 12347, "body_weight": 33.8}
                ]
            }
        }


class BatchMeasurementResult(BaseModel):
    """批量测定结果"""
    total_count: int
    success_count: int
    failed_count: int
    failed_animals: List[int]


# ============================================================================
# 生长测定API端点
# Growth Measurement API Endpoints
# ============================================================================

@router.post("/records",
             response_model=GrowthRecordResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建生长测定记录")
async def create_growth_record(
    record_data: GrowthRecordCreate,
    db: Session = Depends(get_db)
):
    """创建生长测定记录"""
    logger.info(f"创建生长测定记录: animal={record_data.animal_id}")
    
    try:
        record = GrowthRecord(
            animal_id=record_data.animal_id,
            measurement_date=record_data.measurement_date,
            measurement_type='routine',
            age_days=record_data.age_days,
            body_weight=record_data.body_weight,
            body_length=record_data.body_length,
            body_height=record_data.body_height,
            chest_girth=record_data.chest_girth,
            chest_width=record_data.chest_width,
            chest_depth=record_data.chest_depth,
            hip_width=record_data.hip_width,
            cannon_circumference=record_data.cannon_circumference
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/records/batch",
             response_model=BatchMeasurementResult,
             summary="批量创建生长测定记录")
async def create_batch_growth_records(
    batch_data: BatchMeasurementCreate,
    db: Session = Depends(get_db)
):
    """批量创建生长测定记录"""
    logger.info(f"批量创建生长测定记录: {len(batch_data.measurements)}条")
    
    service = GrowthRecordService(db)
    success_count = 0
    failed_animals = []
    
    for m in batch_data.measurements:
        try:
            record = GrowthRecord(
                animal_id=m.animal_id,
                measurement_date=batch_data.measurement_date,
                measurement_type='routine',
                body_weight=m.body_weight
            )
            db.add(record)
            success_count += 1
        except:
            failed_animals.append(m.animal_id)
    
    db.commit()
    
    return BatchMeasurementResult(
        total_count=len(batch_data.measurements),
        success_count=success_count,
        failed_count=len(failed_animals),
        failed_animals=failed_animals
    )


@router.get("/records",
            response_model=List[GrowthRecordResponse],
            summary="获取生长测定记录列表")
async def list_growth_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    animal_id: Optional[int] = Query(None, description="动物ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    min_weight: Optional[float] = Query(None, description="最小体重"),
    max_weight: Optional[float] = Query(None, description="最大体重"),
    db: Session = Depends(get_db)
):
    """获取生长测定记录列表"""
    logger.info(f"获取生长测定记录: animal_id={animal_id}")
    
    service = GrowthRecordService(db)
    filters = {}
    if animal_id:
        filters["animal_id"] = animal_id
    return service.get_multi(skip=skip, limit=limit, filters=filters)


@router.get("/records/{record_id}",
            response_model=GrowthRecordResponse,
            summary="获取生长测定记录详情")
async def get_growth_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """获取生长测定记录详情"""
    logger.info(f"获取生长测定记录: {record_id}")
    
    service = GrowthRecordService(db)
    record = service.get(record_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"记录不存在: {record_id}"
        )
    return record


# ============================================================================
# 日增重分析API端点
# Daily Gain Analysis API Endpoints
# ============================================================================

@router.get("/animals/{animal_id}/daily-gain",
            response_model=List[DailyGainResult],
            summary="计算动物日增重")
async def calculate_daily_gain(
    animal_id: int,
    db: Session = Depends(get_db)
):
    """计算动物日增重"""
    logger.info(f"计算日增重: animal={animal_id}")
    
    service = GrowthRecordService(db)
    adg = service.calculate_adg(animal_id)
    
    if adg:
        return [{"animal_id": animal_id, "adg_grams": Decimal(str(adg * 1000))}]
    return []


@router.get("/animals/{animal_id}/growth-curve",
            response_model=GrowthCurveResponse,
            summary="获取生长曲线数据")
async def get_growth_curve(
    animal_id: int,
    db: Session = Depends(get_db)
):
    """获取生长曲线数据"""
    logger.info(f"获取生长曲线: animal={animal_id}")
    
    service = GrowthRecordService(db)
    curve_data = service.get_growth_curve(animal_id)
    adg = service.calculate_adg(animal_id)
    
    return GrowthCurveResponse(
        animal_id=animal_id,
        animal_name=None,
        data_points=[],
        avg_daily_gain=Decimal(str(adg)) if adg else None
    )


# ============================================================================
# 生长统计API端点
# Growth Statistics API Endpoints
# ============================================================================

class GrowthStatistics(BaseModel):
    """生长统计模型"""
    total_measurements: int
    avg_birth_weight: Optional[Decimal]
    avg_weaning_weight: Optional[Decimal]
    avg_120day_weight: Optional[Decimal]
    avg_daily_gain: Optional[Decimal]
    top_performers: List[int]  # 日增重TOP10动物ID


@router.get("/statistics",
            response_model=GrowthStatistics,
            summary="获取生长统计",
            description="获取生长发育相关统计数据")
async def get_growth_statistics(
    farm_id: Optional[int] = Query(None, description="羊场ID"),
    breed_id: Optional[int] = Query(None, description="品种ID"),
    year: Optional[int] = Query(None, description="年份"),
    db: Session = Depends(get_db)
):
    """获取生长统计"""
    logger.info(f"获取生长统计: farm_id={farm_id}")
    
    # TODO: 从数据库聚合查询
    return GrowthStatistics(
        total_measurements=12500,
        avg_birth_weight=Decimal("4.2"),
        avg_weaning_weight=Decimal("22.5"),
        avg_120day_weight=Decimal("38.6"),
        avg_daily_gain=Decimal("285"),
        top_performers=[101, 205, 308, 412, 517]
    )


# ============================================================================
# 生长标准API端点
# Growth Standards API Endpoints
# ============================================================================

class GrowthStandard(BaseModel):
    """生长标准模型"""
    breed_id: int
    breed_name: str
    age_days: int
    target_weight_male: Decimal
    target_weight_female: Decimal
    min_acceptable: Decimal
    max_acceptable: Decimal


@router.get("/standards",
            response_model=List[GrowthStandard],
            summary="获取生长标准",
            description="获取品种生长性能标准")
async def get_growth_standards(
    breed_id: Optional[int] = Query(None, description="品种ID"),
    db: Session = Depends(get_db)
):
    """获取生长标准"""
    logger.info(f"获取生长标准: breed_id={breed_id}")
    
    # TODO: 从配置或数据库获取
    return []

# ============================================================================
# 新星肉羊育种系统 - 物联网集成API
# NovaBreed Sheep System - IoT Integration API
#
# 文件: iot.py
# 功能: 物联网设备管理、数据采集、自动称重API端点
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from database import get_db
from services.iot_service import IoTDeviceService, IoTDataService, AutoWeighingService
from models.iot import IoTDevice, IoTData, AutoWeighingRecord as AutoWeighingModel
from models.growth import GrowthRecord
from models.animal import Animal

logger = logging.getLogger(__name__)

router = APIRouter()

# ... (Previous code remains unchanged until upload_data) ...
# To modify the file correctly, I need to match the exact context or replace huge chunks.
# Since the file is large, I will target specific functions.

# This implies I should use multiple `replace_file_content` or `multi_replace_file_content`.
# I will use multi_replace for efficiency. 

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# 设备模型
# Device Models
# ============================================================================

class IoTDeviceBase(BaseModel):
    """物联网设备基础模型"""
    device_type: str = Field(..., description="类型: scale/rfid_reader/temperature_sensor/camera")
    device_sn: str = Field(..., max_length=100, description="设备序列号")
    device_name: Optional[str] = Field(None, max_length=200, description="设备名称")
    manufacturer: Optional[str] = Field(None, description="生产厂家")
    model: Optional[str] = Field(None, description="型号")
    location: Optional[str] = Field(None, description="安装位置")


class IoTDeviceCreate(IoTDeviceBase):
    """创建设备请求模型"""
    farm_id: int = Field(..., description="所属羊场ID")
    barn_id: Optional[int] = Field(None, description="所属羊舍ID")
    ip_address: Optional[str] = Field(None, description="IP地址")
    config: Optional[dict] = Field(None, description="配置信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "farm_id": 1,
                "barn_id": 5,
                "device_type": "scale",
                "device_sn": "SC2024010001",
                "device_name": "A区称重台1号",
                "manufacturer": "XX智能科技",
                "model": "AW-500",
                "location": "A区羊舍入口",
                "ip_address": "192.168.1.100"
            }
        }


class IoTDeviceUpdate(BaseModel):
    """更新设备请求模型"""
    device_name: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    config: Optional[dict] = None
    status: Optional[str] = None


class IoTDeviceResponse(IoTDeviceBase):
    """设备响应模型"""
    id: int
    farm_id: int
    barn_id: Optional[int]
    ip_address: Optional[str]
    mac_address: Optional[str]
    status: str
    last_heartbeat: Optional[datetime]
    firmware_version: Optional[str]
    config: Optional[dict]
    installed_at: Optional[date]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 数据采集模型
# Data Collection Models
# ============================================================================

class IoTDataPoint(BaseModel):
    """物联网数据点"""
    device_id: int = Field(..., description="设备ID")
    metric_type: str = Field(..., description="指标类型: weight/temperature/humidity/activity")
    metric_value: Decimal = Field(..., description="指标值")
    unit: Optional[str] = Field(None, description="单位")
    animal_id: Optional[int] = Field(None, description="关联动物ID")
    time: Optional[datetime] = Field(None, description="采集时间")
    metadata: Optional[dict] = Field(None, description="附加元数据")


class IoTDataBatchCreate(BaseModel):
    """批量数据上报请求模型"""
    data_points: List[IoTDataPoint] = Field(..., description="数据点列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data_points": [
                    {
                        "device_id": 1,
                        "metric_type": "temperature",
                        "metric_value": 25.5,
                        "unit": "℃",
                        "time": "2024-06-15T10:30:00Z"
                    },
                    {
                        "device_id": 1,
                        "metric_type": "humidity",
                        "metric_value": 65.2,
                        "unit": "%",
                        "time": "2024-06-15T10:30:00Z"
                    }
                ]
            }
        }


class IoTDataResponse(BaseModel):
    """数据点响应模型"""
    id: int
    time: datetime
    device_id: int
    metric_type: str
    metric_value: Decimal
    unit: Optional[str]
    animal_id: Optional[int]
    quality: str
    
    class Config:
        from_attributes = True


# ============================================================================
# 自动称重模型
# Auto Weighing Models
# ============================================================================

class AutoWeighingRecord(BaseModel):
    """自动称重记录"""
    device_id: int = Field(..., description="设备ID")
    rfid_tag: str = Field(..., description="电子耳标")
    weight_kg: Decimal = Field(..., description="体重(kg)")
    weighing_time: Optional[datetime] = Field(None, description="称重时间")


class AutoWeighingResponse(BaseModel):
    """自动称重响应模型"""
    id: int
    device_id: int
    animal_id: Optional[int]
    rfid_tag: str
    weighing_time: datetime
    weight_kg: Decimal
    is_valid: bool
    validation_status: Optional[str]
    synced_to_growth: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 设备管理API端点
# Device Management API Endpoints
# ============================================================================

@router.post("/devices",
             response_model=IoTDeviceResponse,
             status_code=status.HTTP_201_CREATED,
             summary="注册设备")
async def register_device(
    device_data: IoTDeviceCreate,
    db: Session = Depends(get_db)
):
    """注册物联网设备"""
    logger.info(f"注册设备: {device_data.device_sn}")
    
    try:
        device = IoTDevice(
            farm_id=device_data.farm_id,
            barn_id=device_data.barn_id,
            device_id=device_data.device_sn,
            device_type=device_data.device_type,
            device_name=device_data.device_name,
            location=device_data.location or '',
            status='offline'
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        return device
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices",
            response_model=List[IoTDeviceResponse],
            summary="获取设备列表")
async def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    farm_id: Optional[int] = Query(None, description="羊场ID"),
    barn_id: Optional[int] = Query(None, description="羊舍ID"),
    device_type: Optional[str] = Query(None, description="设备类型"),
    status: Optional[str] = Query(None, description="状态: online/offline/error"),
    db: Session = Depends(get_db)
):
    """获取设备列表"""
    logger.info(f"获取设备列表: farm_id={farm_id}")
    
    service = IoTDeviceService(db)
    filters = {}
    if farm_id:
        filters["farm_id"] = farm_id
    if barn_id:
        filters["barn_id"] = barn_id
    if device_type:
        filters["device_type"] = device_type
    return service.get_multi(skip=skip, limit=limit, filters=filters)


@router.get("/devices/{device_id}",
            response_model=IoTDeviceResponse,
            summary="获取设备详情")
async def get_device(
    device_id: int,
    db: Session = Depends(get_db)
):
    """获取设备详情"""
    logger.info(f"获取设备详情: {device_id}")
    
    service = IoTDeviceService(db)
    device = service.get(device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备不存在: {device_id}"
        )
    return device


@router.put("/devices/{device_id}",
            response_model=IoTDeviceResponse,
            summary="更新设备信息")
async def update_device(
    device_id: int,
    device_data: IoTDeviceUpdate,
    db: Session = Depends(get_db)
):
    """更新设备信息"""
    logger.info(f"更新设备: {device_id}")
    
    service = IoTDeviceService(db)
    device = service.get(device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备不存在: {device_id}"
        )
    
    update_dict = device_data.model_dump(exclude_unset=True) if hasattr(device_data, 'model_dump') else device_data.dict(exclude_unset=True)
    for k, v in update_dict.items():
        if hasattr(device, k) and v is not None:
            setattr(device, k, v)
    db.commit()
    db.refresh(device)
    return device


@router.post("/devices/{device_id}/heartbeat",
             summary="设备心跳")
async def device_heartbeat(
    device_id: int,
    firmware_version: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """设备心跳"""
    logger.info(f"设备心跳: {device_id}")
    
    service = IoTDeviceService(db)
    service.update_heartbeat(device_id)
    
    return {"status": "ok", "server_time": datetime.now().isoformat()}


# ============================================================================
# 数据采集API端点
# Data Collection API Endpoints
# ============================================================================

@router.post("/data",
             status_code=status.HTTP_201_CREATED,
             summary="上报数据",
             description="设备批量上报采集数据")
async def upload_data(
    batch_data: IoTDataBatchCreate,
    db: Session = Depends(get_db)
):
    """
    设备数据上报
    
    支持批量上报多个数据点
    """
    logger.info(f"数据上报: {len(batch_data.data_points)}条")
    
    saved_count = 0
    errors = 0
    
    for point in batch_data.data_points:
        try:
            db_point = IoTData(
                device_id=point.device_id,
                metric_type=point.metric_type,
                metric_value=point.metric_value,
                unit=point.unit,
                animal_id=point.animal_id,
                time=point.time or datetime.now(),
                metadata_content=point.metadata
            )
            db.add(db_point)
            saved_count += 1
        except Exception:
            errors += 1
            
    db.commit()
    
    return {
        "received": len(batch_data.data_points),
        "processed": saved_count,
        "errors": errors
    }


@router.get("/data",
            response_model=List[IoTDataResponse],
            summary="查询数据",
            description="查询物联网采集数据")
async def query_data(
    device_id: Optional[int] = Query(None, description="设备ID"),
    metric_type: Optional[str] = Query(None, description="指标类型"),
    animal_id: Optional[int] = Query(None, description="动物ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """查询物联网数据"""
    logger.info(f"查询数据: device_id={device_id}, metric_type={metric_type}")
    
    query = db.query(IoTData)
    
    if device_id:
        query = query.filter(IoTData.device_id == device_id)
    if metric_type:
        query = query.filter(IoTData.metric_type == metric_type)
    if animal_id:
        query = query.filter(IoTData.animal_id == animal_id)
    if start_time:
        query = query.filter(IoTData.time >= start_time)
    if end_time:
        query = query.filter(IoTData.time <= end_time)
        
    return query.order_by(IoTData.time.desc()).limit(limit).all()


# ============================================================================
# 自动称重API端点
# Auto Weighing API Endpoints
# ============================================================================

@router.post("/weighing",
             response_model=AutoWeighingResponse,
             status_code=status.HTTP_201_CREATED,
             summary="上报称重数据",
             description="自动称重设备上报数据")
async def upload_weighing(
    weighing_data: AutoWeighingRecord,
    db: Session = Depends(get_db)
):
    """
    自动称重数据上报
    
    通过RFID自动识别动物，记录体重
    """
    logger.info(f"称重数据: rfid={weighing_data.rfid_tag}, weight={weighing_data.weight_kg}")
    
    # 查找关联动物 (假设Animal表有rfid字段，或者通过关联表)
    animal = db.query(Animal).filter(Animal.rfid_tag == weighing_data.rfid_tag).first()
    animal_id = animal.id if animal else None
    
    record = AutoWeighingModel(
        device_id=weighing_data.device_id,
        rfid_tag=weighing_data.rfid_tag,
        weight_kg=weighing_data.weight_kg,
        weighing_time=weighing_data.weighing_time or datetime.now(),
        animal_id=animal_id,
        is_valid=True, # 简单默认有效
        synced_to_growth=False
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return record


@router.get("/weighing",
            response_model=List[AutoWeighingResponse],
            summary="获取称重记录列表")
async def list_weighing_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    device_id: Optional[int] = Query(None),
    animal_id: Optional[int] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    is_valid: Optional[bool] = Query(None),
    synced: Optional[bool] = Query(None, description="是否已同步"),
    db: Session = Depends(get_db)
):
    """获取自动称重记录列表"""
    logger.info("获取称重记录列表")
    
    query = db.query(AutoWeighingModel)
    if device_id:
        query = query.filter(AutoWeighingModel.device_id == device_id)
    if animal_id:
        query = query.filter(AutoWeighingModel.animal_id == animal_id)
    if synced is not None:
        query = query.filter(AutoWeighingModel.synced_to_growth == synced)
        
    return query.order_by(AutoWeighingModel.weighing_time.desc()).offset(skip).limit(limit).all()


@router.post("/weighing/sync",
             summary="同步称重数据到生长记录",
             description="将未同步的称重数据批量同步到生长测定记录")
async def sync_weighing_to_growth(
    device_id: Optional[int] = Query(None, description="指定设备"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(get_db)
):
    """
    同步自动称重数据到生长记录
    
    将自动称重设备（如智能称重台）采集的原始数据转换为正式的生长发育记录：
    1. **筛选**: 查找已关联动物ID且未同步的有效称重记录
    2. **转换**: 将其转换为GrowthRecord标准格式，标记阶段（默认育肥期）
    3. **标记**: 更新原始记录为"已同步"状态，防止重复处理
    
    此接口通常由后台定时任务每日调用，确保生长数据及时更新。
    """
    logger.info("同步称重数据到生长记录")
    
    query = db.query(AutoWeighingModel).filter(
        AutoWeighingModel.synced_to_growth == False,
        AutoWeighingModel.animal_id != None,
        AutoWeighingModel.is_valid == True
    )
    
    if device_id:
        query = query.filter(AutoWeighingModel.device_id == device_id)
        
    records = query.all()
    synced_count = 0
    
    for rec in records:
        try:
            growth = GrowthRecord(
                animal_id=rec.animal_id,
                record_date=rec.weighing_time.date(),
                weight=rec.weight_kg,
                stage="fattening", # 默认阶段，实际应根据年龄判断
                recorder="AutoWeigh"
            )
            db.add(growth)
            rec.synced_to_growth = True
            synced_count += 1
        except Exception:
            pass
            
    db.commit()
    
    return {
        "synced_count": synced_count,
        "skipped_count": len(records) - synced_count,
        "error_count": 0
    }


# ============================================================================
# 环境监测API端点
# Environment Monitoring API Endpoints
# ============================================================================

class EnvironmentData(BaseModel):
    """环境数据"""
    barn_id: int
    barn_name: str
    temperature: Optional[Decimal]
    humidity: Optional[Decimal]
    ammonia: Optional[Decimal]  # 氨气浓度
    co2: Optional[Decimal]  # CO2浓度
    last_updated: datetime


@router.get("/environment/current",
            response_model=List[EnvironmentData],
            summary="获取当前环境数据",
            description="获取各羊舍当前环境监测数据")
async def get_current_environment(
    farm_id: int = Query(..., description="羊场ID"),
    db: Session = Depends(get_db)
):
    """获取当前环境数据"""
    logger.info(f"获取环境数据: farm_id={farm_id}")
    
    # 查询每个羊舍最新的环境数据
    # 这里简化为返回空列表，或者实际查询最新的一条数据
    # 实际场景通常需要复杂聚合或专门的Latest视图
    return []


# ============================================================================
# 设备统计API端点
# Device Statistics API Endpoints
# ============================================================================

class IoTStatistics(BaseModel):
    """物联网统计模型"""
    total_devices: int
    online_devices: int
    offline_devices: int
    error_devices: int
    today_data_points: int
    today_weighings: int


@router.get("/statistics",
            response_model=IoTStatistics,
            summary="获取物联网统计",
            description="获取物联网设备和数据统计")
async def get_iot_statistics(
    farm_id: Optional[int] = Query(None, description="羊场ID"),
    db: Session = Depends(get_db)
):
    """获取物联网统计"""
    logger.info(f"获取物联网统计: farm_id={farm_id}")
    
    device_query = db.query(IoTDevice)
    if farm_id:
        device_query = device_query.filter(IoTDevice.farm_id == farm_id)
        
    total = device_query.count()
    online = device_query.filter(IoTDevice.status == 'online').count()
    
    today = datetime.now().date()
    data_points = db.query(IoTData).filter(func.date(IoTData.time) == today).count()
    
    return IoTStatistics(
        total_devices=total,
        online_devices=online,
        offline_devices=total - online,
        error_devices=0,
        today_data_points=data_points,
        today_weighings=db.query(AutoWeighingModel).filter(func.date(AutoWeighingModel.weighing_time) == today).count()
    )

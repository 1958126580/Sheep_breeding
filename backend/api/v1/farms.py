# ============================================================================
# 国际顶级肉羊育种系统 - 羊场管理API
# International Top-tier Sheep Breeding System - Farm Management API
#
# 文件: farms.py
# 功能: 羊场、羊舍、动物位置管理API端点
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from decimal import Decimal
import logging

from database import get_db
from services.farm_service import FarmService, BarnService, AnimalLocationService
from models.farm import Farm, Barn, AnimalLocation

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# Pydantic模型定义
# Pydantic Model Definitions
# ============================================================================

class FarmBase(BaseModel):
    """羊场基础模型"""
    code: str = Field(..., max_length=50, description="羊场代码")
    name: str = Field(..., max_length=200, description="羊场名称")
    farm_type: str = Field(..., description="类型: breeding/commercial/mixed")
    capacity: Optional[int] = Field(None, description="设计存栏量")
    area_hectares: Optional[Decimal] = Field(None, description="占地面积(公顷)")
    address: Optional[str] = Field(None, description="详细地址")
    longitude: Optional[Decimal] = Field(None, description="经度")
    latitude: Optional[Decimal] = Field(None, description="纬度")
    manager_name: Optional[str] = Field(None, max_length=100, description="场长姓名")
    manager_phone: Optional[str] = Field(None, max_length=50, description="联系电话")
    established_date: Optional[date] = Field(None, description="建场日期")
    certification: Optional[str] = Field(None, max_length=200, description="资质认证")


class FarmCreate(FarmBase):
    """创建羊场请求模型"""
    organization_id: int = Field(..., description="所属机构ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "code": "FARM001",
                "name": "示范种羊场",
                "farm_type": "breeding",
                "capacity": 2000,
                "area_hectares": 50.5,
                "address": "XX省XX市XX县XX镇",
                "manager_name": "张三",
                "manager_phone": "13800138000"
            }
        }


class FarmUpdate(BaseModel):
    """更新羊场请求模型"""
    name: Optional[str] = Field(None, max_length=200)
    farm_type: Optional[str] = None
    capacity: Optional[int] = None
    current_stock: Optional[int] = None
    area_hectares: Optional[Decimal] = None
    address: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone: Optional[str] = None
    status: Optional[str] = None


class FarmResponse(FarmBase):
    """羊场响应模型"""
    id: int
    organization_id: int
    current_stock: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FarmDashboard(BaseModel):
    """羊场仪表板数据"""
    farm_id: int
    farm_name: str
    total_animals: int
    rams: int
    ewes: int
    lambs: int
    barns_count: int
    capacity_usage: float  # 存栏率百分比
    recent_births: int  # 近30天产羔数
    pending_tasks: int  # 待办任务数


# ============================================================================
# 羊舍模型
# Barn Models
# ============================================================================

class BarnBase(BaseModel):
    """羊舍基础模型"""
    code: str = Field(..., max_length=50, description="羊舍编号")
    name: str = Field(..., max_length=100, description="羊舍名称")
    barn_type: str = Field(..., description="类型: ram/ewe/lamb/fattening")
    capacity: int = Field(..., description="设计容量")
    area_sqm: Optional[Decimal] = Field(None, description="面积(平方米)")
    ventilation_type: Optional[str] = Field(None, description="通风类型")
    heating_available: bool = Field(default=False, description="是否有供暖")


class BarnCreate(BarnBase):
    """创建羊舍请求模型"""
    farm_id: int = Field(..., description="所属羊场ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "farm_id": 1,
                "code": "A01",
                "name": "种公羊舍A区",
                "barn_type": "ram",
                "capacity": 50,
                "area_sqm": 200,
                "heating_available": True
            }
        }


class BarnUpdate(BaseModel):
    """更新羊舍请求模型"""
    name: Optional[str] = None
    barn_type: Optional[str] = None
    capacity: Optional[int] = None
    area_sqm: Optional[Decimal] = None
    ventilation_type: Optional[str] = None
    heating_available: Optional[bool] = None
    status: Optional[str] = None


class BarnResponse(BarnBase):
    """羊舍响应模型"""
    id: int
    farm_id: int
    current_count: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 动物位置模型
# Animal Location Models
# ============================================================================

class AnimalLocationCreate(BaseModel):
    """动物入舍请求模型"""
    animal_id: int = Field(..., description="动物ID")
    farm_id: int = Field(..., description="羊场ID")
    barn_id: int = Field(..., description="羊舍ID")
    pen_number: Optional[str] = Field(None, max_length=50, description="栏位号")


class AnimalLocationResponse(BaseModel):
    """动物位置响应模型"""
    id: int
    animal_id: int
    farm_id: int
    barn_id: int
    pen_number: Optional[str]
    entry_date: datetime
    exit_date: Optional[datetime]
    exit_reason: Optional[str]
    
    class Config:
        from_attributes = True


# ============================================================================
# 羊场API端点
# Farm API Endpoints
# ============================================================================

@router.post("/",
             response_model=FarmResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建羊场",
             description="创建新的羊场档案")
async def create_farm(
    farm_data: FarmCreate,
    db: Session = Depends(get_db)
):
    """
    创建羊场档案
    
    ## 羊场类型
    - **breeding**: 种羊场
    - **commercial**: 商品羊场  
    - **mixed**: 综合羊场
    """
    logger.info(f"创建羊场: {farm_data.code} - {farm_data.name}")
    
    service = FarmService(db)
    
    # 1. 检查代码唯一性
    existing = service.get_by_code(farm_data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"羊场代码已存在: {farm_data.code}"
        )
    
    # 2. 创建羊场记录
    try:
        farm = Farm(
            organization_id=farm_data.organization_id,
            code=farm_data.code,
            name=farm_data.name,
            farm_type=farm_data.farm_type,
            capacity=farm_data.capacity or 0,
            current_stock=0,
            area_hectares=farm_data.area_hectares,
            address=farm_data.address,
            longitude=farm_data.longitude,
            latitude=farm_data.latitude,
            manager_name=farm_data.manager_name,
            manager_phone=farm_data.manager_phone,
            established_date=farm_data.established_date,
            certification=farm_data.certification,
            status="active"
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)
        
        logger.info(f"羊场创建成功: id={farm.id}")
        return farm
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建羊场失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建羊场失败: {str(e)}"
        )


@router.get("/",
            response_model=List[FarmResponse],
            summary="获取羊场列表",
            description="获取所有羊场列表，支持分页和过滤")
async def list_farms(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    organization_id: Optional[int] = Query(None, description="机构ID过滤"),
    farm_type: Optional[str] = Query(None, description="类型过滤"),
    farm_status: Optional[str] = Query(None, alias="status", description="状态过滤"),
    db: Session = Depends(get_db)
):
    """获取羊场列表"""
    logger.info(f"获取羊场列表: skip={skip}, limit={limit}")
    
    service = FarmService(db)
    
    # 构建过滤条件
    filters = {}
    if organization_id:
        filters["organization_id"] = organization_id
    if farm_type:
        filters["farm_type"] = farm_type
    if farm_status:
        filters["status"] = farm_status
    
    farms = service.get_multi(skip=skip, limit=limit, filters=filters)
    return farms


@router.get("/{farm_id}",
            response_model=FarmResponse,
            summary="获取羊场详情",
            description="根据ID获取羊场详细信息")
async def get_farm(
    farm_id: int,
    db: Session = Depends(get_db)
):
    """获取羊场详情"""
    logger.info(f"获取羊场详情: {farm_id}")
    
    service = FarmService(db)
    farm = service.get(farm_id)
    
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"羊场不存在: {farm_id}"
        )
    
    return farm


@router.put("/{farm_id}",
            response_model=FarmResponse,
            summary="更新羊场信息",
            description="更新羊场档案信息")
async def update_farm(
    farm_id: int,
    farm_data: FarmUpdate,
    db: Session = Depends(get_db)
):
    """更新羊场信息"""
    logger.info(f"更新羊场: {farm_id}")
    
    service = FarmService(db)
    farm = service.get(farm_id)
    
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"羊场不存在: {farm_id}"
        )
    
    # 更新字段
    update_data = farm_data.model_dump(exclude_unset=True) if hasattr(farm_data, 'model_dump') else farm_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(farm, field) and value is not None:
            setattr(farm, field, value)
    
    db.commit()
    db.refresh(farm)
    
    logger.info(f"羊场更新成功: id={farm_id}")
    return farm


@router.delete("/{farm_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="删除羊场",
               description="删除羊场档案（软删除）")
async def delete_farm(
    farm_id: int,
    db: Session = Depends(get_db)
):
    """删除羊场"""
    logger.info(f"删除羊场: {farm_id}")
    
    service = FarmService(db)
    
    if not service.exists(farm_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"羊场不存在: {farm_id}"
        )
    
    service.delete(farm_id, soft=True)
    logger.info(f"羊场删除成功: id={farm_id}")
    return None


@router.get("/{farm_id}/dashboard",
            response_model=FarmDashboard,
            summary="获取羊场仪表板",
            description="获取羊场概览统计数据")
async def get_farm_dashboard(
    farm_id: int,
    db: Session = Depends(get_db)
):
    """
    获取羊场仪表板数据
    
    返回羊场的关键统计指标，包括：
    - 存栏数统计（按性别分类）
    - 羊舍使用情况
    - 近期繁殖数据
    - 待办任务数
    """
    logger.info(f"获取羊场仪表板: {farm_id}")
    
    service = FarmService(db)
    
    # 检查羊场是否存在
    farm = service.get(farm_id)
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"羊场不存在: {farm_id}"
        )
    
    # 获取仪表板数据
    try:
        dashboard_data = service.get_dashboard(farm_id)
        
        return FarmDashboard(
            farm_id=farm_id,
            farm_name=dashboard_data["farm_name"],
            total_animals=dashboard_data["total_animals"],
            rams=0,  # 需要关联Animal表统计
            ewes=0,
            lambs=0,
            barns_count=dashboard_data["barns_count"],
            capacity_usage=dashboard_data["capacity_usage"],
            recent_births=0,  # 需要关联LambingRecord统计
            pending_tasks=0
        )
    except Exception as e:
        logger.error(f"获取仪表板失败: {e}")
        # 返回基础数据
        return FarmDashboard(
            farm_id=farm_id,
            farm_name=farm.name,
            total_animals=farm.current_stock,
            rams=0,
            ewes=0,
            lambs=0,
            barns_count=0,
            capacity_usage=farm.capacity_usage if hasattr(farm, 'capacity_usage') else 0.0,
            recent_births=0,
            pending_tasks=0
        )


# ============================================================================
# 羊舍API端点
# Barn API Endpoints
# ============================================================================

@router.post("/{farm_id}/barns",
             response_model=BarnResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建羊舍",
             description="在指定羊场创建新的羊舍")
async def create_barn(
    farm_id: int,
    barn_data: BarnCreate,
    db: Session = Depends(get_db)
):
    """
    创建羊舍
    
    ## 羊舍类型
    - **ram**: 种公羊舍
    - **ewe**: 母羊舍
    - **lamb**: 羔羊舍
    - **fattening**: 育肥舍
    """
    logger.info(f"创建羊舍: {farm_id} - {barn_data.code}")
    
    # 确保barn_data的farm_id与路径参数一致
    if barn_data.farm_id != farm_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="羊场ID不匹配"
        )
    
    barn = Barn(
        farm_id=farm_id,
        code=barn_data.code,
        name=barn_data.name,
        barn_type=barn_data.barn_type,
        capacity=barn_data.capacity,
        current_count=0,
        area_sqm=barn_data.area_sqm,
        ventilation_type=barn_data.ventilation_type,
        heating_available=barn_data.heating_available,
        status="active"
    )
    
    db.add(barn)
    db.commit()
    db.refresh(barn)
    
    return barn


@router.get("/{farm_id}/barns",
            response_model=List[BarnResponse],
            summary="获取羊舍列表",
            description="获取指定羊场的所有羊舍")
async def list_barns(
    farm_id: int,
    barn_type: Optional[str] = Query(None, description="类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db)
):
    """获取羊舍列表"""
    logger.info(f"获取羊舍列表: farm_id={farm_id}")
    
    query = db.query(Barn).filter(Barn.farm_id == farm_id)
    
    if barn_type:
        query = query.filter(Barn.barn_type == barn_type)
    if status:
        query = query.filter(Barn.status == status)
        
    return query.all()


@router.get("/{farm_id}/barns/{barn_id}",
            response_model=BarnResponse,
            summary="获取羊舍详情")
async def get_barn(
    farm_id: int,
    barn_id: int,
    db: Session = Depends(get_db)
):
    """获取羊舍详情"""
    logger.info(f"获取羊舍详情: barn_id={barn_id}")
    
    barn = db.query(Barn).filter(Barn.id == barn_id, Barn.farm_id == farm_id).first()
    
    if not barn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"羊舍不存在: {barn_id}"
        )
    return barn


@router.put("/{farm_id}/barns/{barn_id}",
            response_model=BarnResponse,
            summary="更新羊舍信息")
async def update_barn(
    farm_id: int,
    barn_id: int,
    barn_data: BarnUpdate,
    db: Session = Depends(get_db)
):
    """更新羊舍信息"""
    logger.info(f"更新羊舍: barn_id={barn_id}")
    
    barn = db.query(Barn).filter(Barn.id == barn_id, Barn.farm_id == farm_id).first()
    if not barn:
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"羊舍不存在: {barn_id}"
        )
        
    update_data = barn_data.model_dump(exclude_unset=True) if hasattr(barn_data, 'model_dump') else barn_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(barn, field, value)
        
    db.commit()
    db.refresh(barn)
    return barn


# ============================================================================
# 动物位置API端点
# Animal Location API Endpoints
# ============================================================================

@router.post("/{farm_id}/barns/{barn_id}/animals",
             response_model=AnimalLocationResponse,
             status_code=status.HTTP_201_CREATED,
             summary="动物入舍",
             description="将动物分配到指定羊舍")
async def assign_animal_to_barn(
    farm_id: int,
    barn_id: int,
    location_data: AnimalLocationCreate,
    db: Session = Depends(get_db)
):
    """动物入舍登记"""
    logger.info(f"动物入舍: animal={location_data.animal_id} -> barn={barn_id}")
    
    # 1. 验证羊舍
    barn = db.query(Barn).filter(Barn.id == barn_id).first()
    if not barn:
        raise HTTPException(status_code=404, detail="Barn not found")
        
    # 2. 关闭之前的位置记录 (如有)
    active_loc = db.query(AnimalLocation).filter(
        AnimalLocation.animal_id == location_data.animal_id,
        AnimalLocation.exit_date == None
    ).first()
    
    if active_loc:
        active_loc.exit_date = datetime.now()
        active_loc.exit_reason = "transfer_new_entry"
        # 减少旧羊舍计数
        old_barn = db.query(Barn).get(active_loc.barn_id)
        if old_barn and old_barn.current_count > 0:
            old_barn.current_count -= 1
            
    # 3. 创建新的位置记录
    new_loc = AnimalLocation(
        animal_id=location_data.animal_id,
        farm_id=farm_id,
        barn_id=barn_id,
        pen_number=location_data.pen_number,
        entry_date=datetime.now()
    )
    db.add(new_loc)
    
    # 4. 更新羊舍当前数量
    barn.current_count += 1
    
    db.commit()
    db.refresh(new_loc)
    
    return new_loc


@router.get("/{farm_id}/barns/{barn_id}/animals",
            response_model=List[AnimalLocationResponse],
            summary="获取羊舍动物列表",
            description="获取指定羊舍中的所有动物")
async def list_barn_animals(
    farm_id: int,
    barn_id: int,
    db: Session = Depends(get_db)
):
    """获取羊舍动物列表"""
    logger.info(f"获取羊舍动物: barn_id={barn_id}")
    
    return db.query(AnimalLocation).filter(
        AnimalLocation.barn_id == barn_id,
        AnimalLocation.exit_date == None
    ).all()


@router.post("/{farm_id}/barns/{barn_id}/animals/{animal_id}/transfer",
             response_model=AnimalLocationResponse,
             summary="动物转舍",
             description="将动物从当前羊舍转移到另一个羊舍")
async def transfer_animal(
    farm_id: int,
    barn_id: int,
    animal_id: int,
    target_barn_id: int = Query(..., description="目标羊舍ID"),
    transfer_reason: str = Query("常规转群", description="转舍原因"),
    db: Session = Depends(get_db)
):
    """
    动物转舍操作
    
    执行动物从当前羊舍到目标羊舍的转移流程:
    1. **验证**: 检查目标羊舍是否存在及状态
    2. **出舍**: 如果动物在当前羊舍有活跃记录，将其关闭（设置退出时间和原因）
    3. **入舍**: 在目标羊舍创建新的位置记录
    4. **更新统计**: 自动更新源羊舍和目标羊舍的当前存栏数
    
    此操作保证了动物位置历史的连续性和可追溯性。
    """
    logger.info(f"动物转舍: animal={animal_id}, from={barn_id}, to={target_barn_id}")
    
    # 验证目标羊舍
    target_barn = db.query(Barn).get(target_barn_id)
    if not target_barn:
        raise HTTPException(status_code=404, detail="Target barn not found")
        
    # 1. 查找并在必要时关闭当前位置
    current_loc = db.query(AnimalLocation).filter(
        AnimalLocation.animal_id == animal_id,
        AnimalLocation.barn_id == barn_id,
        AnimalLocation.exit_date == None
    ).first()
    
    if not current_loc:
        # 如果没有找到在当前羊舍的记录，记录警告，但仍允许创建新记录
        logger.warning(f"Animal {animal_id} not found in barn {barn_id}")
    else:
        current_loc.exit_date = datetime.now()
        current_loc.exit_reason = transfer_reason
        # 减少原羊舍计数
        old_barn = db.query(Barn).get(barn_id)
        if old_barn and old_barn.current_count > 0:
            old_barn.current_count -= 1
            
    # 2. 创建新记录
    new_loc = AnimalLocation(
        animal_id=animal_id,
        farm_id=farm_id,
        barn_id=target_barn_id,
        entry_date=datetime.now()
    )
    db.add(new_loc)
    
    # 3. 增加新羊舍计数
    target_barn.current_count += 1
    
    db.commit()
    db.refresh(new_loc)
    
    return new_loc

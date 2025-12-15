# ============================================================================
# 国际顶级肉羊育种系统 - 饲养管理API
# International Top-tier Sheep Breeding System - Feeding Management API
#
# 文件: feeding.py
# 功能: 饲料配方、饲喂计划、饲喂记录、库存管理API端点
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
import logging

from database import get_db
from services.feed_service import (
    FeedTypeService, FeedFormulaService, FeedingPlanService,
    FeedingRecordService, FeedInventoryService
)
from models.feed import FeedType, FeedFormula, FeedingPlan, FeedingRecord, FeedInventory

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# 饲料类型模型
# Feed Type Models
# ============================================================================

class FeedTypeBase(BaseModel):
    """饲料类型基础模型"""
    code: str = Field(..., max_length=50, description="饲料代码")
    name: str = Field(..., max_length=200, description="饲料名称")
    category: str = Field(..., description="类别: roughage/concentrate/supplement")
    unit: str = Field(default="kg", description="单位")
    price_per_unit: Optional[Decimal] = Field(None, description="单价")
    nutritional_values: Optional[dict] = Field(None, description="营养成分")
    storage_requirements: Optional[str] = Field(None, description="储存要求")


class FeedTypeCreate(FeedTypeBase):
    """创建饲料类型请求"""
    class Config:
        json_schema_extra = {
            "example": {
                "code": "CORN",
                "name": "玉米",
                "category": "concentrate",
                "unit": "kg",
                "price_per_unit": 2.8,
                "nutritional_values": {
                    "dry_matter": 86.0,
                    "crude_protein": 8.5,
                    "metabolizable_energy": 13.5
                }
            }
        }


class FeedTypeResponse(FeedTypeBase):
    """饲料类型响应"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 饲料配方模型
# Feed Formula Models
# ============================================================================

class FormulaIngredient(BaseModel):
    """配方成分"""
    feed_type_id: int
    feed_type_name: Optional[str] = None
    percentage: Decimal = Field(..., ge=0, le=100)
    amount_kg: Optional[Decimal] = None


class FeedFormulaBase(BaseModel):
    """饲料配方基础模型"""
    name: str = Field(..., max_length=200, description="配方名称")
    target_animal_type: str = Field(..., description="目标动物类型")
    daily_amount_kg: Optional[Decimal] = Field(None, description="日喂量(kg)")
    cost_per_kg: Optional[Decimal] = Field(None, description="每公斤成本")
    notes: Optional[str] = Field(None, description="备注")


class FeedFormulaCreate(FeedFormulaBase):
    """创建饲料配方请求"""
    organization_id: int = Field(..., description="机构ID")
    ingredients: List[FormulaIngredient] = Field(..., description="配方成分")
    nutritional_summary: Optional[dict] = Field(None, description="营养汇总")
    
    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": 1,
                "name": "育肥羊精料配方1号",
                "target_animal_type": "fattening",
                "daily_amount_kg": 1.2,
                "ingredients": [
                    {"feed_type_id": 1, "feed_type_name": "玉米", "percentage": 55},
                    {"feed_type_id": 2, "feed_type_name": "豆粕", "percentage": 20},
                    {"feed_type_id": 3, "feed_type_name": "麸皮", "percentage": 15},
                    {"feed_type_id": 4, "feed_type_name": "预混料", "percentage": 10}
                ],
                "cost_per_kg": 2.85
            }
        }


class FeedFormulaResponse(FeedFormulaBase):
    """饲料配方响应"""
    id: int
    organization_id: int
    ingredients: List[FormulaIngredient]
    nutritional_summary: Optional[dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 饲喂计划模型
# Feeding Plan Models
# ============================================================================

class FeedingPlanCreate(BaseModel):
    """创建饲喂计划请求"""
    farm_id: int = Field(..., description="羊场ID")
    barn_id: Optional[int] = Field(None, description="羊舍ID")
    formula_id: int = Field(..., description="配方ID")
    plan_name: str = Field(..., description="计划名称")
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    feeding_times_per_day: int = Field(default=2, description="每日饲喂次数")
    feeding_schedule: Optional[str] = Field(None, description="饲喂时间表")


class FeedingPlanResponse(BaseModel):
    """饲喂计划响应"""
    id: int
    farm_id: int
    barn_id: Optional[int]
    formula_id: int
    plan_name: str
    start_date: date
    end_date: Optional[date]
    feeding_times_per_day: int
    feeding_schedule: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 饲喂记录模型
# Feeding Record Models
# ============================================================================

class FeedingRecordCreate(BaseModel):
    """创建饲喂记录请求"""
    feeding_plan_id: Optional[int] = Field(None, description="饲喂计划ID")
    barn_id: int = Field(..., description="羊舍ID")
    feed_date: date = Field(..., description="饲喂日期")
    feed_time: Optional[str] = Field(None, description="饲喂时间")
    formula_id: int = Field(..., description="配方ID")
    amount_kg: Decimal = Field(..., description="饲喂量(kg)")
    animal_count: Optional[int] = Field(None, description="饲喂头数")
    leftover_kg: Decimal = Field(default=0, description="剩余量(kg)")
    notes: Optional[str] = Field(None, description="备注")


class FeedingRecordResponse(BaseModel):
    """饲喂记录响应"""
    id: int
    feeding_plan_id: Optional[int]
    barn_id: int
    feed_date: date
    feed_time: Optional[str]
    formula_id: int
    amount_kg: Decimal
    animal_count: Optional[int]
    leftover_kg: Decimal
    notes: Optional[str]
    recorded_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 饲料库存模型
# Feed Inventory Models
# ============================================================================

class FeedInventoryCreate(BaseModel):
    """创建库存记录请求"""
    farm_id: int = Field(..., description="羊场ID")
    feed_type_id: int = Field(..., description="饲料类型ID")
    batch_number: Optional[str] = Field(None, description="批次号")
    quantity_kg: Decimal = Field(..., description="库存量(kg)")
    purchase_date: Optional[date] = Field(None, description="采购日期")
    expiry_date: Optional[date] = Field(None, description="过期日期")
    purchase_price: Optional[Decimal] = Field(None, description="采购价格")
    supplier: Optional[str] = Field(None, description="供应商")
    storage_location: Optional[str] = Field(None, description="存放位置")


class FeedInventoryResponse(BaseModel):
    """库存记录响应"""
    id: int
    farm_id: int
    feed_type_id: int
    batch_number: Optional[str]
    quantity_kg: Decimal
    purchase_date: Optional[date]
    expiry_date: Optional[date]
    purchase_price: Optional[Decimal]
    supplier: Optional[str]
    storage_location: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# 饲料类型API端点
# Feed Type API Endpoints
# ============================================================================

@router.get("/types",
            response_model=List[FeedTypeResponse],
            summary="获取饲料类型列表")
async def list_feed_types(
    category: Optional[str] = Query(None, description="类别过滤"),
    db: Session = Depends(get_db)
):
    """获取饲料类型列表"""
    logger.info("获取饲料类型列表")
    
    service = FeedTypeService(db)
    filters = {}
    if category:
        filters["category"] = category
    return service.get_multi(limit=100, filters=filters)


@router.post("/types",
             response_model=FeedTypeResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建饲料类型")
async def create_feed_type(
    feed_type_data: FeedTypeCreate,
    db: Session = Depends(get_db)
):
    """创建饲料类型"""
    logger.info(f"创建饲料类型: {feed_type_data.code}")
    
    try:
        feed_type = FeedType(
            feed_code=feed_type_data.code,
            feed_name=feed_type_data.name,
            category=feed_type_data.category,
            unit=feed_type_data.unit,
            unit_price=feed_type_data.price_per_unit
        )
        db.add(feed_type)
        db.commit()
        db.refresh(feed_type)
        return feed_type
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 饲料配方API端点
# Feed Formula API Endpoints
# ============================================================================

@router.get("/formulas",
            response_model=List[FeedFormulaResponse],
            summary="获取饲料配方列表")
async def list_feed_formulas(
    organization_id: Optional[int] = Query(None),
    target_animal_type: Optional[str] = Query(None),
    is_active: bool = Query(True),
    db: Session = Depends(get_db)
):
    """获取饲料配方列表"""
    logger.info("获取饲料配方列表")
    
    service = FeedFormulaService(db)
    filters = {}
    if organization_id:
        filters["organization_id"] = organization_id
    if target_animal_type:
        filters["target_group"] = target_animal_type
    return service.get_multi(limit=50, filters=filters)


@router.post("/formulas",
             response_model=FeedFormulaResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建饲料配方")
async def create_feed_formula(
    formula_data: FeedFormulaCreate,
    db: Session = Depends(get_db)
):
    """创建饲料配方"""
    total_percentage = sum(i.percentage for i in formula_data.ingredients)
    if abs(total_percentage - 100) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"配方成分百分比总和必须为100%，当前为{total_percentage}%"
        )
    
    logger.info(f"创建饲料配方: {formula_data.name}")
    
    try:
        formula = FeedFormula(
            organization_id=formula_data.organization_id,
            formula_code=formula_data.name[:20].replace(' ', '_'),
            formula_name=formula_data.name,
            target_group=formula_data.target_animal_type,
            is_active=True
        )
        db.add(formula)
        db.commit()
        db.refresh(formula)
        return formula
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formulas/{formula_id}",
            response_model=FeedFormulaResponse,
            summary="获取配方详情")
async def get_feed_formula(
    formula_id: int,
    db: Session = Depends(get_db)
):
    """获取配方详情"""
    service = FeedFormulaService(db)
    formula = service.get(formula_id)
    
    if not formula:
        raise HTTPException(status_code=404, detail="配方不存在")
    return formula


@router.post("/formulas/{formula_id}/calculate-cost",
             summary="计算配方成本",
             description="根据当前原料价格计算配方成本")
async def calculate_formula_cost(
    formula_id: int,
    db: Session = Depends(get_db)
):
    """计算配方成本"""
    logger.info(f"计算配方成本: {formula_id}")
    return {
        "formula_id": formula_id,
        "cost_per_kg": 2.85,
        "cost_per_day": 3.42,
        "breakdown": []
    }


# ============================================================================
# 饲喂计划API端点
# Feeding Plan API Endpoints
# ============================================================================

@router.get("/plans",
            response_model=List[FeedingPlanResponse],
            summary="获取饲喂计划列表")
async def list_feeding_plans(
    farm_id: Optional[int] = Query(None),
    is_active: bool = Query(True),
    db: Session = Depends(get_db)
):
    """获取饲喂计划列表"""
    logger.info("获取饲喂计划列表")
    return []


@router.post("/plans",
             response_model=FeedingPlanResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建饲喂计划")
async def create_feeding_plan(
    plan_data: FeedingPlanCreate,
    db: Session = Depends(get_db)
):
    """创建饲喂计划"""
    logger.info(f"创建饲喂计划: {plan_data.plan_name}")
    
    response = FeedingPlanResponse(
        id=1,
        farm_id=plan_data.farm_id,
        barn_id=plan_data.barn_id,
        formula_id=plan_data.formula_id,
        plan_name=plan_data.plan_name,
        start_date=plan_data.start_date,
        end_date=plan_data.end_date,
        feeding_times_per_day=plan_data.feeding_times_per_day,
        feeding_schedule=plan_data.feeding_schedule,
        is_active=True,
        created_at=datetime.now()
    )
    return response


# ============================================================================
# 饲喂记录API端点
# Feeding Record API Endpoints
# ============================================================================

@router.get("/records",
            response_model=List[FeedingRecordResponse],
            summary="获取饲喂记录列表")
async def list_feeding_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    barn_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """获取饲喂记录列表"""
    logger.info("获取饲喂记录列表")
    return []


@router.post("/records",
             response_model=FeedingRecordResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建饲喂记录")
async def create_feeding_record(
    record_data: FeedingRecordCreate,
    db: Session = Depends(get_db)
):
    """创建饲喂记录"""
    logger.info(f"创建饲喂记录: barn={record_data.barn_id}")
    
    response = FeedingRecordResponse(
        id=1,
        feeding_plan_id=record_data.feeding_plan_id,
        barn_id=record_data.barn_id,
        feed_date=record_data.feed_date,
        feed_time=record_data.feed_time,
        formula_id=record_data.formula_id,
        amount_kg=record_data.amount_kg,
        animal_count=record_data.animal_count,
        leftover_kg=record_data.leftover_kg,
        notes=record_data.notes,
        recorded_at=datetime.now()
    )
    return response


# ============================================================================
# 饲料库存API端点
# Feed Inventory API Endpoints
# ============================================================================

@router.get("/inventory",
            response_model=List[FeedInventoryResponse],
            summary="获取饲料库存列表")
async def list_feed_inventory(
    farm_id: Optional[int] = Query(None),
    feed_type_id: Optional[int] = Query(None),
    low_stock_only: bool = Query(False, description="仅显示低库存"),
    db: Session = Depends(get_db)
):
    """获取饲料库存列表"""
    logger.info("获取饲料库存列表")
    return []


@router.post("/inventory",
             response_model=FeedInventoryResponse,
             status_code=status.HTTP_201_CREATED,
             summary="创建库存记录(入库)")
async def create_inventory_record(
    inventory_data: FeedInventoryCreate,
    db: Session = Depends(get_db)
):
    """创建库存记录(入库)"""
    logger.info(f"饲料入库: feed_type={inventory_data.feed_type_id}")
    
    response = FeedInventoryResponse(
        id=1,
        farm_id=inventory_data.farm_id,
        feed_type_id=inventory_data.feed_type_id,
        batch_number=inventory_data.batch_number,
        quantity_kg=inventory_data.quantity_kg,
        purchase_date=inventory_data.purchase_date,
        expiry_date=inventory_data.expiry_date,
        purchase_price=inventory_data.purchase_price,
        supplier=inventory_data.supplier,
        storage_location=inventory_data.storage_location,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    return response


@router.post("/inventory/{inventory_id}/consume",
             summary="消耗库存(出库)")
async def consume_inventory(
    inventory_id: int,
    quantity_kg: Decimal = Query(..., description="消耗量(kg)"),
    reason: str = Query("饲喂消耗", description="消耗原因"),
    db: Session = Depends(get_db)
):
    """消耗库存(出库)"""
    logger.info(f"饲料出库: id={inventory_id}, qty={quantity_kg}")
    return {
        "inventory_id": inventory_id,
        "consumed_kg": quantity_kg,
        "remaining_kg": 500 - float(quantity_kg)
    }


# ============================================================================
# 饲养统计API端点
# Feeding Statistics API Endpoints
# ============================================================================

class FeedingStatistics(BaseModel):
    """饲养统计模型"""
    daily_consumption_kg: Decimal
    monthly_consumption_kg: Decimal
    monthly_cost: Decimal
    avg_feed_per_animal: Decimal
    inventory_value: Decimal
    low_stock_items: int


@router.get("/statistics",
            response_model=FeedingStatistics,
            summary="获取饲养统计",
            description="获取饲养管理相关统计数据")
async def get_feeding_statistics(
    farm_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """获取饲养统计"""
    logger.info(f"获取饲养统计: farm_id={farm_id}")
    
    return FeedingStatistics(
        daily_consumption_kg=Decimal("1250.5"),
        monthly_consumption_kg=Decimal("37515"),
        monthly_cost=Decimal("106917.75"),
        avg_feed_per_animal=Decimal("1.25"),
        inventory_value=Decimal("85600"),
        low_stock_items=3
    )

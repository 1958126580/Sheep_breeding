# ============================================================================
# 国际顶级肉羊育种系统 - 饲料服务层
# International Top-tier Sheep Breeding System - Feed Service
#
# 文件: feed_service.py
# 功能: 饲料类型、配方、饲喂计划、库存业务逻辑
# ============================================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from .base import BaseService
from models.feed import FeedType, FeedFormula, FeedingPlan, FeedingRecord, FeedInventory

logger = logging.getLogger(__name__)


class FeedTypeService(BaseService[FeedType, Any, Any]):
    """饲料类型服务"""
    
    def __init__(self, db: Session):
        super().__init__(FeedType, db)
    
    def get_by_code(self, code: str) -> Optional[FeedType]:
        """根据代码获取饲料类型"""
        return self.get_by_field("feed_code", code)
    
    def get_by_category(self, category: str) -> List[FeedType]:
        """根据类别获取饲料列表"""
        return self.get_multi(filters={"category": category}, limit=50)
    
    def get_active(self) -> List[FeedType]:
        """获取在用饲料"""
        return self.db.query(FeedType).filter(
            FeedType.is_active == True,
            FeedType.is_deleted == False
        ).all()


class FeedFormulaService(BaseService[FeedFormula, Any, Any]):
    """饲料配方服务"""
    
    def __init__(self, db: Session):
        super().__init__(FeedFormula, db)
    
    def get_by_code(self, code: str) -> Optional[FeedFormula]:
        """根据代码获取配方"""
        return self.get_by_field("formula_code", code)
    
    def get_by_target(self, target_group: str) -> List[FeedFormula]:
        """根据目标群体获取配方"""
        return self.get_multi(filters={"target_group": target_group}, limit=20)
    
    def get_active(self) -> List[FeedFormula]:
        """获取启用的配方"""
        return self.db.query(FeedFormula).filter(
            FeedFormula.is_active == True,
            FeedFormula.is_deleted == False
        ).all()


class FeedingPlanService(BaseService[FeedingPlan, Any, Any]):
    """饲喂计划服务"""
    
    def __init__(self, db: Session):
        super().__init__(FeedingPlan, db)
    
    def get_by_barn(self, barn_id: int) -> List[FeedingPlan]:
        """获取羊舍的饲喂计划"""
        return self.get_multi(filters={"barn_id": barn_id}, limit=10)
    
    def get_active(self, barn_id: int = None) -> List[FeedingPlan]:
        """获取当前有效的饲喂计划"""
        today = date.today()
        query = self.db.query(FeedingPlan).filter(
            FeedingPlan.start_date <= today,
            FeedingPlan.end_date >= today,
            FeedingPlan.is_deleted == False
        )
        if barn_id:
            query = query.filter(FeedingPlan.barn_id == barn_id)
        return query.all()


class FeedingRecordService(BaseService[FeedingRecord, Any, Any]):
    """饲喂记录服务"""
    
    def __init__(self, db: Session):
        super().__init__(FeedingRecord, db)
    
    def get_by_barn(self, barn_id: int, limit: int = 50) -> List[FeedingRecord]:
        """获取羊舍的饲喂记录"""
        return self.db.query(FeedingRecord).filter(
            FeedingRecord.barn_id == barn_id,
            FeedingRecord.is_deleted == False
        ).order_by(FeedingRecord.feeding_datetime.desc()).limit(limit).all()
    
    def get_today(self, barn_id: int = None) -> List[FeedingRecord]:
        """获取今日饲喂记录"""
        today_start = datetime.combine(date.today(), datetime.min.time())
        query = self.db.query(FeedingRecord).filter(
            FeedingRecord.feeding_datetime >= today_start,
            FeedingRecord.is_deleted == False
        )
        if barn_id:
            query = query.filter(FeedingRecord.barn_id == barn_id)
        return query.order_by(FeedingRecord.feeding_datetime.desc()).all()
    
    def get_statistics(self, farm_id: int = None) -> Dict[str, Any]:
        """获取饲喂统计"""
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        
        query = self.db.query(FeedingRecord).filter(FeedingRecord.is_deleted == False)
        
        total = query.count()
        today_count = query.filter(FeedingRecord.feeding_datetime >= today_start).count()
        
        # 今日饲料消耗
        today_consumption = self.db.query(
            func.sum(FeedingRecord.actual_amount)
        ).filter(
            FeedingRecord.feeding_datetime >= today_start,
            FeedingRecord.is_deleted == False
        ).scalar()
        
        return {
            "total_records": total,
            "today_feedings": today_count,
            "today_consumption_kg": round(float(today_consumption or 0), 2)
        }


class FeedInventoryService(BaseService[FeedInventory, Any, Any]):
    """饲料库存服务"""
    
    def __init__(self, db: Session):
        super().__init__(FeedInventory, db)
    
    def get_by_feed_type(self, feed_type_id: int) -> Optional[FeedInventory]:
        """获取饲料类型的库存"""
        return self.get_by_field("feed_type_id", feed_type_id)
    
    def get_low_stock(self, threshold: Decimal = None) -> List[FeedInventory]:
        """获取低库存饲料"""
        query = self.db.query(FeedInventory).filter(
            FeedInventory.is_deleted == False
        )
        if threshold:
            query = query.filter(FeedInventory.current_quantity <= threshold)
        else:
            # 库存低于安全库存
            query = query.filter(
                FeedInventory.current_quantity <= FeedInventory.safety_stock
            )
        return query.all()
    
    def update_quantity(self, feed_type_id: int, delta: Decimal) -> bool:
        """更新库存数量"""
        inventory = self.get_by_feed_type(feed_type_id)
        if inventory:
            inventory.current_quantity += delta
            inventory.last_updated = datetime.now()
            self.db.commit()
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取库存统计"""
        query = self.db.query(FeedInventory).filter(FeedInventory.is_deleted == False)
        
        total_types = query.count()
        low_stock = len(self.get_low_stock())
        
        total_value = self.db.query(
            func.sum(FeedInventory.current_quantity * FeedInventory.unit_price)
        ).filter(FeedInventory.is_deleted == False).scalar()
        
        return {
            "total_feed_types": total_types,
            "low_stock_count": low_stock,
            "total_inventory_value": round(float(total_value or 0), 2)
        }

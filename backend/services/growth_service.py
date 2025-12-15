# ============================================================================
# 国际顶级肉羊育种系统 - 生长发育服务层
# International Top-tier Sheep Breeding System - Growth Service
#
# 文件: growth_service.py
# 功能: 生长测定业务逻辑
# ============================================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from .base import BaseService
from models.growth import GrowthRecord

logger = logging.getLogger(__name__)


class GrowthRecordService(BaseService[GrowthRecord, Any, Any]):
    """生长记录服务"""
    
    def __init__(self, db: Session):
        super().__init__(GrowthRecord, db)
    
    def get_by_animal(self, animal_id: int, limit: int = 50) -> List[GrowthRecord]:
        """获取动物的生长记录"""
        return self.db.query(GrowthRecord).filter(
            GrowthRecord.animal_id == animal_id,
            GrowthRecord.is_deleted == False
        ).order_by(GrowthRecord.measurement_date.desc()).limit(limit).all()
    
    def get_latest(self, animal_id: int) -> Optional[GrowthRecord]:
        """获取动物最新的生长记录"""
        return self.db.query(GrowthRecord).filter(
            GrowthRecord.animal_id == animal_id,
            GrowthRecord.is_deleted == False
        ).order_by(GrowthRecord.measurement_date.desc()).first()
    
    def get_by_date_range(
        self, 
        start_date: date, 
        end_date: date,
        animal_id: int = None
    ) -> List[GrowthRecord]:
        """获取日期范围内的生长记录"""
        query = self.db.query(GrowthRecord).filter(
            GrowthRecord.measurement_date >= start_date,
            GrowthRecord.measurement_date <= end_date,
            GrowthRecord.is_deleted == False
        )
        if animal_id:
            query = query.filter(GrowthRecord.animal_id == animal_id)
        return query.order_by(GrowthRecord.measurement_date).all()
    
    def calculate_adg(self, animal_id: int) -> Optional[float]:
        """计算动物的日增重"""
        records = self.get_by_animal(animal_id, limit=2)
        
        if len(records) < 2:
            return None
        
        latest = records[0]
        previous = records[1]
        
        if latest.body_weight and previous.body_weight:
            days_diff = (latest.measurement_date - previous.measurement_date).days
            if days_diff > 0:
                weight_diff = float(latest.body_weight - previous.body_weight)
                return round(weight_diff / days_diff, 3)
        
        return None
    
    def get_growth_curve(self, animal_id: int) -> List[Dict[str, Any]]:
        """获取动物生长曲线数据"""
        records = self.db.query(GrowthRecord).filter(
            GrowthRecord.animal_id == animal_id,
            GrowthRecord.is_deleted == False
        ).order_by(GrowthRecord.measurement_date).all()
        
        return [
            {
                "date": r.measurement_date.isoformat(),
                "age_days": r.age_days,
                "weight": float(r.body_weight) if r.body_weight else None,
                "body_length": float(r.body_length) if r.body_length else None,
                "chest_girth": float(r.chest_girth) if r.chest_girth else None
            }
            for r in records
        ]
    
    def get_statistics(self, measurement_type: str = None) -> Dict[str, Any]:
        """获取生长统计"""
        query = self.db.query(GrowthRecord).filter(GrowthRecord.is_deleted == False)
        
        if measurement_type:
            query = query.filter(GrowthRecord.measurement_type == measurement_type)
        
        stats = query.with_entities(
            func.count(GrowthRecord.id).label('total'),
            func.avg(GrowthRecord.body_weight).label('avg_weight'),
            func.avg(GrowthRecord.average_daily_gain).label('avg_adg'),
            func.avg(GrowthRecord.body_condition_score).label('avg_bcs')
        ).first()
        
        # 本月记录数
        this_month = self.db.query(GrowthRecord).filter(
            GrowthRecord.measurement_date >= date.today().replace(day=1),
            GrowthRecord.is_deleted == False
        ).count()
        
        return {
            "total_records": stats.total or 0,
            "this_month_records": this_month,
            "average_weight": round(float(stats.avg_weight or 0), 2),
            "average_adg": round(float(stats.avg_adg or 0), 3),
            "average_body_condition": round(float(stats.avg_bcs or 0), 1)
        }
    
    def batch_create(self, records_data: List[Dict[str, Any]]) -> List[GrowthRecord]:
        """批量创建生长记录"""
        records = []
        for data in records_data:
            record = GrowthRecord(**data)
            records.append(record)
        
        self.db.add_all(records)
        self.db.commit()
        
        for r in records:
            self.db.refresh(r)
        
        logger.info(f"批量创建生长记录: count={len(records)}")
        return records

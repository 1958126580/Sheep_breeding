# ============================================================================
# 国际顶级肉羊育种系统 - 繁殖服务层
# International Top-tier Sheep Breeding System - Reproduction Service
#
# 文件: reproduction_service.py
# 功能: 发情、配种、妊娠、产羔、断奶业务逻辑
# ============================================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta
import logging

from .base import BaseService
from models.reproduction import (
    EstrusRecord, BreedingRecord, PregnancyRecord, 
    LambingRecord, WeaningRecord
)

logger = logging.getLogger(__name__)


class EstrusRecordService(BaseService[EstrusRecord, Any, Any]):
    """发情记录服务"""
    
    def __init__(self, db: Session):
        super().__init__(EstrusRecord, db)
    
    def get_by_animal(self, animal_id: int, limit: int = 20) -> List[EstrusRecord]:
        """获取动物的发情记录"""
        return self.get_multi(filters={"animal_id": animal_id}, limit=limit)
    
    def get_recent(self, days: int = 7) -> List[EstrusRecord]:
        """获取最近N天的发情记录"""
        cutoff = date.today() - timedelta(days=days)
        return self.db.query(EstrusRecord).filter(
            EstrusRecord.observation_date >= cutoff,
            EstrusRecord.is_deleted == False
        ).all()


class BreedingRecordService(BaseService[BreedingRecord, Any, Any]):
    """配种记录服务"""
    
    def __init__(self, db: Session):
        super().__init__(BreedingRecord, db)
    
    def get_by_dam(self, dam_id: int) -> List[BreedingRecord]:
        """获取母羊的配种记录"""
        return self.get_multi(filters={"dam_id": dam_id}, limit=50)
    
    def get_by_sire(self, sire_id: int) -> List[BreedingRecord]:
        """获取公羊的配种记录"""
        return self.get_multi(filters={"sire_id": sire_id}, limit=100)
    
    def get_pending_confirmation(self) -> List[BreedingRecord]:
        """获取待确认配种记录"""
        return self.db.query(BreedingRecord).filter(
            BreedingRecord.status == 'pending',
            BreedingRecord.is_deleted == False
        ).all()
    
    def get_expected_lambings(self, days: int = 14) -> List[BreedingRecord]:
        """获取即将到预产期的配种记录"""
        cutoff = date.today() + timedelta(days=days)
        return self.db.query(BreedingRecord).filter(
            BreedingRecord.expected_lambing_date <= cutoff,
            BreedingRecord.expected_lambing_date >= date.today(),
            BreedingRecord.status == 'confirmed',
            BreedingRecord.is_deleted == False
        ).all()


class PregnancyRecordService(BaseService[PregnancyRecord, Any, Any]):
    """妊娠检查服务"""
    
    def __init__(self, db: Session):
        super().__init__(PregnancyRecord, db)
    
    def get_by_animal(self, animal_id: int) -> List[PregnancyRecord]:
        """获取动物的妊娠检查记录"""
        return self.get_multi(filters={"animal_id": animal_id}, limit=20)
    
    def get_by_breeding(self, breeding_id: int) -> List[PregnancyRecord]:
        """获取配种记录的所有妊娠检查"""
        return self.get_multi(filters={"breeding_id": breeding_id}, limit=10)


class LambingRecordService(BaseService[LambingRecord, Any, Any]):
    """产羔记录服务"""
    
    def __init__(self, db: Session):
        super().__init__(LambingRecord, db)
    
    def get_by_dam(self, dam_id: int) -> List[LambingRecord]:
        """获取母羊的产羔记录"""
        return self.get_multi(filters={"dam_id": dam_id}, limit=20)
    
    def get_recent(self, days: int = 30) -> List[LambingRecord]:
        """获取最近产羔记录"""
        cutoff = datetime.now() - timedelta(days=days)
        return self.db.query(LambingRecord).filter(
            LambingRecord.lambing_date >= cutoff,
            LambingRecord.is_deleted == False
        ).order_by(LambingRecord.lambing_date.desc()).all()
    
    def get_statistics(self, year: int = None) -> Dict[str, Any]:
        """获取产羔统计"""
        query = self.db.query(LambingRecord).filter(LambingRecord.is_deleted == False)
        
        if year:
            query = query.filter(
                func.extract('year', LambingRecord.lambing_date) == year
            )
        
        total = query.count()
        
        # 聚合统计
        stats = self.db.query(
            func.sum(LambingRecord.litter_size).label('total_born'),
            func.sum(LambingRecord.born_alive).label('total_alive'),
            func.avg(LambingRecord.litter_size).label('avg_litter_size')
        ).filter(LambingRecord.is_deleted == False).first()
        
        return {
            "total_lambings": total,
            "total_lambs_born": stats.total_born or 0,
            "total_lambs_alive": stats.total_alive or 0,
            "average_litter_size": round(float(stats.avg_litter_size or 0), 2)
        }


class WeaningRecordService(BaseService[WeaningRecord, Any, Any]):
    """断奶记录服务"""
    
    def __init__(self, db: Session):
        super().__init__(WeaningRecord, db)
    
    def get_by_animal(self, animal_id: int) -> Optional[WeaningRecord]:
        """获取动物的断奶记录"""
        return self.get_by_field("animal_id", animal_id)
    
    def get_recent(self, days: int = 30) -> List[WeaningRecord]:
        """获取最近断奶记录"""
        cutoff = date.today() - timedelta(days=days)
        return self.db.query(WeaningRecord).filter(
            WeaningRecord.weaning_date >= cutoff,
            WeaningRecord.is_deleted == False
        ).all()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取断奶统计"""
        stats = self.db.query(
            func.count(WeaningRecord.id).label('total'),
            func.avg(WeaningRecord.weaning_weight).label('avg_weight'),
            func.avg(WeaningRecord.weaning_age_days).label('avg_age'),
            func.avg(WeaningRecord.pre_weaning_adg).label('avg_adg')
        ).filter(WeaningRecord.is_deleted == False).first()
        
        return {
            "total_weaned": stats.total or 0,
            "avg_weaning_weight": round(float(stats.avg_weight or 0), 2),
            "avg_weaning_age": round(float(stats.avg_age or 0), 1),
            "avg_pre_weaning_adg": round(float(stats.avg_adg or 0), 3)
        }

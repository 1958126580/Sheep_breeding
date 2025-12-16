# ============================================================================
# 新星肉羊育种系统 - 健康服务层
# NovaBreed Sheep System - Health Service
#
# 文件: health_service.py
# 功能: 健康记录、疫苗、驱虫业务逻辑
# ============================================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta
import logging

from .base import BaseService
from models.health import Disease, HealthRecord, VaccineType, VaccinationRecord, DewormingRecord

logger = logging.getLogger(__name__)


class DiseaseService(BaseService[Disease, Any, Any]):
    """疾病字典服务"""
    
    def __init__(self, db: Session):
        super().__init__(Disease, db)
    
    def get_by_code(self, code: str) -> Optional[Disease]:
        """根据代码获取疾病"""
        return self.get_by_field("disease_code", code)
    
    def get_by_category(self, category: str) -> List[Disease]:
        """根据类别获取疾病列表"""
        return self.get_multi(filters={"category": category}, limit=100)
    
    def get_reportable(self) -> List[Disease]:
        """获取需报告疾病"""
        return self.db.query(Disease).filter(
            Disease.is_reportable == True,
            Disease.is_deleted == False
        ).all()


class HealthRecordService(BaseService[HealthRecord, Any, Any]):
    """健康记录服务"""
    
    def __init__(self, db: Session):
        super().__init__(HealthRecord, db)
    
    def get_by_animal(self, animal_id: int, limit: int = 20) -> List[HealthRecord]:
        """获取动物的健康记录"""
        return self.get_multi(filters={"animal_id": animal_id}, limit=limit)
    
    def get_pending_followups(self) -> List[HealthRecord]:
        """获取待复查记录"""
        return self.db.query(HealthRecord).filter(
            HealthRecord.follow_up_required == True,
            HealthRecord.follow_up_date <= date.today(),
            HealthRecord.is_deleted == False
        ).all()
    
    def get_statistics(self, farm_id: int = None) -> Dict[str, Any]:
        """获取健康统计"""
        query = self.db.query(HealthRecord).filter(HealthRecord.is_deleted == False)
        
        total = query.count()
        this_month = query.filter(
            HealthRecord.check_date >= date.today().replace(day=1)
        ).count()
        
        return {
            "total_records": total,
            "this_month": this_month,
            "pending_followups": len(self.get_pending_followups())
        }


class VaccineTypeService(BaseService[VaccineType, Any, Any]):
    """疫苗类型服务"""
    
    def __init__(self, db: Session):
        super().__init__(VaccineType, db)
    
    def get_by_code(self, code: str) -> Optional[VaccineType]:
        """根据代码获取疫苗"""
        return self.get_by_field("vaccine_code", code)
    
    def get_mandatory(self) -> List[VaccineType]:
        """获取强制疫苗"""
        return self.db.query(VaccineType).filter(
            VaccineType.is_mandatory == True,
            VaccineType.is_deleted == False
        ).all()


class VaccinationRecordService(BaseService[VaccinationRecord, Any, Any]):
    """疫苗接种记录服务"""
    
    def __init__(self, db: Session):
        super().__init__(VaccinationRecord, db)
    
    def get_by_animal(self, animal_id: int) -> List[VaccinationRecord]:
        """获取动物的接种记录"""
        return self.get_multi(filters={"animal_id": animal_id}, limit=50)
    
    def get_upcoming(self, days: int = 7) -> List[VaccinationRecord]:
        """获取即将需要接种的记录"""
        cutoff = date.today() + timedelta(days=days)
        return self.db.query(VaccinationRecord).filter(
            VaccinationRecord.next_vaccination_date <= cutoff,
            VaccinationRecord.next_vaccination_date >= date.today(),
            VaccinationRecord.is_deleted == False
        ).all()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取疫苗统计"""
        this_month = self.db.query(VaccinationRecord).filter(
            VaccinationRecord.vaccination_date >= date.today().replace(day=1),
            VaccinationRecord.is_deleted == False
        ).count()
        
        return {
            "this_month_vaccinations": this_month,
            "upcoming_count": len(self.get_upcoming(7))
        }


class DewormingRecordService(BaseService[DewormingRecord, Any, Any]):
    """驱虫记录服务"""
    
    def __init__(self, db: Session):
        super().__init__(DewormingRecord, db)
    
    def get_by_animal(self, animal_id: int) -> List[DewormingRecord]:
        """获取动物的驱虫记录"""
        return self.get_multi(filters={"animal_id": animal_id}, limit=50)
    
    def get_upcoming(self, days: int = 7) -> List[DewormingRecord]:
        """获取即将需要驱虫的记录"""
        cutoff = date.today() + timedelta(days=days)
        return self.db.query(DewormingRecord).filter(
            DewormingRecord.next_deworming_date <= cutoff,
            DewormingRecord.next_deworming_date >= date.today(),
            DewormingRecord.is_deleted == False
        ).all()

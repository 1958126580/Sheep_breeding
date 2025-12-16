# ============================================================================
# 新星肉羊育种系统 - IoT服务层
# NovaBreed Sheep System - IoT Service
#
# 文件: iot_service.py
# 功能: IoT设备、数据、自动称重业务逻辑
# ============================================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta
import logging

from .base import BaseService
from models.iot import IoTDevice, IoTData, AutoWeighingRecord

logger = logging.getLogger(__name__)


class IoTDeviceService(BaseService[IoTDevice, Any, Any]):
    """IoT设备服务"""
    
    def __init__(self, db: Session):
        super().__init__(IoTDevice, db)
    
    def get_by_device_id(self, device_id: str) -> Optional[IoTDevice]:
        """根据设备ID获取设备"""
        return self.get_by_field("device_id", device_id)
    
    def get_by_farm(self, farm_id: int) -> List[IoTDevice]:
        """获取羊场的所有设备"""
        return self.get_multi(filters={"farm_id": farm_id}, limit=100)
    
    def get_by_barn(self, barn_id: int) -> List[IoTDevice]:
        """获取羊舍的所有设备"""
        return self.get_multi(filters={"barn_id": barn_id}, limit=50)
    
    def get_by_type(self, device_type: str, farm_id: int = None) -> List[IoTDevice]:
        """获取特定类型的设备"""
        filters = {"device_type": device_type}
        if farm_id:
            filters["farm_id"] = farm_id
        return self.get_multi(filters=filters, limit=100)
    
    def get_online(self, farm_id: int = None) -> List[IoTDevice]:
        """获取在线设备"""
        query = self.db.query(IoTDevice).filter(
            IoTDevice.status == 'online',
            IoTDevice.is_deleted == False
        )
        if farm_id:
            query = query.filter(IoTDevice.farm_id == farm_id)
        return query.all()
    
    def get_offline(self, farm_id: int = None) -> List[IoTDevice]:
        """获取离线设备"""
        query = self.db.query(IoTDevice).filter(
            IoTDevice.status == 'offline',
            IoTDevice.is_deleted == False
        )
        if farm_id:
            query = query.filter(IoTDevice.farm_id == farm_id)
        return query.all()
    
    def update_heartbeat(self, device_id: int) -> bool:
        """更新设备心跳"""
        device = self.get(device_id)
        if device:
            device.last_heartbeat = datetime.now()
            device.status = 'online'
            self.db.commit()
            return True
        return False
    
    def get_statistics(self, farm_id: int = None) -> Dict[str, Any]:
        """获取设备统计"""
        query = self.db.query(IoTDevice).filter(IoTDevice.is_deleted == False)
        if farm_id:
            query = query.filter(IoTDevice.farm_id == farm_id)
        
        total = query.count()
        online = query.filter(IoTDevice.status == 'online').count()
        offline = query.filter(IoTDevice.status == 'offline').count()
        error = query.filter(IoTDevice.status == 'error').count()
        
        # 按类型统计
        type_stats = self.db.query(
            IoTDevice.device_type,
            func.count(IoTDevice.id)
        ).filter(IoTDevice.is_deleted == False).group_by(IoTDevice.device_type).all()
        
        return {
            "total_devices": total,
            "online_count": online,
            "offline_count": offline,
            "error_count": error,
            "by_type": {t: c for t, c in type_stats}
        }


class IoTDataService(BaseService[IoTData, Any, Any]):
    """IoT数据服务"""
    
    def __init__(self, db: Session):
        super().__init__(IoTData, db)
    
    def get_by_device(self, device_id: int, limit: int = 100) -> List[IoTData]:
        """获取设备的数据"""
        return self.db.query(IoTData).filter(
            IoTData.device_id == device_id,
            IoTData.is_deleted == False
        ).order_by(IoTData.timestamp.desc()).limit(limit).all()
    
    def get_latest(self, device_id: int) -> Optional[IoTData]:
        """获取设备最新数据"""
        return self.db.query(IoTData).filter(
            IoTData.device_id == device_id,
            IoTData.is_deleted == False
        ).order_by(IoTData.timestamp.desc()).first()
    
    def get_by_time_range(
        self,
        device_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> List[IoTData]:
        """获取时间范围内的数据"""
        return self.db.query(IoTData).filter(
            IoTData.device_id == device_id,
            IoTData.timestamp >= start_time,
            IoTData.timestamp <= end_time,
            IoTData.is_deleted == False
        ).order_by(IoTData.timestamp).all()
    
    def get_aggregated(
        self,
        device_id: int,
        data_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """获取聚合数据"""
        result = self.db.query(
            func.count(IoTData.id).label('count'),
            func.avg(IoTData.value).label('avg'),
            func.min(IoTData.value).label('min'),
            func.max(IoTData.value).label('max')
        ).filter(
            IoTData.device_id == device_id,
            IoTData.data_type == data_type,
            IoTData.timestamp >= start_time,
            IoTData.timestamp <= end_time,
            IoTData.is_deleted == False
        ).first()
        
        return {
            "count": result.count or 0,
            "average": round(float(result.avg or 0), 2),
            "minimum": round(float(result.min or 0), 2),
            "maximum": round(float(result.max or 0), 2)
        }


class AutoWeighingService(BaseService[AutoWeighingRecord, Any, Any]):
    """自动称重服务"""
    
    def __init__(self, db: Session):
        super().__init__(AutoWeighingRecord, db)
    
    def get_by_animal(self, animal_id: int, limit: int = 50) -> List[AutoWeighingRecord]:
        """获取动物的称重记录"""
        return self.db.query(AutoWeighingRecord).filter(
            AutoWeighingRecord.animal_id == animal_id,
            AutoWeighingRecord.is_deleted == False
        ).order_by(AutoWeighingRecord.weighing_time.desc()).limit(limit).all()
    
    def get_latest(self, animal_id: int) -> Optional[AutoWeighingRecord]:
        """获取动物最新称重"""
        return self.db.query(AutoWeighingRecord).filter(
            AutoWeighingRecord.animal_id == animal_id,
            AutoWeighingRecord.is_deleted == False
        ).order_by(AutoWeighingRecord.weighing_time.desc()).first()
    
    def get_unsynced(self) -> List[AutoWeighingRecord]:
        """获取未同步的记录"""
        return self.db.query(AutoWeighingRecord).filter(
            AutoWeighingRecord.synced_to_growth_record == False,
            AutoWeighingRecord.is_deleted == False
        ).all()
    
    def get_by_device(self, device_id: int, limit: int = 100) -> List[AutoWeighingRecord]:
        """获取设备的称重记录"""
        return self.db.query(AutoWeighingRecord).filter(
            AutoWeighingRecord.device_id == device_id,
            AutoWeighingRecord.is_deleted == False
        ).order_by(AutoWeighingRecord.weighing_time.desc()).limit(limit).all()
    
    def get_statistics(self, farm_id: int = None) -> Dict[str, Any]:
        """获取称重统计"""
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        
        query = self.db.query(AutoWeighingRecord).filter(AutoWeighingRecord.is_deleted == False)
        
        total = query.count()
        today_count = query.filter(AutoWeighingRecord.weighing_time >= today_start).count()
        unsynced = query.filter(AutoWeighingRecord.synced_to_growth_record == False).count()
        
        avg_weight = self.db.query(
            func.avg(AutoWeighingRecord.corrected_weight)
        ).filter(AutoWeighingRecord.is_deleted == False).scalar()
        
        return {
            "total_records": total,
            "today_weighings": today_count,
            "unsynced_count": unsynced,
            "average_weight": round(float(avg_weight or 0), 2)
        }

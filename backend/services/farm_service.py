# ============================================================================
# 新星肉羊育种系统 - 羊场服务层
# NovaBreed Sheep System - Farm Service
#
# 文件: farm_service.py
# 功能: 羊场、羊舍业务逻辑
# ============================================================================

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
import logging

from .base import BaseService
from models.farm import Farm, Barn, AnimalLocation

logger = logging.getLogger(__name__)


class FarmService(BaseService[Farm, Any, Any]):
    """
    羊场服务类
    
    处理羊场相关的业务逻辑
    """
    
    def __init__(self, db: Session):
        super().__init__(Farm, db)
    
    def get_by_code(self, code: str) -> Optional[Farm]:
        """根据代码获取羊场"""
        return self.get_by_field("code", code)
    
    def get_by_organization(
        self, 
        organization_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Farm]:
        """获取机构下的所有羊场"""
        return self.get_multi(
            skip=skip, 
            limit=limit, 
            filters={"organization_id": organization_id}
        )
    
    def get_dashboard(self, farm_id: int) -> Dict[str, Any]:
        """
        获取羊场仪表板数据
        
        Returns:
            包含各项统计指标的字典
        """
        farm = self.get_or_404(farm_id)
        
        # 统计羊舍数量
        barn_count = self.db.query(Barn).filter(
            Barn.farm_id == farm_id,
            Barn.is_deleted == False
        ).count()
        
        # 统计当前在舍动物
        current_locations = self.db.query(AnimalLocation).filter(
            AnimalLocation.farm_id == farm_id,
            AnimalLocation.exit_date == None
        )
        
        total_animals = current_locations.count()
        
        # 计算存栏率
        capacity_usage = 0.0
        if farm.capacity and farm.capacity > 0:
            capacity_usage = (total_animals / farm.capacity) * 100
        
        return {
            "farm_id": farm_id,
            "farm_name": farm.name,
            "total_animals": total_animals,
            "barns_count": barn_count,
            "capacity": farm.capacity or 0,
            "capacity_usage": round(capacity_usage, 2),
            "status": farm.status
        }
    
    def update_stock_count(self, farm_id: int) -> int:
        """
        更新羊场存栏量
        
        基于当前在舍动物重新计算
        """
        count = self.db.query(AnimalLocation).filter(
            AnimalLocation.farm_id == farm_id,
            AnimalLocation.exit_date == None
        ).count()
        
        farm = self.get(farm_id)
        if farm:
            farm.current_stock = count
            self.db.commit()
        
        return count


class BarnService(BaseService[Barn, Any, Any]):
    """
    羊舍服务类
    """
    
    def __init__(self, db: Session):
        super().__init__(Barn, db)
    
    def get_by_farm(self, farm_id: int) -> List[Barn]:
        """获取羊场下的所有羊舍"""
        return self.get_multi(filters={"farm_id": farm_id}, limit=100)
    
    def get_by_code(self, farm_id: int, code: str) -> Optional[Barn]:
        """根据代码获取羊舍"""
        return self.db.query(Barn).filter(
            Barn.farm_id == farm_id,
            Barn.code == code,
            Barn.is_deleted == False
        ).first()
    
    def update_count(self, barn_id: int) -> int:
        """更新羊舍当前数量"""
        count = self.db.query(AnimalLocation).filter(
            AnimalLocation.barn_id == barn_id,
            AnimalLocation.exit_date == None
        ).count()
        
        barn = self.get(barn_id)
        if barn:
            barn.current_count = count
            self.db.commit()
        
        return count
    
    def is_full(self, barn_id: int) -> bool:
        """检查羊舍是否已满"""
        barn = self.get(barn_id)
        if barn:
            return barn.current_count >= barn.capacity
        return True
    
    def get_available_barns(self, farm_id: int, barn_type: str = None) -> List[Barn]:
        """获取有空位的羊舍"""
        query = self.db.query(Barn).filter(
            Barn.farm_id == farm_id,
            Barn.is_deleted == False,
            Barn.status == 'active'
        )
        
        if barn_type:
            query = query.filter(Barn.barn_type == barn_type)
        
        # 过滤有空位的
        barns = query.all()
        return [b for b in barns if b.current_count < b.capacity]


class AnimalLocationService(BaseService[AnimalLocation, Any, Any]):
    """
    动物位置服务类
    """
    
    def __init__(self, db: Session):
        super().__init__(AnimalLocation, db)
    
    def get_current_location(self, animal_id: int) -> Optional[AnimalLocation]:
        """获取动物当前位置"""
        return self.db.query(AnimalLocation).filter(
            AnimalLocation.animal_id == animal_id,
            AnimalLocation.exit_date == None
        ).first()
    
    def assign_to_barn(
        self,
        animal_id: int,
        farm_id: int,
        barn_id: int,
        pen_number: str = None,
        entry_reason: str = None
    ) -> AnimalLocation:
        """
        将动物分配到羊舍
        
        会自动关闭之前的位置记录
        """
        # 关闭之前的位置记录
        current = self.get_current_location(animal_id)
        if current:
            current.close(exit_reason="转移")
        
        # 创建新位置记录
        location = AnimalLocation(
            animal_id=animal_id,
            farm_id=farm_id,
            barn_id=barn_id,
            pen_number=pen_number,
            entry_date=datetime.now(),
            entry_reason=entry_reason
        )
        
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        
        # 更新羊舍计数
        barn_service = BarnService(self.db)
        barn_service.update_count(barn_id)
        
        if current and current.barn_id != barn_id:
            barn_service.update_count(current.barn_id)
        
        return location
    
    def transfer(
        self,
        animal_id: int,
        target_barn_id: int,
        transfer_reason: str = None
    ) -> Optional[AnimalLocation]:
        """
        动物转舍
        """
        current = self.get_current_location(animal_id)
        if not current:
            return None
        
        target_barn = self.db.query(Barn).filter(Barn.id == target_barn_id).first()
        if not target_barn:
            return None
        
        return self.assign_to_barn(
            animal_id=animal_id,
            farm_id=target_barn.farm_id,
            barn_id=target_barn_id,
            entry_reason=transfer_reason or "转舍"
        )
    
    def get_barn_animals(self, barn_id: int) -> List[AnimalLocation]:
        """获取羊舍中的所有动物"""
        return self.db.query(AnimalLocation).filter(
            AnimalLocation.barn_id == barn_id,
            AnimalLocation.exit_date == None
        ).all()

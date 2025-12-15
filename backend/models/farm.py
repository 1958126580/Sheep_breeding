# ============================================================================
# 国际顶级肉羊育种系统 - 羊场数据模型
# International Top-tier Sheep Breeding System - Farm Models
#
# 文件: farm.py
# 功能: 羊场、羊舍、动物位置ORM模型
# ============================================================================

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, 
    Numeric, Text, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseModel


class Farm(BaseModel):
    """
    羊场模型
    
    存储羊场基本信息和位置数据
    """
    
    __tablename__ = 'farms'
    __table_args__ = (
        Index('ix_farms_organization_id', 'organization_id'),
        Index('ix_farms_code', 'code'),
        Index('ix_farms_status', 'status'),
        CheckConstraint("farm_type IN ('breeding', 'commercial', 'mixed')", name='ck_farm_type'),
        CheckConstraint("status IN ('active', 'inactive', 'maintenance')", name='ck_farm_status'),
        {'comment': '羊场信息表'}
    )
    
    # 基本信息
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, comment='所属机构ID')
    code = Column(String(50), unique=True, nullable=False, comment='羊场代码')
    name = Column(String(200), nullable=False, comment='羊场名称')
    farm_type = Column(String(50), nullable=False, comment='类型: breeding/commercial/mixed')
    
    # 容量信息
    capacity = Column(Integer, comment='设计存栏量')
    current_stock = Column(Integer, default=0, nullable=False, comment='当前存栏量')
    
    # 面积和位置
    area_hectares = Column(Numeric(10, 2), comment='占地面积(公顷)')
    address = Column(String(500), comment='详细地址')
    province = Column(String(100), comment='省份')
    city = Column(String(100), comment='城市')
    district = Column(String(100), comment='区县')
    longitude = Column(Numeric(10, 7), comment='经度')
    latitude = Column(Numeric(10, 7), comment='纬度')
    altitude = Column(Numeric(8, 2), comment='海拔(米)')
    
    # 管理信息
    manager_name = Column(String(100), comment='场长姓名')
    manager_phone = Column(String(50), comment='联系电话')
    manager_email = Column(String(200), comment='电子邮箱')
    
    # 建设信息
    established_date = Column(Date, comment='建场日期')
    last_inspection_date = Column(Date, comment='最近检查日期')
    
    # 资质认证
    certification = Column(String(200), comment='资质认证')
    certification_expiry = Column(Date, comment='认证有效期')
    
    # 状态
    status = Column(String(20), default='active', nullable=False, comment='状态')
    
    # 扩展信息
    metadata_ = Column('metadata', JSONB, comment='扩展元数据')
    
    # 关系
    barns = relationship('Barn', back_populates='farm', lazy='dynamic')
    animal_locations = relationship('AnimalLocation', back_populates='farm', lazy='dynamic')
    
    def __repr__(self):
        return f"<Farm(id={self.id}, code='{self.code}', name='{self.name}')>"
    
    @property
    def capacity_usage(self) -> float:
        """计算存栏率"""
        if self.capacity and self.capacity > 0:
            return (self.current_stock / self.capacity) * 100
        return 0.0
    
    def update_stock_count(self, delta: int) -> None:
        """更新存栏量"""
        self.current_stock = max(0, self.current_stock + delta)


class Barn(BaseModel):
    """
    羊舍模型
    
    存储羊舍信息和环境配置
    """
    
    __tablename__ = 'barns'
    __table_args__ = (
        Index('ix_barns_farm_id', 'farm_id'),
        Index('ix_barns_code', 'code'),
        CheckConstraint("barn_type IN ('ram', 'ewe', 'lamb', 'fattening', 'quarantine', 'other')", 
                       name='ck_barn_type'),
        CheckConstraint("status IN ('active', 'inactive', 'maintenance', 'cleaning')", 
                       name='ck_barn_status'),
        {'comment': '羊舍信息表'}
    )
    
    # 基本信息
    farm_id = Column(Integer, ForeignKey('farms.id'), nullable=False, comment='所属羊场ID')
    code = Column(String(50), nullable=False, comment='羊舍编号')
    name = Column(String(100), nullable=False, comment='羊舍名称')
    barn_type = Column(String(50), nullable=False, comment='类型')
    
    # 容量
    capacity = Column(Integer, nullable=False, comment='设计容量')
    current_count = Column(Integer, default=0, nullable=False, comment='当前数量')
    
    # 面积
    area_sqm = Column(Numeric(10, 2), comment='面积(平方米)')
    length_m = Column(Numeric(8, 2), comment='长(米)')
    width_m = Column(Numeric(8, 2), comment='宽(米)')
    height_m = Column(Numeric(6, 2), comment='高(米)')
    
    # 设施
    ventilation_type = Column(String(50), comment='通风类型')
    heating_available = Column(Boolean, default=False, comment='是否有供暖')
    cooling_available = Column(Boolean, default=False, comment='是否有降温')
    auto_feeding = Column(Boolean, default=False, comment='是否自动饲喂')
    auto_watering = Column(Boolean, default=False, comment='是否自动饮水')
    
    # 环境参数目标
    target_temp_min = Column(Numeric(5, 2), comment='目标最低温度')
    target_temp_max = Column(Numeric(5, 2), comment='目标最高温度')
    target_humidity_min = Column(Numeric(5, 2), comment='目标最低湿度')
    target_humidity_max = Column(Numeric(5, 2), comment='目标最高湿度')
    
    # 状态
    status = Column(String(20), default='active', nullable=False, comment='状态')
    last_cleaning_date = Column(Date, comment='最近清洁日期')
    last_disinfection_date = Column(Date, comment='最近消毒日期')
    
    # 扩展信息
    metadata_ = Column('metadata', JSONB, comment='扩展元数据')
    
    # 关系
    farm = relationship('Farm', back_populates='barns')
    animal_locations = relationship('AnimalLocation', back_populates='barn', lazy='dynamic')
    
    def __repr__(self):
        return f"<Barn(id={self.id}, code='{self.code}', name='{self.name}')>"
    
    @property
    def capacity_usage(self) -> float:
        """计算使用率"""
        if self.capacity and self.capacity > 0:
            return (self.current_count / self.capacity) * 100
        return 0.0
    
    @property
    def is_full(self) -> bool:
        """判断是否已满"""
        return self.current_count >= self.capacity
    
    def update_count(self, delta: int) -> None:
        """更新数量"""
        self.current_count = max(0, self.current_count + delta)


class AnimalLocation(BaseModel):
    """
    动物位置记录模型
    
    记录动物在羊舍中的位置历史
    """
    
    __tablename__ = 'animal_locations'
    __table_args__ = (
        Index('ix_animal_locations_animal_id', 'animal_id'),
        Index('ix_animal_locations_barn_id', 'barn_id'),
        Index('ix_animal_locations_entry_date', 'entry_date'),
        Index('ix_animal_locations_current', 'animal_id', 'exit_date'),  # 查找当前位置
        {'comment': '动物位置记录表'}
    )
    
    # 关联
    animal_id = Column(Integer, ForeignKey('animals.id'), nullable=False, comment='动物ID')
    farm_id = Column(Integer, ForeignKey('farms.id'), nullable=False, comment='羊场ID')
    barn_id = Column(Integer, ForeignKey('barns.id'), nullable=False, comment='羊舍ID')
    
    # 位置详情
    pen_number = Column(String(50), comment='栏位号')
    pen_position = Column(String(50), comment='栏内位置')
    
    # 时间
    entry_date = Column(DateTime(timezone=True), nullable=False, comment='入舍时间')
    exit_date = Column(DateTime(timezone=True), comment='出舍时间')
    
    # 原因
    entry_reason = Column(String(100), comment='入舍原因')
    exit_reason = Column(String(100), comment='出舍原因')
    
    # 备注
    notes = Column(Text, comment='备注')
    
    # 关系
    farm = relationship('Farm', back_populates='animal_locations')
    barn = relationship('Barn', back_populates='animal_locations')
    
    def __repr__(self):
        return f"<AnimalLocation(id={self.id}, animal_id={self.animal_id}, barn_id={self.barn_id})>"
    
    @property
    def is_current(self) -> bool:
        """是否为当前位置"""
        return self.exit_date is None
    
    def close(self, exit_reason: str = None) -> None:
        """关闭位置记录"""
        from datetime import datetime
        self.exit_date = datetime.now()
        self.exit_reason = exit_reason

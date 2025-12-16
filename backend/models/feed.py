# ============================================================================
# 新星肉羊育种系统 - 饲料数据模型
# NovaBreed Sheep System - Feed Models
#
# 文件: feed.py
# 功能: 饲料类型、配方、计划、记录、库存ORM模型
# ============================================================================

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, 
    Numeric, Text, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseModel


class FeedType(BaseModel):
    """饲料类型模型"""
    
    __tablename__ = 'feed_types'
    __table_args__ = (
        Index('ix_feed_types_code', 'feed_code', unique=True),
        Index('ix_feed_types_category', 'category'),
        {'comment': '饲料类型表'}
    )
    
    feed_code = Column(String(50), unique=True, nullable=False, comment='饲料代码')
    name = Column(String(200), nullable=False, comment='饲料名称')
    category = Column(String(50), nullable=False, 
                     comment='类别: roughage/concentrate/supplement/premix')
    
    # 营养成分
    dry_matter = Column(Numeric(5, 2), comment='干物质(%)')
    crude_protein = Column(Numeric(5, 2), comment='粗蛋白(%)')
    crude_fiber = Column(Numeric(5, 2), comment='粗纤维(%)')
    crude_fat = Column(Numeric(5, 2), comment='粗脂肪(%)')
    calcium = Column(Numeric(5, 3), comment='钙(%)')
    phosphorus = Column(Numeric(5, 3), comment='磷(%)')
    metabolizable_energy = Column(Numeric(6, 2), comment='代谢能(MJ/kg)')
    
    # 价格和单位
    unit = Column(String(20), default='kg', comment='计量单位')
    unit_price = Column(Numeric(10, 2), comment='单价(元)')
    
    # 存储要求
    storage_conditions = Column(String(200), comment='存储条件')
    shelf_life_days = Column(Integer, comment='保质期(天)')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    def __repr__(self):
        return f"<FeedType(code='{self.feed_code}', name='{self.name}')>"


class FeedFormula(BaseModel):
    """饲料配方模型"""
    
    __tablename__ = 'feed_formulas'
    __table_args__ = (
        Index('ix_feed_formulas_organization_id', 'organization_id'),
        Index('ix_feed_formulas_target_animal_type', 'target_animal_type'),
        {'comment': '饲料配方表'}
    )
    
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, comment='机构ID')
    
    name = Column(String(200), nullable=False, comment='配方名称')
    formula_code = Column(String(50), comment='配方代码')
    description = Column(Text, comment='描述')
    
    # 适用对象
    target_animal_type = Column(String(50), nullable=False, 
                               comment='适用类型: ram/ewe/lamb/fattening/pregnant/lactating')
    target_weight_min = Column(Numeric(6, 2), comment='适用最小体重')
    target_weight_max = Column(Numeric(6, 2), comment='适用最大体重')
    target_age_min = Column(Integer, comment='适用最小日龄')
    target_age_max = Column(Integer, comment='适用最大日龄')
    
    # 配方成分 (JSONB)
    ingredients = Column(JSONB, nullable=False, comment='配方成分')
    """
    ingredients 结构:
    [
        {"feed_type_id": 1, "percentage": 50, "min_amount": 0.5, "max_amount": 1.0},
        {"feed_type_id": 2, "percentage": 30, ...}
    ]
    """
    
    # 营养指标
    total_crude_protein = Column(Numeric(5, 2), comment='总粗蛋白(%)')
    total_metabolizable_energy = Column(Numeric(6, 2), comment='总代谢能(MJ/kg)')
    
    # 饲喂量
    daily_amount_kg = Column(Numeric(6, 2), comment='日饲喂量(kg)')
    
    # 成本
    cost_per_kg = Column(Numeric(10, 2), comment='每公斤成本(元)')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    version = Column(Integer, default=1, comment='版本号')
    
    def __repr__(self):
        return f"<FeedFormula(id={self.id}, name='{self.name}')>"


class FeedingPlan(BaseModel):
    """饲喂计划模型"""
    
    __tablename__ = 'feeding_plans'
    __table_args__ = (
        Index('ix_feeding_plans_barn_id', 'barn_id'),
        Index('ix_feeding_plans_formula_id', 'formula_id'),
        {'comment': '饲喂计划表'}
    )
    
    barn_id = Column(Integer, ForeignKey('barns.id'), nullable=False, comment='羊舍ID')
    formula_id = Column(Integer, ForeignKey('feed_formulas.id'), nullable=False, comment='配方ID')
    
    name = Column(String(200), nullable=False, comment='计划名称')
    
    # 时间范围
    start_date = Column(Date, nullable=False, comment='开始日期')
    end_date = Column(Date, comment='结束日期')
    
    # 饲喂次数和时间
    feeds_per_day = Column(Integer, default=2, comment='每天饲喂次数')
    feeding_times = Column(JSONB, comment='饲喂时间点')  # ["07:00", "17:00"]
    
    # 饲喂量
    amount_per_animal = Column(Numeric(6, 2), comment='每头饲喂量(kg)')
    target_animal_count = Column(Integer, comment='目标头数')
    
    # 状态
    status = Column(String(20), default='active', comment='状态: draft/active/completed/cancelled')
    
    # 关系
    formula = relationship('FeedFormula')


class FeedingRecord(BaseModel):
    """饲喂记录模型"""
    
    __tablename__ = 'feeding_records'
    __table_args__ = (
        Index('ix_feeding_records_barn_id', 'barn_id'),
        Index('ix_feeding_records_feeding_date', 'feeding_date'),
        {'comment': '饲喂记录表'}
    )
    
    plan_id = Column(Integer, ForeignKey('feeding_plans.id'), comment='计划ID')
    barn_id = Column(Integer, ForeignKey('barns.id'), nullable=False, comment='羊舍ID')
    formula_id = Column(Integer, ForeignKey('feed_formulas.id'), comment='配方ID')
    
    feeding_date = Column(Date, nullable=False, comment='饲喂日期')
    feeding_time = Column(DateTime(timezone=True), nullable=False, comment='饲喂时间')
    feeding_number = Column(Integer, comment='当天第几次饲喂')
    
    # 饲喂量
    animal_count = Column(Integer, nullable=False, comment='饲喂头数')
    planned_amount = Column(Numeric(8, 2), comment='计划量(kg)')
    actual_amount = Column(Numeric(8, 2), nullable=False, comment='实际量(kg)')
    
    # 采食情况
    consumption_rate = Column(Numeric(5, 2), comment='采食率(%)')
    leftover = Column(Numeric(6, 2), comment='剩余量(kg)')
    
    # 人员
    feeder = Column(String(100), comment='饲喂员')
    notes = Column(Text, comment='备注')


class FeedInventory(BaseModel):
    """饲料库存模型"""
    
    __tablename__ = 'feed_inventory'
    __table_args__ = (
        Index('ix_feed_inventory_farm_id', 'farm_id'),
        Index('ix_feed_inventory_feed_type_id', 'feed_type_id'),
        {'comment': '饲料库存表'}
    )
    
    farm_id = Column(Integer, ForeignKey('farms.id'), nullable=False, comment='羊场ID')
    feed_type_id = Column(Integer, ForeignKey('feed_types.id'), nullable=False, comment='饲料类型ID')
    
    # 当前库存
    current_quantity = Column(Numeric(10, 2), default=0, nullable=False, comment='当前库存(kg)')
    
    # 库存预警
    min_quantity = Column(Numeric(10, 2), comment='最低库存预警')
    max_quantity = Column(Numeric(10, 2), comment='最高库存限制')
    
    # 存储位置
    storage_location = Column(String(100), comment='存储位置')
    
    # 最近入库
    last_purchase_date = Column(Date, comment='最近入库日期')
    last_purchase_quantity = Column(Numeric(10, 2), comment='最近入库数量')
    last_purchase_price = Column(Numeric(10, 2), comment='最近入库单价')
    
    # 关系
    feed_type = relationship('FeedType')
    
    @property
    def is_low_stock(self) -> bool:
        """是否低库存"""
        if self.min_quantity:
            return self.current_quantity <= self.min_quantity
        return False

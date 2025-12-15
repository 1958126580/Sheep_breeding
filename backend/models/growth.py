# ============================================================================
# 国际顶级肉羊育种系统 - 生长发育数据模型
# International Top-tier Sheep Breeding System - Growth Models
#
# 文件: growth.py
# 功能: 生长记录ORM模型
# ============================================================================

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, 
    Numeric, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseModel


class GrowthRecord(BaseModel):
    """
    生长测定记录模型
    
    记录动物的体重、体尺测量数据
    """
    
    __tablename__ = 'growth_records'
    __table_args__ = (
        Index('ix_growth_records_animal_id', 'animal_id'),
        Index('ix_growth_records_measurement_date', 'measurement_date'),
        Index('ix_growth_records_measurement_type', 'measurement_type'),
        Index('ix_growth_records_animal_date', 'animal_id', 'measurement_date'),
        {'comment': '生长测定记录表'}
    )
    
    # 关联
    animal_id = Column(Integer, ForeignKey('animals.id'), nullable=False, comment='动物ID')
    
    # 测量信息
    measurement_date = Column(Date, nullable=False, comment='测量日期')
    measurement_type = Column(String(50), nullable=False, 
                             comment='类型: routine/weaning/yearling/selection')
    age_days = Column(Integer, comment='测量时日龄')
    
    # 体重
    body_weight = Column(Numeric(8, 2), nullable=False, comment='体重(kg)')
    weight_source = Column(String(20), comment='来源: manual/auto_scale')
    device_id = Column(Integer, comment='称重设备ID')
    
    # 体尺测量
    body_length = Column(Numeric(6, 2), comment='体长(cm)')
    body_height = Column(Numeric(6, 2), comment='体高(cm)')
    chest_girth = Column(Numeric(6, 2), comment='胸围(cm)')
    chest_width = Column(Numeric(6, 2), comment='胸宽(cm)')
    chest_depth = Column(Numeric(6, 2), comment='胸深(cm)')
    hip_width = Column(Numeric(6, 2), comment='臀宽(cm)')
    cannon_circumference = Column(Numeric(6, 2), comment='管围(cm)')
    
    # 体况评分
    body_condition_score = Column(Numeric(3, 1), comment='体况评分(1-5)')
    muscle_score = Column(Integer, comment='肌肉评分')
    fat_score = Column(Integer, comment='脂肪评分')
    
    # 计算指标
    average_daily_gain = Column(Numeric(6, 3), comment='日增重(kg/d)')
    days_since_last_measurement = Column(Integer, comment='距上次测量天数')
    
    # 人员和设备
    measured_by = Column(String(100), comment='测量人员')
    
    # 备注
    notes = Column(Text, comment='备注')
    
    # 原始数据(用于质控)
    raw_data = Column(JSONB, comment='原始测量数据')
    
    def __repr__(self):
        return f"<GrowthRecord(id={self.id}, animal_id={self.animal_id}, weight={self.body_weight})>"
    
    @classmethod
    def calculate_adg(cls, weight_before: float, weight_after: float, days: int) -> float:
        """计算日增重"""
        if days > 0:
            return (weight_after - weight_before) / days
        return 0.0

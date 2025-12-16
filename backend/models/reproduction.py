# ============================================================================
# 新星肉羊育种系统 - 繁殖数据模型
# NovaBreed Sheep System - Reproduction Models
#
# 文件: reproduction.py
# 功能: 发情、配种、妊娠、产羔、断奶ORM模型
# ============================================================================

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, 
    Numeric, Text, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseModel


class EstrusRecord(BaseModel):
    """发情记录模型"""
    
    __tablename__ = 'estrus_records'
    __table_args__ = (
        Index('ix_estrus_records_animal_id', 'animal_id'),
        Index('ix_estrus_records_observation_date', 'observation_date'),
        {'comment': '发情记录表'}
    )
    
    animal_id = Column(Integer, ForeignKey('animals.id'), nullable=False, comment='动物ID(母羊)')
    
    observation_date = Column(DateTime(timezone=True), nullable=False, comment='观察时间')
    estrus_signs = Column(JSONB, comment='发情症状')
    estrus_score = Column(Integer, comment='发情评分(1-5)')
    
    # AI辅助检测
    ai_detected = Column(Boolean, default=False, comment='是否AI检测')
    ai_confidence = Column(Numeric(5, 2), comment='AI置信度')
    
    # 处理
    action_taken = Column(String(50), comment='处理措施: bred/recorded/skipped')
    observer = Column(String(100), comment='观察员')
    notes = Column(Text, comment='备注')


class BreedingRecord(BaseModel):
    """配种记录模型"""
    
    __tablename__ = 'breeding_records'
    __table_args__ = (
        Index('ix_breeding_records_dam_id', 'dam_id'),
        Index('ix_breeding_records_sire_id', 'sire_id'),
        Index('ix_breeding_records_breeding_date', 'breeding_date'),
        Index('ix_breeding_records_status', 'status'),
        {'comment': '配种记录表'}
    )
    
    # 配种双方
    dam_id = Column(Integer, ForeignKey('animals.id'), nullable=False, comment='母本ID')
    sire_id = Column(Integer, ForeignKey('animals.id'), comment='父本ID')
    
    # 配种信息
    breeding_date = Column(DateTime(timezone=True), nullable=False, comment='配种时间')
    breeding_method = Column(String(50), nullable=False, comment='方式: natural/ai/et')
    
    # AI配种详情
    semen_batch = Column(String(100), comment='精液批号')
    semen_dose = Column(Numeric(5, 2), comment='精液剂量(ml)')
    inseminator = Column(String(100), comment='配种员')
    
    # 预期
    expected_lambing_date = Column(Date, comment='预产期')
    gestation_days = Column(Integer, default=150, comment='妊娠天数')
    
    # 结果
    status = Column(String(20), default='pending', nullable=False, 
                   comment='状态: pending/confirmed/failed')
    
    # 关系
    dam = relationship('Animal', foreign_keys=[dam_id])
    sire = relationship('Animal', foreign_keys=[sire_id])


class PregnancyRecord(BaseModel):
    """妊娠检查记录模型"""
    
    __tablename__ = 'pregnancy_records'
    __table_args__ = (
        Index('ix_pregnancy_records_breeding_id', 'breeding_id'),
        Index('ix_pregnancy_records_animal_id', 'animal_id'),
        Index('ix_pregnancy_records_check_date', 'check_date'),
        {'comment': '妊娠检查记录表'}
    )
    
    breeding_id = Column(Integer, ForeignKey('breeding_records.id'), comment='配种记录ID')
    animal_id = Column(Integer, ForeignKey('animals.id'), nullable=False, comment='动物ID')
    
    check_date = Column(Date, nullable=False, comment='检查日期')
    check_method = Column(String(50), nullable=False, comment='方法: ultrasound/palpation/blood')
    days_post_breeding = Column(Integer, comment='配种后天数')
    
    result = Column(String(20), nullable=False, comment='结果: positive/negative/uncertain')
    fetus_count = Column(Integer, comment='胎儿数')
    fetus_viability = Column(String(50), comment='胎儿活力评估')
    
    examiner = Column(String(100), comment='检查人员')
    notes = Column(Text, comment='备注')
    ultrasound_images = Column(JSONB, comment='超声图像')


class LambingRecord(BaseModel):
    """产羔记录模型"""
    
    __tablename__ = 'lambing_records'
    __table_args__ = (
        Index('ix_lambing_records_dam_id', 'dam_id'),
        Index('ix_lambing_records_breeding_id', 'breeding_id'),
        Index('ix_lambing_records_lambing_date', 'lambing_date'),
        {'comment': '产羔记录表'}
    )
    
    breeding_id = Column(Integer, ForeignKey('breeding_records.id'), comment='配种记录ID')
    dam_id = Column(Integer, ForeignKey('animals.id'), nullable=False, comment='母羊ID')
    
    # 产羔信息
    lambing_date = Column(DateTime(timezone=True), nullable=False, comment='产羔时间')
    gestation_length = Column(Integer, comment='实际妊娠天数')
    
    # 产羔结果
    litter_size = Column(Integer, nullable=False, comment='产羔总数')
    born_alive = Column(Integer, nullable=False, comment='活羔数')
    born_dead = Column(Integer, default=0, comment='死羔数')
    
    # 产羔难易度
    lambing_ease = Column(Integer, comment='难易度(1-5)')
    assistance = Column(String(50), comment='助产情况: none/minor/major/cesarean')
    
    # 母羊状态
    dam_condition = Column(String(50), comment='母羊产后状态')
    placenta_expelled = Column(Boolean, comment='胎盘是否排出')
    
    # 人员
    attendant = Column(String(100), comment='接产人员')
    notes = Column(Text, comment='备注')
    
    # 羔羊详情(JSONB存储每只羔羊信息)
    lamb_details = Column(JSONB, comment='羔羊详情')
    """
    lamb_details 结构:
    [
        {
            "lamb_id": 123,  # 创建后填入
            "sex": "male",
            "birth_weight": 3.5,
            "vigor_score": 4,
            "coat_color": "white",
            "notes": ""
        }
    ]
    """


class WeaningRecord(BaseModel):
    """断奶记录模型"""
    
    __tablename__ = 'weaning_records'
    __table_args__ = (
        Index('ix_weaning_records_animal_id', 'animal_id'),
        Index('ix_weaning_records_dam_id', 'dam_id'),
        Index('ix_weaning_records_weaning_date', 'weaning_date'),
        {'comment': '断奶记录表'}
    )
    
    animal_id = Column(Integer, ForeignKey('animals.id'), nullable=False, comment='羔羊ID')
    dam_id = Column(Integer, ForeignKey('animals.id'), nullable=False, comment='母羊ID')
    lambing_id = Column(Integer, ForeignKey('lambing_records.id'), comment='产羔记录ID')
    
    weaning_date = Column(Date, nullable=False, comment='断奶日期')
    weaning_age_days = Column(Integer, comment='断奶日龄')
    weaning_weight = Column(Numeric(8, 2), comment='断奶体重(kg)')
    
    # 计算指标
    pre_weaning_adg = Column(Numeric(6, 3), comment='断奶前日增重(kg/d)')
    
    # 断奶后去向
    destination = Column(String(50), comment='去向: fattening/replacement/sale')
    destination_barn_id = Column(Integer, ForeignKey('barns.id'), comment='目标羊舍ID')
    
    notes = Column(Text, comment='备注')

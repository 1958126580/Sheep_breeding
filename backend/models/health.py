# ============================================================================
# 国际顶级肉羊育种系统 - 健康数据模型
# International Top-tier Sheep Breeding System - Health Models
#
# 文件: health.py
# 功能: 疾病、健康记录、疫苗、驱虫ORM模型
# ============================================================================

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, 
    Numeric, Text, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

from .base import BaseModel


class Disease(BaseModel):
    """
    疾病字典模型
    """
    
    __tablename__ = 'diseases'
    __table_args__ = (
        Index('ix_diseases_code', 'disease_code', unique=True),
        Index('ix_diseases_category', 'category'),
        {'comment': '疾病字典表'}
    )
    
    disease_code = Column(String(50), unique=True, nullable=False, comment='疾病代码')
    name = Column(String(200), nullable=False, comment='疾病名称')
    name_en = Column(String(200), comment='英文名称')
    category = Column(String(50), nullable=False, comment='类别: infectious/parasitic/metabolic/other')
    
    description = Column(Text, comment='描述')
    symptoms = Column(Text, comment='症状描述')
    treatment_standard = Column(Text, comment='标准治疗方案')
    prevention_measures = Column(Text, comment='预防措施')
    
    is_reportable = Column(Boolean, default=False, comment='是否需报告')
    quarantine_days = Column(Integer, comment='隔离天数')
    
    metadata_ = Column('metadata', JSONB, comment='扩展元数据')
    
    def __repr__(self):
        return f"<Disease(code='{self.disease_code}', name='{self.name}')>"


class HealthRecord(BaseModel):
    """
    健康检查记录模型
    """
    
    __tablename__ = 'health_records'
    __table_args__ = (
        Index('ix_health_records_animal_id', 'animal_id'),
        Index('ix_health_records_check_date', 'check_date'),
        Index('ix_health_records_check_type', 'check_type'),
        Index('ix_health_records_disease_id', 'disease_id'),
        {'comment': '健康检查记录表'}
    )
    
    # 关联
    animal_id = Column(Integer, ForeignKey('animals.id'), nullable=False, comment='动物ID')
    disease_id = Column(Integer, ForeignKey('diseases.id'), comment='疾病ID')
    
    # 检查信息
    check_date = Column(Date, nullable=False, comment='检查日期')
    check_type = Column(String(50), nullable=False, comment='检查类型: routine/diagnosis/follow_up')
    
    # 体征数据
    body_temperature = Column(Numeric(4, 1), comment='体温(℃)')
    heart_rate = Column(Integer, comment='心率(次/分)')
    respiratory_rate = Column(Integer, comment='呼吸率(次/分)')
    body_weight = Column(Numeric(8, 2), comment='体重(kg)')
    body_condition_score = Column(Integer, comment='体况评分(1-5)')
    
    # 症状和诊断
    symptoms = Column(Text, comment='症状描述')
    diagnosis = Column(String(500), comment='诊断结果')
    severity = Column(String(20), comment='严重程度: mild/moderate/severe')
    
    # 治疗
    treatment = Column(Text, comment='治疗方案')
    medications = Column(JSONB, comment='用药记录')
    treatment_cost = Column(Numeric(10, 2), comment='治疗费用')
    
    # 后续
    follow_up_required = Column(Boolean, default=False, comment='是否需要复查')
    follow_up_date = Column(Date, comment='复查日期')
    prognosis = Column(String(200), comment='预后评估')
    
    # 人员
    veterinarian = Column(String(100), comment='兽医姓名')
    veterinarian_license = Column(String(50), comment='兽医执照号')
    
    # 备注
    notes = Column(Text, comment='备注')
    attachments = Column(JSONB, comment='附件(图片等)')
    
    # 关系
    disease = relationship('Disease')
    
    def __repr__(self):
        return f"<HealthRecord(id={self.id}, animal_id={self.animal_id}, date={self.check_date})>"


class VaccineType(BaseModel):
    """
    疫苗类型模型
    """
    
    __tablename__ = 'vaccine_types'
    __table_args__ = (
        Index('ix_vaccine_types_code', 'vaccine_code', unique=True),
        {'comment': '疫苗类型表'}
    )
    
    vaccine_code = Column(String(50), unique=True, nullable=False, comment='疫苗代码')
    name = Column(String(200), nullable=False, comment='疫苗名称')
    manufacturer = Column(String(200), comment='生产厂家')
    
    target_diseases = Column(ARRAY(String), comment='目标疾病')
    dosage = Column(String(100), comment='剂量')
    injection_route = Column(String(50), comment='接种途径')
    
    interval_days = Column(Integer, comment='接种间隔(天)')
    booster_required = Column(Boolean, default=False, comment='是否需要加强针')
    booster_interval_days = Column(Integer, comment='加强针间隔(天)')
    
    storage_temp_min = Column(Numeric(5, 2), comment='存储最低温度')
    storage_temp_max = Column(Numeric(5, 2), comment='存储最高温度')
    shelf_life_months = Column(Integer, comment='保质期(月)')
    
    contraindications = Column(Text, comment='禁忌症')
    side_effects = Column(Text, comment='副作用')
    
    is_mandatory = Column(Boolean, default=False, comment='是否强制接种')
    
    def __repr__(self):
        return f"<VaccineType(code='{self.vaccine_code}', name='{self.name}')>"


class VaccinationRecord(BaseModel):
    """
    疫苗接种记录模型
    """
    
    __tablename__ = 'vaccination_records'
    __table_args__ = (
        Index('ix_vaccination_records_animal_id', 'animal_id'),
        Index('ix_vaccination_records_vaccine_type_id', 'vaccine_type_id'),
        Index('ix_vaccination_records_vaccination_date', 'vaccination_date'),
        Index('ix_vaccination_records_next_date', 'next_vaccination_date'),
        {'comment': '疫苗接种记录表'}
    )
    
    # 关联
    animal_id = Column(Integer, ForeignKey('animals.id'), nullable=False, comment='动物ID')
    vaccine_type_id = Column(Integer, ForeignKey('vaccine_types.id'), nullable=False, comment='疫苗类型ID')
    
    # 接种信息
    vaccination_date = Column(Date, nullable=False, comment='接种日期')
    batch_number = Column(String(100), comment='疫苗批号')
    dosage = Column(String(50), comment='剂量')
    injection_site = Column(String(50), comment='接种部位')
    
    # 疫苗信息
    expiry_date = Column(Date, comment='疫苗有效期')
    
    # 下次接种
    next_vaccination_date = Column(Date, comment='下次接种日期')
    is_booster = Column(Boolean, default=False, comment='是否为加强针')
    
    # 反应
    adverse_reaction = Column(Boolean, default=False, comment='是否有不良反应')
    reaction_description = Column(Text, comment='反应描述')
    
    # 人员
    administered_by = Column(String(100), comment='接种人员')
    
    # 关系
    vaccine_type = relationship('VaccineType')
    
    def __repr__(self):
        return f"<VaccinationRecord(id={self.id}, animal_id={self.animal_id})>"


class DewormingRecord(BaseModel):
    """
    驱虫记录模型
    """
    
    __tablename__ = 'deworming_records'
    __table_args__ = (
        Index('ix_deworming_records_animal_id', 'animal_id'),
        Index('ix_deworming_records_deworming_date', 'deworming_date'),
        {'comment': '驱虫记录表'}
    )
    
    # 关联 (可以是单只或批量)
    animal_id = Column(Integer, ForeignKey('animals.id'), comment='动物ID(单只)')
    barn_id = Column(Integer, ForeignKey('barns.id'), comment='羊舍ID(批量)')
    
    # 驱虫信息
    deworming_date = Column(Date, nullable=False, comment='驱虫日期')
    deworming_type = Column(String(50), nullable=False, comment='类型: internal/external/both')
    
    # 药物信息
    drug_name = Column(String(200), nullable=False, comment='药物名称')
    drug_batch = Column(String(100), comment='药物批号')
    dosage = Column(String(100), comment='剂量')
    administration_route = Column(String(50), comment='给药途径')
    
    # 批量信息
    animal_count = Column(Integer, comment='驱虫头数')
    
    # 下次驱虫
    next_deworming_date = Column(Date, comment='下次驱虫日期')
    
    # 效果
    fecal_egg_count_before = Column(Integer, comment='驱虫前粪便虫卵数')
    fecal_egg_count_after = Column(Integer, comment='驱虫后粪便虫卵数')
    
    # 人员
    administered_by = Column(String(100), comment='操作人员')
    
    # 备注
    notes = Column(Text, comment='备注')
    
    def __repr__(self):
        return f"<DewormingRecord(id={self.id}, date={self.deworming_date})>"

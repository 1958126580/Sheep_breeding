# ============================================================================
# 国际顶级肉羊育种系统 - 动物数据模型
# International Top-tier Sheep Breeding System - Animal Models
#
# 文件: animal.py
# 功能: 动物、系谱ORM模型
# ============================================================================

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, 
    Numeric, Text, ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR

from .base import BaseModel


class Animal(BaseModel):
    """
    动物模型
    
    存储羊只基本信息和档案数据
    """
    
    __tablename__ = 'animals'
    __table_args__ = (
        Index('ix_animals_organization_id', 'organization_id'),
        Index('ix_animals_animal_code', 'animal_code'),
        Index('ix_animals_electronic_id', 'electronic_id'),
        Index('ix_animals_breed', 'breed'),
        Index('ix_animals_sex', 'sex'),
        Index('ix_animals_birth_date', 'birth_date'),
        Index('ix_animals_status', 'status'),
        Index('ix_animals_search', 'search_vector', postgresql_using='gin'),
        UniqueConstraint('organization_id', 'animal_code', name='uq_animal_code_per_org'),
        CheckConstraint("sex IN ('male', 'female')", name='ck_animal_sex'),
        CheckConstraint("status IN ('active', 'sold', 'deceased', 'culled', 'transferred')", 
                       name='ck_animal_status'),
        {'comment': '动物信息表'}
    )
    
    # 归属
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, comment='所属机构ID')
    
    # 标识信息
    animal_code = Column(String(50), nullable=False, comment='动物编号')
    electronic_id = Column(String(50), unique=True, comment='电子标签ID')
    ear_tag_left = Column(String(50), comment='左耳号')
    ear_tag_right = Column(String(50), comment='右耳号')
    tattoo_number = Column(String(50), comment='纹身号')
    name = Column(String(100), comment='名称/昵称')
    
    # 品种信息
    breed = Column(String(100), nullable=False, comment='品种')
    breed_code = Column(String(20), comment='品种代码')
    breed_percentage = Column(JSONB, comment='品种组成百分比')
    
    # 出生信息
    birth_date = Column(Date, nullable=False, comment='出生日期')
    birth_weight = Column(Numeric(8, 2), comment='出生体重(kg)')
    birth_type = Column(String(20), comment='出生类型: single/twin/triplet')
    birth_order = Column(Integer, comment='出生顺序')
    birth_ease = Column(Integer, comment='产羔难易度(1-5)')
    
    # 性别和繁殖状态
    sex = Column(String(10), nullable=False, comment='性别')
    is_breeding_animal = Column(Boolean, default=False, comment='是否种用')
    breeding_status = Column(String(50), comment='繁殖状态')
    
    # 系谱
    sire_id = Column(Integer, ForeignKey('animals.id'), comment='父本ID')
    dam_id = Column(Integer, ForeignKey('animals.id'), comment='母本ID')
    generation = Column(Integer, comment='世代数')
    
    # 遗传信息
    inbreeding_coefficient = Column(Numeric(8, 6), comment='近交系数')
    has_genotype = Column(Boolean, default=False, comment='是否有基因型数据')
    genotype_file_id = Column(Integer, comment='基因型文件ID')
    
    # 当前状态
    status = Column(String(20), default='active', nullable=False, comment='状态')
    current_farm_id = Column(Integer, ForeignKey('farms.id'), comment='当前羊场ID')
    current_barn_id = Column(Integer, ForeignKey('barns.id'), comment='当前羊舍ID')
    current_weight = Column(Numeric(8, 2), comment='当前体重(kg)')
    last_weight_date = Column(Date, comment='最近称重日期')
    
    # 死亡/淘汰信息
    death_date = Column(Date, comment='死亡/淘汰日期')
    death_cause = Column(String(200), comment='死亡/淘汰原因')
    sale_date = Column(Date, comment='销售日期')
    sale_price = Column(Numeric(10, 2), comment='销售价格')
    
    # 备注
    notes = Column(Text, comment='备注')
    
    # 全文搜索向量
    search_vector = Column(TSVECTOR, comment='搜索向量')
    
    # 扩展信息
    metadata_ = Column('metadata', JSONB, comment='扩展元数据')
    
    # 自引用关系
    sire = relationship('Animal', remote_side='Animal.id', foreign_keys=[sire_id], 
                        backref='progeny_as_sire')
    dam = relationship('Animal', remote_side='Animal.id', foreign_keys=[dam_id], 
                       backref='progeny_as_dam')
    
    # 关系
    current_farm = relationship('Farm', foreign_keys=[current_farm_id])
    current_barn = relationship('Barn', foreign_keys=[current_barn_id])
    
    def __repr__(self):
        return f"<Animal(id={self.id}, code='{self.animal_code}', breed='{self.breed}')>"
    
    @property
    def age_days(self) -> int:
        """计算日龄"""
        from datetime import date
        if self.birth_date:
            return (date.today() - self.birth_date).days
        return 0
    
    @property
    def age_months(self) -> float:
        """计算月龄"""
        return self.age_days / 30.44
    
    @property
    def is_adult(self) -> bool:
        """是否成年 (>12月龄)"""
        return self.age_months >= 12


class Pedigree(BaseModel):
    """
    系谱扩展模型
    
    存储详细的系谱信息，支持多代祖先
    """
    
    __tablename__ = 'pedigree_extended'
    __table_args__ = (
        Index('ix_pedigree_animal_id', 'animal_id'),
        Index('ix_pedigree_ancestor_id', 'ancestor_id'),
        {'comment': '系谱扩展信息表'}
    )
    
    # 关联
    animal_id = Column(Integer, ForeignKey('animals.id'), nullable=False, comment='动物ID')
    ancestor_id = Column(Integer, ForeignKey('animals.id'), nullable=False, comment='祖先ID')
    
    # 关系类型
    relationship_type = Column(String(20), nullable=False, comment='关系类型: sire/dam/grand_sire/grand_dam等')
    generation_distance = Column(Integer, nullable=False, comment='世代距离')
    path_code = Column(String(50), comment='路径编码')
    
    # 遗传贡献
    genetic_contribution = Column(Numeric(8, 6), comment='遗传贡献率')
    
    # 关系
    animal = relationship('Animal', foreign_keys=[animal_id])
    ancestor = relationship('Animal', foreign_keys=[ancestor_id])
    
    def __repr__(self):
        return f"<Pedigree(animal={self.animal_id}, ancestor={self.ancestor_id}, type='{self.relationship_type}')>"

# ============================================================================
# 国际顶级肉羊育种系统 - 区块链数据模型
# International Top-tier Sheep Breeding System - Blockchain Database Models
# ============================================================================

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
import enum

from database import Base
from .base import BaseModel, TimestampMixin

class BlockchainNetwork(str, enum.Enum):
    """区块链网络"""
    PRIVATE = "private"           # 私有链
    CONSORTIUM = "consortium"     # 联盟链
    PUBLIC = "public"             # 公有链

class RecordType(str, enum.Enum):
    """存证记录类型"""
    ANIMAL_REGISTER = "animal_register"        # 动物登记
    BREEDING_VALUE = "breeding_value"          # 育种值
    PEDIGREE = "pedigree"                      # 系谱信息
    GENOTYPE = "genotype"                      # 基因型
    HEALTH_RECORD = "health_record"            # 健康记录
    OWNERSHIP_TRANSFER = "ownership_transfer"  # 所有权转移
    CERTIFICATE = "certificate"                # 证书

class VerificationStatus(str, enum.Enum):
    """验证状态"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"

class BlockchainRecord(BaseModel, TimestampMixin):
    """
    区块链存证记录模型
    
    存储上链数据的本地副本和交易哈希，用于快速查询和验证
    """
    __tablename__ = "blockchain_records"

    tx_hash = Column(String(100), index=True, nullable=False, comment="交易哈希")
    block_number = Column(Integer, index=True, comment="区块高度")
    record_type = Column(SAEnum(RecordType), index=True, nullable=False, comment="记录类型")
    animal_id = Column(Integer, ForeignKey("animals.id"), index=True, nullable=True, comment="关联动物ID")
    data_hash = Column(String(100), nullable=False, comment="数据哈希")
    data_content = Column(JSON, comment="上链数据内容(JSON)")
    network = Column(SAEnum(BlockchainNetwork), default=BlockchainNetwork.CONSORTIUM, comment="区块链网络")
    verified = Column(Boolean, default=False, comment="是否验证通过")

    # 关联
    # animal = relationship("Animal", back_populates="blockchain_records")

class AnimalCertificate(BaseModel, TimestampMixin):
    """
    电子证书模型
    """
    __tablename__ = "animal_certificates"

    certificate_id = Column(String(50), unique=True, index=True, nullable=False, comment="证书编号")
    animal_id = Column(Integer, ForeignKey("animals.id"), index=True, nullable=False, comment="动物ID")
    certificate_type = Column(String(50), nullable=False, comment="证书类型")
    issue_date = Column(DateTime, nullable=False, comment="签发日期")
    expiry_date = Column(DateTime, nullable=True, comment="过期日期")
    issuer = Column(String(100), nullable=False, comment="发证机构")
    tx_hash = Column(String(100), nullable=False, comment="交易哈希")
    status = Column(SAEnum(VerificationStatus), default=VerificationStatus.VERIFIED, comment="状态")
    
    metadata_content = Column(JSON, comment="证书元数据")

    # 关联
    # animal = relationship("Animal", back_populates="certificates")

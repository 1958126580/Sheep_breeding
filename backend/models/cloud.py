# ============================================================================
# 国际顶级肉羊育种系统 - 云端数据交换模型
# International Top-tier Sheep Breeding System - Cloud Data Exchange Models
# ============================================================================

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, JSON, Boolean, Date, Float
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel, TimestampMixin

class SyncDirection(str, enum.Enum):
    UPLOAD = "upload"
    DOWNLOAD = "download"
    BIDIRECTIONAL = "bidirectional"

class DataCategory(str, enum.Enum):
    ANIMALS = "animals"
    PEDIGREE = "pedigree"
    PHENOTYPES = "phenotypes"
    GENOTYPES = "genotypes"
    BREEDING_VALUES = "breeding_values"
    ALL = "all"

class SyncStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class SharePermission(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class SyncTask(BaseModel, TimestampMixin):
    """
    同步任务模型
    """
    __tablename__ = "sync_tasks"

    organization_id = Column(Integer, nullable=False, comment="机构ID")
    direction = Column(SAEnum(SyncDirection), nullable=False, comment="同步方向")
    categories = Column(JSON, nullable=False, comment="同步类别列表")
    status = Column(SAEnum(SyncStatus), default=SyncStatus.PENDING, comment="任务状态")
    
    progress_percent = Column(Integer, default=0, comment="进度百分比")
    records_synced = Column(Integer, default=0, comment="已同步记录数")
    records_total = Column(Integer, default=0, comment="总记录数")
    
    started_at = Column(DateTime, nullable=True, comment="开始时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    error_message = Column(String(500), nullable=True, comment="错误信息")

class ShareAgreement(BaseModel, TimestampMixin):
    """
    数据共享协议模型
    """
    __tablename__ = "share_agreements"

    provider_org_id = Column(Integer, nullable=False, comment="提供方机构ID")
    provider_org_name = Column(String(100), nullable=False, comment="提供方机构名称")
    consumer_org_id = Column(Integer, nullable=False, comment="使用方机构ID")
    consumer_org_name = Column(String(100), nullable=False, comment="使用方机构名称")
    
    data_categories = Column(JSON, nullable=False, comment="共享数据类别")
    permission = Column(SAEnum(SharePermission), default=SharePermission.READ, comment="权限")
    
    start_date = Column(Date, nullable=False, comment="生效日期")
    end_date = Column(Date, nullable=True, comment="失效日期")
    is_active = Column(Boolean, default=True, comment="是否激活")
    terms = Column(String(2000), nullable=True, comment="协议条款")

class ImportJob(BaseModel, TimestampMixin):
    """数据导入任务"""
    __tablename__ = "import_jobs"
    
    file_name = Column(String(255), nullable=False)
    data_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    records_imported = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_log = Column(String(2000), nullable=True)
    completed_at = Column(DateTime, nullable=True)

class ExportJob(BaseModel, TimestampMixin):
    """数据导出任务"""
    __tablename__ = "export_jobs"
    
    data_type = Column(String(50), nullable=False)
    format = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    record_count = Column(Integer, default=0)
    file_url = Column(String(255), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

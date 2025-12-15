# ============================================================================
# 国际顶级肉羊育种系统 - 数据模型基类
# International Top-tier Sheep Breeding System - Base Models
#
# 文件: base.py
# 功能: SQLAlchemy模型基类和混入类
# ============================================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from typing import Optional

from database import Base


class TimestampMixin:
    """
    时间戳混入类
    
    自动添加创建时间和更新时间字段
    """
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )


class SoftDeleteMixin:
    """
    软删除混入类
    
    提供软删除功能，记录删除时间和删除者
    """
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="删除时间"
    )
    
    deleted_by = Column(
        Integer,
        nullable=True,
        comment="删除者ID"
    )
    
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已删除"
    )
    
    def soft_delete(self, user_id: Optional[int] = None) -> None:
        """执行软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.now()
        self.deleted_by = user_id
    
    def restore(self) -> None:
        """恢复软删除"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None


class AuditMixin:
    """
    审计混入类
    
    记录创建者和更新者
    """
    
    created_by = Column(
        Integer,
        nullable=True,
        comment="创建者ID"
    )
    
    updated_by = Column(
        Integer,
        nullable=True,
        comment="更新者ID"
    )


class BaseModel(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    模型基类
    
    所有业务模型应继承此类
    """
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"

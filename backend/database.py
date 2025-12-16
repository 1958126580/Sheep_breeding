# ============================================================================
# 新星肉羊育种系统 - 数据库连接
# NovaBreed Sheep System - Database Connection
#
# 文件: database.py
# 功能: 数据库连接和会话管理
# ============================================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# 数据库引擎配置
# Database Engine Configuration
# ============================================================================

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # 连接池预检查
    echo=settings.DEBUG,  # SQL语句日志
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建基类
Base = declarative_base()

# ============================================================================
# 依赖注入函数
# Dependency Injection Functions
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    用于FastAPI依赖注入
    
    使用示例:
    ```python
    @app.get("/items")
    def read_items(db: Session = Depends(get_db)):
        items = db.query(Item).all()
        return items
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# 数据库初始化
# Database Initialization
# ============================================================================

def init_db():
    """
    初始化数据库
    
    创建所有表
    """
    logger.info("初始化数据库...")
    Base.metadata.create_all(bind=engine)
    logger.info("数据库初始化完成")

def drop_db():
    """
    删除所有表
    
    警告：此操作会删除所有数据！
    """
    logger.warning("删除所有数据库表...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("数据库表已删除")

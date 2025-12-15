# ============================================================================
# 国际顶级肉羊育种系统 - 配置文件
# International Top-tier Sheep Breeding System - Configuration
#
# 文件: config.py
# 功能: 系统配置管理
# ============================================================================

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """
    系统配置类
    
    使用pydantic-settings从环境变量加载配置
    """
    
    # ========================================================================
    # 基本配置
    # Basic Configuration
    # ========================================================================
    
    APP_NAME: str = "国际顶级肉羊育种系统"
    APP_NAME_EN: str = "International Top-tier Sheep Breeding System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # ========================================================================
    # 数据库配置
    # Database Configuration
    # ========================================================================
    
    # PostgreSQL
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/sheep_breeding"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # TimescaleDB (用于时序表型数据)
    TIMESCALE_ENABLED: bool = True
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 缓存过期时间(秒)
    
    # ========================================================================
    # Julia配置
    # Julia Configuration
    # ========================================================================
    
    JULIA_PATH: str = "julia"  # Julia可执行文件路径
    JULIA_VERSION: str = "1.12.2"
    JULIA_PROJECT_PATH: str = "./julia"  # Julia项目路径
    JULIA_NUM_THREADS: int = 8  # Julia线程数
    
    # GPU配置
    GPU_ENABLED: bool = True
    CUDA_VISIBLE_DEVICES: str = "0"  # 可见的GPU设备
    
    # ========================================================================
    # 文件存储配置
    # File Storage Configuration
    # ========================================================================
    
    # MinIO对象存储
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_GENOTYPES: str = "genotypes"
    MINIO_BUCKET_REPORTS: str = "reports"
    MINIO_BUCKET_EXPORTS: str = "exports"
    
    # 本地文件存储
    UPLOAD_DIR: str = "./uploads"
    TEMP_DIR: str = "./temp"
    LOG_DIR: str = "./logs"
    
    # 文件大小限制
    MAX_UPLOAD_SIZE: int = 1024 * 1024 * 1024  # 1GB
    
    # ========================================================================
    # 安全配置
    # Security Configuration
    # ========================================================================
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 密码策略
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React开发服务器
        "http://localhost:8080",  # Vue开发服务器
        "http://localhost:19006", # React Native开发服务器
    ]
    
    # ========================================================================
    # 消息队列配置
    # Message Queue Configuration
    # ========================================================================
    
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672/"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # ========================================================================
    # 业务配置
    # Business Configuration
    # ========================================================================
    
    # 遗传评估默认参数
    DEFAULT_HERITABILITY: float = 0.3
    DEFAULT_MAX_INBREEDING: float = 0.05
    DEFAULT_GENERATION_INTERVAL: float = 2.5  # 年
    
    # 质控默认参数
    QC_MIN_CALL_RATE: float = 0.90
    QC_MIN_MAF: float = 0.01
    QC_MAX_MISSING_PER_ANIMAL: float = 0.10
    QC_HWE_PVALUE: float = 0.0001
    
    # 分页默认参数
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # ========================================================================
    # 国际化配置
    # Internationalization Configuration
    # ========================================================================
    
    DEFAULT_LANGUAGE: str = "zh-CN"
    SUPPORTED_LANGUAGES: List[str] = ["zh-CN", "en-US"]
    
    # ========================================================================
    # 监控和日志配置
    # Monitoring and Logging Configuration
    # ========================================================================
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT: int = 5
    
    # Sentry (错误追踪)
    SENTRY_DSN: str = ""
    SENTRY_ENABLED: bool = False
    
    # Prometheus (指标监控)
    PROMETHEUS_ENABLED: bool = False
    PROMETHEUS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.TEMP_DIR, exist_ok=True)
os.makedirs(settings.LOG_DIR, exist_ok=True)

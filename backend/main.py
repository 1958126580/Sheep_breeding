# ============================================================================
# 国际顶级肉羊育种系统 - FastAPI后端主应用
# International Top-tier Sheep Breeding System - FastAPI Backend Main Application
#
# 文件: main.py
# 功能: FastAPI应用入口、路由配置、中间件设置
# 作者: AdvancedGenomics Team
# 版本: 1.0.0
# Python版本: 3.10+
# ============================================================================

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime

# 导入配置
from config import settings

# 导入路由 - 核心模块
from api.v1 import breeding_values

# 导入路由 - 新增模块 (按需导入，支持模块缺失)
try:
    from api.v1 import farms
    HAS_FARMS = True
except ImportError:
    HAS_FARMS = False

try:
    from api.v1 import health
    HAS_HEALTH = True
except ImportError:
    HAS_HEALTH = False

try:
    from api.v1 import reproduction
    HAS_REPRODUCTION = True
except ImportError:
    HAS_REPRODUCTION = False

try:
    from api.v1 import growth
    HAS_GROWTH = True
except ImportError:
    HAS_GROWTH = False

try:
    from api.v1 import iot
    HAS_IOT = True
except ImportError:
    HAS_IOT = False

try:
    from api.v1 import feeding
    HAS_FEEDING = True
except ImportError:
    HAS_FEEDING = False

try:
    from api.v1 import reports
    HAS_REPORTS = True
except ImportError:
    HAS_REPORTS = False

try:
    from api.v1 import cloud
    HAS_CLOUD = True
except ImportError:
    HAS_CLOUD = False

try:
    from api.v1 import blockchain
    HAS_BLOCKCHAIN = True
except ImportError:
    HAS_BLOCKCHAIN = False

try:
    from api.v1 import deep_learning
    HAS_DEEP_LEARNING = True
except ImportError:
    HAS_DEEP_LEARNING = False

try:
    from api.v1 import gwas
    HAS_GWAS = True
except ImportError:
    HAS_GWAS = False

# 占位模块 (待实现)
auth = None
animals = None
phenotypes = None
genotypes = None
selection = None
visualization = None
collaboration = None

# 导入数据库
from database import engine, Base

# ============================================================================
# 日志配置
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================================
# 应用生命周期管理
# Application Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用启动和关闭时的生命周期管理
    
    启动时：
    - 创建数据库表
    - 初始化Julia运行时
    - 加载配置
    
    关闭时：
    - 清理资源
    - 关闭数据库连接
    """
    # 启动
    logger.info("="*70)
    logger.info("国际顶级肉羊育种系统启动")
    logger.info("International Top-tier Sheep Breeding System Starting")
    logger.info("="*70)
    logger.info(f"环境: {settings.ENVIRONMENT}")
    logger.info(f"数据库: {settings.DATABASE_URL}")
    logger.info(f"Julia路径: {settings.JULIA_PATH}")
    
    # 创建数据库表
    logger.info("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    
    # 初始化Julia运行时
    logger.info("初始化Julia运行时...")
    from services.julia_service import JuliaService
    julia_service = JuliaService()
    await julia_service.initialize()
    
    logger.info("系统启动完成!")
    logger.info("="*70)
    
    yield
    
    # 关闭
    logger.info("系统关闭中...")
    await julia_service.shutdown()
    logger.info("系统已关闭")

# ============================================================================
# FastAPI应用实例
# FastAPI Application Instance
# ============================================================================

app = FastAPI(
    title="国际顶级肉羊育种系统 API",
    description="""
    # International Top-tier Sheep Breeding System API
    
    ## 功能特性 Features
    
    * **种羊管理** Animal Management - 种羊登记、系谱管理
    * **表型数据** Phenotype Data - 表型记录、数据质控
    * **基因组数据** Genomic Data - 基因型管理、SNP质控
    * **育种值估计** Breeding Value Estimation - BLUP/GBLUP/ssGBLUP
    * **选种决策** Selection Decision - 最优贡献选择、选配优化
    * **可视化** Visualization - 遗传趋势图、系谱图
    * **多机构协作** Collaboration - 数据共享、权限管理
    
    ## 技术栈 Tech Stack
    
    * **后端**: FastAPI + Python 3.10+
    * **计算引擎**: Julia 1.12.2
    * **数据库**: PostgreSQL + TimescaleDB
    * **缓存**: Redis
    * **消息队列**: RabbitMQ
    
    ## 文档 Documentation
    
    * API文档: /docs (Swagger UI)
    * ReDoc: /redoc
    * OpenAPI Schema: /openapi.json
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# ============================================================================
# 中间件配置
# Middleware Configuration
# ============================================================================

# CORS中间件 - 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request, call_next):
    """记录所有HTTP请求"""
    start_time = datetime.now()
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = (datetime.now() - start_time).total_seconds()
    
    # 记录日志
    logger.info(
        f"{request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.3f}s"
    )
    
    # 添加处理时间到响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# ============================================================================
# 路由注册
# Route Registration
# ============================================================================

# 育种值API (核心模块)
app.include_router(
    breeding_values.router,
    prefix="/api/v1/breeding-values",
    tags=["育种值估计 Breeding Value Estimation"]
)

# 羊场管理API (新增)
if HAS_FARMS:
    app.include_router(
        farms.router,
        prefix="/api/v1/farms",
        tags=["羊场管理 Farm Management"]
    )

# 健康管理API (新增)
if HAS_HEALTH:
    app.include_router(
        health.router,
        prefix="/api/v1/health",
        tags=["健康管理 Health Management"]
    )

# 繁殖管理API (新增)
if HAS_REPRODUCTION:
    app.include_router(
        reproduction.router,
        prefix="/api/v1/reproduction",
        tags=["繁殖管理 Reproduction Management"]
    )

# 生长发育API (新增)
if HAS_GROWTH:
    app.include_router(
        growth.router,
        prefix="/api/v1/growth",
        tags=["生长发育 Growth Development"]
    )

# 物联网API (新增)
if HAS_IOT:
    app.include_router(
        iot.router,
        prefix="/api/v1/iot",
        tags=["物联网 IoT Integration"]
    )

# 饲养管理API (新增)
if HAS_FEEDING:
    app.include_router(
        feeding.router,
        prefix="/api/v1/feeding",
        tags=["饲养管理 Feeding Management"]
    )

# 报表分析API (新增)
if HAS_REPORTS:
    app.include_router(
        reports.router,
        prefix="/api/v1/reports",
        tags=["报表分析 Reports & Analysis"]
    )

# 云服务API (新增)
if HAS_CLOUD:
    app.include_router(
        cloud.router,
        prefix="/api/v1/cloud",
        tags=["云服务 Cloud Service"]
    )

# 区块链溯源API (新增)
if HAS_BLOCKCHAIN:
    app.include_router(
        blockchain.router,
        prefix="/api/v1/blockchain",
        tags=["区块链溯源 Blockchain Traceability"]
    )

# 深度学习育种API (新增)
if HAS_DEEP_LEARNING:
    app.include_router(
        deep_learning.router,
        prefix="/api/v1/deep-learning",
        tags=["深度学习育种 Deep Learning Breeding"]
    )

# GWAS分析API (新增)
if HAS_GWAS:
    app.include_router(
        gwas.router,
        prefix="/api/v1/gwas",
        tags=["GWAS分析 GWAS Analysis"]
    )

# TODO: 以下模块待实现
# - auth (认证)
# - animals (种羊管理)
# - phenotypes (表型数据)
# - genotypes (基因组数据)
# - selection (选种决策)
# - visualization (可视化)
# - collaboration (协作)

# ============================================================================
# 根路由和健康检查
# Root Route and Health Check
# ============================================================================

@app.get("/", tags=["系统 System"])
async def root():
    """
    根路由 - 返回API基本信息
    """
    return {
        "name": "国际顶级肉羊育种系统 API",
        "name_en": "International Top-tier Sheep Breeding System API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["系统 System"])
async def health_check():
    """
    健康检查端点
    
    检查系统各组件状态：
    - 数据库连接
    - Redis连接
    - Julia运行时
    """
    from database import SessionLocal
    from services.julia_service import JuliaService
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # 检查数据库
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # 检查Julia运行时
    try:
        julia_service = JuliaService()
        if julia_service.is_initialized():
            health_status["components"]["julia"] = "healthy"
        else:
            health_status["components"]["julia"] = "not initialized"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["julia"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/api/v1/info", tags=["系统 System"])
async def system_info():
    """
    系统信息端点
    
    返回系统配置和运行信息
    """
    import platform
    import sys
    
    return {
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version,
            "julia_version": settings.JULIA_VERSION
        },
        "application": {
            "name": "国际顶级肉羊育种系统",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT
        },
        "features": {
            "gpu_enabled": settings.GPU_ENABLED,
            "parallel_computing": True,
            "multi_institution": True,
            "languages": ["zh-CN", "en-US"]
        }
    }

# ============================================================================
# 异常处理
# Exception Handling
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "内部服务器错误 Internal Server Error",
            "detail": str(exc) if settings.DEBUG else None
        }
    )

# ============================================================================
# 应用启动
# Application Startup
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
        log_level="info"
    )

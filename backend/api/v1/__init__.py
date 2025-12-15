# ============================================================================
# 国际顶级肉羊育种系统 - API v1 模块
# International Top-tier Sheep Breeding System - API v1 Module
# ============================================================================

from . import breeding_values

# 新增模块（按需导入，支持模块缺失时优雅降级）
# New modules (import as needed, graceful fallback if missing)

try:
    from . import farms
except ImportError:
    farms = None

try:
    from . import health
except ImportError:
    health = None

try:
    from . import reproduction
except ImportError:
    reproduction = None

try:
    from . import growth
except ImportError:
    growth = None

try:
    from . import feeding
except ImportError:
    feeding = None

try:
    from . import iot
except ImportError:
    iot = None

try:
    from . import reports
except ImportError:
    reports = None

try:
    from . import cloud
except ImportError:
    cloud = None

try:
    from . import blockchain
except ImportError:
    blockchain = None

# 导出所有可用模块
__all__ = [
    'breeding_values',
    'farms',
    'health', 
    'reproduction',
    'growth',
    'feeding',
    'iot',
    'reports',
    'cloud',
    'blockchain'
]


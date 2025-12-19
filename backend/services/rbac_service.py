# ============================================================================
# 新星肉羊育种系统 - RBAC 权限管理服务
# NovaBreed Sheep System - RBAC Permission Service
# ============================================================================

import logging
from typing import List, Dict, Any, Optional, Set
from functools import wraps

from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class Permission:
    """权限定义"""
    
    # 羊场管理权限
    FARM_VIEW = 'farm:view'
    FARM_CREATE = 'farm:create'
    FARM_UPDATE = 'farm:update'
    FARM_DELETE = 'farm:delete'
    FARM_EXPORT = 'farm:export'
    
    # 种羊管理权限
    ANIMAL_VIEW = 'animal:view'
    ANIMAL_CREATE = 'animal:create'
    ANIMAL_UPDATE = 'animal:update'
    ANIMAL_DELETE = 'animal:delete'
    ANIMAL_EXPORT = 'animal:export'
    
    # 育种分析权限
    BREEDING_VIEW = 'breeding:view'
    BREEDING_RUN = 'breeding:run'
    BREEDING_EXPORT = 'breeding:export'
    
    # 健康管理权限
    HEALTH_VIEW = 'health:view'
    HEALTH_MANAGE = 'health:manage'
    
    # 报表权限
    REPORT_VIEW = 'report:view'
    REPORT_GENERATE = 'report:generate'
    
    # 系统管理权限
    SYSTEM_MANAGE = 'system:manage'
    USER_MANAGE = 'user:manage'
    ROLE_MANAGE = 'role:manage'


# 预定义角色配置
ROLE_PERMISSIONS = {
    'admin': {
        'name': '系统管理员',
        'description': '拥有所有系统权限',
        'permissions': [
            Permission.FARM_VIEW, Permission.FARM_CREATE, Permission.FARM_UPDATE, Permission.FARM_DELETE, Permission.FARM_EXPORT,
            Permission.ANIMAL_VIEW, Permission.ANIMAL_CREATE, Permission.ANIMAL_UPDATE, Permission.ANIMAL_DELETE, Permission.ANIMAL_EXPORT,
            Permission.BREEDING_VIEW, Permission.BREEDING_RUN, Permission.BREEDING_EXPORT,
            Permission.HEALTH_VIEW, Permission.HEALTH_MANAGE,
            Permission.REPORT_VIEW, Permission.REPORT_GENERATE,
            Permission.SYSTEM_MANAGE, Permission.USER_MANAGE, Permission.ROLE_MANAGE,
        ],
        'is_system': True,
    },
    'manager': {
        'name': '场长',
        'description': '管理羊场和种羊',
        'permissions': [
            Permission.FARM_VIEW, Permission.FARM_CREATE, Permission.FARM_UPDATE, Permission.FARM_EXPORT,
            Permission.ANIMAL_VIEW, Permission.ANIMAL_CREATE, Permission.ANIMAL_UPDATE, Permission.ANIMAL_EXPORT,
            Permission.BREEDING_VIEW, Permission.BREEDING_RUN,
            Permission.HEALTH_VIEW, Permission.HEALTH_MANAGE,
            Permission.REPORT_VIEW, Permission.REPORT_GENERATE,
        ],
        'is_system': False,
    },
    'breeder': {
        'name': '育种员',
        'description': '负责育种分析工作',
        'permissions': [
            Permission.FARM_VIEW,
            Permission.ANIMAL_VIEW, Permission.ANIMAL_UPDATE,
            Permission.BREEDING_VIEW, Permission.BREEDING_RUN, Permission.BREEDING_EXPORT,
            Permission.REPORT_VIEW,
        ],
        'is_system': False,
    },
    'veterinarian': {
        'name': '兽医',
        'description': '负责健康管理',
        'permissions': [
            Permission.FARM_VIEW,
            Permission.ANIMAL_VIEW,
            Permission.HEALTH_VIEW, Permission.HEALTH_MANAGE,
            Permission.REPORT_VIEW,
        ],
        'is_system': False,
    },
    'viewer': {
        'name': '访客',
        'description': '只读权限',
        'permissions': [
            Permission.FARM_VIEW,
            Permission.ANIMAL_VIEW,
            Permission.BREEDING_VIEW,
            Permission.HEALTH_VIEW,
            Permission.REPORT_VIEW,
        ],
        'is_system': True,
    },
}


class RBACService:
    """RBAC 权限管理服务"""
    
    def __init__(self):
        self._role_permissions_cache: Dict[str, Set[str]] = {}
        self._load_role_permissions()
    
    def _load_role_permissions(self):
        """加载角色权限到缓存"""
        for role_code, role_config in ROLE_PERMISSIONS.items():
            self._role_permissions_cache[role_code] = set(role_config['permissions'])
        logger.info(f"加载了 {len(self._role_permissions_cache)} 个角色权限配置")
    
    def get_role_permissions(self, role_code: str) -> Set[str]:
        """获取角色的权限列表"""
        return self._role_permissions_cache.get(role_code, set())
    
    def get_user_permissions(self, user_roles: List[str]) -> Set[str]:
        """获取用户的所有权限（合并所有角色的权限）"""
        permissions = set()
        for role in user_roles:
            permissions |= self.get_role_permissions(role)
        return permissions
    
    def has_permission(self, user_roles: List[str], required_permission: str) -> bool:
        """检查用户是否有指定权限"""
        user_permissions = self.get_user_permissions(user_roles)
        return required_permission in user_permissions
    
    def has_any_permission(self, user_roles: List[str], required_permissions: List[str]) -> bool:
        """检查用户是否有任一指定权限"""
        user_permissions = self.get_user_permissions(user_roles)
        return bool(user_permissions & set(required_permissions))
    
    def has_all_permissions(self, user_roles: List[str], required_permissions: List[str]) -> bool:
        """检查用户是否有所有指定权限"""
        user_permissions = self.get_user_permissions(user_roles)
        return set(required_permissions).issubset(user_permissions)
    
    def list_roles(self) -> List[Dict[str, Any]]:
        """获取所有角色列表"""
        roles = []
        for role_code, role_config in ROLE_PERMISSIONS.items():
            roles.append({
                'code': role_code,
                'name': role_config['name'],
                'description': role_config['description'],
                'permissions': role_config['permissions'],
                'permission_count': len(role_config['permissions']),
                'is_system': role_config.get('is_system', False),
            })
        return roles
    
    def list_permissions(self) -> List[Dict[str, Any]]:
        """获取所有权限列表"""
        permissions = []
        
        # 权限定义
        PERMISSION_DEFINITIONS = {
            Permission.FARM_VIEW: {'name': '查看羊场', 'module': 'farm', 'type': 'menu'},
            Permission.FARM_CREATE: {'name': '创建羊场', 'module': 'farm', 'type': 'button'},
            Permission.FARM_UPDATE: {'name': '编辑羊场', 'module': 'farm', 'type': 'button'},
            Permission.FARM_DELETE: {'name': '删除羊场', 'module': 'farm', 'type': 'button'},
            Permission.FARM_EXPORT: {'name': '导出羊场', 'module': 'farm', 'type': 'button'},
            Permission.ANIMAL_VIEW: {'name': '查看种羊', 'module': 'animal', 'type': 'menu'},
            Permission.ANIMAL_CREATE: {'name': '创建种羊', 'module': 'animal', 'type': 'button'},
            Permission.ANIMAL_UPDATE: {'name': '编辑种羊', 'module': 'animal', 'type': 'button'},
            Permission.ANIMAL_DELETE: {'name': '删除种羊', 'module': 'animal', 'type': 'button'},
            Permission.ANIMAL_EXPORT: {'name': '导出种羊', 'module': 'animal', 'type': 'button'},
            Permission.BREEDING_VIEW: {'name': '查看育种分析', 'module': 'breeding', 'type': 'menu'},
            Permission.BREEDING_RUN: {'name': '运行育种分析', 'module': 'breeding', 'type': 'button'},
            Permission.BREEDING_EXPORT: {'name': '导出育种结果', 'module': 'breeding', 'type': 'button'},
            Permission.HEALTH_VIEW: {'name': '查看健康记录', 'module': 'health', 'type': 'menu'},
            Permission.HEALTH_MANAGE: {'name': '管理健康记录', 'module': 'health', 'type': 'button'},
            Permission.REPORT_VIEW: {'name': '查看报表', 'module': 'report', 'type': 'menu'},
            Permission.REPORT_GENERATE: {'name': '生成报表', 'module': 'report', 'type': 'button'},
            Permission.SYSTEM_MANAGE: {'name': '系统管理', 'module': 'system', 'type': 'menu'},
            Permission.USER_MANAGE: {'name': '用户管理', 'module': 'system', 'type': 'button'},
            Permission.ROLE_MANAGE: {'name': '角色管理', 'module': 'system', 'type': 'button'},
        }
        
        for code, definition in PERMISSION_DEFINITIONS.items():
            permissions.append({
                'code': code,
                'name': definition['name'],
                'module': definition['module'],
                'type': definition['type'],
            })
        
        return permissions
    
    def create_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新角色"""
        role_code = role_data.get('code')
        if role_code in ROLE_PERMISSIONS:
            raise HTTPException(status_code=400, detail=f"角色代码 '{role_code}' 已存在")
        
        ROLE_PERMISSIONS[role_code] = {
            'name': role_data.get('name'),
            'description': role_data.get('description', ''),
            'permissions': role_data.get('permissions', []),
            'is_system': False,
        }
        
        self._role_permissions_cache[role_code] = set(role_data.get('permissions', []))
        
        logger.info(f"创建角色: {role_code}")
        return {'code': role_code, **ROLE_PERMISSIONS[role_code]}
    
    def update_role(self, role_code: str, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新角色"""
        if role_code not in ROLE_PERMISSIONS:
            raise HTTPException(status_code=404, detail=f"角色 '{role_code}' 不存在")
        
        if ROLE_PERMISSIONS[role_code].get('is_system'):
            raise HTTPException(status_code=403, detail="系统角色不可修改")
        
        ROLE_PERMISSIONS[role_code].update({
            'name': role_data.get('name', ROLE_PERMISSIONS[role_code]['name']),
            'description': role_data.get('description', ROLE_PERMISSIONS[role_code]['description']),
            'permissions': role_data.get('permissions', ROLE_PERMISSIONS[role_code]['permissions']),
        })
        
        self._role_permissions_cache[role_code] = set(role_data.get('permissions', []))
        
        logger.info(f"更新角色: {role_code}")
        return {'code': role_code, **ROLE_PERMISSIONS[role_code]}
    
    def delete_role(self, role_code: str) -> bool:
        """删除角色"""
        if role_code not in ROLE_PERMISSIONS:
            raise HTTPException(status_code=404, detail=f"角色 '{role_code}' 不存在")
        
        if ROLE_PERMISSIONS[role_code].get('is_system'):
            raise HTTPException(status_code=403, detail="系统角色不可删除")
        
        del ROLE_PERMISSIONS[role_code]
        del self._role_permissions_cache[role_code]
        
        logger.info(f"删除角色: {role_code}")
        return True


# 创建服务实例
rbac_service = RBACService()


# 权限检查装饰器
def require_permission(permission: str):
    """
    权限检查装饰器
    
    用法:
    @require_permission(Permission.FARM_CREATE)
    async def create_farm(...):
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从请求上下文获取当前用户
            # 这里需要根据实际认证实现来获取用户信息
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证"
                )
            
            user_roles = current_user.get('roles', [])
            
            if not rbac_service.has_permission(user_roles, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要权限: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: str):
    """
    任一权限检查装饰器
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证"
                )
            
            user_roles = current_user.get('roles', [])
            
            if not rbac_service.has_any_permission(user_roles, list(permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要权限之一: {', '.join(permissions)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

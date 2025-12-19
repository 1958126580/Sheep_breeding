# ============================================================================
# 新星肉羊育种系统 - RBAC 权限管理服务测试
# NovaBreed Sheep System - RBAC Permission Service Tests
# ============================================================================

import pytest
from unittest.mock import MagicMock, patch

# 导入被测试的模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rbac_service import (
    Permission, ROLE_PERMISSIONS, RBACService, 
    rbac_service, require_permission, require_any_permission
)


class TestPermission:
    """权限定义测试"""
    
    def test_permission_constants_exist(self):
        """测试权限常量存在"""
        assert hasattr(Permission, 'FARM_VIEW')
        assert hasattr(Permission, 'FARM_CREATE')
        assert hasattr(Permission, 'FARM_UPDATE')
        assert hasattr(Permission, 'FARM_DELETE')
        assert hasattr(Permission, 'ANIMAL_VIEW')
        assert hasattr(Permission, 'BREEDING_VIEW')
        assert hasattr(Permission, 'SYSTEM_MANAGE')
    
    def test_permission_values_format(self):
        """测试权限值格式正确"""
        assert Permission.FARM_VIEW == 'farm:view'
        assert Permission.FARM_CREATE == 'farm:create'
        assert Permission.ANIMAL_VIEW == 'animal:view'
        assert Permission.BREEDING_RUN == 'breeding:run'


class TestRolePermissions:
    """角色权限配置测试"""
    
    def test_admin_role_exists(self):
        """测试管理员角色存在"""
        assert 'admin' in ROLE_PERMISSIONS
        assert ROLE_PERMISSIONS['admin']['is_system'] == True
    
    def test_admin_has_all_permissions(self):
        """测试管理员拥有所有权限"""
        admin_perms = ROLE_PERMISSIONS['admin']['permissions']
        assert Permission.FARM_VIEW in admin_perms
        assert Permission.SYSTEM_MANAGE in admin_perms
        assert Permission.USER_MANAGE in admin_perms
    
    def test_viewer_role_limited(self):
        """测试访客角色权限受限"""
        viewer_perms = ROLE_PERMISSIONS['viewer']['permissions']
        assert Permission.FARM_VIEW in viewer_perms
        assert Permission.FARM_DELETE not in viewer_perms
        assert Permission.SYSTEM_MANAGE not in viewer_perms
    
    def test_all_roles_have_required_fields(self):
        """测试所有角色都有必需字段"""
        required_fields = ['name', 'description', 'permissions']
        for role_code, role_config in ROLE_PERMISSIONS.items():
            for field in required_fields:
                assert field in role_config, f"角色 {role_code} 缺少字段 {field}"


class TestRBACService:
    """RBAC 服务测试"""
    
    @pytest.fixture
    def service(self):
        """创建测试用服务实例"""
        return RBACService()
    
    def test_get_role_permissions(self, service):
        """测试获取角色权限"""
        admin_perms = service.get_role_permissions('admin')
        assert isinstance(admin_perms, set)
        assert len(admin_perms) > 0
        assert Permission.SYSTEM_MANAGE in admin_perms
    
    def test_get_role_permissions_invalid_role(self, service):
        """测试获取无效角色权限返回空集合"""
        perms = service.get_role_permissions('nonexistent')
        assert perms == set()
    
    def test_get_user_permissions_single_role(self, service):
        """测试单角色用户权限"""
        perms = service.get_user_permissions(['viewer'])
        assert Permission.FARM_VIEW in perms
        assert Permission.FARM_DELETE not in perms
    
    def test_get_user_permissions_multiple_roles(self, service):
        """测试多角色用户权限合并"""
        perms = service.get_user_permissions(['viewer', 'breeder'])
        # 应该包含两个角色的权限并集
        assert Permission.FARM_VIEW in perms  # viewer有
        assert Permission.BREEDING_RUN in perms  # breeder有
    
    def test_has_permission_positive(self, service):
        """测试有权限-正向"""
        result = service.has_permission(['admin'], Permission.SYSTEM_MANAGE)
        assert result == True
    
    def test_has_permission_negative(self, service):
        """测试有权限-负向"""
        result = service.has_permission(['viewer'], Permission.SYSTEM_MANAGE)
        assert result == False
    
    def test_has_any_permission(self, service):
        """测试任一权限检查"""
        result = service.has_any_permission(
            ['viewer'], 
            [Permission.FARM_VIEW, Permission.SYSTEM_MANAGE]
        )
        assert result == True  # viewer有farm:view
    
    def test_has_all_permissions(self, service):
        """测试所有权限检查"""
        # admin应该有所有权限
        result = service.has_all_permissions(
            ['admin'],
            [Permission.FARM_VIEW, Permission.SYSTEM_MANAGE]
        )
        assert result == True
        
        # viewer不应该有system:manage
        result = service.has_all_permissions(
            ['viewer'],
            [Permission.FARM_VIEW, Permission.SYSTEM_MANAGE]
        )
        assert result == False
    
    def test_list_roles(self, service):
        """测试列出角色"""
        roles = service.list_roles()
        assert isinstance(roles, list)
        assert len(roles) >= 4  # 至少有admin, manager, breeder, viewer
        
        role_codes = [r['code'] for r in roles]
        assert 'admin' in role_codes
        assert 'viewer' in role_codes
    
    def test_list_permissions(self, service):
        """测试列出权限"""
        perms = service.list_permissions()
        assert isinstance(perms, list)
        assert len(perms) > 0
        
        # 检查权限结构
        for perm in perms:
            assert 'code' in perm
            assert 'name' in perm
            assert 'module' in perm


class TestSecurityFeatures:
    """安全特性测试"""
    
    def test_system_role_protection(self):
        """测试系统角色不可删除"""
        service = RBACService()
        with pytest.raises(Exception):
            service.delete_role('admin')
        with pytest.raises(Exception):
            service.delete_role('viewer')
    
    def test_system_role_update_protection(self):
        """测试系统角色不可修改"""
        service = RBACService()
        with pytest.raises(Exception):
            service.update_role('admin', {'name': '新名称'})
    
    def test_duplicate_role_prevention(self):
        """测试防止创建重复角色"""
        service = RBACService()
        with pytest.raises(Exception):
            service.create_role({'code': 'admin', 'name': '重复管理员'})


class TestPermissionDecorators:
    """权限装饰器测试"""
    
    @pytest.mark.asyncio
    async def test_require_permission_no_user(self):
        """测试无用户时权限检查"""
        @require_permission(Permission.FARM_VIEW)
        async def test_func(current_user=None):
            return "success"
        
        # 没有用户应该抛出401
        with pytest.raises(Exception):
            await test_func()
    
    @pytest.mark.asyncio
    async def test_require_permission_insufficient(self):
        """测试权限不足时"""
        @require_permission(Permission.SYSTEM_MANAGE)
        async def test_func(current_user=None):
            return "success"
        
        # viewer没有system:manage权限
        with pytest.raises(Exception):
            await test_func(current_user={'roles': ['viewer']})


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

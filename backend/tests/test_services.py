# ============================================================================
# 国际顶级肉羊育种系统 - 服务层单元测试
# International Top-tier Sheep Breeding System - Service Layer Tests
#
# 文件: test_services.py
# 覆盖: CRUD服务层和业务逻辑
# ============================================================================

import pytest
from datetime import date, datetime
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base


# ============================================================================
# 测试数据库配置
# ============================================================================

@pytest.fixture(scope="module")
def test_engine():
    """创建测试数据库引擎"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    """创建测试数据库会话"""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ============================================================================
# BaseService测试
# ============================================================================

class TestBaseService:
    """基础服务测试"""
    
    def test_create(self, db_session):
        """测试创建"""
        from services.farm_service import FarmService
        from models.farm import Farm
        
        service = FarmService(db_session)
        
        class FarmCreate:
            def model_dump(self):
                return {
                    "organization_id": 1,
                    "code": "TEST001",
                    "name": "测试羊场",
                    "farm_type": "breeding",
                    "capacity": 500,
                    "current_stock": 0,
                    "status": "active"
                }
        
        farm = service.create(FarmCreate())
        
        assert farm.id is not None
        assert farm.code == "TEST001"
    
    def test_get(self, db_session):
        """测试查询"""
        from services.farm_service import FarmService
        from models.farm import Farm
        
        # 先创建
        farm = Farm(
            organization_id=1,
            code="GET001",
            name="查询测试",
            farm_type="commercial",
            capacity=100,
            current_stock=0,
            status="active"
        )
        db_session.add(farm)
        db_session.commit()
        
        # 再查询
        service = FarmService(db_session)
        result = service.get(farm.id)
        
        assert result is not None
        assert result.code == "GET001"
    
    def test_get_multi(self, db_session):
        """测试批量查询"""
        from services.farm_service import FarmService
        from models.farm import Farm
        
        # 创建多个
        for i in range(5):
            farm = Farm(
                organization_id=1,
                code=f"MULTI{i:03d}",
                name=f"批量测试{i}",
                farm_type="mixed",
                capacity=100,
                current_stock=0,
                status="active"
            )
            db_session.add(farm)
        db_session.commit()
        
        service = FarmService(db_session)
        results = service.get_multi(limit=3)
        
        assert len(results) <= 3
    
    def test_update(self, db_session):
        """测试更新"""
        from services.farm_service import FarmService
        from models.farm import Farm
        
        farm = Farm(
            organization_id=1,
            code="UPD001",
            name="更新前",
            farm_type="breeding",
            capacity=100,
            current_stock=0,
            status="active"
        )
        db_session.add(farm)
        db_session.commit()
        
        class FarmUpdate:
            def model_dump(self, exclude_unset=False):
                return {"name": "更新后", "capacity": 200}
        
        service = FarmService(db_session)
        updated = service.update(farm.id, FarmUpdate())
        
        assert updated.name == "更新后"
        assert updated.capacity == 200
    
    def test_soft_delete(self, db_session):
        """测试软删除"""
        from services.farm_service import FarmService
        from models.farm import Farm
        
        farm = Farm(
            organization_id=1,
            code="DEL001",
            name="删除测试",
            farm_type="commercial",
            capacity=50,
            current_stock=0,
            status="active"
        )
        db_session.add(farm)
        db_session.commit()
        
        service = FarmService(db_session)
        result = service.delete(farm.id, soft=True)
        
        assert result == True
        
        # 软删除后应该查不到
        assert service.get(farm.id) is None
    
    def test_count(self, db_session):
        """测试计数"""
        from services.farm_service import FarmService
        from models.farm import Farm
        
        for i in range(3):
            farm = Farm(
                organization_id=1,
                code=f"CNT{i:03d}",
                name=f"计数测试{i}",
                farm_type="breeding",
                capacity=100,
                current_stock=0,
                status="active"
            )
            db_session.add(farm)
        db_session.commit()
        
        service = FarmService(db_session)
        count = service.count()
        
        assert count >= 3


# ============================================================================
# FarmService测试
# ============================================================================

class TestFarmService:
    """羊场服务测试"""
    
    def test_get_by_code(self, db_session):
        """测试按代码查询"""
        from services.farm_service import FarmService
        from models.farm import Farm
        
        farm = Farm(
            organization_id=1,
            code="CODE001",
            name="代码查询测试",
            farm_type="breeding",
            capacity=100,
            current_stock=0,
            status="active"
        )
        db_session.add(farm)
        db_session.commit()
        
        service = FarmService(db_session)
        result = service.get_by_code("CODE001")
        
        assert result is not None
        assert result.name == "代码查询测试"
    
    def test_get_dashboard(self, db_session):
        """测试仪表板数据"""
        from services.farm_service import FarmService
        from models.farm import Farm
        
        farm = Farm(
            organization_id=1,
            code="DASH001",
            name="仪表板测试",
            farm_type="breeding",
            capacity=1000,
            current_stock=500,
            status="active"
        )
        db_session.add(farm)
        db_session.commit()
        
        service = FarmService(db_session)
        dashboard = service.get_dashboard(farm.id)
        
        assert dashboard["farm_id"] == farm.id
        assert dashboard["farm_name"] == "仪表板测试"
        assert "capacity_usage" in dashboard


# ============================================================================
# BarnService测试
# ============================================================================

class TestBarnService:
    """羊舍服务测试"""
    
    def test_get_by_farm(self, db_session):
        """测试按羊场查询羊舍"""
        from services.farm_service import BarnService
        from models.farm import Farm, Barn
        
        farm = Farm(
            organization_id=1,
            code="FARM_BARN",
            name="羊舍测试羊场",
            farm_type="breeding",
            capacity=500,
            current_stock=0,
            status="active"
        )
        db_session.add(farm)
        db_session.commit()
        
        for i in range(3):
            barn = Barn(
                farm_id=farm.id,
                code=f"B{i:02d}",
                name=f"羊舍{i}",
                barn_type="ewe",
                capacity=50,
                current_count=0,
                status="active"
            )
            db_session.add(barn)
        db_session.commit()
        
        service = BarnService(db_session)
        barns = service.get_by_farm(farm.id)
        
        assert len(barns) == 3
    
    def test_is_full(self, db_session):
        """测试满员检查"""
        from services.farm_service import BarnService
        from models.farm import Barn
        
        barn = Barn(
            farm_id=1,
            code="FULL01",
            name="满员测试",
            barn_type="ram",
            capacity=10,
            current_count=10,
            status="active"
        )
        db_session.add(barn)
        db_session.commit()
        
        service = BarnService(db_session)
        assert service.is_full(barn.id) == True
        
        barn.current_count = 5
        db_session.commit()
        assert service.is_full(barn.id) == False


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

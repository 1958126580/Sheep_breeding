# ============================================================================
# 国际顶级肉羊育种系统 - 模型单元测试
# International Top-tier Sheep Breeding System - Model Unit Tests
#
# 文件: test_models.py
# 覆盖: 所有SQLAlchemy ORM模型
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
    """创建测试数据库引擎 (SQLite内存数据库)"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def test_session(test_engine):
    """创建测试会话"""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ============================================================================
# Farm模型测试
# ============================================================================

class TestFarmModel:
    """羊场模型测试"""
    
    def test_farm_creation(self, test_session):
        """测试创建羊场"""
        from models.farm import Farm
        
        farm = Farm(
            organization_id=1,
            code="FARM001",
            name="测试种羊场",
            farm_type="breeding",
            capacity=1000,
            current_stock=500,
            status="active"
        )
        
        test_session.add(farm)
        test_session.commit()
        
        assert farm.id is not None
        assert farm.code == "FARM001"
        assert farm.capacity_usage == 50.0
    
    def test_farm_capacity_usage(self, test_session):
        """测试存栏率计算"""
        from models.farm import Farm
        
        farm = Farm(
            organization_id=1,
            code="FARM002",
            name="测试羊场",
            farm_type="commercial",
            capacity=200,
            current_stock=150,
            status="active"
        )
        
        assert farm.capacity_usage == 75.0
        
        # 零容量
        farm.capacity = 0
        assert farm.capacity_usage == 0.0
    
    def test_farm_update_stock(self, test_session):
        """测试更新存栏量"""
        from models.farm import Farm
        
        farm = Farm(
            organization_id=1,
            code="FARM003",
            name="测试羊场",
            farm_type="mixed",
            capacity=500,
            current_stock=100,
            status="active"
        )
        
        farm.update_stock_count(50)
        assert farm.current_stock == 150
        
        farm.update_stock_count(-200)
        assert farm.current_stock == 0  # 不能为负


class TestBarnModel:
    """羊舍模型测试"""
    
    def test_barn_creation(self, test_session):
        """测试创建羊舍"""
        from models.farm import Barn
        
        barn = Barn(
            farm_id=1,
            code="A01",
            name="种公羊舍",
            barn_type="ram",
            capacity=50,
            current_count=30,
            status="active"
        )
        
        assert barn.capacity_usage == 60.0
        assert barn.is_full == False
    
    def test_barn_full_check(self, test_session):
        """测试满员检查"""
        from models.farm import Barn
        
        barn = Barn(
            farm_id=1,
            code="B01",
            name="母羊舍",
            barn_type="ewe",
            capacity=100,
            current_count=100,
            status="active"
        )
        
        assert barn.is_full == True


class TestAnimalLocationModel:
    """动物位置模型测试"""
    
    def test_location_is_current(self, test_session):
        """测试当前位置判断"""
        from models.farm import AnimalLocation
        
        location = AnimalLocation(
            animal_id=1,
            farm_id=1,
            barn_id=1,
            entry_date=datetime.now()
        )
        
        assert location.is_current == True
        
        location.close("转移")
        assert location.is_current == False


# ============================================================================
# Animal模型测试
# ============================================================================

class TestAnimalModel:
    """动物模型测试"""
    
    def test_animal_age_calculation(self, test_session):
        """测试日龄计算"""
        from models.animal import Animal
        
        animal = Animal(
            organization_id=1,
            animal_code="SH2024001",
            breed="杜泊羊",
            sex="male",
            birth_date=date(2024, 1, 15),
            status="active"
        )
        
        assert animal.age_days >= 0
        assert animal.age_months >= 0
    
    def test_animal_adult_check(self, test_session):
        """测试成年判断"""
        from models.animal import Animal
        from datetime import timedelta
        
        # 幼年
        young_animal = Animal(
            organization_id=1,
            animal_code="SH2024002",
            breed="杜泊羊",
            sex="female",
            birth_date=date.today() - timedelta(days=180),
            status="active"
        )
        assert young_animal.is_adult == False
        
        # 成年
        adult_animal = Animal(
            organization_id=1,
            animal_code="SH2023001",
            breed="杜泊羊",
            sex="female",
            birth_date=date.today() - timedelta(days=400),
            status="active"
        )
        assert adult_animal.is_adult == True


# ============================================================================
# Health模型测试
# ============================================================================

class TestHealthModels:
    """健康模型测试"""
    
    def test_disease_creation(self, test_session):
        """测试疾病创建"""
        from models.health import Disease
        
        disease = Disease(
            disease_code="D001",
            name="口蹄疫",
            category="infectious",
            is_reportable=True
        )
        
        assert disease.disease_code == "D001"
        assert disease.is_reportable == True
    
    def test_health_record_creation(self, test_session):
        """测试健康记录创建"""
        from models.health import HealthRecord
        
        record = HealthRecord(
            animal_id=1,
            check_date=date.today(),
            check_type="routine",
            body_temperature=Decimal("39.2"),
            body_weight=Decimal("45.5"),
            body_condition_score=3
        )
        
        assert record.check_type == "routine"


# ============================================================================
# Growth模型测试
# ============================================================================

class TestGrowthModel:
    """生长模型测试"""
    
    def test_growth_record_creation(self, test_session):
        """测试生长记录创建"""
        from models.growth import GrowthRecord
        
        record = GrowthRecord(
            animal_id=1,
            measurement_date=date.today(),
            measurement_type="routine",
            body_weight=Decimal("55.5")
        )
        
        assert record.body_weight == Decimal("55.5")
    
    def test_adg_calculation(self, test_session):
        """测试日增重计算"""
        from models.growth import GrowthRecord
        
        adg = GrowthRecord.calculate_adg(40.0, 55.0, 30)
        assert abs(adg - 0.5) < 0.01
        
        # 零天数
        adg_zero = GrowthRecord.calculate_adg(40.0, 55.0, 0)
        assert adg_zero == 0.0


# ============================================================================
# Feed模型测试
# ============================================================================

class TestFeedModels:
    """饲料模型测试"""
    
    def test_feed_type_creation(self, test_session):
        """测试饲料类型创建"""
        from models.feed import FeedType
        
        feed_type = FeedType(
            feed_code="F001",
            name="玉米",
            category="concentrate",
            crude_protein=Decimal("8.5"),
            unit_price=Decimal("2.5")
        )
        
        assert feed_type.category == "concentrate"
    
    def test_inventory_low_stock(self, test_session):
        """测试低库存判断"""
        from models.feed import FeedInventory
        
        inventory = FeedInventory(
            farm_id=1,
            feed_type_id=1,
            current_quantity=Decimal("100"),
            min_quantity=Decimal("200")
        )
        
        assert inventory.is_low_stock == True
        
        inventory.current_quantity = Decimal("300")
        assert inventory.is_low_stock == False


# ============================================================================
# IoT模型测试
# ============================================================================

class TestIoTModels:
    """IoT模型测试"""
    
    def test_device_creation(self, test_session):
        """测试设备创建"""
        from models.iot import IoTDevice
        
        device = IoTDevice(
            device_id="DEV001",
            name="自动秤1号",
            device_type="scale",
            farm_id=1,
            status="online"
        )
        
        assert device.is_online == True
        
        device.status = "offline"
        assert device.is_online == False


# ============================================================================
# Base模型测试
# ============================================================================

class TestBaseMixins:
    """基类混入测试"""
    
    def test_soft_delete(self, test_session):
        """测试软删除"""
        from models.farm import Farm
        
        farm = Farm(
            organization_id=1,
            code="DEL001",
            name="待删除羊场",
            farm_type="breeding",
            status="active"
        )
        
        farm.soft_delete(user_id=1)
        
        assert farm.is_deleted == True
        assert farm.deleted_by == 1
        assert farm.deleted_at is not None
    
    def test_restore(self, test_session):
        """测试恢复软删除"""
        from models.farm import Farm
        
        farm = Farm(
            organization_id=1,
            code="REST001",
            name="恢复羊场",
            farm_type="breeding",
            status="active"
        )
        
        farm.soft_delete()
        farm.restore()
        
        assert farm.is_deleted == False
        assert farm.deleted_at is None


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

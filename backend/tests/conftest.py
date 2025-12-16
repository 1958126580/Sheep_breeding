# ============================================================================
# 新星肉羊育种系统 - 测试配置
# NovaBreed Sheep System - Test Configuration
# ============================================================================

import pytest
import os
import sys

# 确保backend目录在路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    """创建测试客户端"""
    from main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def db_session():
    """创建测试数据库会话"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_farm_data():
    """示例羊场数据"""
    return {
        "organization_id": 1,
        "name": "测试种羊场",
        "code": "TEST001",
        "farm_type": "breeding",
        "capacity": 500,
        "area": 25.0,
        "address": "山东省济南市测试路1号",
        "province": "山东省",
        "city": "济南市"
    }


@pytest.fixture
def sample_animal_data():
    """示例动物数据"""
    return {
        "animal_code": "SH2024TEST001",
        "birth_date": "2024-01-15",
        "sex": "female",
        "breed": "杜泊羊",
        "father_code": "SH2021001",
        "mother_code": "SH2022001"
    }


@pytest.fixture
def sample_health_record():
    """示例健康记录"""
    return {
        "animal_id": 1,
        "check_date": "2024-12-01",
        "check_type": "routine",
        "body_temperature": 39.2,
        "body_weight": 45.5,
        "body_condition_score": 3,
        "notes": "正常"
    }


@pytest.fixture
def sample_breeding_record():
    """示例配种记录"""
    return {
        "dam_id": 1,
        "sire_id": 2,
        "breeding_date": "2024-10-01",
        "breeding_method": "natural",
        "technician": "张技术员"
    }


@pytest.fixture
def sample_feed_formula():
    """示例饲料配方"""
    return {
        "organization_id": 1,
        "name": "育肥羊精料1号",
        "target_animal_type": "fattening",
        "daily_amount_kg": 1.2,
        "ingredients": [
            {"feed_type_id": 1, "feed_type_name": "玉米", "percentage": 55},
            {"feed_type_id": 2, "feed_type_name": "豆粕", "percentage": 25},
            {"feed_type_id": 3, "feed_type_name": "麸皮", "percentage": 15},
            {"feed_type_id": 4, "feed_type_name": "预混料", "percentage": 5}
        ],
        "cost_per_kg": 2.85
    }

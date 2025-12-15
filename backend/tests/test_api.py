# ============================================================================
# 国际顶级肉羊育种系统 - 测试套件
# International Top-tier Sheep Breeding System - Test Suite
# ============================================================================

import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime
from decimal import Decimal
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


# ============================================================================
# 系统基础测试
# System Basic Tests
# ============================================================================

class TestSystemBasic:
    """系统基础功能测试"""
    
    def test_root_endpoint(self):
        """测试根路由"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"
    
    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_openapi_docs(self):
        """测试OpenAPI文档"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


# ============================================================================
# 羊场管理API测试
# Farm Management API Tests
# ============================================================================

class TestFarmsAPI:
    """羊场管理API测试"""
    
    def test_list_farms(self):
        """测试获取羊场列表"""
        response = client.get("/api/v1/farms/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_farm(self):
        """测试创建羊场"""
        farm_data = {
            "organization_id": 1,
            "name": "测试羊场",
            "code": "TST001",
            "farm_type": "breeding",
            "capacity": 1000,
            "area": 50.5,
            "address": "测试地址",
            "province": "山东省",
            "city": "济南市"
        }
        response = client.post("/api/v1/farms/", json=farm_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == farm_data["name"]


# ============================================================================
# 健康管理API测试
# Health Management API Tests
# ============================================================================

class TestHealthAPI:
    """健康管理API测试"""
    
    def test_list_health_records(self):
        """测试获取健康记录列表"""
        response = client.get("/api/v1/health/records")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_list_diseases(self):
        """测试获取疾病字典"""
        response = client.get("/api/v1/health/diseases")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ============================================================================
# 繁殖管理API测试
# Reproduction Management API Tests
# ============================================================================

class TestReproductionAPI:
    """繁殖管理API测试"""
    
    def test_list_breeding_records(self):
        """测试获取配种记录"""
        response = client.get("/api/v1/reproduction/breeding")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_reproduction_statistics(self):
        """测试获取繁殖统计"""
        response = client.get("/api/v1/reproduction/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_breedings" in data


# ============================================================================
# 生长发育API测试
# Growth Development API Tests
# ============================================================================

class TestGrowthAPI:
    """生长发育API测试"""
    
    def test_list_growth_records(self):
        """测试获取生长记录"""
        response = client.get("/api/v1/growth/records")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_growth_statistics(self):
        """测试获取生长统计"""
        response = client.get("/api/v1/growth/statistics")
        assert response.status_code == 200


# ============================================================================
# 物联网API测试
# IoT API Tests
# ============================================================================

class TestIoTAPI:
    """物联网API测试"""
    
    def test_list_devices(self):
        """测试获取设备列表"""
        response = client.get("/api/v1/iot/devices")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_environment_data(self):
        """测试获取环境数据"""
        response = client.get("/api/v1/iot/environment/current")
        assert response.status_code == 200


# ============================================================================
# 饲养管理API测试
# Feeding Management API Tests
# ============================================================================

class TestFeedingAPI:
    """饲养管理API测试"""
    
    def test_list_feed_types(self):
        """测试获取饲料类型"""
        response = client.get("/api/v1/feeding/types")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_list_feed_formulas(self):
        """测试获取饲料配方"""
        response = client.get("/api/v1/feeding/formulas")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_feeding_statistics(self):
        """测试获取饲养统计"""
        response = client.get("/api/v1/feeding/statistics")
        assert response.status_code == 200


# ============================================================================
# 报表分析API测试
# Reports API Tests
# ============================================================================

class TestReportsAPI:
    """报表分析API测试"""
    
    def test_get_annual_breeding_report(self):
        """测试获取育种年报"""
        response = client.get("/api/v1/reports/breeding/annual?year=2024")
        assert response.status_code == 200
        data = response.json()
        assert "report_year" in data
    
    def test_get_inbreeding_report(self):
        """测试获取近交监控报告"""
        response = client.get("/api/v1/reports/inbreeding")
        assert response.status_code == 200
    
    def test_get_dashboard_data(self):
        """测试获取仪表板数据"""
        response = client.get("/api/v1/reports/dashboard")
        assert response.status_code == 200


# ============================================================================
# 云服务API测试
# Cloud Service API Tests
# ============================================================================

class TestCloudAPI:
    """云服务API测试"""
    
    def test_get_cloud_status(self):
        """测试获取云服务状态"""
        response = client.get("/api/v1/cloud/status")
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
    
    def test_list_sync_tasks(self):
        """测试获取同步任务"""
        response = client.get("/api/v1/cloud/sync/tasks")
        assert response.status_code == 200
    
    def test_list_data_standards(self):
        """测试获取数据标准"""
        response = client.get("/api/v1/cloud/standards")
        assert response.status_code == 200


# ============================================================================
# 区块链API测试
# Blockchain API Tests
# ============================================================================

class TestBlockchainAPI:
    """区块链API测试"""
    
    def test_list_records(self):
        """测试获取存证记录"""
        response = client.get("/api/v1/blockchain/records")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_list_certificates(self):
        """测试获取证书列表"""
        response = client.get("/api/v1/blockchain/certificates")
        assert response.status_code == 200
    
    def test_get_blockchain_stats(self):
        """测试获取区块链统计"""
        response = client.get("/api/v1/blockchain/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_records" in data


# ============================================================================
# 育种值API测试
# Breeding Values API Tests
# ============================================================================

class TestBreedingValuesAPI:
    """育种值API测试"""
    
    def test_list_runs(self):
        """测试获取评估运行列表"""
        response = client.get("/api/v1/breeding-values/runs")
        assert response.status_code == 200


# ============================================================================
# 运行测试
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

# ============================================================================
# 新星肉羊育种系统 - 数据导入导出服务测试
# NovaBreed Sheep System - Data Import/Export Service Tests
# ============================================================================

import pytest
import io
import pandas as pd
from unittest.mock import MagicMock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_io_service import DataImportExportService, data_io_service


class TestDataImportExportService:
    """数据导入导出服务测试"""
    
    @pytest.fixture
    def service(self):
        """创建测试用服务实例"""
        return DataImportExportService()
    
    def test_entity_configs_exist(self, service):
        """测试实体配置存在"""
        assert 'farms' in service.ENTITY_CONFIGS
        assert 'animals' in service.ENTITY_CONFIGS
        assert 'phenotypes' in service.ENTITY_CONFIGS
        assert 'genotypes' in service.ENTITY_CONFIGS
    
    def test_entity_configs_have_required_fields(self, service):
        """测试实体配置有必需字段"""
        required_fields = ['model', 'required_columns', 'validators']
        for entity_type, config in service.ENTITY_CONFIGS.items():
            for field in required_fields:
                assert field in config, f"实体 {entity_type} 缺少字段 {field}"
    
    def test_farm_required_columns(self, service):
        """测试羊场必填列"""
        required = service.ENTITY_CONFIGS['farms']['required_columns']
        assert 'code' in required
        assert 'name' in required
        assert 'farm_type' in required
        assert 'capacity' in required
    
    def test_animal_required_columns(self, service):
        """测试种羊必填列"""
        required = service.ENTITY_CONFIGS['animals']['required_columns']
        assert 'animal_id' in required
        assert 'farm_id' in required
        assert 'birth_date' in required
        assert 'gender' in required


class TestValidators:
    """数据验证器测试"""
    
    @pytest.fixture
    def service(self):
        return DataImportExportService()
    
    def test_farm_code_validator(self, service):
        """测试羊场代码验证"""
        validator = service.ENTITY_CONFIGS['farms']['validators']['code']
        assert validator('FARM001') == True
        assert validator('A' * 100) == False  # 超长
    
    def test_farm_type_validator(self, service):
        """测试羊场类型验证"""
        validator = service.ENTITY_CONFIGS['farms']['validators']['farm_type']
        assert validator('breeding') == True
        assert validator('commercial') == True
        assert validator('research') == True
        assert validator('invalid') == False
    
    def test_capacity_validator(self, service):
        """测试容量验证"""
        validator = service.ENTITY_CONFIGS['farms']['validators']['capacity']
        assert validator(1000) == True
        assert validator(1) == True
        assert validator(0) == False
        assert validator(-1) == False


class TestTemplateGeneration:
    """模板生成测试"""
    
    @pytest.fixture
    def service(self):
        return DataImportExportService()
    
    def test_generate_farms_template(self, service):
        """测试生成羊场导入模板"""
        content, filename = service.generate_template('farms')
        
        assert filename == 'farms_template.xlsx'
        assert len(content) > 0
        assert isinstance(content, bytes)
    
    def test_generate_animals_template(self, service):
        """测试生成种羊导入模板"""
        content, filename = service.generate_template('animals')
        
        assert filename == 'animals_template.xlsx'
        assert len(content) > 0
    
    def test_generate_template_invalid_entity(self, service):
        """测试生成无效实体模板抛出异常"""
        with pytest.raises(Exception):
            service.generate_template('invalid_entity')


class TestExportFunctionality:
    """导出功能测试"""
    
    @pytest.fixture
    def service(self):
        return DataImportExportService()
    
    @pytest.mark.asyncio
    async def test_export_xlsx(self, service):
        """测试导出Excel格式"""
        content, filename = await service.export_data('farms', 'xlsx')
        
        assert filename.endswith('.xlsx')
        assert 'farms_export_' in filename
        assert len(content) > 0
    
    @pytest.mark.asyncio
    async def test_export_csv(self, service):
        """测试导出CSV格式"""
        content, filename = await service.export_data('farms', 'csv')
        
        assert filename.endswith('.csv')
        assert 'farms_export_' in filename
        assert len(content) > 0
    
    @pytest.mark.asyncio
    async def test_export_invalid_format(self, service):
        """测试导出无效格式抛出异常"""
        with pytest.raises(Exception):
            await service.export_data('farms', 'invalid')


class TestPreviewFunctionality:
    """预览功能测试"""
    
    @pytest.fixture
    def service(self):
        return DataImportExportService()
    
    @pytest.fixture
    def valid_xlsx_file(self):
        """创建有效的测试Excel文件"""
        df = pd.DataFrame({
            'code': ['FARM001', 'FARM002'],
            'name': ['测试羊场1', '测试羊场2'],
            'farm_type': ['breeding', 'commercial'],
            'capacity': [1000, 2000]
        })
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        
        mock_file = MagicMock()
        mock_file.filename = 'test.xlsx'
        mock_file.read = AsyncMock(return_value=buffer.getvalue())
        mock_file.seek = AsyncMock()
        
        return mock_file
    
    @pytest.mark.asyncio
    async def test_preview_valid_file(self, service, valid_xlsx_file):
        """测试预览有效文件"""
        result = await service.preview_file(valid_xlsx_file, 'farms')
        
        assert 'data' in result
        assert 'total_rows' in result
        assert 'columns' in result
        assert 'is_valid' in result
        assert result['total_rows'] == 2
    
    @pytest.mark.asyncio
    async def test_preview_invalid_entity(self, service, valid_xlsx_file):
        """测试预览无效实体类型"""
        with pytest.raises(Exception):
            await service.preview_file(valid_xlsx_file, 'invalid_entity')


class TestDataSecurity:
    """数据安全测试"""
    
    @pytest.fixture
    def service(self):
        return DataImportExportService()
    
    def test_sql_injection_prevention(self, service):
        """测试SQL注入防护"""
        # 验证器应该拒绝可疑输入
        validator = service.ENTITY_CONFIGS['farms']['validators']['farm_type']
        
        # SQL注入尝试
        assert validator("'; DROP TABLE farms; --") == False
        assert validator("breeding OR 1=1") == False
    
    def test_xss_prevention_in_names(self, service):
        """测试名称字段XSS防护"""
        validator = service.ENTITY_CONFIGS['farms']['validators']['name']
        
        # 正常名称应该通过
        assert validator('正常羊场名称') == True
        
        # 超长名称应该被拒绝
        assert validator('x' * 200) == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

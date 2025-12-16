# ============================================================================
# 新星肉羊育种系统 - 服务层包
# NovaBreed Sheep System - Services Package
# ============================================================================

from .base import BaseService
from .farm_service import FarmService, BarnService, AnimalLocationService
from .health_service import (
    DiseaseService, HealthRecordService, VaccineTypeService,
    VaccinationRecordService, DewormingRecordService
)
from .reproduction_service import (
    EstrusRecordService, BreedingRecordService, PregnancyRecordService,
    LambingRecordService, WeaningRecordService
)
from .growth_service import GrowthRecordService
from .iot_service import IoTDeviceService, IoTDataService, AutoWeighingService
from .feed_service import (
    FeedTypeService, FeedFormulaService, FeedingPlanService,
    FeedingRecordService, FeedInventoryService
)

__all__ = [
    'BaseService',
    # Farm (3)
    'FarmService', 'BarnService', 'AnimalLocationService',
    # Health (5)
    'DiseaseService', 'HealthRecordService', 'VaccineTypeService',
    'VaccinationRecordService', 'DewormingRecordService',
    # Reproduction (5)
    'EstrusRecordService', 'BreedingRecordService', 'PregnancyRecordService',
    'LambingRecordService', 'WeaningRecordService',
    # Growth (1)
    'GrowthRecordService',
    # IoT (3)
    'IoTDeviceService', 'IoTDataService', 'AutoWeighingService',
    # Feed (5)
    'FeedTypeService', 'FeedFormulaService', 'FeedingPlanService',
    'FeedingRecordService', 'FeedInventoryService',
]

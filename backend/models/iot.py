# ============================================================================
# 新星肉羊育种系统 - 物联网数据模型
# NovaBreed Sheep System - IoT Models
#
# 文件: iot.py
# 功能: IoT设备、数据、自动称重ORM模型
# ============================================================================

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, 
    Numeric, Text, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseModel


class IoTDevice(BaseModel):
    """IoT设备模型"""
    
    __tablename__ = 'iot_devices'
    __table_args__ = (
        Index('ix_iot_devices_device_id', 'device_id', unique=True),
        Index('ix_iot_devices_farm_id', 'farm_id'),
        Index('ix_iot_devices_barn_id', 'barn_id'),
        Index('ix_iot_devices_device_type', 'device_type'),
        Index('ix_iot_devices_status', 'status'),
        CheckConstraint(
            "device_type IN ('scale', 'rfid_reader', 'temperature_sensor', 'humidity_sensor', "
            "'camera', 'water_meter', 'feed_dispenser', 'activity_monitor', 'gps_tracker')",
            name='ck_device_type'
        ),
        {'comment': 'IoT设备表'}
    )
    
    # 设备标识
    device_id = Column(String(100), unique=True, nullable=False, comment='设备ID')
    name = Column(String(200), nullable=False, comment='设备名称')
    device_type = Column(String(50), nullable=False, comment='设备类型')
    
    # 位置
    farm_id = Column(Integer, ForeignKey('farms.id'), nullable=False, comment='羊场ID')
    barn_id = Column(Integer, ForeignKey('barns.id'), comment='羊舍ID')
    location_description = Column(String(200), comment='位置描述')
    
    # 设备信息
    manufacturer = Column(String(100), comment='制造商')
    model = Column(String(100), comment='型号')
    serial_number = Column(String(100), comment='序列号')
    firmware_version = Column(String(50), comment='固件版本')
    
    # 网络信息
    ip_address = Column(String(50), comment='IP地址')
    mac_address = Column(String(50), comment='MAC地址')
    protocol = Column(String(50), comment='通信协议: mqtt/http/modbus')
    
    # 状态
    status = Column(String(20), default='online', nullable=False, 
                   comment='状态: online/offline/error/maintenance')
    last_heartbeat = Column(DateTime(timezone=True), comment='最后心跳时间')
    last_data_time = Column(DateTime(timezone=True), comment='最后数据时间')
    
    # 配置
    config = Column(JSONB, comment='设备配置')
    calibration_date = Column(Date, comment='校准日期')
    calibration_due = Column(Date, comment='下次校准日期')
    
    # 电池(如果适用)
    battery_level = Column(Integer, comment='电池电量(%)')
    
    # 关系
    data_records = relationship('IoTData', back_populates='device', lazy='dynamic')
    
    def __repr__(self):
        return f"<IoTDevice(id='{self.device_id}', type='{self.device_type}')>"
    
    @property
    def is_online(self) -> bool:
        """设备是否在线"""
        return self.status == 'online'


class IoTData(BaseModel):
    """IoT数据模型"""
    
    __tablename__ = 'iot_data'
    __table_args__ = (
        Index('ix_iot_data_device_id', 'device_id'),
        Index('ix_iot_data_timestamp', 'timestamp'),
        Index('ix_iot_data_data_type', 'data_type'),
        Index('ix_iot_data_device_timestamp', 'device_id', 'timestamp'),
        {'comment': 'IoT数据表'}
    )
    
    # 关联
    device_id = Column(Integer, ForeignKey('iot_devices.id'), nullable=False, comment='设备ID')
    
    # 时间戳
    timestamp = Column(DateTime(timezone=True), nullable=False, comment='数据时间戳')
    received_at = Column(DateTime(timezone=True), nullable=False, comment='接收时间')
    
    # 数据类型
    data_type = Column(String(50), nullable=False, 
                      comment='类型: weight/temperature/humidity/rfid/activity')
    
    # 数据值
    value = Column(Numeric(12, 4), comment='数值(用于单值数据)')
    unit = Column(String(20), comment='单位')
    
    # 复杂数据
    data_payload = Column(JSONB, comment='完整数据负载')
    """
    data_payload 结构示例:
    温度传感器: {"temperature": 25.5, "humidity": 60}
    RFID: {"rfid_tag": "xxx", "animal_id": 123}
    体重秤: {"weight": 45.5, "stable": true}
    活动监测: {"steps": 1500, "resting_time": 480}
    """
    
    # 质量标记
    is_valid = Column(Boolean, default=True, comment='数据是否有效')
    quality_flag = Column(String(50), comment='质量标记')
    
    # 关联的动物(如果适用)
    animal_id = Column(Integer, ForeignKey('animals.id'), comment='关联动物ID')
    
    # 关系
    device = relationship('IoTDevice', back_populates='data_records')
    
    def __repr__(self):
        return f"<IoTData(device={self.device_id}, type='{self.data_type}', time={self.timestamp})>"


class AutoWeighingRecord(BaseModel):
    """自动称重记录模型"""
    
    __tablename__ = 'auto_weighing_records'
    __table_args__ = (
        Index('ix_auto_weighing_animal_id', 'animal_id'),
        Index('ix_auto_weighing_weighing_time', 'weighing_time'),
        Index('ix_auto_weighing_device_id', 'device_id'),
        {'comment': '自动称重记录表'}
    )
    
    # 关联
    animal_id = Column(Integer, ForeignKey('animals.id'), comment='动物ID')
    device_id = Column(Integer, ForeignKey('iot_devices.id'), nullable=False, comment='设备ID')
    
    # 识别信息
    rfid_tag = Column(String(100), comment='RFID标签')
    identification_confidence = Column(Numeric(5, 2), comment='识别置信度(%)')
    
    # 称重数据
    weighing_time = Column(DateTime(timezone=True), nullable=False, comment='称重时间')
    raw_weight = Column(Numeric(8, 2), nullable=False, comment='原始重量(kg)')
    corrected_weight = Column(Numeric(8, 2), comment='校正重量(kg)')
    
    # 质量控制
    stable_reading = Column(Boolean, default=True, comment='读数是否稳定')
    duration_seconds = Column(Integer, comment='称重持续时间(秒)')
    outlier_flag = Column(Boolean, default=False, comment='是否异常值')
    
    # 是否同步
    synced_to_growth_record = Column(Boolean, default=False, comment='是否已同步到生长记录')
    growth_record_id = Column(Integer, ForeignKey('growth_records.id'), comment='关联的生长记录ID')
    
    # 图片(用于验证)
    image_url = Column(String(500), comment='称重图片URL')
    
    def __repr__(self):
        return f"<AutoWeighingRecord(id={self.id}, weight={self.raw_weight})>"

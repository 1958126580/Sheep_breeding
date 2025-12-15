from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import BaseModel

class BreedingValueRun(BaseModel):
    """育种值评估运行记录"""
    __tablename__ = "breeding_value_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    run_name = Column(String(200), nullable=False)
    trait_id = Column(Integer, nullable=False)
    method = Column(String(50), nullable=False)
    status = Column(String(20), default="pending") # pending, running, completed, failed
    
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    computation_time_seconds = Column(Integer, nullable=True)
    
    model_spec = Column(JSON, nullable=True)
    n_animals = Column(Integer, nullable=True)
    n_records = Column(Integer, nullable=True)
    
    results = relationship("BreedingValueResult", back_populates="run", cascade="all, delete-orphan")

class BreedingValueResult(BaseModel):
    """育种值评估结果"""
    __tablename__ = "breeding_value_results"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("breeding_value_runs.id"), nullable=False, index=True)
    animal_id = Column(Integer, nullable=False, index=True)
    
    ebv = Column(Float, nullable=False)
    reliability = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=False)
    percentile_rank = Column(Float, nullable=True)
    
    run = relationship("BreedingValueRun", back_populates="results")

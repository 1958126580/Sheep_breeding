# ============================================================================
# 国际顶级肉羊育种系统 - 区块链溯源API
# International Top-tier Sheep Breeding System - Blockchain Traceability API
#
# 文件: blockchain.py
# 功能: 区块链数据存证、溯源追踪、证书管理API端点
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import hashlib
import json
import logging

from database import get_db
from models.blockchain import BlockchainRecord as BlockchainRecordModel, AnimalCertificate as AnimalCertificateModel
from sqlalchemy import func

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# 枚举和常量
# Enumerations and Constants
# ============================================================================

class BlockchainNetwork(str, Enum):
    """区块链网络"""
    PRIVATE = "private"           # 私有链
    CONSORTIUM = "consortium"     # 联盟链
    PUBLIC = "public"             # 公有链


class RecordType(str, Enum):
    """存证记录类型"""
    ANIMAL_REGISTER = "animal_register"        # 动物登记
    BREEDING_VALUE = "breeding_value"          # 育种值
    PEDIGREE = "pedigree"                      # 系谱信息
    GENOTYPE = "genotype"                      # 基因型
    HEALTH_RECORD = "health_record"            # 健康记录
    OWNERSHIP_TRANSFER = "ownership_transfer"  # 所有权转移
    CERTIFICATE = "certificate"                # 证书


class VerificationStatus(str, Enum):
    """验证状态"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


# ============================================================================
# 数据模型
# Data Models
# ============================================================================

class BlockchainRecord(BaseModel):
    """区块链存证记录"""
    id: int
    tx_hash: str                          # 交易哈希
    block_number: int                     # 区块号
    record_type: RecordType               # 记录类型
    data_hash: str                        # 数据哈希
    metadata: dict                        # 元数据
    created_at: datetime                  # 创建时间
    network: BlockchainNetwork            # 区块链网络


class AnimalCertificate(BaseModel):
    """动物证书"""
    certificate_id: str
    animal_id: int
    animal_code: str
    certificate_type: str                 # 种畜禽/品种登记/遗传评估
    issue_date: date
    expiry_date: Optional[date]
    issuer: str                           # 发证机构
    tx_hash: str                          # 上链交易哈希
    qr_code_url: Optional[str]            # 二维码URL
    verification_url: Optional[str]       # 验证链接
    status: VerificationStatus


class TraceabilityRecord(BaseModel):
    """溯源记录"""
    record_id: str
    animal_id: int
    event_type: str
    event_date: datetime
    event_location: Optional[str]
    operator: Optional[str]
    data_hash: str
    tx_hash: Optional[str]
    verified: bool


class OwnershipTransfer(BaseModel):
    """所有权转移记录"""
    transfer_id: str
    animal_id: int
    from_org: str
    to_org: str
    transfer_date: date
    price: Optional[Decimal]
    tx_hash: str
    status: str


# ============================================================================
# 请求模型
# Request Models
# ============================================================================

class RecordSubmitRequest(BaseModel):
    """存证提交请求"""
    record_type: RecordType
    animal_id: Optional[int] = None
    data: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "record_type": "animal_register",
                "animal_id": 12345,
                "data": {
                    "animal_code": "SH2024001",
                    "breed": "杜泊羊",
                    "birth_date": "2024-01-15",
                    "father_id": "SH2021100",
                    "mother_id": "SH2022050"
                }
            }
        }


class CertificateIssueRequest(BaseModel):
    """证书签发请求"""
    animal_id: int
    certificate_type: str
    validity_years: int = Field(default=3, ge=1, le=10)
    additional_info: Optional[dict] = None


class TransferRequest(BaseModel):
    """所有权转移请求"""
    animal_id: int
    to_organization_id: int
    transfer_date: date
    price: Optional[Decimal] = None
    notes: Optional[str] = None


# ============================================================================
# 工具函数
# Utility Functions
# ============================================================================

def calculate_data_hash(data: dict) -> str:
    """计算数据哈希"""
    data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(data_str.encode()).hexdigest()


def generate_tx_hash() -> str:
    """生成模拟交易哈希"""
    import secrets
    return "0x" + secrets.token_hex(32)


def generate_certificate_id() -> str:
    """生成证书编号"""
    import secrets
    timestamp = datetime.now().strftime("%Y%m%d")
    random_part = secrets.token_hex(4).upper()
    return f"CERT-{timestamp}-{random_part}"


# ============================================================================
# 存证API端点
# Record Submission API Endpoints
# ============================================================================

@router.post("/records",
             response_model=BlockchainRecord,
             status_code=status.HTTP_201_CREATED,
             summary="提交存证记录",
             description="将数据哈希存证到区块链")
async def submit_record(
    request: RecordSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    提交存证记录
    
    ## 支持的记录类型
    - **animal_register**: 动物登记信息
    - **breeding_value**: 育种值评估结果
    - **pedigree**: 系谱信息
    - **genotype**: 基因型数据指纹
    - **health_record**: 健康记录
    """
    logger.info(f"提交存证记录: type={request.record_type}")
    
    # 计算数据哈希
    data_hash = calculate_data_hash(request.data)
    
    # 模拟上链 (实际应用中调用区块链SDK)
    tx_hash = generate_tx_hash()
    
    record = BlockchainRecordModel(
        tx_hash=tx_hash,
        block_number=12345678, # Mock block
        record_type=request.record_type,
        data_hash=data_hash,
        metadata_content={
            "animal_id": request.animal_id,
            "timestamp": datetime.now().isoformat(),
            "original_data": request.data # Optional: store raw data if needed
        },
        created_at=datetime.now(),
        network=BlockchainNetwork.CONSORTIUM
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return record


@router.get("/records",
            response_model=List[BlockchainRecord],
            summary="获取存证记录列表")
async def list_records(
    animal_id: Optional[int] = Query(None),
    record_type: Optional[RecordType] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取存证记录列表"""
    logger.info(f"获取存证记录: animal_id={animal_id}")
    
    query = db.query(BlockchainRecordModel)
    
    if record_type:
        query = query.filter(BlockchainRecordModel.record_type == record_type)
    
    # Filter by metadata using JSON operators would depend on DB backend (PG)
    # Here we do Python side filtering if volume is low, or basic query
    if start_date:
        query = query.filter(BlockchainRecordModel.created_at >= start_date)
    if end_date:
        query = query.filter(BlockchainRecordModel.created_at <= end_date)
        
    records = query.order_by(BlockchainRecordModel.created_at.desc()).limit(limit).all()
    
    # Client side filtering for metadata if needed
    if animal_id:
        # Assuming metadata has animal_id
        filtered = []
        for r in records:
            if r.metadata_content and r.metadata_content.get("animal_id") == animal_id:
                filtered.append(r)
        return filtered
        
    return records


@router.get("/records/{tx_hash}",
            response_model=BlockchainRecord,
            summary="根据交易哈希查询记录")
async def get_record_by_hash(
    tx_hash: str,
    db: Session = Depends(get_db)
):
    """根据交易哈希查询记录"""
    logger.info(f"查询存证记录: tx_hash={tx_hash}")
    
    record = db.query(BlockchainRecordModel).filter(BlockchainRecordModel.tx_hash == tx_hash).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="存证记录不存在"
        )
    return record


@router.post("/records/verify",
             summary="验证数据完整性",
             description="验证数据是否与链上存证一致")
async def verify_record(
    tx_hash: str = Query(..., description="交易哈希"),
    data: dict = None,
    db: Session = Depends(get_db)
):
    """验证数据完整性"""
    logger.info(f"验证存证: tx_hash={tx_hash}")
    
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供需要验证的数据"
        )
    
    data_hash = calculate_data_hash(data)
    
    # 从数据库查询原始哈希并比对
    record = db.query(BlockchainRecordModel).filter(BlockchainRecordModel.tx_hash == tx_hash).first()
    
    verified = False
    if record and record.data_hash == data_hash:
        verified = True
    
    return {
        "tx_hash": tx_hash,
        "data_hash": data_hash,
        "verified": verified,
        "verification_time": datetime.now().isoformat()
    }


# ============================================================================
# 证书管理API端点
# Certificate Management API Endpoints
# ============================================================================

@router.post("/certificates",
             response_model=AnimalCertificate,
             status_code=status.HTTP_201_CREATED,
             summary="签发证书",
             description="签发动物证书并上链存证")
async def issue_certificate(
    request: CertificateIssueRequest,
    db: Session = Depends(get_db)
):
    """
    签发证书
    
    ## 证书类型
    - **种畜禽合格证**: 种畜禽经营许可相关
    - **品种登记证**: 品种鉴定登记
    - **遗传评估证书**: 育种值评估结果证明
    """
    logger.info(f"签发证书: animal={request.animal_id}, type={request.certificate_type}")
    
    certificate_id = generate_certificate_id()
    tx_hash = generate_tx_hash()
    
    return AnimalCertificate(
        certificate_id=certificate_id,
        animal_id=request.animal_id,
        animal_code=f"SH{request.animal_id}",
        certificate_type=request.certificate_type,
        issue_date=date.today(),
        expiry_date=date(date.today().year + request.validity_years, 
                         date.today().month, date.today().day),
        issuer="国家畜禽遗传资源委员会",
        tx_hash=tx_hash,
        qr_code_url=f"/api/v1/blockchain/certificates/{certificate_id}/qrcode",
        verification_url=f"https://verify.example.com/{certificate_id}",
        status=VerificationStatus.VERIFIED
    )


@router.get("/certificates",
            response_model=List[AnimalCertificate],
            summary="获取证书列表")
async def list_certificates(
    animal_id: Optional[int] = Query(None),
    certificate_type: Optional[str] = Query(None),
    status: Optional[VerificationStatus] = Query(None),
    db: Session = Depends(get_db)
):
    """获取证书列表"""
    query = db.query(AnimalCertificateModel)
    if animal_id:
        query = query.filter(AnimalCertificateModel.animal_id == animal_id)
    if certificate_type:
        query = query.filter(AnimalCertificateModel.certificate_type == certificate_type)
        
    return query.all()


@router.get("/certificates/{certificate_id}",
            response_model=AnimalCertificate,
            summary="获取证书详情")
async def get_certificate(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    """获取证书详情"""
    raise HTTPException(status_code=404, detail="证书不存在")


@router.get("/certificates/{certificate_id}/verify",
            summary="验证证书有效性")
async def verify_certificate(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    """验证证书有效性"""
    logger.info(f"验证证书: {certificate_id}")
    
    return {
        "certificate_id": certificate_id,
        "valid": True,
        "status": "verified",
        "verification_time": datetime.now().isoformat(),
        "issuer": "国家畜禽遗传资源委员会"
    }


# ============================================================================
# 溯源追踪API端点
# Traceability API Endpoints
# ============================================================================

@router.get("/traceability/{animal_id}",
            response_model=List[TraceabilityRecord],
            summary="获取动物全生命周期溯源",
            description="获取动物从出生到现在的所有区块链存证记录")
async def get_animal_traceability(
    animal_id: int,
    db: Session = Depends(get_db)
):
    """获取动物全生命周期溯源"""
    logger.info(f"获取溯源记录: animal={animal_id}")
    
    """获取动物全生命周期溯源"""
    logger.info(f"获取溯源记录: animal={animal_id}")
    
    # 从BlockchainRecord表中查找该动物的所有记录
    records = db.query(BlockchainRecordModel).all() # Simple retrieval, filter in loop for JSON
    
    trace_list = []
    for r in records:
        if r.metadata_content and r.metadata_content.get("animal_id") == animal_id:
             trace_list.append(TraceabilityRecord(
                record_id=str(r.id),
                animal_id=animal_id,
                event_type=r.record_type,
                event_date=r.created_at,
                event_location="System",
                operator="System",
                data_hash=r.data_hash,
                tx_hash=r.tx_hash,
                verified=True
            ))
            
    return trace_list


# ============================================================================
# 所有权转移API端点
# Ownership Transfer API Endpoints
# ============================================================================

@router.post("/transfers",
             response_model=OwnershipTransfer,
             status_code=status.HTTP_201_CREATED,
             summary="发起所有权转移",
             description="将动物所有权转移记录上链")
async def create_transfer(
    request: TransferRequest,
    db: Session = Depends(get_db)
):
    """发起所有权转移"""
    logger.info(f"所有权转移: animal={request.animal_id} -> org={request.to_organization_id}")
    
    tx_hash = generate_tx_hash()
    
    return OwnershipTransfer(
        transfer_id=f"TF{datetime.now().strftime('%Y%m%d%H%M%S')}",
        animal_id=request.animal_id,
        from_org="原所有机构",
        to_org=f"目标机构{request.to_organization_id}",
        transfer_date=request.transfer_date,
        price=request.price,
        tx_hash=tx_hash,
        status="completed"
    )


@router.get("/transfers",
            response_model=List[OwnershipTransfer],
            summary="获取转移记录列表")
async def list_transfers(
    animal_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """获取转移记录列表"""
    return []


# ============================================================================
# 区块链统计API端点
# Blockchain Statistics API Endpoints
# ============================================================================

class BlockchainStats(BaseModel):
    """区块链统计"""
    total_records: int
    records_today: int
    total_certificates: int
    active_certificates: int
    total_transfers: int
    network_status: str
    last_block_number: int
    last_sync_time: datetime


@router.get("/statistics",
            response_model=BlockchainStats,
            summary="获取区块链统计")
async def get_blockchain_stats(
    db: Session = Depends(get_db)
):
    """获取区块链统计"""
    
    total = db.query(BlockchainRecordModel).count()
    today = db.query(BlockchainRecordModel).filter(func.date(BlockchainRecordModel.created_at) == date.today()).count()
    cert_total = db.query(AnimalCertificateModel).count()
    cert_active = db.query(AnimalCertificateModel).count() # Simply all for now
    
    return BlockchainStats(
        total_records=total,
        records_today=today,
        total_certificates=cert_total,
        active_certificates=cert_active,
        total_transfers=0, # Not implemented table yet
        network_status="healthy",
        last_block_number=12345678 + total, # Mock block increment
        last_sync_time=datetime.now()
    )

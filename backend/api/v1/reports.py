# ============================================================================
# 国际顶级肉羊育种系统 - 报表与分析API
# International Top-tier Sheep Breeding System - Reports API
#
# 文件: reports.py
# 功能: 育种报告、遗传趋势、近交监控、经济效益报表API端点
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
import logging
import io

from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# 报表请求模型
# Report Request Models
# ============================================================================

class ReportRequest(BaseModel):
    """报表请求基础模型"""
    organization_id: Optional[int] = Field(None, description="机构ID")
    farm_id: Optional[int] = Field(None, description="羊场ID")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    format: str = Field(default="json", description="输出格式: json/excel/pdf")


# ============================================================================
# 育种年度报告模型
# Annual Breeding Report Models
# ============================================================================

class PopulationSummary(BaseModel):
    """种群概况"""
    total_animals: int
    rams: int
    ewes: int
    lambs: int
    breeding_rams: int
    breeding_ewes: int


class ReproductionSummary(BaseModel):
    """繁殖性能汇总"""
    total_breedings: int
    conception_rate: float
    total_lambings: int
    avg_litter_size: float
    lamb_survival_rate: float
    lambs_weaned: int


class GeneticProgress(BaseModel):
    """遗传进展"""
    trait_name: str
    avg_ebv_sires: float
    avg_ebv_dams: float
    avg_ebv_progeny: float
    genetic_trend: float  # 遗传进展每年


class AnnualBreedingReport(BaseModel):
    """育种年度报告"""
    report_year: int
    organization_name: str
    farm_name: Optional[str]
    report_date: datetime
    population: PopulationSummary
    reproduction: ReproductionSummary
    genetic_progress: List[GeneticProgress]
    recommendations: List[str]


# ============================================================================
# 遗传趋势模型
# Genetic Trend Models
# ============================================================================

class GeneticTrendPoint(BaseModel):
    """遗传趋势数据点"""
    year: int
    birth_year: int
    avg_ebv: float
    std_ebv: float
    n_animals: int


class GeneticTrendReport(BaseModel):
    """遗传趋势报告"""
    trait_id: int
    trait_name: str
    trait_unit: Optional[str]
    trend_data: List[GeneticTrendPoint]
    annual_genetic_gain: float  # 每年遗传进展
    total_genetic_gain: float  # 总遗传进展


# ============================================================================
# 近交监控模型
# Inbreeding Monitoring Models
# ============================================================================

class InbreedingDistribution(BaseModel):
    """近交系数分布"""
    range_label: str  # e.g., "0-5%", "5-10%"
    count: int
    percentage: float


class InbreedingReport(BaseModel):
    """近交监控报告"""
    report_date: datetime
    avg_pedigree_inbreeding: float
    avg_genomic_inbreeding: Optional[float]
    max_inbreeding: float
    animals_over_threshold: int  # 超过阈值(如6.25%)的动物数
    distribution: List[InbreedingDistribution]
    high_risk_matings: int  # 高风险配对数
    recommendations: List[str]


# ============================================================================
# 选种候选模型
# Selection Candidate Models
# ============================================================================

class SelectionCandidate(BaseModel):
    """选种候选"""
    animal_id: int
    animal_code: str
    name: Optional[str]
    sex: str
    birth_date: date
    breed: str
    composite_index: float
    rank: int
    ebv_values: dict
    inbreeding_coefficient: float
    recommendation: str


class SelectionReport(BaseModel):
    """选种报告"""
    report_date: datetime
    selection_type: str
    total_candidates: int
    selected_count: int
    selection_intensity: float
    avg_index_selected: float
    candidates: List[SelectionCandidate]


# ============================================================================
# 经济效益模型
# Economic Analysis Models
# ============================================================================

class EconomicMetric(BaseModel):
    """经济指标"""
    metric_name: str
    value: Decimal
    unit: str
    change_from_last_year: Optional[float]


class EconomicReport(BaseModel):
    """经济效益报告"""
    report_year: int
    farm_id: int
    farm_name: str
    metrics: List[EconomicMetric]
    total_revenue: Decimal
    total_cost: Decimal
    net_profit: Decimal
    profit_per_animal: Decimal
    roi: float  # 投资回报率


# ============================================================================
# 育种报告API端点
# Breeding Report API Endpoints
# ============================================================================

@router.get("/breeding/annual",
            response_model=AnnualBreedingReport,
            summary="生成育种年度报告",
            description="生成指定年份的育种工作年度报告")
async def get_annual_breeding_report(
    year: int = Query(..., description="报告年份"),
    organization_id: Optional[int] = Query(None),
    farm_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """生成育种年度报告"""
    logger.info(f"生成育种年度报告: year={year}")
    
    # TODO: 从数据库汇总数据生成报告
    return AnnualBreedingReport(
        report_year=year,
        organization_name="示范羊场",
        farm_name="核心育种场",
        report_date=datetime.now(),
        population=PopulationSummary(
            total_animals=1500,
            rams=80,
            ewes=850,
            lambs=570,
            breeding_rams=50,
            breeding_ewes=650
        ),
        reproduction=ReproductionSummary(
            total_breedings=720,
            conception_rate=85.5,
            total_lambings=615,
            avg_litter_size=1.82,
            lamb_survival_rate=92.3,
            lambs_weaned=1038
        ),
        genetic_progress=[
            GeneticProgress(
                trait_name="断奶重",
                avg_ebv_sires=2.85,
                avg_ebv_dams=1.25,
                avg_ebv_progeny=2.05,
                genetic_trend=0.35
            ),
            GeneticProgress(
                trait_name="产羔数",
                avg_ebv_sires=0.12,
                avg_ebv_dams=0.18,
                avg_ebv_progeny=0.15,
                genetic_trend=0.02
            )
        ],
        recommendations=[
            "建议增加断奶重选择强度",
            "关注近交系数上升趋势",
            "考虑引进优良种公羊"
        ]
    )


@router.get("/genetic-trend",
            response_model=List[GeneticTrendReport],
            summary="获取遗传趋势报告",
            description="获取指定性状的遗传趋势分析")
async def get_genetic_trend_report(
    trait_ids: List[int] = Query(..., description="性状ID列表"),
    organization_id: Optional[int] = Query(None),
    start_year: int = Query(2015, description="起始年份"),
    end_year: int = Query(2024, description="结束年份"),
    db: Session = Depends(get_db)
):
    """获取遗传趋势报告"""
    logger.info(f"获取遗传趋势报告: traits={trait_ids}")
    
    # TODO: 从数据库计算遗传趋势
    results = []
    for trait_id in trait_ids:
        results.append(GeneticTrendReport(
            trait_id=trait_id,
            trait_name=f"性状{trait_id}",
            trait_unit="kg",
            trend_data=[
                GeneticTrendPoint(year=y, birth_year=y, avg_ebv=0.3*(y-2015), std_ebv=0.8, n_animals=100+y*10)
                for y in range(start_year, end_year+1)
            ],
            annual_genetic_gain=0.32,
            total_genetic_gain=2.88
        ))
    
    return results


@router.get("/inbreeding",
            response_model=InbreedingReport,
            summary="获取近交监控报告",
            description="获取近交系数分析和监控报告")
async def get_inbreeding_report(
    organization_id: Optional[int] = Query(None),
    farm_id: Optional[int] = Query(None),
    threshold: float = Query(0.0625, description="近交系数阈值"),
    db: Session = Depends(get_db)
):
    """获取近交监控报告"""
    logger.info("获取近交监控报告")
    
    return InbreedingReport(
        report_date=datetime.now(),
        avg_pedigree_inbreeding=0.032,
        avg_genomic_inbreeding=0.028,
        max_inbreeding=0.125,
        animals_over_threshold=45,
        distribution=[
            InbreedingDistribution(range_label="0-2.5%", count=850, percentage=56.7),
            InbreedingDistribution(range_label="2.5-5%", count=420, percentage=28.0),
            InbreedingDistribution(range_label="5-10%", count=185, percentage=12.3),
            InbreedingDistribution(range_label=">10%", count=45, percentage=3.0)
        ],
        high_risk_matings=12,
        recommendations=[
            "避免近交系数>10%的个体留种",
            "建议引进无血缘关系的外源种羊",
            "优化选配方案以控制近交增量"
        ]
    )


@router.get("/selection",
            response_model=SelectionReport,
            summary="生成选种报告",
            description="生成选种候选和建议报告")
async def get_selection_report(
    organization_id: Optional[int] = Query(None),
    selection_type: str = Query("breeding", description="选择类型: breeding/replacement"),
    sex: Optional[str] = Query(None, description="性别: male/female"),
    top_n: int = Query(50, description="前N名"),
    db: Session = Depends(get_db)
):
    """生成选种报告"""
    logger.info(f"生成选种报告: type={selection_type}")
    
    # TODO: 从数据库生成候选列表
    return SelectionReport(
        report_date=datetime.now(),
        selection_type=selection_type,
        total_candidates=200,
        selected_count=top_n,
        selection_intensity=1.4,
        avg_index_selected=125.6,
        candidates=[]
    )


@router.get("/economic",
            response_model=EconomicReport,
            summary="获取经济效益报告",
            description="获取羊场经济效益分析报告")
async def get_economic_report(
    farm_id: int = Query(..., description="羊场ID"),
    year: int = Query(..., description="分析年份"),
    db: Session = Depends(get_db)
):
    """获取经济效益报告"""
    logger.info(f"获取经济效益报告: farm={farm_id}, year={year}")
    
    return EconomicReport(
        report_year=year,
        farm_id=farm_id,
        farm_name="示范羊场",
        metrics=[
            EconomicMetric(metric_name="种羊销售收入", value=Decimal("1250000"), unit="元", change_from_last_year=8.5),
            EconomicMetric(metric_name="育肥羊销售收入", value=Decimal("2150000"), unit="元", change_from_last_year=12.3),
            EconomicMetric(metric_name="饲料成本", value=Decimal("980000"), unit="元", change_from_last_year=-3.2),
            EconomicMetric(metric_name="人工成本", value=Decimal("450000"), unit="元", change_from_last_year=5.0)
        ],
        total_revenue=Decimal("3400000"),
        total_cost=Decimal("2100000"),
        net_profit=Decimal("1300000"),
        profit_per_animal=Decimal("867"),
        roi=61.9
    )


# ============================================================================
# 报表导出API端点
# Report Export API Endpoints
# ============================================================================

@router.post("/export/excel",
             summary="导出Excel报表",
             description="将报表导出为Excel格式")
async def export_to_excel(
    report_type: str = Query(..., description="报表类型"),
    request: ReportRequest = None,
    db: Session = Depends(get_db)
):
    """导出Excel报表"""
    logger.info(f"导出Excel报表: type={report_type}")
    
    # TODO: 生成Excel文件
    # 暂时返回一个模拟的响应
    return {
        "message": "Excel导出功能开发中",
        "report_type": report_type,
        "format": "xlsx"
    }


@router.post("/export/pdf",
             summary="导出PDF报表",
             description="将报表导出为PDF格式")
async def export_to_pdf(
    report_type: str = Query(..., description="报表类型"),
    request: ReportRequest = None,
    db: Session = Depends(get_db)
):
    """导出PDF报表"""
    logger.info(f"导出PDF报表: type={report_type}")
    
    return {
        "message": "PDF导出功能开发中",
        "report_type": report_type,
        "format": "pdf"
    }


# ============================================================================
# 仪表板数据API端点
# Dashboard Data API Endpoints
# ============================================================================

class DashboardKPI(BaseModel):
    """仪表板KPI"""
    kpi_name: str
    current_value: float
    previous_value: Optional[float]
    unit: str
    change_percentage: Optional[float]
    trend: str  # up/down/stable


class DashboardData(BaseModel):
    """仪表板数据"""
    last_updated: datetime
    kpis: List[DashboardKPI]
    alerts: List[dict]
    recent_activities: List[dict]


@router.get("/dashboard",
            response_model=DashboardData,
            summary="获取仪表板数据",
            description="获取系统仪表板展示数据")
async def get_dashboard_data(
    organization_id: Optional[int] = Query(None),
    farm_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """获取仪表板数据"""
    logger.info("获取仪表板数据")
    
    return DashboardData(
        last_updated=datetime.now(),
        kpis=[
            DashboardKPI(kpi_name="存栏总数", current_value=1500, previous_value=1420, unit="头", change_percentage=5.6, trend="up"),
            DashboardKPI(kpi_name="平均育种值", current_value=2.35, previous_value=2.12, unit="kg", change_percentage=10.8, trend="up"),
            DashboardKPI(kpi_name="受胎率", current_value=85.5, previous_value=82.3, unit="%", change_percentage=3.9, trend="up"),
            DashboardKPI(kpi_name="近交系数", current_value=3.2, previous_value=2.8, unit="%", change_percentage=14.3, trend="up")
        ],
        alerts=[
            {"type": "warning", "message": "5只动物近交系数超过10%", "created_at": datetime.now().isoformat()},
            {"type": "info", "message": "12只母羊预计本周产羔", "created_at": datetime.now().isoformat()}
        ],
        recent_activities=[
            {"action": "新增育种值评估", "user": "admin", "time": datetime.now().isoformat()},
            {"action": "导入基因型数据", "user": "技术员1", "time": datetime.now().isoformat()}
        ]
    )

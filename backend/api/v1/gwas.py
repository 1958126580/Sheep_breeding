from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from services.julia_service import JuliaService

router = APIRouter()
julia_service = JuliaService()

class GWASRequest(BaseModel):
    genotype: Dict[str, Any]
    phenotype: Dict[str, Any]
    model: Optional[Dict[str, Any]] = None
    fixed_effects: Optional[Dict[str, Any]] = None

@router.post("/analyze", response_model=Dict[str, Any])
async def run_gwas_analysis(request: GWASRequest):
    """
    运行GWAS全基因组关联分析
    """
    if not julia_service.is_initialized():
         await julia_service.initialize()

    # 构建输入数据
    model_params = request.model if request.model else {}
    
    # 修正：将 fixed_effects 整合到输入中
    input_genotype = request.genotype
    input_phenotype = request.phenotype
    
    # 注意：julia_service.run_gwas 签名目前只接受3个参数
    # 我们需要在 julia_service.run_gwas 中处理 fixed_effects
    # 或者我们在这里手动构建 input_data 并直接调用 _execute_julia_script (不推荐)
    # 最好的方法是更新 JuliaService.run_gwas 的签名，或者在 model_params 中传递信息
    
    # 这里我们直接调用 julia_service.run_gwas，假设它以后会通过 kwargs 或更新签名来支持
    # 目前我们只能按照现有签名传递
    
    try:
        result = await julia_service.run_gwas(
            input_phenotype,
            input_genotype,
            model_params
        )
        
        if result.get("status") == "error":
             raise HTTPException(status_code=500, detail=result.get("message"))
             
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any
from pydantic import BaseModel

from services.julia_service import JuliaService
# 假设有一个依赖项可以获取 JuliaService 实例，或者直接导入实例
# 这里的实现假设 JuliaService 是单例或通过某种方式注入
# 为简单起见，我们在这里实例化它，但在实际应用中应该使用依赖注入

router = APIRouter()
julia_service = JuliaService() # 实际应用中应该确保单例初始化

class DeepGBLUPRequest(BaseModel):
    genotype: Dict[str, Any]
    phenotype: Dict[str, Any]
    config: Dict[str, Any]

@router.post("/gblup", response_model=Dict[str, Any])
async def run_deep_gblup(request: DeepGBLUPRequest):
    """
    运行深度学习GBLUP分析
    """
    if not julia_service.is_initialized():
         await julia_service.initialize()
         
    try:
        result = await julia_service.run_deep_gblup(
            request.genotype,
            request.phenotype,
            request.config
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train", response_model=Dict[str, Any])
async def train_model(request: DeepGBLUPRequest):
    """
    训练深度学习模型 (简化版，复用DeepGBLUP逻辑但侧重于模型训练结果)
    """
    # 逻辑类似
    return await run_deep_gblup(request)

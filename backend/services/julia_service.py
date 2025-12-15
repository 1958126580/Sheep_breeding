# ============================================================================
# 国际顶级肉羊育种系统 - Julia服务
# International Top-tier Sheep Breeding System - Julia Service
#
# 文件: julia_service.py
# 功能: Julia运行时管理和计算任务调用
# ============================================================================

import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio

from config import settings

logger = logging.getLogger(__name__)

class JuliaService:
    """
    Julia服务类
    
    管理Julia运行时，执行育种值计算任务
    """
    
    def __init__(self):
        self.julia_path = settings.JULIA_PATH
        self.project_path = Path(settings.JULIA_PROJECT_PATH).absolute()
        self.initialized = False
        self.process = None
        
    async def initialize(self):
        """
        初始化Julia运行时
        
        - 检查Julia可执行文件
        - 加载项目环境
        - 预编译模块
        """
        logger.info("初始化Julia运行时...")
        logger.info(f"Julia路径: {self.julia_path}")
        logger.info(f"项目路径: {self.project_path}")
        
        try:
            # 检查Julia版本
            result = subprocess.run(
                [self.julia_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info(f"Julia版本: {result.stdout.strip()}")
            else:
                raise RuntimeError(f"Julia版本检查失败: {result.stderr}")
            
            # 实例化项目环境
            logger.info("实例化Julia项目环境...")
            instantiate_cmd = f"""
            using Pkg
            Pkg.activate("{str(self.project_path)}")
            Pkg.instantiate()
            """
            
            result = subprocess.run(
                [self.julia_path, "-e", instantiate_cmd],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                logger.error(f"Julia环境实例化失败: {result.stderr}")
                raise RuntimeError("Julia环境实例化失败")
            
            logger.info("Julia环境实例化完成")
            
            # 预编译核心模块
            logger.info("预编译核心模块...")
            precompile_cmd = f"""
            using Pkg
            Pkg.activate("{str(self.project_path)}")
            include("{str(self.project_path / 'BreedingCore.jl')}")
            """
            
            result = subprocess.run(
                [self.julia_path, "-e", precompile_cmd],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("核心模块预编译完成")
            else:
                logger.warning(f"核心模块预编译警告: {result.stderr}")
            
            self.initialized = True
            logger.info("Julia运行时初始化完成!")
            
        except Exception as e:
            logger.error(f"Julia运行时初始化失败: {str(e)}")
            raise
    
    def is_initialized(self) -> bool:
        """检查Julia运行时是否已初始化"""
        return self.initialized
    
    async def run_blup(self, 
                      phenotype_data: Dict[str, Any],
                      pedigree_data: Dict[str, Any],
                      model_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行BLUP分析
        
        参数:
            phenotype_data: 表型数据
            pedigree_data: 系谱数据
            model_params: 模型参数
        
        返回:
            分析结果字典
        """
        logger.info("运行BLUP分析...")
        
        # 准备输入数据
        input_data = {
            "phenotype": phenotype_data,
            "pedigree": pedigree_data,
            "model": model_params
        }
        
        # 调用Julia脚本
        result = await self._execute_julia_script(
            "run_blup_analysis.jl",
            input_data
        )
        
        return result
    
    async def run_gblup(self,
                       phenotype_data: Dict[str, Any],
                       genotype_data: Dict[str, Any],
                       model_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行GBLUP分析
        
        参数:
            phenotype_data: 表型数据
            genotype_data: 基因型数据
            model_params: 模型参数
        
        返回:
            分析结果字典
        """
        logger.info("运行GBLUP分析...")
        
        input_data = {
            "phenotype": phenotype_data,
            "genotype": genotype_data,
            "model": model_params
        }
        
        result = await self._execute_julia_script(
            "run_gblup_analysis.jl",
            input_data
        )
        
        return result
    
    async def run_ssgblup(self,
                         phenotype_data: Dict[str, Any],
                         pedigree_data: Dict[str, Any],
                         genotype_data: Dict[str, Any],
                         model_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行ssGBLUP分析
        
        参数:
            phenotype_data: 表型数据
            pedigree_data: 系谱数据
            genotype_data: 基因型数据
            model_params: 模型参数
        
        返回:
            分析结果字典
        """
        logger.info("运行ssGBLUP分析...")
        
        input_data = {
            "phenotype": phenotype_data,
            "pedigree": pedigree_data,
            "genotype": genotype_data,
            "model": model_params
        }
        
        result = await self._execute_julia_script(
            "run_ssgblup_analysis.jl",
            input_data
        )
        
        return result
    
    async def _execute_julia_script(self,
                                    script_name: str,
                                    input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Julia脚本
        
        参数:
            script_name: 脚本文件名
            input_data: 输入数据
        
        返回:
            执行结果
        """
        if not self.initialized:
            raise RuntimeError("Julia运行时未初始化")
        
        # 创建临时输入文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(input_data, f)
            input_file = f.name
        
        # 创建临时输出文件
        output_file = tempfile.mktemp(suffix='.json')
        
        try:
            # 构建Julia命令
            script_path = self.project_path / "scripts" / script_name
            julia_cmd = f"""
            using Pkg
            Pkg.activate("{str(self.project_path)}")
            
            using JSON3
            include("{str(script_path)}")
            
            # 读取输入数据
            input_data = JSON3.read("{input_file}")
            
            # 执行分析
            result = run_analysis(input_data)
            
            # 写入输出
            open("{output_file}", "w") do io
                JSON3.write(io, result)
            end
            """
            
            # 设置环境变量
            env = {
                **subprocess.os.environ,
                "JULIA_NUM_THREADS": str(settings.JULIA_NUM_THREADS)
            }
            
            if settings.GPU_ENABLED:
                env["CUDA_VISIBLE_DEVICES"] = settings.CUDA_VISIBLE_DEVICES
            
            # 执行Julia命令
            logger.info(f"执行Julia脚本: {script_name}")
            
            process = await asyncio.create_subprocess_exec(
                self.julia_path,
                "-e",
                julia_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Julia脚本执行失败: {stderr.decode()}")
                raise RuntimeError(f"Julia脚本执行失败: {stderr.decode()}")
            
            # 读取输出结果
            with open(output_file, 'r') as f:
                result = json.load(f)
            
            logger.info(f"Julia脚本执行成功: {script_name}")
            return result
            
        finally:
            # 清理临时文件
            Path(input_file).unlink(missing_ok=True)
            Path(output_file).unlink(missing_ok=True)
    
    async def shutdown(self):
        """关闭Julia运行时"""
        logger.info("关闭Julia运行时...")
        self.initialized = False
        logger.info("Julia运行时已关闭")

    # ========================================================================
    # 新增高级分析方法
    # Advanced Analysis Methods
    # ========================================================================
    
    async def run_gwas(self,
                      phenotype_data: Dict[str, Any],
                      genotype_data: Dict[str, Any],
                      model_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行GWAS分析
        
        参数:
            phenotype_data: 表型数据
            genotype_data: 基因型数据 (SNP矩阵)
            model_params: GWAS模型参数
        
        返回:
            GWAS结果字典,包含SNP效应、P值、曼哈顿图数据等
        """
        logger.info("运行GWAS分析...")
        
        input_data = {
            "phenotype": phenotype_data,
            "genotype": genotype_data,
            "model": model_params
        }
        
        result = await self._execute_julia_script(
            "run_gwas_analysis.jl",
            input_data
        )
        
        return result
    
    async def run_multitriat_blup(self,
                                  phenotype_data: Dict[str, Any],
                                  pedigree_data: Dict[str, Any],
                                  model_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行多性状BLUP分析
        
        参数:
            phenotype_data: 多性状表型数据
            pedigree_data: 系谱数据
            model_params: 模型参数(包含遗传协方差矩阵)
        
        返回:
            多性状育种值结果
        """
        logger.info("运行多性状BLUP分析...")
        
        input_data = {
            "phenotype": phenotype_data,
            "pedigree": pedigree_data,
            "model": model_params
        }
        
        result = await self._execute_julia_script(
            "run_mtblup_analysis.jl",
            input_data
        )
        
        return result
    
    async def run_federated_blup(self,
                                 client_data: List[Dict[str, Any]],
                                 config: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行联邦BLUP分析
        
        参数:
            client_data: 各机构客户端数据列表
            config: 联邦学习配置
        
        返回:
            联邦育种值结果
        """
        logger.info("运行联邦BLUP分析...")
        
        input_data = {
            "clients": client_data,
            "config": config
        }
        
        result = await self._execute_julia_script(
            "run_federated_blup.jl",
            input_data
        )
        
        return result
    
    async def run_deep_gblup(self,
                            genotype_data: Dict[str, Any],
                            phenotype_data: Dict[str, Any],
                            config: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行深度学习GBLUP分析
        
        参数:
            genotype_data: 基因型数据
            phenotype_data: 表型数据
            config: 深度学习配置
        
        返回:
            深度学习育种值预测结果
        """
        logger.info("运行深度学习GBLUP分析...")
        
        input_data = {
            "genotype": genotype_data,
            "phenotype": phenotype_data,
            "config": config
        }
        
        result = await self._execute_julia_script(
            "run_deep_gblup.jl",
            input_data
        )
        
        return result
    
    async def calculate_selection_index(self,
                                       ebv_data: Dict[str, Any],
                                       weights: Dict[str, float]) -> Dict[str, Any]:
        """
        计算选择指数
        
        参数:
            ebv_data: 各性状育种值数据
            weights: 经济权重
        
        返回:
            选择指数结果和排名
        """
        logger.info("计算选择指数...")
        
        input_data = {
            "ebv": ebv_data,
            "weights": weights
        }
        
        result = await self._execute_julia_script(
            "calculate_selection_index.jl",
            input_data
        )
        
        return result


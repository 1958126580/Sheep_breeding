# ============================================================================
# 新星肉羊育种系统 - GWAS分析脚本
# NovaBreed Sheep System - GWAS Analysis Script
# ============================================================================

using JSON3
using LinearAlgebra
using Statistics
using GWASAnalysis

"""
    run_analysis(input_data)

运行GWAS分析
"""
function run_analysis(input_data::Dict)
    try
        # 1. 解析输入数据
        genotype = input_data["genotype"]
        phenotype = input_data["phenotype"]
        model_params = input_data["model"]
        
        # 转换基因型矩阵 (samples × markers)
        # 假设输入是二维数组列表
        Z = hcat([Vector{Float64}(col) for col in genotype["matrix"]]...)'
        
        # 转换表型向量
        y = Vector{Float64}(phenotype["values"])
        
        # 转换固定效应矩阵 (如果存在)
        X = nothing
        if haskey(input_data, "fixed_effects") && !isempty(input_data["fixed_effects"])
             X = hcat([Vector{Float64}(col) for col in input_data["fixed_effects"]]...)'
        end

        # SNP信息
        snp_ids = Vector{String}(get(genotype, "snp_ids", String[]))
        chromosomes = Vector{Int}(get(genotype, "chromosomes", Int[]))
        positions = Vector{Int}(get(genotype, "positions", Int[]))
        
        # 2. 配置GWAS参数
        params = GWASModelParams(
            fixed_effects = Vector{String}(get(model_params, "fixed_effects_names", String[])),
            h2 = Float64(get(model_params, "h2", 0.3)),
            alpha = Float64(get(model_params, "alpha", 0.05)),
            maf_threshold = Float64(get(model_params, "maf_threshold", 0.01)),
            missing_threshold = Float64(get(model_params, "missing_threshold", 0.1))
        )
        
        method = String(get(model_params, "method", "mlma_loco"))
        
        # 3. 运行GWAS
        result = run_gwas(
            y, Z, X;
            method = method,
            snp_ids = snp_ids,
            chromosomes = chromosomes,
            positions = positions,
            params = params
        )
        
        # 4. 生成图表数据
        manhattan_data = manhattan_plot_data(result)
        qq_data = qq_plot_data(result)
        
        # 5. 格式化输出
        output = Dict(
            "status" => "success",
            "summary" => Dict(
                "n_samples" => result.n_samples,
                "n_snps" => result.n_snps,
                "lambda_gc" => result.lambda_gc,
                "method" => result.method
            ),
            "manhattan_plot" => manhattan_data,
            "qq_plot" => qq_data,
            "top_snps" => [
                Dict(
                    "id" => result.snp_ids[i],
                    "chr" => result.chromosomes[i],
                    "pos" => result.positions[i],
                    "pvalue" => result.pvalues[i],
                    "effect" => result.effects[i]
                ) 
                for i in sortperm(result.pvalues)[1:min(50, end)]
            ]
        )
        
        return output
        
    catch e
        return Dict(
            "status" => "error",
            "message" => string(e),
            "stacktrace" => stacktrace(catch_backtrace())
        )
    end
end

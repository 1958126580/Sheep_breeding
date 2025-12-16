# ============================================================================
# 新星肉羊育种系统 - Julia高级算法模块
# NovaBreed Sheep System - Advanced Algorithms Module
#
# 模块: AdvancedMethods
# 功能: GBLUP、ssGBLUP、贝叶斯方法等高级算法
# 作者: AdvancedGenomics Team
# 版本: 1.0.0
# Julia版本: 1.12.2
# ============================================================================

module AdvancedMethods

using LinearAlgebra
using SparseArrays
using Statistics
using Distributions
using ProgressMeter
using CUDA

# 引入BreedingCore模块的类型
include("BreedingCore.jl")
using .BreedingCore

export run_gblup, run_ssgblup, run_bayesian_regression
export run_bayes_a, run_bayes_b, run_bayes_c, run_bayes_r

# ============================================================================
# GBLUP算法实现
# GBLUP Algorithm Implementation
# ============================================================================

"""
    run_gblup(pheno::PhenotypeData, geno::GenotypeData, model::GeneticModel;
              use_gpu=false, solver="cholesky")

运行基因组BLUP分析（GBLUP）

使用基因组关系矩阵G代替系谱关系矩阵A

# 参数
- `pheno::PhenotypeData`: 表型数据
- `geno::GenotypeData`: 基因型数据  
- `model::GeneticModel`: 遗传模型
- `use_gpu::Bool`: 是否使用GPU加速
- `solver::String`: 求解器类型

# 返回
- `Dict`: 包含基因组育种值(GEBV)和其他结果
"""
function run_gblup(pheno::PhenotypeData, geno::GenotypeData, model::GeneticModel;
                   use_gpu=false, solver="cholesky")
    println("\n" * "="^70)
    println("运行GBLUP分析")
    println("="^70)
    println("动物数: $(geno.n_animals)")
    println("标记数: $(geno.n_markers)")
    println("记录数: $(pheno.n)")
    println("遗传力: $(model.h2)")
    println("GPU加速: $use_gpu")
    println("="^70)
    
    # 构建G矩阵
    G = BreedingCore.build_G_matrix(geno, method="VanRaden", use_gpu=use_gpu)
    
    # 构建设计矩阵
    n_records = pheno.n
    n_animals = geno.n_animals
    
    # X矩阵（固定效应）
    X = ones(Float64, n_records, 1)
    
    # Z矩阵（随机效应）
    animal_to_idx = Dict(geno.animal_id[i] => i for i in 1:n_animals)
    Z = spzeros(Float64, n_records, n_animals)
    for i in 1:n_records
        if haskey(animal_to_idx, pheno.animal_id[i])
            animal_idx = animal_to_idx[pheno.animal_id[i]]
            Z[i, animal_idx] = 1.0
        end
    end
    
    y = pheno.trait_values
    
    # 计算G逆矩阵
    println("\n计算G逆矩阵...")
    G_inv = inv(G)
    
    # 计算λ
    λ = model.σ2_e / model.σ2_a
    
    println("构建混合模型方程...")
    
    # 构建MME
    XtX = X' * X
    XtZ = X' * Z
    ZtX = Z' * X
    ZtZ = Z' * Z
    
    C11 = sparse(XtX)
    C12 = sparse(XtZ)
    C21 = sparse(ZtX)
    C22 = ZtZ + λ * sparse(G_inv)
    
    C = [C11 C12; C21 C22]
    rhs = [X' * y; Z' * y]
    
    println("求解混合模型方程...")
    println("方程维度: $(size(C, 1)) × $(size(C, 2))")
    
    # 求解
    sol = C \ rhs
    
    n_fixed = size(X, 2)
    β = sol[1:n_fixed]
    gebv = sol[(n_fixed+1):end]
    
    # 计算可靠性
    println("\n计算可靠性...")
    C_inv_diag = diag(inv(Matrix(C)))
    PEV = C_inv_diag[(n_fixed+1):end] .* model.σ2_e
    reliability = 1.0 .- (PEV ./ model.σ2_a)
    reliability = clamp.(reliability, 0.0, 1.0)
    accuracy = sqrt.(reliability)
    
    println("\n分析完成!")
    println("平均可靠性: $(round(mean(reliability), digits=4))")
    println("平均准确性: $(round(mean(accuracy), digits=4))")
    
    results = Dict(
        "method" => "GBLUP",
        "gebv" => gebv,
        "fixed_effects" => β,
        "reliability" => reliability,
        "accuracy" => accuracy,
        "animal_id" => geno.animal_id,
        "h2" => model.h2,
        "sigma2_a" => model.σ2_a,
        "sigma2_e" => model.σ2_e,
        "n_animals" => n_animals,
        "n_records" => n_records,
        "n_markers" => geno.n_markers
    )
    
    return results
end

# ============================================================================
# ssGBLUP算法实现
# Single-step GBLUP Algorithm Implementation
# ============================================================================

"""
    run_ssgblup(pheno::PhenotypeData, ped::Pedigree, geno::GenotypeData, 
                model::GeneticModel; use_gpu=false, solver="cholesky")

运行单步基因组BLUP分析（ssGBLUP）

整合系谱和基因组信息，可以同时预测有基因型和无基因型动物的育种值

# 参数
- `pheno::PhenotypeData`: 表型数据
- `ped::Pedigree`: 系谱数据
- `geno::GenotypeData`: 基因型数据
- `model::GeneticModel`: 遗传模型
- `use_gpu::Bool`: 是否使用GPU加速
- `solver::String`: 求解器类型

# 返回
- `Dict`: 包含所有动物的育种值预测结果
"""
function run_ssgblup(pheno::PhenotypeData, ped::Pedigree, geno::GenotypeData,
                     model::GeneticModel; use_gpu=false, solver="cholesky")
    println("\n" * "="^70)
    println("运行ssGBLUP分析")
    println("="^70)
    println("总动物数: $(ped.n)")
    println("有基因型动物数: $(geno.n_animals)")
    println("标记数: $(geno.n_markers)")
    println("记录数: $(pheno.n)")
    println("遗传力: $(model.h2)")
    println("GPU加速: $use_gpu")
    println("="^70)
    
    # 构建H逆矩阵
    H_inv = BreedingCore.build_H_matrix(ped, geno, use_gpu=use_gpu)
    
    # 构建设计矩阵
    n_records = pheno.n
    n_animals = ped.n
    
    # X矩阵（固定效应）
    X = ones(Float64, n_records, 1)
    
    # Z矩阵（随机效应）
    animal_to_idx = Dict(ped.id[i] => i for i in 1:n_animals)
    Z = spzeros(Float64, n_records, n_animals)
    for i in 1:n_records
        if haskey(animal_to_idx, pheno.animal_id[i])
            animal_idx = animal_to_idx[pheno.animal_id[i]]
            Z[i, animal_idx] = 1.0
        end
    end
    
    y = pheno.trait_values
    
    # 计算λ
    λ = model.σ2_e / model.σ2_a
    
    println("\n构建混合模型方程...")
    
    # 构建MME
    XtX = X' * X
    XtZ = X' * Z
    ZtX = Z' * X
    ZtZ = Z' * Z
    
    C11 = sparse(XtX)
    C12 = sparse(XtZ)
    C21 = sparse(ZtX)
    C22 = ZtZ + λ * H_inv
    
    C = [C11 C12; C21 C22]
    rhs = [X' * y; Z' * y]
    
    println("求解混合模型方程...")
    println("方程维度: $(size(C, 1)) × $(size(C, 2))")
    
    # 求解
    sol = C \ rhs
    
    n_fixed = size(X, 2)
    β = sol[1:n_fixed]
    ebv = sol[(n_fixed+1):end]
    
    # 计算可靠性
    println("\n计算可靠性...")
    C_inv_diag = diag(inv(Matrix(C)))
    PEV = C_inv_diag[(n_fixed+1):end] .* model.σ2_e
    reliability = 1.0 .- (PEV ./ model.σ2_a)
    reliability = clamp.(reliability, 0.0, 1.0)
    accuracy = sqrt.(reliability)
    
    # 区分有基因型和无基因型动物的可靠性
    genotyped_idx = indexin(geno.animal_id, ped.id)
    rel_genotyped = reliability[genotyped_idx]
    rel_nongenotyped = reliability[setdiff(1:n_animals, genotyped_idx)]
    
    println("\n分析完成!")
    println("所有动物平均可靠性: $(round(mean(reliability), digits=4))")
    println("有基因型动物平均可靠性: $(round(mean(rel_genotyped), digits=4))")
    println("无基因型动物平均可靠性: $(round(mean(rel_nongenotyped), digits=4))")
    
    results = Dict(
        "method" => "ssGBLUP",
        "breeding_values" => ebv,
        "fixed_effects" => β,
        "reliability" => reliability,
        "accuracy" => accuracy,
        "animal_id" => ped.id,
        "genotyped_animals" => geno.animal_id,
        "h2" => model.h2,
        "sigma2_a" => model.σ2_a,
        "sigma2_e" => model.σ2_e,
        "n_animals" => n_animals,
        "n_genotyped" => geno.n_animals,
        "n_records" => n_records,
        "n_markers" => geno.n_markers
    )
    
    return results
end

# ============================================================================
# 贝叶斯回归方法
# Bayesian Regression Methods
# ============================================================================

"""
    run_bayesian_regression(pheno::PhenotypeData, geno::GenotypeData;
                           method="BayesA", n_iter=10000, burn_in=5000,
                           use_gpu=false)

运行贝叶斯回归分析（BayesA/B/C/Cπ/R）

# 参数
- `pheno::PhenotypeData`: 表型数据
- `geno::GenotypeData`: 基因型数据
- `method::String`: 贝叶斯方法 ("BayesA", "BayesB", "BayesC", "BayesCpi", "BayesR")
- `n_iter::Int`: MCMC迭代次数
- `burn_in::Int`: 燃烧期迭代次数
- `use_gpu::Bool`: 是否使用GPU加速

# 返回
- `Dict`: 包含SNP效应、基因组育种值等结果
"""
function run_bayesian_regression(pheno::PhenotypeData, geno::GenotypeData;
                                 method="BayesA", n_iter=10000, burn_in=5000,
                                 use_gpu=false)
    println("\n" * "="^70)
    println("运行贝叶斯回归分析: $method")
    println("="^70)
    println("动物数: $(geno.n_animals)")
    println("标记数: $(geno.n_markers)")
    println("MCMC迭代: $n_iter (燃烧期: $burn_in)")
    println("GPU加速: $use_gpu")
    println("="^70)
    
    n = geno.n_animals
    m = geno.n_markers
    
    # 准备数据
    animal_to_idx = Dict(geno.animal_id[i] => i for i in 1:n)
    
    # 提取有基因型动物的表型
    y_idx = [animal_to_idx[id] for id in pheno.animal_id if haskey(animal_to_idx, id)]
    y = pheno.trait_values[1:length(y_idx)]
    
    # 标准化表型
    y_mean = mean(y)
    y_std = std(y)
    y_scaled = (y .- y_mean) ./ y_std
    
    # 标准化基因型矩阵
    X = Float64.(geno.markers[y_idx, :])
    
    # 初始化参数
    β = zeros(Float64, m)                    # SNP效应
    σ2_β = ones(Float64, m)                  # SNP方差
    σ2_e = 1.0                               # 残差方差
    
    # 超参数
    ν = 4.0                                  # 自由度
    S = 0.5                                  # 尺度参数
    
    # 存储MCMC样本
    β_samples = zeros(Float64, m, n_iter - burn_in)
    σ2_e_samples = zeros(Float64, n_iter - burn_in)
    
    println("\n开始MCMC采样...")
    
    @showprogress desc="MCMC迭代..." for iter in 1:n_iter
        # 更新SNP效应
        for j in 1:m
            # 计算部分残差
            r = y_scaled - X * β + X[:, j] * β[j]
            
            # 计算后验均值和方差
            x_j = X[:, j]
            v = 1.0 / (dot(x_j, x_j) / σ2_e + 1.0 / σ2_β[j])
            μ = v * dot(x_j, r) / σ2_e
            
            # 从后验分布采样
            β[j] = μ + sqrt(v) * randn()
            
            # 更新SNP方差（BayesA）
            if method == "BayesA"
                σ2_β[j] = rand(InverseGamma((ν + 1) / 2, (ν * S + β[j]^2) / 2))
            end
        end
        
        # 更新残差方差
        residuals = y_scaled - X * β
        σ2_e = rand(InverseGamma((length(y) + ν) / 2, 
                                 (dot(residuals, residuals) + ν * S) / 2))
        
        # 存储样本（燃烧期后）
        if iter > burn_in
            sample_idx = iter - burn_in
            β_samples[:, sample_idx] = β
            σ2_e_samples[sample_idx] = σ2_e
        end
    end
    
    println("\nMCMC采样完成!")
    
    # 计算后验均值
    β_mean = vec(mean(β_samples, dims=2))
    σ2_e_mean = mean(σ2_e_samples)
    
    # 计算基因组育种值
    gebv = X * β_mean
    
    # 反标准化
    gebv = gebv .* y_std .+ y_mean
    
    # 计算SNP效应的后验标准差
    β_sd = vec(std(β_samples, dims=2))
    
    println("\n分析完成!")
    println("平均残差方差: $(round(σ2_e_mean, digits=4))")
    println("非零SNP效应数: $(sum(abs.(β_mean) .> 1e-6))")
    
    results = Dict(
        "method" => method,
        "snp_effects" => β_mean,
        "snp_effects_sd" => β_sd,
        "snp_variance" => σ2_β,
        "gebv" => gebv,
        "residual_variance" => σ2_e_mean,
        "animal_id" => geno.animal_id[y_idx],
        "marker_names" => geno.marker_names,
        "n_iter" => n_iter,
        "burn_in" => burn_in,
        "n_animals" => length(y_idx),
        "n_markers" => m
    )
    
    return results
end

end # module AdvancedMethods

# ============================================================================
# 新星肉羊育种系统 - Julia计算核心
# NovaBreed Sheep System - Julia Computation Core
#
# 模块: BreedingCore
# 功能: 高性能育种值估计算法（BLUP/GBLUP/ssGBLUP）
# 作者: AdvancedGenomics Team
# 版本: 1.0.0
# Julia版本: 1.12.2
# ============================================================================

module BreedingCore

# ============================================================================
# 依赖包导入
# Package Imports
# ============================================================================

using LinearAlgebra          # 线性代数运算
using SparseArrays          # 稀疏矩阵支持
using Statistics            # 统计函数
using DataFrames            # 数据框操作
using CSV                   # CSV文件读写
using Distributions         # 概率分布
using ProgressMeter         # 进度条显示
using Dates                 # 日期时间处理
using JSON3                 # JSON解析
using CUDA                  # GPU加速支持
using Distributed           # 分布式计算
using SharedArrays          # 共享数组
using ThreadsX              # 多线程增强

# 导出主要类型和函数
export Pedigree, PhenotypeData, GenotypeData, GeneticModel
export build_pedigree, build_A_matrix, build_A_inverse
export build_G_matrix, build_H_matrix
export run_blup, run_gblup, run_ssgblup
export run_bayesian_regression
export calculate_reliability, calculate_accuracy
export predict_breeding_values

# ============================================================================
# 数据结构定义
# Data Structure Definitions
# ============================================================================

"""
    Pedigree

系谱数据结构，存储动物的系谱信息

# 字段
- `id::Vector{Int64}`: 动物ID向量
- `sire::Vector{Int64}`: 父亲ID向量（0表示未知）
- `dam::Vector{Int64}`: 母亲ID向量（0表示未知）
- `generation::Vector{Int64}`: 世代数向量
- `n::Int64`: 动物总数

# 示例
```julia
ped = Pedigree(
    id = [1, 2, 3, 4, 5],
    sire = [0, 0, 1, 1, 3],
    dam = [0, 0, 2, 2, 4]
)
```
"""
struct Pedigree
    id::Vector{Int64}
    sire::Vector{Int64}
    dam::Vector{Int64}
    generation::Vector{Int64}
    n::Int64
    
    # 内部构造函数，自动计算世代数
    function Pedigree(id::Vector{Int64}, sire::Vector{Int64}, dam::Vector{Int64})
        @assert length(id) == length(sire) == length(dam) "系谱向量长度必须相同"
        n = length(id)
        generation = calculate_generation(id, sire, dam)
        new(id, sire, dam, generation, n)
    end
end

"""
    PhenotypeData

表型数据结构，存储动物的表型观测值和固定/随机效应

# 字段
- `animal_id::Vector{Int64}`: 动物ID
- `trait_values::Vector{Float64}`: 性状观测值
- `fixed_effects::DataFrame`: 固定效应数据框
- `random_effects::DataFrame`: 随机效应数据框
- `contemporary_group::Vector{Int64}`: 同期群编码
- `n::Int64`: 记录数
"""
struct PhenotypeData
    animal_id::Vector{Int64}
    trait_values::Vector{Float64}
    fixed_effects::DataFrame
    random_effects::DataFrame
    contemporary_group::Vector{Int64}
    n::Int64
    
    function PhenotypeData(animal_id, trait_values, fixed_effects, random_effects, contemporary_group)
        @assert length(animal_id) == length(trait_values) "动物ID和性状值数量必须相同"
        n = length(animal_id)
        new(animal_id, trait_values, fixed_effects, random_effects, contemporary_group, n)
    end
end

"""
    GenotypeData

基因型数据结构，存储SNP标记数据

# 字段
- `animal_id::Vector{Int64}`: 动物ID
- `markers::Matrix{Int8}`: 标记矩阵（-1, 0, 1编码，行为动物，列为SNP）
- `marker_names::Vector{String}`: 标记名称
- `chromosome::Vector{Int64}`: 染色体编号
- `position::Vector{Int64}`: 物理位置
- `n_animals::Int64`: 动物数量
- `n_markers::Int64`: 标记数量
"""
struct GenotypeData
    animal_id::Vector{Int64}
    markers::Matrix{Int8}
    marker_names::Vector{String}
    chromosome::Vector{Int64}
    position::Vector{Int64}
    n_animals::Int64
    n_markers::Int64
    
    function GenotypeData(animal_id, markers, marker_names, chromosome, position)
        n_animals, n_markers = size(markers)
        @assert length(animal_id) == n_animals "动物数量不匹配"
        @assert length(marker_names) == n_markers "标记数量不匹配"
        new(animal_id, markers, marker_names, chromosome, position, n_animals, n_markers)
    end
end

"""
    GeneticModel

遗传模型定义，包含方差组分和模型参数

# 字段
- `h2::Float64`: 遗传力
- `σ2_a::Float64`: 加性遗传方差
- `σ2_e::Float64`: 残差方差
- `fixed_effects::Vector{Symbol}`: 固定效应列表
- `random_effects::Vector{Symbol}`: 随机效应列表
"""
struct GeneticModel
    h2::Float64
    σ2_a::Float64
    σ2_e::Float64
    fixed_effects::Vector{Symbol}
    random_effects::Vector{Symbol}
    
    function GeneticModel(h2::Float64; fixed_effects=Symbol[], random_effects=Symbol[])
        @assert 0.0 <= h2 <= 1.0 "遗传力必须在0到1之间"
        # 假设表型方差为1，计算方差组分
        σ2_a = h2
        σ2_e = 1.0 - h2
        new(h2, σ2_a, σ2_e, fixed_effects, random_effects)
    end
end

# ============================================================================
# 系谱处理函数
# Pedigree Processing Functions
# ============================================================================

"""
    calculate_generation(id, sire, dam)

计算每个动物的世代数

# 参数
- `id::Vector{Int64}`: 动物ID
- `sire::Vector{Int64}`: 父亲ID
- `dam::Vector{Int64}`: 母亲ID

# 返回
- `Vector{Int64}`: 世代数向量
"""
function calculate_generation(id::Vector{Int64}, sire::Vector{Int64}, dam::Vector{Int64})
    n = length(id)
    generation = zeros(Int64, n)
    
    # 创建ID到索引的映射
    id_to_idx = Dict(id[i] => i for i in 1:n)
    
    # 递归计算世代数
    function get_gen(idx::Int)
        if generation[idx] > 0
            return generation[idx]
        end
        
        s_id = sire[idx]
        d_id = dam[idx]
        
        if s_id == 0 && d_id == 0
            generation[idx] = 1
        else
            s_gen = s_id == 0 ? 0 : get_gen(id_to_idx[s_id])
            d_gen = d_id == 0 ? 0 : get_gen(id_to_idx[d_id])
            generation[idx] = max(s_gen, d_gen) + 1
        end
        
        return generation[idx]
    end
    
    for i in 1:n
        get_gen(i)
    end
    
    return generation
end

"""
    build_A_matrix(ped::Pedigree)

构建加性亲缘关系矩阵（A矩阵）

使用Henderson算法高效构建A矩阵

# 参数
- `ped::Pedigree`: 系谱数据

# 返回
- `Matrix{Float64}`: A矩阵（n×n对称矩阵）

# 算法复杂度
- 时间复杂度: O(n²)
- 空间复杂度: O(n²)
"""
function build_A_matrix(ped::Pedigree)
    n = ped.n
    A = zeros(Float64, n, n)
    
    # 创建ID到索引的映射
    id_to_idx = Dict(ped.id[i] => i for i in 1:n)
    
    # 按世代顺序处理（父母在子代之前）
    sorted_idx = sortperm(ped.generation)
    
    @showprogress desc="构建A矩阵..." for idx in sorted_idx
        i = idx
        s = ped.sire[i]
        d = ped.dam[i]
        
        # 对角元素
        if s == 0 && d == 0
            A[i, i] = 1.0
        elseif s != 0 && d == 0
            s_idx = id_to_idx[s]
            A[i, i] = 1.0 + 0.5 * A[s_idx, s_idx]
        elseif s == 0 && d != 0
            d_idx = id_to_idx[d]
            A[i, i] = 1.0 + 0.5 * A[d_idx, d_idx]
        else
            s_idx = id_to_idx[s]
            d_idx = id_to_idx[d]
            A[i, i] = 1.0 + 0.5 * A[s_idx, d_idx]
        end
        
        # 非对角元素
        for j in 1:(i-1)
            if s == 0 && d == 0
                A[i, j] = 0.0
            elseif s != 0 && d == 0
                s_idx = id_to_idx[s]
                A[i, j] = 0.5 * A[j, s_idx]
            elseif s == 0 && d != 0
                d_idx = id_to_idx[d]
                A[i, j] = 0.5 * A[j, d_idx]
            else
                s_idx = id_to_idx[s]
                d_idx = id_to_idx[d]
                A[i, j] = 0.5 * (A[j, s_idx] + A[j, d_idx])
            end
            A[j, i] = A[i, j]  # 对称矩阵
        end
    end
    
    return A
end

"""
    build_A_inverse(ped::Pedigree)

构建A矩阵的逆矩阵（A⁻¹）

使用Henderson的直接算法，无需先构建A矩阵
这是混合模型方程中的关键组件

# 参数
- `ped::Pedigree`: 系谱数据

# 返回
- `SparseMatrixCSC{Float64}`: A⁻¹稀疏矩阵

# 算法优势
- 直接构建逆矩阵，避免矩阵求逆
- 利用稀疏性，节省内存
- 时间复杂度: O(n)
"""
function build_A_inverse(ped::Pedigree)
    n = ped.n
    
    # 使用稀疏矩阵存储
    I_idx = Int64[]
    J_idx = Int64[]
    V_val = Float64[]
    
    # 创建ID到索引的映射
    id_to_idx = Dict(ped.id[i] => i for i in 1:n)
    
    @showprogress desc="构建A逆矩阵..." for i in 1:n
        s = ped.sire[i]
        d = ped.dam[i]
        
        if s == 0 && d == 0
            # 基础动物
            push!(I_idx, i); push!(J_idx, i); push!(V_val, 1.0)
        elseif s != 0 && d == 0
            # 只知道父亲
            s_idx = id_to_idx[s]
            push!(I_idx, i); push!(J_idx, i); push!(V_val, 4.0/3.0)
            push!(I_idx, i); push!(J_idx, s_idx); push!(V_val, -2.0/3.0)
            push!(I_idx, s_idx); push!(J_idx, i); push!(V_val, -2.0/3.0)
            push!(I_idx, s_idx); push!(J_idx, s_idx); push!(V_val, 1.0/3.0)
        elseif s == 0 && d != 0
            # 只知道母亲
            d_idx = id_to_idx[d]
            push!(I_idx, i); push!(J_idx, i); push!(V_val, 4.0/3.0)
            push!(I_idx, i); push!(J_idx, d_idx); push!(V_val, -2.0/3.0)
            push!(I_idx, d_idx); push!(J_idx, i); push!(V_val, -2.0/3.0)
            push!(I_idx, d_idx); push!(J_idx, d_idx); push!(V_val, 1.0/3.0)
        else
            # 父母都已知
            s_idx = id_to_idx[s]
            d_idx = id_to_idx[d]
            push!(I_idx, i); push!(J_idx, i); push!(V_val, 2.0)
            push!(I_idx, i); push!(J_idx, s_idx); push!(V_val, -1.0)
            push!(I_idx, i); push!(J_idx, d_idx); push!(V_val, -1.0)
            push!(I_idx, s_idx); push!(J_idx, i); push!(V_val, -1.0)
            push!(I_idx, d_idx); push!(J_idx, i); push!(V_val, -1.0)
            push!(I_idx, s_idx); push!(J_idx, s_idx); push!(V_val, 0.5)
            push!(I_idx, s_idx); push!(J_idx, d_idx); push!(V_val, 0.5)
            push!(I_idx, d_idx); push!(J_idx, s_idx); push!(V_val, 0.5)
            push!(I_idx, d_idx); push!(J_idx, d_idx); push!(V_val, 0.5)
        end
    end
    
    # 构建稀疏矩阵
    A_inv = sparse(I_idx, J_idx, V_val, n, n)
    
    return A_inv
end

# ============================================================================
# 基因组关系矩阵构建
# Genomic Relationship Matrix Construction
# ============================================================================

"""
    build_G_matrix(geno::GenotypeData; method="VanRaden", use_gpu=false)

构建基因组关系矩阵（G矩阵）

# 参数
- `geno::GenotypeData`: 基因型数据
- `method::String`: 计算方法，可选 "VanRaden" (默认) 或 "UAR"
- `use_gpu::Bool`: 是否使用GPU加速

# 返回
- `Matrix{Float64}`: G矩阵（n×n对称矩阵）

# 方法说明
- VanRaden方法: G = ZZ'/[2Σp(1-p)]
- UAR方法: 统一加性关系矩阵

# GPU加速
当use_gpu=true且CUDA可用时，使用GPU加速矩阵乘法
"""
function build_G_matrix(geno::GenotypeData; method="VanRaden", use_gpu=false)
    n = geno.n_animals
    m = geno.n_markers
    
    println("构建G矩阵: $n 个动物, $m 个标记")
    println("方法: $method, GPU加速: $use_gpu")
    
    if method == "VanRaden"
        # 计算等位基因频率
        p = vec(mean(geno.markers .+ 1, dims=1)) ./ 2.0  # 转换为0,1,2编码后计算频率
        
        # 中心化标记矩阵: Z = M - 2p
        Z = similar(geno.markers, Float64)
        for j in 1:m
            Z[:, j] = geno.markers[:, j] .- (2.0 * p[j] - 1.0)
        end
        
        # 计算分母: 2Σp(1-p)
        denominator = 2.0 * sum(p .* (1.0 .- p))
        
        # 计算G矩阵
        if use_gpu && CUDA.functional()
            println("使用GPU加速计算...")
            Z_gpu = CuArray(Z)
            G_gpu = (Z_gpu * Z_gpu') ./ denominator
            G = Array(G_gpu)
            CUDA.unsafe_free!(Z_gpu)
            CUDA.unsafe_free!(G_gpu)
        else
            println("使用CPU计算...")
            G = (Z * Z') ./ denominator
        end
        
    elseif method == "UAR"
        # UAR方法实现
        # G = (M * M') / m
        M = Float64.(geno.markers)
        
        if use_gpu && CUDA.functional()
            M_gpu = CuArray(M)
            G_gpu = (M_gpu * M_gpu') ./ m
            G = Array(G_gpu)
            CUDA.unsafe_free!(M_gpu)
            CUDA.unsafe_free!(G_gpu)
        else
            G = (M * M') ./ m
        end
    else
        error("未知的G矩阵构建方法: $method")
    end
    
    return G
end

"""
    build_H_matrix(ped::Pedigree, geno::GenotypeData; 
                   ω=0.05, τ=0.02, use_gpu=false)

构建单步法H矩阵，整合系谱和基因组信息

H⁻¹ = A⁻¹ + [0  0; 0  G⁻¹ - A22⁻¹]

# 参数
- `ped::Pedigree`: 系谱数据
- `geno::GenotypeData`: 基因型数据
- `ω::Float64`: G矩阵调整参数（默认0.05）
- `τ::Float64`: G矩阵调整参数（默认0.02）
- `use_gpu::Bool`: 是否使用GPU

# 返回
- `SparseMatrixCSC{Float64}`: H⁻¹矩阵
"""
function build_H_matrix(ped::Pedigree, geno::GenotypeData; 
                        ω=0.05, τ=0.02, use_gpu=false)
    println("构建单步法H矩阵...")
    
    # 构建A逆矩阵
    A_inv = build_A_inverse(ped)
    
    # 找到有基因型的动物索引
    genotyped_idx = indexin(geno.animal_id, ped.id)
    n_genotyped = length(genotyped_idx)
    
    println("有基因型的动物数: $n_genotyped / $(ped.n)")
    
    # 构建G矩阵
    G = build_G_matrix(geno, method="VanRaden", use_gpu=use_gpu)
    
    # 调整G矩阵以避免奇异性
    # G* = (1-ω-τ)G + ωA22 + τI
    A = build_A_matrix(ped)
    A22 = A[genotyped_idx, genotyped_idx]
    
    G_adjusted = (1.0 - ω - τ) .* G .+ ω .* A22 .+ τ .* I(n_genotyped)
    
    # 计算G逆矩阵
    G_inv = inv(G_adjusted)
    
    # 计算A22逆矩阵
    A22_inv = inv(A22)
    
    # 构建H逆矩阵
    # H⁻¹ = A⁻¹ + [0  0; 0  G⁻¹ - A22⁻¹]
    H_inv = copy(A_inv)
    
    # 添加基因组信息的贡献
    diff = G_inv - A22_inv
    for i in 1:n_genotyped
        for j in 1:n_genotyped
            idx_i = genotyped_idx[i]
            idx_j = genotyped_idx[j]
            H_inv[idx_i, idx_j] += diff[i, j]
        end
    end
    
    return H_inv
end

# ============================================================================
# BLUP算法实现
# BLUP Algorithm Implementation
# ============================================================================

"""
    run_blup(pheno::PhenotypeData, ped::Pedigree, model::GeneticModel;
             use_sparse=true, solver="cholesky")

运行传统BLUP分析（基于系谱的最佳线性无偏预测）

求解混合模型方程(MME):
[X'X    X'Z  ] [β]   [X'y]
[Z'X  Z'Z+λA⁻¹] [u] = [Z'y]

其中 λ = σ²ₑ/σ²ₐ

# 参数
- `pheno::PhenotypeData`: 表型数据
- `ped::Pedigree`: 系谱数据
- `model::GeneticModel`: 遗传模型
- `use_sparse::Bool`: 是否使用稀疏矩阵（推荐）
- `solver::String`: 求解器类型 ("cholesky", "pcg", "gmres")

# 返回
- `Dict`: 包含育种值、固定效应解、方差组分等结果
"""
function run_blup(pheno::PhenotypeData, ped::Pedigree, model::GeneticModel;
                  use_sparse=true, solver="cholesky")
    println("\n" * "="^70)
    println("运行BLUP分析")
    println("="^70)
    println("动物数: $(ped.n)")
    println("记录数: $(pheno.n)")
    println("遗传力: $(model.h2)")
    println("求解器: $solver")
    println("="^70)
    
    # 构建设计矩阵
    n_records = pheno.n
    n_animals = ped.n
    
    # X矩阵（固定效应设计矩阵）
    # 这里简化处理，假设只有截距项
    X = ones(Float64, n_records, 1)
    
    # Z矩阵（随机效应设计矩阵）
    # 将表型记录关联到动物
    animal_to_idx = Dict(ped.id[i] => i for i in 1:n_animals)
    Z = spzeros(Float64, n_records, n_animals)
    for i in 1:n_records
        animal_idx = animal_to_idx[pheno.animal_id[i]]
        Z[i, animal_idx] = 1.0
    end
    
    # 观测向量
    y = pheno.trait_values
    
    # 构建A逆矩阵
    A_inv = build_A_inverse(ped)
    
    # 计算λ = σ²ₑ/σ²ₐ
    λ = model.σ2_e / model.σ2_a
    
    println("\n构建混合模型方程...")
    
    # 构建MME左侧矩阵
    # [X'X    X'Z  ]
    # [Z'X  Z'Z+λA⁻¹]
    
    XtX = X' * X
    XtZ = X' * Z
    ZtX = Z' * X
    ZtZ = Z' * Z
    
    if use_sparse
        # 使用稀疏矩阵
        C11 = sparse(XtX)
        C12 = sparse(XtZ)
        C21 = sparse(ZtX)
        C22 = ZtZ + λ * A_inv
        
        # 组装完整的MME矩阵
        C = [C11 C12; C21 C22]
    else
        # 使用密集矩阵
        C11 = Matrix(XtX)
        C12 = Matrix(XtZ)
        C21 = Matrix(ZtX)
        C22 = Matrix(ZtZ) + λ * Matrix(A_inv)
        
        C = [C11 C12; C21 C22]
    end
    
    # 构建MME右侧向量
    rhs = [X' * y; Z' * y]
    
    println("求解混合模型方程...")
    println("方程维度: $(size(C, 1)) × $(size(C, 2))")
    
    # 求解方程
    if solver == "cholesky"
        # Cholesky分解（适用于正定矩阵）
        sol = C \ rhs
    elseif solver == "pcg"
        # 预条件共轭梯度法（适用于大规模稀疏系统）
        using IterativeSolvers
        sol = cg(C, rhs, maxiter=1000, tol=1e-6)
    elseif solver == "gmres"
        # 广义最小残差法
        using IterativeSolvers
        sol = gmres(C, rhs, maxiter=1000, tol=1e-6)
    else
        error("未知的求解器: $solver")
    end
    
    # 提取解
    n_fixed = size(X, 2)
    β = sol[1:n_fixed]                    # 固定效应解
    u = sol[(n_fixed+1):end]              # 育种值（随机效应解）
    
    println("\n计算可靠性...")
    
    # 计算预测误差方差(PEV)和可靠性
    # 可靠性 = 1 - PEV/σ²ₐ
    # 这里使用对角元素的近似
    C_inv_diag = diag(inv(Matrix(C)))
    PEV = C_inv_diag[(n_fixed+1):end] .* model.σ2_e
    reliability = 1.0 .- (PEV ./ model.σ2_a)
    reliability = clamp.(reliability, 0.0, 1.0)  # 限制在[0,1]范围
    
    # 计算准确性
    accuracy = sqrt.(reliability)
    
    println("\n分析完成!")
    println("平均可靠性: $(round(mean(reliability), digits=4))")
    println("平均准确性: $(round(mean(accuracy), digits=4))")
    
    # 返回结果
    results = Dict(
        "method" => "BLUP",
        "breeding_values" => u,
        "fixed_effects" => β,
        "reliability" => reliability,
        "accuracy" => accuracy,
        "animal_id" => ped.id,
        "h2" => model.h2,
        "sigma2_a" => model.σ2_a,
        "sigma2_e" => model.σ2_e,
        "n_animals" => n_animals,
        "n_records" => n_records
    )
    
    return results
end

# ============================================================================
# 模块初始化
# Module Initialization
# ============================================================================

function __init__()
    println("="^70)
    println("新星肉羊育种系统 - Julia计算核心")
    println("NovaBreed Sheep System")
    println("="^70)
    println("版本: 1.0.0")
    println("Julia版本: $(VERSION)")
    
    # 检查GPU可用性
    if CUDA.functional()
        println("✓ GPU加速可用 (CUDA)")
        println("  设备: $(CUDA.name(CUDA.device()))")
        println("  显存: $(CUDA.totalmem(CUDA.device()) / 1024^3) GB")
    else
        println("✗ GPU不可用，将使用CPU计算")
    end
    
    # 检查线程数
    println("CPU线程数: $(Threads.nthreads())")
    println("="^70)
end

end # module BreedingCore

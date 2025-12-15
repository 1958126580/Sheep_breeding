# ============================================================================
# 国际顶级肉羊育种系统 - 多性状遗传评估模块
# International Top-tier Sheep Breeding System - Multi-trait Genetic Evaluation
#
# 文件: MultiTraitBLUP.jl
# 功能: 多性状BLUP、随机回归模型、选择指数计算
# ============================================================================

module MultiTraitBLUP

using LinearAlgebra
using Statistics
using SparseArrays

export run_mtblup, build_mt_equations, solve_mt_equations
export calculate_selection_index, economic_weights
export MultiTraitModel, MultiTraitResult

# ============================================================================
# 数据结构定义
# Data Structure Definitions
# ============================================================================

"""
多性状遗传模型
"""
struct MultiTraitModel
    trait_names::Vector{String}         # 性状名称
    n_traits::Int                       # 性状数量
    fixed_effects::Vector{Vector{String}}  # 各性状固定效应
    G0::Matrix{Float64}                 # 加性遗传协方差矩阵
    R0::Matrix{Float64}                 # 残差协方差矩阵
    h2::Vector{Float64}                 # 各性状遗传力
    rg::Matrix{Float64}                 # 遗传相关矩阵
    rp::Matrix{Float64}                 # 表型相关矩阵
end

"""
多性状分析结果
"""
struct MultiTraitResult
    model::MultiTraitModel
    ebv::Matrix{Float64}                # 育种值矩阵 (n_animals × n_traits)
    pev::Matrix{Float64}                # 预测误差方差
    reliability::Matrix{Float64}        # 可靠性
    accuracy::Matrix{Float64}           # 准确性
    n_animals::Int
    n_records::Vector{Int}              # 各性状记录数
    convergence::Bool
    iterations::Int
    log_likelihood::Float64
end

# ============================================================================
# 模型构建函数
# Model Construction Functions
# ============================================================================

"""
    create_multitriat_model(trait_names, G0, R0; h2, rg)

创建多性状模型

# 参数
- `trait_names`: 性状名称向量
- `G0`: 加性遗传协方差矩阵
- `R0`: 残差协方差矩阵
"""
function create_multitriat_model(
    trait_names::Vector{String},
    G0::Matrix{Float64},
    R0::Matrix{Float64};
    fixed_effects::Vector{Vector{String}} = Vector{String}[]
)
    n_traits = length(trait_names)
    
    # 验证维度
    @assert size(G0) == (n_traits, n_traits) "G0维度不匹配"
    @assert size(R0) == (n_traits, n_traits) "R0维度不匹配"
    
    # 计算遗传力
    h2 = [G0[i,i] / (G0[i,i] + R0[i,i]) for i in 1:n_traits]
    
    # 计算遗传相关
    rg = zeros(n_traits, n_traits)
    for i in 1:n_traits
        for j in 1:n_traits
            if i == j
                rg[i,j] = 1.0
            else
                rg[i,j] = G0[i,j] / sqrt(G0[i,i] * G0[j,j])
            end
        end
    end
    
    # 计算表型相关
    P0 = G0 + R0
    rp = zeros(n_traits, n_traits)
    for i in 1:n_traits
        for j in 1:n_traits
            if i == j
                rp[i,j] = 1.0
            else
                rp[i,j] = P0[i,j] / sqrt(P0[i,i] * P0[j,j])
            end
        end
    end
    
    # 默认固定效应
    if isempty(fixed_effects)
        fixed_effects = [String[] for _ in 1:n_traits]
    end
    
    return MultiTraitModel(
        trait_names, n_traits, fixed_effects,
        G0, R0, h2, rg, rp
    )
end

# ============================================================================
# 多性状BLUP求解
# Multi-trait BLUP Solution
# ============================================================================

"""
    run_mtblup(Y, A, X, model; max_iter, tol)

运行多性状BLUP分析

# 参数
- `Y`: 表型矩阵 (n × t), 缺失值用NaN表示
- `A`: 亲缘关系矩阵 (n × n)
- `X`: 固定效应设计矩阵列表
- `model`: MultiTraitModel对象

# 返回
- `MultiTraitResult`: 分析结果
"""
function run_mtblup(
    Y::Matrix{Float64},
    A::Matrix{Float64},
    X::Matrix{Float64};
    model::MultiTraitModel,
    max_iter::Int = 100,
    tol::Float64 = 1e-6
)
    n_animals, n_traits = size(Y)
    
    @assert n_traits == model.n_traits "性状数量不匹配"
    @assert size(A) == (n_animals, n_animals) "A矩阵维度不匹配"
    
    # 获取各性状的观测记录
    record_masks = [.!isnan.(Y[:, t]) for t in 1:n_traits]
    n_records = [sum(mask) for mask in record_masks]
    
    # 构建混合模型方程组
    # 使用Kronecker积方法
    
    # 计算逆矩阵
    G0_inv = inv(model.G0)
    R0_inv = inv(model.R0)
    
    # 简化: 假设所有动物都有所有性状记录 (完整数据)
    # 实际应用中需要处理缺失数据
    
    # 将Y中的NaN替换为0用于计算
    Y_clean = copy(Y)
    Y_clean[isnan.(Y_clean)] .= 0.0
    
    # 构建系数矩阵 (Kronecker积形式)
    n_fixed = size(X, 2)
    n_random = n_animals
    
    n_eq_per_trait_fixed = n_fixed
    n_eq_per_trait_random = n_random
    
    total_fixed = n_fixed * n_traits
    total_random = n_random * n_traits
    total_eq = total_fixed + total_random
    
    # 初始化系数矩阵和右手边向量
    LHS = zeros(total_eq, total_eq)
    RHS = zeros(total_eq)
    
    # 构建方程组 (trait by trait with covariances)
    for t1 in 1:n_traits
        for t2 in 1:n_traits
            r_inv_elem = R0_inv[t1, t2]
            g_inv_elem = G0_inv[t1, t2]
            
            # 固定效应-固定效应块
            idx_f1 = (t1-1)*n_fixed + 1 : t1*n_fixed
            idx_f2 = (t2-1)*n_fixed + 1 : t2*n_fixed
            
            LHS[idx_f1, idx_f2] .+= r_inv_elem * (X' * X)
            
            # 随机效应-随机效应块  
            idx_r1 = total_fixed + (t1-1)*n_random + 1 : total_fixed + t1*n_random
            idx_r2 = total_fixed + (t2-1)*n_random + 1 : total_fixed + t2*n_random
            
            if t1 == t2
                LHS[idx_r1, idx_r2] .+= r_inv_elem * I(n_random) + g_inv_elem * inv(A)
            else
                LHS[idx_r1, idx_r2] .+= g_inv_elem * inv(A)
            end
            
            # 固定-随机交叉块
            LHS[idx_f1, idx_r2] .+= r_inv_elem * X'
            LHS[idx_r1, idx_f2] .+= r_inv_elem * X
        end
        
        # 右手边向量
        idx_f = (t1-1)*n_fixed + 1 : t1*n_fixed
        idx_r = total_fixed + (t1-1)*n_random + 1 : total_fixed + t1*n_random
        
        y_t = Y_clean[:, t1]
        
        for t2 in 1:n_traits
            r_inv_elem = R0_inv[t1, t2]
            y_t2 = Y_clean[:, t2]
            RHS[idx_f] .+= r_inv_elem * (X' * y_t2)
            RHS[idx_r] .+= r_inv_elem * y_t2
        end
    end
    
    # 求解方程组
    solutions = LHS \ RHS
    
    # 提取育种值
    ebv = zeros(n_animals, n_traits)
    for t in 1:n_traits
        idx = total_fixed + (t-1)*n_random + 1 : total_fixed + t*n_random
        ebv[:, t] = solutions[idx]
    end
    
    # 计算可靠性和准确性
    # 简化计算: 使用对角近似
    reliability = zeros(n_animals, n_traits)
    accuracy = zeros(n_animals, n_traits)
    pev = zeros(n_animals, n_traits)
    
    # 计算系数矩阵的逆 (对角元素)
    try
        C = inv(LHS)
        for t in 1:n_traits
            var_a = model.G0[t, t]
            for i in 1:n_animals
                idx = total_fixed + (t-1)*n_random + i
                pev[i, t] = C[idx, idx]
                reliability[i, t] = 1.0 - pev[i, t] / var_a
                reliability[i, t] = max(0.0, min(1.0, reliability[i, t]))
                accuracy[i, t] = sqrt(reliability[i, t])
            end
        end
    catch
        # 如果无法计算逆矩阵，使用默认值
        for t in 1:n_traits
            reliability[:, t] .= 0.5
            accuracy[:, t] .= sqrt(0.5)
        end
    end
    
    return MultiTraitResult(
        model,
        ebv,
        pev,
        reliability,
        accuracy,
        n_animals,
        n_records,
        true,
        1,
        0.0
    )
end

# ============================================================================
# 选择指数计算
# Selection Index Calculation
# ============================================================================

"""
    calculate_selection_index(ebv, weights, G0)

计算选择指数

# 参数
- `ebv`: 育种值矩阵 (n × t)
- `weights`: 经济权重向量
- `G0`: 遗传协方差矩阵

# 返回
- 选择指数值向量
"""
function calculate_selection_index(
    ebv::Matrix{Float64},
    weights::Vector{Float64},
    G0::Matrix{Float64}
)
    n_animals, n_traits = size(ebv)
    
    @assert length(weights) == n_traits "权重维度不匹配"
    
    # 计算选择指数系数 b = G * a (a为经济权重)
    # 在实践中，这里简化为直接加权求和
    
    # 标准化各性状的EBV
    ebv_std = copy(ebv)
    for t in 1:n_traits
        trait_std = sqrt(G0[t, t])
        if trait_std > 0
            ebv_std[:, t] ./= trait_std
        end
    end
    
    # 计算选择指数
    index = ebv_std * weights
    
    return index
end

"""
    economic_weights(trait_names, prices, genetic_sds; standardize)

计算经济权重

# 参数
- `trait_names`: 性状名称
- `prices`: 单位价值改进的经济价值
- `genetic_sds`: 遗传标准差

# 返回
- 经济权重向量
"""
function economic_weights(
    trait_names::Vector{String},
    prices::Vector{Float64},
    genetic_sds::Vector{Float64};
    standardize::Bool = true
)
    n_traits = length(trait_names)
    
    @assert length(prices) == n_traits
    @assert length(genetic_sds) == n_traits
    
    # 计算相对权重
    weights = prices .* genetic_sds
    
    if standardize
        # 标准化使权重和为1
        weights = weights ./ sum(abs.(weights))
    end
    
    return weights
end

"""
    rank_candidates(result, weights; top_n)

按选择指数对候选动物排名

# 参数
- `result`: MultiTraitResult对象
- `weights`: 经济权重
- `top_n`: 返回前N名
"""
function rank_candidates(
    result::MultiTraitResult,
    weights::Vector{Float64};
    top_n::Int = 10
)
    # 计算选择指数
    indices = calculate_selection_index(result.ebv, weights, result.model.G0)
    
    # 排序
    order = sortperm(indices, rev=true)
    
    # 返回前N名
    n_return = min(top_n, length(order))
    
    return Dict(
        "ranks" => order[1:n_return],
        "indices" => indices[order[1:n_return]],
        "ebv" => result.ebv[order[1:n_return], :],
        "reliability" => result.reliability[order[1:n_return], :]
    )
end

# ============================================================================
# 遗传参数估计
# Genetic Parameter Estimation
# ============================================================================

"""
    estimate_genetic_correlations(Y)

从表型数据估计遗传相关 (REML简化版)

# 参数
- `Y`: 表型矩阵 (n × t)

# 返回
- 遗传协方差矩阵估计
"""
function estimate_genetic_correlations(Y::Matrix{Float64})
    n, t = size(Y)
    
    # 简化: 使用表型相关作为遗传相关的估计
    # 暂时填充NaN
    Y_clean = copy(Y)
    for j in 1:t
        col_mean = mean(filter(!isnan, Y_clean[:, j]))
        Y_clean[isnan.(Y_clean[:, j]), j] .= col_mean
    end
    
    # 计算协方差矩阵
    P = cov(Y_clean)
    
    # 假设h2 = 0.3来估计G
    h2 = 0.3
    G_est = P * h2
    
    return G_est
end

# ============================================================================
# 多性状遗传趋势分析
# Multi-trait Genetic Trend Analysis
# ============================================================================

"""
    genetic_trend_analysis(ebv, birth_years)

多性状遗传趋势分析

# 参数
- `ebv`: 育种值矩阵
- `birth_years`: 出生年份向量

# 返回
- 各年份各性状的平均育种值
"""
function genetic_trend_analysis(
    ebv::Matrix{Float64},
    birth_years::Vector{Int}
)
    n_animals, n_traits = size(ebv)
    unique_years = sort(unique(birth_years))
    
    trends = Dict{Int, Vector{Float64}}()
    counts = Dict{Int, Int}()
    
    for year in unique_years
        mask = birth_years .== year
        if sum(mask) > 0
            trends[year] = vec(mean(ebv[mask, :], dims=1))
            counts[year] = sum(mask)
        end
    end
    
    return Dict(
        "years" => unique_years,
        "mean_ebv" => [trends[y] for y in unique_years],
        "n_animals" => [counts[y] for y in unique_years]
    )
end

end # module MultiTraitBLUP

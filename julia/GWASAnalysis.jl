# ============================================================================
# 新星肉羊育种系统 - GWAS全基因组关联分析模块
# NovaBreed Sheep System - GWAS Analysis Module
#
# 文件: GWASAnalysis.jl
# 功能: 全基因组关联分析、QTL定位、曼哈顿图数据
# ============================================================================

module GWASAnalysis

using LinearAlgebra
using Statistics
using Distributions
using Random

export run_gwas, run_single_marker_gwas, run_mlma_loco
export calculate_lambda_gc, manhattan_plot_data, qq_plot_data
export identify_qtl_regions, calculate_genetic_variance_snp
export permutation_test, multiple_testing_correction

# ============================================================================
# 数据结构定义
# Data Structure Definitions
# ============================================================================

"""
GWAS分析结果
"""
struct GWASResult
    snp_ids::Vector{String}         # SNP标识符
    chromosomes::Vector{Int}        # 染色体号
    positions::Vector{Int}          # 物理位置
    effects::Vector{Float64}        # SNP效应
    se::Vector{Float64}             # 标准误
    test_stats::Vector{Float64}     # 检验统计量
    pvalues::Vector{Float64}        # P值
    mafs::Vector{Float64}           # 最小等位基因频率
    n_samples::Int                  # 样本量
    n_snps::Int                     # SNP数量
    lambda_gc::Float64              # 基因组膨胀因子
    method::String                  # 分析方法
end

"""
QTL区域结果
"""
struct QTLRegion
    chromosome::Int
    start_position::Int
    end_position::Int
    peak_position::Int
    peak_pvalue::Float64
    n_significant_snps::Int
    variance_explained::Float64
    candidate_genes::Vector{String}
end

"""
GWAS模型参数
"""
struct GWASModelParams
    fixed_effects::Vector{String}   # 固定效应
    random_effects::Vector{String}  # 随机效应
    h2::Float64                     # 遗传力
    alpha::Float64                  # 显著性水平
    maf_threshold::Float64          # MAF阈值
    missing_threshold::Float64      # 缺失率阈值
end

# 默认参数构造函数
function GWASModelParams(;
    fixed_effects::Vector{String} = String[],
    random_effects::Vector{String} = ["animal"],
    h2::Float64 = 0.3,
    alpha::Float64 = 0.05,
    maf_threshold::Float64 = 0.01,
    missing_threshold::Float64 = 0.1
)
    return GWASModelParams(fixed_effects, random_effects, h2, alpha, 
                           maf_threshold, missing_threshold)
end

# ============================================================================
# 单标记GWAS分析
# Single Marker GWAS Analysis
# ============================================================================

"""
    run_single_marker_gwas(y, Z, X; params)

运行单标记GWAS分析

# 参数
- `y`: 表型向量 (n×1)
- `Z`: 基因型矩阵 (n×m), 编码为 0/1/2
- `X`: 固定效应矩阵 (n×p), 如果为nothing则仅包含截距

# 返回
- `GWASResult`: GWAS分析结果
"""
function run_single_marker_gwas(
    y::Vector{Float64},
    Z::Matrix{Float64},
    X::Union{Matrix{Float64}, Nothing} = nothing;
    snp_ids::Vector{String} = String[],
    chromosomes::Vector{Int} = Int[],
    positions::Vector{Int} = Int[],
    params::GWASModelParams = GWASModelParams()
)
    n, m = size(Z)
    
    # 如果没有提供固定效应矩阵，使用截距
    if X === nothing
        X = ones(n, 1)
    end
    
    # 如果没有提供SNP信息，生成默认值
    if isempty(snp_ids)
        snp_ids = ["SNP_$i" for i in 1:m]
    end
    if isempty(chromosomes)
        chromosomes = ones(Int, m)
    end
    if isempty(positions)
        positions = collect(1:m)
    end
    
    # 初始化结果向量
    effects = zeros(m)
    se = zeros(m)
    test_stats = zeros(m)
    pvalues = zeros(m)
    mafs = zeros(m)
    
    # 表型校正 (去除固定效应)
    y_adj = y - X * (X \ y)
    
    # 对每个SNP进行分析
    for j in 1:m
        z_j = Z[:, j]
        
        # 计算MAF
        maf = mean(z_j) / 2.0
        if maf > 0.5
            maf = 1.0 - maf
        end
        mafs[j] = maf
        
        # 跳过低MAF的SNP
        if maf < params.maf_threshold
            pvalues[j] = 1.0
            continue
        end
        
        # 简单线性回归
        z_centered = z_j .- mean(z_j)
        var_z = sum(z_centered .^ 2)
        
        if var_z > 1e-10
            # 计算效应
            beta = sum(z_centered .* y_adj) / var_z
            effects[j] = beta
            
            # 计算残差方差
            residuals = y_adj .- z_centered .* beta
            sigma2 = sum(residuals .^ 2) / (n - 2)
            
            # 计算标准误
            se_j = sqrt(sigma2 / var_z)
            se[j] = se_j
            
            # 计算检验统计量和P值
            if se_j > 1e-10
                t_stat = beta / se_j
                test_stats[j] = t_stat
                pvalues[j] = 2.0 * ccdf(TDist(n - 2), abs(t_stat))
            else
                pvalues[j] = 1.0
            end
        else
            pvalues[j] = 1.0
        end
    end
    
    # 计算基因组膨胀因子
    lambda_gc = calculate_lambda_gc(pvalues)
    
    return GWASResult(
        snp_ids, chromosomes, positions,
        effects, se, test_stats, pvalues, mafs,
        n, m, lambda_gc, "single_marker"
    )
end

# ============================================================================
# 混合线性模型GWAS (MLMA-LOCO)
# Mixed Linear Model GWAS (Leave-One-Chromosome-Out)
# ============================================================================

"""
    run_mlma_loco(y, Z, X, G; params)

运行MLMA-LOCO分析 (留一染色体法)

# 参数
- `y`: 表型向量
- `Z`: 基因型矩阵
- `X`: 固定效应矩阵
- `G`: 基因组关系矩阵
- `chromosomes`: 染色体向量

# 返回
- `GWASResult`: GWAS分析结果
"""
function run_mlma_loco(
    y::Vector{Float64},
    Z::Matrix{Float64},
    X::Union{Matrix{Float64}, Nothing},
    G::Matrix{Float64};
    snp_ids::Vector{String} = String[],
    chromosomes::Vector{Int} = Int[],
    positions::Vector{Int} = Int[],
    params::GWASModelParams = GWASModelParams()
)
    n, m = size(Z)
    
    # 如果没有提供固定效应矩阵，使用截距
    if X === nothing
        X = ones(n, 1)
    end
    
    # 生成默认SNP信息
    if isempty(snp_ids)
        snp_ids = ["SNP_$i" for i in 1:m]
    end
    if isempty(chromosomes)
        chromosomes = ones(Int, m)
    end
    if isempty(positions)
        positions = collect(1:m)
    end
    
    unique_chr = unique(chromosomes)
    n_chr = length(unique_chr)
    
    # 初始化结果向量
    effects = zeros(m)
    se = zeros(m)
    test_stats = zeros(m)
    pvalues = zeros(m)
    mafs = zeros(m)
    
    # 估计方差组分
    var_a = var(y) * params.h2
    var_e = var(y) * (1.0 - params.h2)
    
    # 对每个染色体进行LOCO分析
    for chr in unique_chr
        # 获取不在当前染色体上的SNP
        mask_other = chromosomes .!= chr
        mask_current = chromosomes .== chr
        
        # 构建不包含当前染色体的GRM
        Z_other = Z[:, mask_other]
        if size(Z_other, 2) > 0
            G_loco = Z_other * Z_other' / size(Z_other, 2)
            G_loco = (G_loco + G_loco') / 2.0  # 保证对称性
        else
            G_loco = G
        end
        
        # 构建V矩阵
        V = var_a * G_loco + var_e * I(n)
        
        # Cholesky分解
        try
            L = cholesky(V + 1e-6 * I(n))
            V_inv = L \ I(n)
            
            # 对当前染色体上的每个SNP进行检验
            snp_indices = findall(mask_current)
            
            for j in snp_indices
                z_j = Z[:, j]
                
                # 计算MAF
                maf = mean(z_j) / 2.0
                if maf > 0.5
                    maf = 1.0 - maf
                end
                mafs[j] = maf
                
                if maf < params.maf_threshold
                    pvalues[j] = 1.0
                    continue
                end
                
                # GLS估计
                X_aug = hcat(X, z_j)
                
                # 广义最小二乘
                XtVinv = X_aug' * V_inv
                XtVinvX = XtVinv * X_aug
                XtVinvy = XtVinv * y
                
                # 解方程
                try
                    beta = XtVinvX \ XtVinvy
                    effects[j] = beta[end]
                    
                    # 计算协方差矩阵
                    cov_beta = inv(XtVinvX)
                    se[j] = sqrt(cov_beta[end, end])
                    
                    # 计算Wald检验统计量
                    if se[j] > 1e-10
                        wald = effects[j]^2 / cov_beta[end, end]
                        test_stats[j] = sqrt(wald)
                        pvalues[j] = ccdf(Chisq(1), wald)
                    else
                        pvalues[j] = 1.0
                    end
                catch
                    pvalues[j] = 1.0
                end
            end
        catch
            # 如果Cholesky分解失败，使用简单模型
            snp_indices = findall(mask_current)
            for j in snp_indices
                pvalues[j] = 1.0
            end
        end
    end
    
    # 计算基因组膨胀因子
    lambda_gc = calculate_lambda_gc(pvalues)
    
    return GWASResult(
        snp_ids, chromosomes, positions,
        effects, se, test_stats, pvalues, mafs,
        n, m, lambda_gc, "mlma_loco"
    )
end

# ============================================================================
# 便捷函数
# Convenience Function
# ============================================================================

"""
    run_gwas(y, Z, X; method, params)

运行GWAS分析的通用接口

# 参数
- `y`: 表型向量
- `Z`: 基因型矩阵
- `X`: 固定效应矩阵
- `method`: 分析方法 ("single_marker", "mlma_loco")
- `params`: 模型参数

# 返回
- `GWASResult`: GWAS分析结果
"""
function run_gwas(
    y::Vector{Float64},
    Z::Matrix{Float64},
    X::Union{Matrix{Float64}, Nothing} = nothing;
    method::String = "single_marker",
    snp_ids::Vector{String} = String[],
    chromosomes::Vector{Int} = Int[],
    positions::Vector{Int} = Int[],
    params::GWASModelParams = GWASModelParams()
)
    if method == "single_marker"
        return run_single_marker_gwas(y, Z, X; 
            snp_ids=snp_ids, chromosomes=chromosomes, 
            positions=positions, params=params)
    elseif method == "mlma_loco"
        # 计算GRM
        n, m = size(Z)
        G = Z * Z' / m
        return run_mlma_loco(y, Z, X, G; 
            snp_ids=snp_ids, chromosomes=chromosomes, 
            positions=positions, params=params)
    else
        error("Unknown GWAS method: $method")
    end
end

# ============================================================================
# 统计分析函数
# Statistical Analysis Functions
# ============================================================================

"""
    calculate_lambda_gc(pvalues)

计算基因组膨胀因子 (Genomic Inflation Factor)
"""
function calculate_lambda_gc(pvalues::Vector{Float64})
    # 过滤有效的P值
    valid_pvals = filter(p -> p > 0 && p < 1, pvalues)
    
    if isempty(valid_pvals)
        return 1.0
    end
    
    # 转换为chi-squared统计量
    chi2_stats = [quantile(Chisq(1), 1.0 - p) for p in valid_pvals]
    
    # 观测中位数 / 期望中位数
    observed_median = median(chi2_stats)
    expected_median = quantile(Chisq(1), 0.5)
    
    return observed_median / expected_median
end

"""
    manhattan_plot_data(result; threshold)

生成曼哈顿图数据

# 参数
- `result`: GWASResult对象
- `threshold`: 显著性阈值

# 返回
- Dict包含绘图所需的数据
"""
function manhattan_plot_data(result::GWASResult; threshold::Float64 = 5e-8)
    # 计算-log10(P)
    log_pvals = [-log10(max(p, 1e-300)) for p in result.pvalues]
    
    # 计算累积位置用于绘图
    chr_lengths = Dict{Int, Int}()
    for i in eachindex(result.chromosomes)
        chr = result.chromosomes[i]
        pos = result.positions[i]
        chr_lengths[chr] = max(get(chr_lengths, chr, 0), pos)
    end
    
    # 按染色体排序
    sorted_chrs = sort(collect(keys(chr_lengths)))
    chr_offsets = Dict{Int, Int}()
    cumulative = 0
    for chr in sorted_chrs
        chr_offsets[chr] = cumulative
        cumulative += chr_lengths[chr]
    end
    
    # 计算累积位置
    cumulative_positions = [
        result.positions[i] + chr_offsets[result.chromosomes[i]]
        for i in eachindex(result.positions)
    ]
    
    # 识别显著SNP
    significant_indices = findall(p -> p < threshold, result.pvalues)
    
    return Dict(
        "snp_ids" => result.snp_ids,
        "chromosomes" => result.chromosomes,
        "positions" => result.positions,
        "cumulative_positions" => cumulative_positions,
        "log_pvalues" => log_pvals,
        "significant_indices" => significant_indices,
        "threshold_line" => -log10(threshold),
        "suggestive_line" => -log10(1e-5),
        "lambda_gc" => result.lambda_gc
    )
end

"""
    qq_plot_data(result)

生成QQ图数据
"""
function qq_plot_data(result::GWASResult)
    valid_pvals = filter(p -> p > 0 && p < 1, result.pvalues)
    n = length(valid_pvals)
    
    if n == 0
        return Dict("observed" => Float64[], "expected" => Float64[])
    end
    
    # 排序P值
    sorted_pvals = sort(valid_pvals)
    
    # 期望P值
    expected_pvals = [(i - 0.5) / n for i in 1:n]
    
    # -log10转换
    observed = [-log10(p) for p in sorted_pvals]
    expected = [-log10(p) for p in expected_pvals]
    
    return Dict(
        "observed" => observed,
        "expected" => expected,
        "lambda_gc" => result.lambda_gc,
        "n_snps" => n
    )
end

# ============================================================================
# QTL区域识别
# QTL Region Identification
# ============================================================================

"""
    identify_qtl_regions(result; threshold, window_kb)

识别QTL区域

# 参数
- `result`: GWASResult对象
- `threshold`: 显著性阈值
- `window_kb`: 区域窗口大小(kb)
"""
function identify_qtl_regions(
    result::GWASResult; 
    threshold::Float64 = 5e-8,
    window_kb::Int = 500
)
    window_bp = window_kb * 1000
    regions = QTLRegion[]
    
    # 获取显著SNP
    sig_mask = result.pvalues .< threshold
    sig_indices = findall(sig_mask)
    
    if isempty(sig_indices)
        return regions
    end
    
    # 按染色体和位置分组
    chr_groups = Dict{Int, Vector{Int}}()
    for idx in sig_indices
        chr = result.chromosomes[idx]
        if !haskey(chr_groups, chr)
            chr_groups[chr] = Int[]
        end
        push!(chr_groups[chr], idx)
    end
    
    # 对每个染色体合并相邻的显著SNP
    for (chr, indices) in chr_groups
        # 按位置排序
        sorted_idx = sort(indices, by=i -> result.positions[i])
        
        current_region = [sorted_idx[1]]
        
        for i in 2:length(sorted_idx)
            idx = sorted_idx[i]
            prev_idx = current_region[end]
            
            if result.positions[idx] - result.positions[prev_idx] <= window_bp
                push!(current_region, idx)
            else
                # 创建区域
                push!(regions, create_qtl_region(result, current_region, chr))
                current_region = [idx]
            end
        end
        
        # 最后一个区域
        push!(regions, create_qtl_region(result, current_region, chr))
    end
    
    return regions
end

function create_qtl_region(result::GWASResult, indices::Vector{Int}, chr::Int)
    positions = [result.positions[i] for i in indices]
    pvalues = [result.pvalues[i] for i in indices]
    
    peak_idx = argmin(pvalues)
    
    return QTLRegion(
        chr,
        minimum(positions),
        maximum(positions),
        positions[peak_idx],
        pvalues[peak_idx],
        length(indices),
        0.0,  # 方差解释率需要额外计算
        String[]  # 候选基因需要注释数据
    )
end

# ============================================================================
# 多重检验校正
# Multiple Testing Correction
# ============================================================================

"""
    multiple_testing_correction(pvalues; method)

多重检验校正

# 方法
- "bonferroni": Bonferroni校正
- "fdr": Benjamini-Hochberg FDR校正
- "permutation": 排列检验
"""
function multiple_testing_correction(
    pvalues::Vector{Float64}; 
    method::String = "fdr",
    alpha::Float64 = 0.05
)
    n = length(pvalues)
    
    if method == "bonferroni"
        threshold = alpha / n
        adjusted = min.(pvalues .* n, 1.0)
        significant = pvalues .< threshold
        
    elseif method == "fdr"
        # Benjamini-Hochberg
        order = sortperm(pvalues)
        ranks = invperm(order)
        
        adjusted = similar(pvalues)
        for i in eachindex(pvalues)
            adjusted[i] = min(pvalues[i] * n / ranks[i], 1.0)
        end
        
        # 保证单调性
        sorted_adj = adjusted[order]
        for i in (n-1):-1:1
            sorted_adj[i] = min(sorted_adj[i], sorted_adj[i+1])
        end
        adjusted = sorted_adj[invperm(order)]
        
        significant = adjusted .< alpha
        threshold = maximum(pvalues[significant], init=0.0)
        
    else
        error("Unknown correction method: $method")
    end
    
    return Dict(
        "adjusted_pvalues" => adjusted,
        "significant" => significant,
        "threshold" => threshold,
        "method" => method,
        "n_significant" => sum(significant)
    )
end

"""
    permutation_test(y, Z, X; n_perm)

排列检验确定经验阈值
"""
function permutation_test(
    y::Vector{Float64},
    Z::Matrix{Float64},
    X::Union{Matrix{Float64}, Nothing} = nothing;
    n_perm::Int = 1000,
    alpha::Float64 = 0.05
)
    n, m = size(Z)
    min_pvals = zeros(n_perm)
    
    for perm in 1:n_perm
        # 随机打乱表型
        y_perm = y[shuffle(1:n)]
        
        # 运行GWAS
        result = run_single_marker_gwas(y_perm, Z, X)
        
        # 记录最小P值
        min_pvals[perm] = minimum(result.pvalues)
    end
    
    # 计算经验阈值
    threshold = quantile(min_pvals, alpha)
    
    return Dict(
        "threshold" => threshold,
        "n_permutations" => n_perm,
        "min_pvalues" => min_pvals
    )
end

"""
    calculate_genetic_variance_snp(y, Z, effects)

计算每个SNP解释的遗传方差
"""
function calculate_genetic_variance_snp(
    y::Vector{Float64},
    Z::Matrix{Float64},
    effects::Vector{Float64}
)
    n, m = size(Z)
    total_var = var(y)
    
    var_explained = zeros(m)
    
    for j in 1:m
        z_j = Z[:, j]
        maf = mean(z_j) / 2.0
        if maf > 0.5
            maf = 1.0 - maf
        end
        
        # 2pq * beta^2
        var_explained[j] = 2.0 * maf * (1.0 - maf) * effects[j]^2 / total_var
    end
    
    return var_explained
end

end # module GWASAnalysis

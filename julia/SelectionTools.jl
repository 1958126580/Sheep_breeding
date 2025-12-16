# ============================================================================
# 新星肉羊育种系统 - 选种决策支持模块
# NovaBreed Sheep System - Selection Decision Support Module
#
# 模块: SelectionTools
# 功能: 最优贡献选择、选配优化、近交系数计算
# 作者: AdvancedGenomics Team
# 版本: 1.0.0
# Julia版本: 1.12.2
# ============================================================================

module SelectionTools

using LinearAlgebra
using SparseArrays
using Statistics
using DataFrames
using JuMP                  # 数学优化建模
using Ipopt                 # 非线性优化求解器
using ProgressMeter

# 引入BreedingCore模块的类型
include("BreedingCore.jl")
using .BreedingCore

export calculate_inbreeding_pedigree, calculate_inbreeding_genomic
export optimal_contribution_selection, mate_allocation
export calculate_genetic_gain, rank_candidates

# ============================================================================
# 近交系数计算
# Inbreeding Coefficient Calculation
# ============================================================================

"""
    calculate_inbreeding_pedigree(ped::Pedigree)

基于系谱计算近交系数

使用Meuwissen和Luo (1992)的算法

# 参数
- `ped::Pedigree`: 系谱数据

# 返回
- `Vector{Float64}`: 每个动物的近交系数
"""
function calculate_inbreeding_pedigree(ped::Pedigree)
    println("计算基于系谱的近交系数...")
    
    n = ped.n
    F = zeros(Float64, n)
    
    # 创建ID到索引的映射
    id_to_idx = Dict(ped.id[i] => i for i in 1:n)
    
    # 按世代顺序处理
    sorted_idx = sortperm(ped.generation)
    
    @showprogress desc="计算近交系数..." for idx in sorted_idx
        i = idx
        s = ped.sire[i]
        d = ped.dam[i]
        
        if s == 0 || d == 0
            # 父母未知，近交系数为0
            F[i] = 0.0
        else
            s_idx = id_to_idx[s]
            d_idx = id_to_idx[d]
            
            # 构建A矩阵（仅需要父母之间的关系）
            A = build_A_matrix(ped)
            
            # F_i = 0.5 * A[sire, dam]
            F[i] = 0.5 * A[s_idx, d_idx]
        end
    end
    
    println("近交系数计算完成!")
    println("平均近交系数: $(round(mean(F), digits=4))")
    println("最大近交系数: $(round(maximum(F), digits=4))")
    
    return F
end

"""
    calculate_inbreeding_genomic(geno::GenotypeData)

基于基因组数据计算近交系数

使用多种方法：
1. 基于G矩阵的近交系数
2. 基于ROH（连续纯合片段）的近交系数
3. 基于杂合度的近交系数

# 参数
- `geno::GenotypeData`: 基因型数据

# 返回
- `Dict`: 包含不同方法计算的近交系数
"""
function calculate_inbreeding_genomic(geno::GenotypeData)
    println("计算基于基因组的近交系数...")
    
    n = geno.n_animals
    m = geno.n_markers
    
    # 方法1: 基于G矩阵
    println("方法1: 基于G矩阵...")
    G = build_G_matrix(geno, method="VanRaden")
    F_G = diag(G) .- 1.0  # F = G_ii - 1
    
    # 方法2: 基于杂合度
    println("方法2: 基于杂合度...")
    # 计算观测杂合度
    H_obs = vec(sum(geno.markers .== 0, dims=2)) ./ m
    
    # 计算期望杂合度（基于等位基因频率）
    p = vec(mean(geno.markers .+ 1, dims=1)) ./ 2.0
    H_exp = mean(2.0 .* p .* (1.0 .- p))
    
    # F = 1 - H_obs/H_exp
    F_H = 1.0 .- (H_obs ./ H_exp)
    
    # 方法3: 基于ROH（简化版本）
    println("方法3: 基于ROH...")
    F_ROH = calculate_roh_inbreeding(geno)
    
    println("\n近交系数计算完成!")
    println("平均近交系数 (G矩阵): $(round(mean(F_G), digits=4))")
    println("平均近交系数 (杂合度): $(round(mean(F_H), digits=4))")
    println("平均近交系数 (ROH): $(round(mean(F_ROH), digits=4))")
    
    results = Dict(
        "animal_id" => geno.animal_id,
        "F_genomic" => F_G,
        "F_heterozygosity" => F_H,
        "F_ROH" => F_ROH,
        "heterozygosity_observed" => H_obs
    )
    
    return results
end

"""
    calculate_roh_inbreeding(geno::GenotypeData; min_snp=20, min_length_mb=1.0)

计算基于ROH（Runs of Homozygosity）的近交系数

# 参数
- `geno::GenotypeData`: 基因型数据
- `min_snp::Int`: ROH的最小SNP数量
- `min_length_mb::Float64`: ROH的最小长度（Mb）

# 返回
- `Vector{Float64}`: 每个动物的ROH近交系数
"""
function calculate_roh_inbreeding(geno::GenotypeData; min_snp=20, min_length_mb=1.0)
    n = geno.n_animals
    m = geno.n_markers
    
    F_ROH = zeros(Float64, n)
    
    # 计算基因组总长度（假设均匀分布）
    genome_length = 2600.0  # 绵羊基因组约2600Mb
    
    for i in 1:n
        roh_length = 0.0
        current_run = 0
        
        for j in 1:(m-1)
            # 检查是否为纯合位点（-1或1，不是0）
            if geno.markers[i, j] != 0
                current_run += 1
            else
                # 遇到杂合位点，检查当前run
                if current_run >= min_snp
                    # 估算物理长度（简化）
                    if j > current_run
                        start_pos = geno.position[j - current_run]
                        end_pos = geno.position[j - 1]
                        length_mb = (end_pos - start_pos) / 1e6
                        
                        if length_mb >= min_length_mb
                            roh_length += length_mb
                        end
                    end
                end
                current_run = 0
            end
        end
        
        # F_ROH = ROH总长度 / 基因组总长度
        F_ROH[i] = roh_length / genome_length
    end
    
    return F_ROH
end

# ============================================================================
# 最优贡献选择（OCS）
# Optimal Contribution Selection
# ============================================================================

"""
    optimal_contribution_selection(ebv::Vector{Float64}, A::Matrix{Float64};
                                   max_inbreeding=0.01, n_selected=10)

最优贡献选择算法

在限制近交增量的前提下，最大化遗传进展

目标函数: maximize Σ(c_i * EBV_i)
约束条件:
1. Σc_i = 1 (贡献之和为1)
2. ΔF = 0.5 * Σ Σ c_i * c_j * A_ij - 0.25 ≤ max_ΔF
3. 0 ≤ c_i ≤ c_max

# 参数
- `ebv::Vector{Float64}`: 估计育种值
- `A::Matrix{Float64}`: 亲缘关系矩阵
- `max_inbreeding::Float64`: 最大近交增量
- `n_selected::Int`: 选择的动物数量

# 返回
- `Dict`: 包含最优贡献和选择的动物
"""
function optimal_contribution_selection(ebv::Vector{Float64}, A::Matrix{Float64};
                                       max_inbreeding=0.01, n_selected=10)
    println("\n" * "="^70)
    println("运行最优贡献选择（OCS）")
    println("="^70)
    println("候选动物数: $(length(ebv))")
    println("选择数量: $n_selected")
    println("最大近交增量: $max_inbreeding")
    println("="^70)
    
    n = length(ebv)
    
    # 创建优化模型
    model = Model(Ipopt.Optimizer)
    set_silent(model)
    
    # 决策变量：每个动物的贡献
    @variable(model, 0 <= c[1:n] <= 1.0/n_selected)
    
    # 目标函数：最大化遗传进展
    @objective(model, Max, sum(c[i] * ebv[i] for i in 1:n))
    
    # 约束1：贡献之和为1
    @constraint(model, sum(c) == 1.0)
    
    # 约束2：近交增量限制
    # ΔF = 0.5 * Σ Σ c_i * c_j * A_ij - 0.25
    @constraint(model, 
        0.5 * sum(c[i] * c[j] * A[i,j] for i in 1:n, j in 1:n) - 0.25 <= max_inbreeding
    )
    
    # 求解
    println("\n求解优化问题...")
    optimize!(model)
    
    # 提取结果
    if termination_status(model) == MOI.LOCALLY_SOLVED || 
       termination_status(model) == MOI.OPTIMAL
        contributions = value.(c)
        
        # 选择贡献大于阈值的动物
        threshold = 1e-6
        selected_idx = findall(contributions .> threshold)
        
        # 计算实际近交增量
        actual_inbreeding = 0.5 * sum(contributions[i] * contributions[j] * A[i,j] 
                                      for i in 1:n, j in 1:n) - 0.25
        
        # 计算预期遗传进展
        genetic_gain = sum(contributions .* ebv)
        
        println("\n优化完成!")
        println("选择的动物数: $(length(selected_idx))")
        println("预期遗传进展: $(round(genetic_gain, digits=4))")
        println("实际近交增量: $(round(actual_inbreeding, digits=6))")
        
        results = Dict(
            "contributions" => contributions,
            "selected_animals" => selected_idx,
            "genetic_gain" => genetic_gain,
            "inbreeding_rate" => actual_inbreeding,
            "status" => "success"
        )
    else
        println("\n优化失败!")
        println("状态: $(termination_status(model))")
        
        results = Dict(
            "status" => "failed",
            "termination_status" => string(termination_status(model))
        )
    end
    
    return results
end

# ============================================================================
# 选配优化
# Mate Allocation
# ============================================================================

"""
    mate_allocation(sire_ebv::Vector{Float64}, dam_ebv::Vector{Float64},
                   A::Matrix{Float64}; max_inbreeding=0.05, 
                   matings_per_sire=10)

选配优化算法

为每头母羊分配最优公羊，在控制近交的前提下最大化后代育种值

# 参数
- `sire_ebv::Vector{Float64}`: 公羊育种值
- `dam_ebv::Vector{Float64}`: 母羊育种值
- `A::Matrix{Float64}`: 完整的亲缘关系矩阵
- `max_inbreeding::Float64`: 最大允许近交系数
- `matings_per_sire::Int`: 每头公羊的最大配种数

# 返回
- `DataFrame`: 选配方案
"""
function mate_allocation(sire_ebv::Vector{Float64}, dam_ebv::Vector{Float64},
                        A::Matrix{Float64}; max_inbreeding=0.05,
                        matings_per_sire=10)
    println("\n" * "="^70)
    println("运行选配优化")
    println("="^70)
    
    n_sires = length(sire_ebv)
    n_dams = length(dam_ebv)
    
    println("公羊数: $n_sires")
    println("母羊数: $n_dams")
    println("每头公羊最大配种数: $matings_per_sire")
    println("最大近交系数: $max_inbreeding")
    println("="^70)
    
    # 创建优化模型
    model = Model(Ipopt.Optimizer)
    set_silent(model)
    
    # 决策变量：x[i,j] = 1 表示公羊i与母羊j配种
    @variable(model, x[1:n_sires, 1:n_dams], Bin)
    
    # 目标函数：最大化后代期望育种值
    # EBV_offspring = 0.5 * (EBV_sire + EBV_dam)
    @objective(model, Max, 
        sum(x[i,j] * 0.5 * (sire_ebv[i] + dam_ebv[j]) 
            for i in 1:n_sires, j in 1:n_dams)
    )
    
    # 约束1：每头母羊只配一头公羊
    for j in 1:n_dams
        @constraint(model, sum(x[i,j] for i in 1:n_sires) == 1)
    end
    
    # 约束2：每头公羊的配种数限制
    for i in 1:n_sires
        @constraint(model, sum(x[i,j] for j in 1:n_dams) <= matings_per_sire)
    end
    
    # 约束3：近交系数限制
    # F_offspring = 0.5 * A[sire, dam]
    for i in 1:n_sires
        for j in 1:n_dams
            # 假设A矩阵索引对应
            if A[i, n_sires + j] > 2 * max_inbreeding
                @constraint(model, x[i,j] == 0)
            end
        end
    end
    
    println("\n求解优化问题...")
    optimize!(model)
    
    # 提取结果
    if termination_status(model) == MOI.LOCALLY_SOLVED || 
       termination_status(model) == MOI.OPTIMAL
        
        mating_pairs = DataFrame(
            sire_id = Int[],
            dam_id = Int[],
            expected_ebv = Float64[],
            expected_inbreeding = Float64[]
        )
        
        for i in 1:n_sires
            for j in 1:n_dams
                if value(x[i,j]) > 0.5  # 二进制变量
                    push!(mating_pairs, (
                        sire_id = i,
                        dam_id = j,
                        expected_ebv = 0.5 * (sire_ebv[i] + dam_ebv[j]),
                        expected_inbreeding = 0.5 * A[i, n_sires + j]
                    ))
                end
            end
        end
        
        println("\n选配方案生成完成!")
        println("配对数: $(nrow(mating_pairs))")
        println("平均后代育种值: $(round(mean(mating_pairs.expected_ebv), digits=4))")
        println("平均近交系数: $(round(mean(mating_pairs.expected_inbreeding), digits=4))")
        
        return mating_pairs
    else
        println("\n优化失败!")
        println("状态: $(termination_status(model))")
        return DataFrame()
    end
end

# ============================================================================
# 遗传进展预测
# Genetic Gain Prediction
# ============================================================================

"""
    calculate_genetic_gain(ebv_current::Vector{Float64}, 
                          ebv_parents::Vector{Float64},
                          generation_interval::Float64)

计算遗传进展

ΔG = (EBV_offspring - EBV_parents) / generation_interval

# 参数
- `ebv_current::Vector{Float64}`: 当前世代育种值
- `ebv_parents::Vector{Float64}`: 父母世代育种值
- `generation_interval::Float64`: 世代间隔（年）

# 返回
- `Dict`: 遗传进展统计
"""
function calculate_genetic_gain(ebv_current::Vector{Float64},
                               ebv_parents::Vector{Float64},
                               generation_interval::Float64)
    println("计算遗传进展...")
    
    # 计算世代间差异
    mean_current = mean(ebv_current)
    mean_parents = mean(ebv_parents)
    
    # 总遗传进展
    total_gain = mean_current - mean_parents
    
    # 年遗传进展
    annual_gain = total_gain / generation_interval
    
    println("父母世代平均育种值: $(round(mean_parents, digits=4))")
    println("当前世代平均育种值: $(round(mean_current, digits=4))")
    println("总遗传进展: $(round(total_gain, digits=4))")
    println("年遗传进展: $(round(annual_gain, digits=4))")
    
    results = Dict(
        "mean_parents" => mean_parents,
        "mean_current" => mean_current,
        "total_gain" => total_gain,
        "annual_gain" => annual_gain,
        "generation_interval" => generation_interval
    )
    
    return results
end

"""
    rank_candidates(ebv::Vector{Float64}, reliability::Vector{Float64};
                   top_n=100, min_reliability=0.3)

对候选动物进行排名

# 参数
- `ebv::Vector{Float64}`: 育种值
- `reliability::Vector{Float64}`: 可靠性
- `top_n::Int`: 返回前N名
- `min_reliability::Float64`: 最小可靠性阈值

# 返回
- `DataFrame`: 排名结果
"""
function rank_candidates(ebv::Vector{Float64}, reliability::Vector{Float64};
                        top_n=100, min_reliability=0.3)
    println("对候选动物进行排名...")
    
    n = length(ebv)
    
    # 过滤低可靠性动物
    valid_idx = findall(reliability .>= min_reliability)
    
    # 创建排名数据框
    ranking = DataFrame(
        animal_idx = valid_idx,
        ebv = ebv[valid_idx],
        reliability = reliability[valid_idx]
    )
    
    # 按育种值降序排序
    sort!(ranking, :ebv, rev=true)
    
    # 添加排名
    ranking.rank = 1:nrow(ranking)
    
    # 返回前N名
    top_ranking = first(ranking, min(top_n, nrow(ranking)))
    
    println("有效候选数: $(length(valid_idx))")
    println("返回前 $(nrow(top_ranking)) 名")
    println("最高育种值: $(round(top_ranking.ebv[1], digits=4))")
    println("平均可靠性: $(round(mean(top_ranking.reliability), digits=4))")
    
    return top_ranking
end

end # module SelectionTools

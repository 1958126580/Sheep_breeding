# ============================================================================
# 国际顶级肉羊育种系统 - 数据质量控制模块
# International Top-tier Sheep Breeding System - Quality Control Module
#
# 模块: QualityControl
# 功能: SNP质控、表型异常检测、系谱验证
# 作者: AdvancedGenomics Team
# 版本: 1.0.0
# Julia版本: 1.12.2
# ============================================================================

module QualityControl

using LinearAlgebra
using Statistics
using DataFrames
using Distributions
using ProgressMeter
using HypothesisTests      # 统计检验

# 引入BreedingCore模块的类型
include("BreedingCore.jl")
using .BreedingCore

export qc_genotypes, qc_phenotypes, verify_pedigree
export detect_outliers, check_parent_offspring

# ============================================================================
# 基因型数据质量控制
# Genotype Data Quality Control
# ============================================================================

"""
    qc_genotypes(geno::GenotypeData; 
                 min_call_rate=0.90, min_maf=0.01, 
                 max_missing_per_animal=0.10,
                 hwe_pvalue=0.0001)

基因型数据质量控制

执行以下QC步骤：
1. SNP检出率过滤
2. 最小等位基因频率(MAF)过滤
3. Hardy-Weinberg平衡检验
4. 个体缺失率过滤
5. 性别一致性检查

# 参数
- `geno::GenotypeData`: 基因型数据
- `min_call_rate::Float64`: 最小SNP检出率
- `min_maf::Float64`: 最小等位基因频率
- `max_missing_per_animal::Float64`: 个体最大缺失率
- `hwe_pvalue::Float64`: HWE检验P值阈值

# 返回
- `Dict`: QC结果和过滤后的数据
"""
function qc_genotypes(geno::GenotypeData;
                     min_call_rate=0.90,
                     min_maf=0.01,
                     max_missing_per_animal=0.10,
                     hwe_pvalue=0.0001)
    println("\n" * "="^70)
    println("基因型数据质量控制")
    println("="^70)
    println("初始动物数: $(geno.n_animals)")
    println("初始SNP数: $(geno.n_markers)")
    println("="^70)
    
    n = geno.n_animals
    m = geno.n_markers
    
    # 创建QC报告
    qc_report = Dict{String, Any}()
    qc_report["initial_animals"] = n
    qc_report["initial_markers"] = m
    
    # 步骤1: SNP检出率过滤
    println("\n步骤1: SNP检出率过滤 (阈值: $min_call_rate)")
    snp_call_rate = vec(1.0 .- sum(geno.markers .== -9, dims=1) ./ n)
    snp_pass_call_rate = snp_call_rate .>= min_call_rate
    
    println("  通过SNP数: $(sum(snp_pass_call_rate)) / $m")
    qc_report["snp_call_rate_pass"] = sum(snp_pass_call_rate)
    
    # 步骤2: MAF过滤
    println("\n步骤2: 最小等位基因频率过滤 (阈值: $min_maf)")
    
    # 计算等位基因频率（排除缺失值）
    maf = zeros(Float64, m)
    for j in 1:m
        valid_geno = geno.markers[:, j][geno.markers[:, j] .!= -9]
        if length(valid_geno) > 0
            p = mean(valid_geno .+ 1) / 2.0  # 转换为0,1,2编码
            maf[j] = min(p, 1.0 - p)
        end
    end
    
    snp_pass_maf = maf .>= min_maf
    println("  通过SNP数: $(sum(snp_pass_maf)) / $m")
    qc_report["snp_maf_pass"] = sum(snp_pass_maf)
    
    # 步骤3: Hardy-Weinberg平衡检验
    println("\n步骤3: Hardy-Weinberg平衡检验 (P值阈值: $hwe_pvalue)")
    hwe_pass = test_hardy_weinberg(geno, pvalue_threshold=hwe_pvalue)
    println("  通过SNP数: $(sum(hwe_pass)) / $m")
    qc_report["snp_hwe_pass"] = sum(hwe_pass)
    
    # 合并SNP过滤结果
    snp_keep = snp_pass_call_rate .& snp_pass_maf .& hwe_pass
    println("\n所有SNP过滤后保留: $(sum(snp_keep)) / $m")
    
    # 步骤4: 个体缺失率过滤
    println("\n步骤4: 个体缺失率过滤 (阈值: $max_missing_per_animal)")
    animal_missing_rate = vec(sum(geno.markers .== -9, dims=2) ./ m)
    animal_keep = animal_missing_rate .<= max_missing_per_animal
    println("  通过动物数: $(sum(animal_keep)) / $n")
    qc_report["animals_pass"] = sum(animal_keep)
    
    # 步骤5: 计算个体杂合度
    println("\n步骤5: 计算个体杂合度")
    heterozygosity = calculate_heterozygosity(geno)
    
    # 检测异常杂合度（±3SD）
    het_mean = mean(heterozygosity)
    het_sd = std(heterozygosity)
    het_outliers = abs.(heterozygosity .- het_mean) .> 3 * het_sd
    
    println("  平均杂合度: $(round(het_mean, digits=4))")
    println("  杂合度异常个体数: $(sum(het_outliers))")
    qc_report["heterozygosity_outliers"] = sum(het_outliers)
    
    # 创建过滤后的数据
    filtered_geno = GenotypeData(
        geno.animal_id[animal_keep],
        geno.markers[animal_keep, snp_keep],
        geno.marker_names[snp_keep],
        geno.chromosome[snp_keep],
        geno.position[snp_keep]
    )
    
    println("\n" * "="^70)
    println("质量控制完成!")
    println("最终动物数: $(filtered_geno.n_animals)")
    println("最终SNP数: $(filtered_geno.n_markers)")
    println("="^70)
    
    results = Dict(
        "filtered_genotypes" => filtered_geno,
        "qc_report" => qc_report,
        "snp_keep" => snp_keep,
        "animal_keep" => animal_keep,
        "snp_call_rate" => snp_call_rate,
        "maf" => maf,
        "heterozygosity" => heterozygosity,
        "heterozygosity_outliers" => het_outliers
    )
    
    return results
end

"""
    test_hardy_weinberg(geno::GenotypeData; pvalue_threshold=0.0001)

Hardy-Weinberg平衡检验

# 参数
- `geno::GenotypeData`: 基因型数据
- `pvalue_threshold::Float64`: P值阈值

# 返回
- `Vector{Bool}`: 每个SNP是否通过HWE检验
"""
function test_hardy_weinberg(geno::GenotypeData; pvalue_threshold=0.0001)
    m = geno.n_markers
    hwe_pass = fill(true, m)
    
    @showprogress desc="HWE检验..." for j in 1:m
        # 统计基因型频率
        geno_counts = Dict(-1 => 0, 0 => 0, 1 => 0)
        
        for i in 1:geno.n_animals
            g = geno.markers[i, j]
            if g != -9  # 排除缺失值
                geno_counts[g] += 1
            end
        end
        
        n_total = sum(values(geno_counts))
        if n_total == 0
            hwe_pass[j] = false
            continue
        end
        
        # 观测基因型频率
        n_aa = geno_counts[-1]  # 纯合AA
        n_ab = geno_counts[0]   # 杂合AB
        n_bb = geno_counts[1]   # 纯合BB
        
        # 计算等位基因频率
        p = (2 * n_aa + n_ab) / (2 * n_total)
        q = 1.0 - p
        
        # 期望基因型频率
        e_aa = n_total * p^2
        e_ab = n_total * 2 * p * q
        e_bb = n_total * q^2
        
        # 卡方检验
        if e_aa > 5 && e_ab > 5 && e_bb > 5
            chi_sq = (n_aa - e_aa)^2 / e_aa + 
                     (n_ab - e_ab)^2 / e_ab + 
                     (n_bb - e_bb)^2 / e_bb
            
            # 自由度为1（3个基因型 - 1个等位基因频率参数 - 1）
            pvalue = 1.0 - cdf(Chisq(1), chi_sq)
            
            if pvalue < pvalue_threshold
                hwe_pass[j] = false
            end
        end
    end
    
    return hwe_pass
end

"""
    calculate_heterozygosity(geno::GenotypeData)

计算每个个体的杂合度

# 参数
- `geno::GenotypeData`: 基因型数据

# 返回
- `Vector{Float64}`: 每个个体的杂合度
"""
function calculate_heterozygosity(geno::GenotypeData)
    n = geno.n_animals
    m = geno.n_markers
    
    heterozygosity = zeros(Float64, n)
    
    for i in 1:n
        valid_markers = geno.markers[i, :] .!= -9
        n_valid = sum(valid_markers)
        
        if n_valid > 0
            n_het = sum(geno.markers[i, valid_markers] .== 0)
            heterozygosity[i] = n_het / n_valid
        end
    end
    
    return heterozygosity
end

# ============================================================================
# 表型数据质量控制
# Phenotype Data Quality Control
# ============================================================================

"""
    qc_phenotypes(pheno::PhenotypeData; 
                  z_threshold=3.5, iqr_multiplier=1.5)

表型数据质量控制

检测和标记异常值

# 参数
- `pheno::PhenotypeData`: 表型数据
- `z_threshold::Float64`: Z分数阈值
- `iqr_multiplier::Float64`: IQR倍数

# 返回
- `Dict`: QC结果
"""
function qc_phenotypes(pheno::PhenotypeData;
                      z_threshold=3.5,
                      iqr_multiplier=1.5)
    println("\n" * "="^70)
    println("表型数据质量控制")
    println("="^70)
    println("记录数: $(pheno.n)")
    println("="^70)
    
    y = pheno.trait_values
    n = length(y)
    
    # 方法1: Z分数法
    println("\n方法1: Z分数法 (阈值: ±$z_threshold)")
    outliers_z = detect_outliers_zscore(y, threshold=z_threshold)
    println("  异常值数量: $(sum(outliers_z))")
    
    # 方法2: IQR法
    println("\n方法2: 四分位距(IQR)法 (倍数: $iqr_multiplier)")
    outliers_iqr = detect_outliers_iqr(y, multiplier=iqr_multiplier)
    println("  异常值数量: $(sum(outliers_iqr))")
    
    # 方法3: Grubbs检验
    println("\n方法3: Grubbs检验")
    outliers_grubbs = detect_outliers_grubbs(y)
    println("  异常值数量: $(sum(outliers_grubbs))")
    
    # 合并异常值标记
    outliers_combined = outliers_z .| outliers_iqr .| outliers_grubbs
    println("\n总异常值数量: $(sum(outliers_combined)) ($(round(100*sum(outliers_combined)/n, digits=2))%)")
    
    # 基本统计
    println("\n基本统计:")
    println("  均值: $(round(mean(y), digits=4))")
    println("  标准差: $(round(std(y), digits=4))")
    println("  最小值: $(round(minimum(y), digits=4))")
    println("  最大值: $(round(maximum(y), digits=4))")
    
    results = Dict(
        "outliers_zscore" => outliers_z,
        "outliers_iqr" => outliers_iqr,
        "outliers_grubbs" => outliers_grubbs,
        "outliers_combined" => outliers_combined,
        "n_outliers" => sum(outliers_combined),
        "mean" => mean(y),
        "std" => std(y),
        "min" => minimum(y),
        "max" => maximum(y)
    )
    
    return results
end

"""
    detect_outliers_zscore(y::Vector{Float64}; threshold=3.5)

使用Z分数法检测异常值

# 参数
- `y::Vector{Float64}`: 数据向量
- `threshold::Float64`: Z分数阈值

# 返回
- `Vector{Bool}`: 异常值标记
"""
function detect_outliers_zscore(y::Vector{Float64}; threshold=3.5)
    μ = mean(y)
    σ = std(y)
    z_scores = abs.((y .- μ) ./ σ)
    return z_scores .> threshold
end

"""
    detect_outliers_iqr(y::Vector{Float64}; multiplier=1.5)

使用四分位距(IQR)法检测异常值

# 参数
- `y::Vector{Float64}`: 数据向量
- `multiplier::Float64`: IQR倍数

# 返回
- `Vector{Bool}`: 异常值标记
"""
function detect_outliers_iqr(y::Vector{Float64}; multiplier=1.5)
    q1 = quantile(y, 0.25)
    q3 = quantile(y, 0.75)
    iqr = q3 - q1
    
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr
    
    return (y .< lower_bound) .| (y .> upper_bound)
end

"""
    detect_outliers_grubbs(y::Vector{Float64}; alpha=0.05)

使用Grubbs检验检测异常值

# 参数
- `y::Vector{Float64}`: 数据向量
- `alpha::Float64`: 显著性水平

# 返回
- `Vector{Bool}`: 异常值标记
"""
function detect_outliers_grubbs(y::Vector{Float64}; alpha=0.05)
    n = length(y)
    outliers = fill(false, n)
    
    # Grubbs检验临界值
    t_dist = TDist(n - 2)
    t_crit = quantile(t_dist, 1 - alpha / (2 * n))
    G_crit = ((n - 1) / sqrt(n)) * sqrt(t_crit^2 / (n - 2 + t_crit^2))
    
    μ = mean(y)
    σ = std(y)
    
    # 计算Grubbs统计量
    G = abs.((y .- μ) ./ σ)
    
    outliers = G .> G_crit
    
    return outliers
end

# ============================================================================
# 系谱验证
# Pedigree Verification
# ============================================================================

"""
    verify_pedigree(ped::Pedigree, geno::GenotypeData)

使用基因型数据验证系谱关系

# 参数
- `ped::Pedigree`: 系谱数据
- `geno::GenotypeData`: 基因型数据

# 返回
- `Dict`: 验证结果
"""
function verify_pedigree(ped::Pedigree, geno::GenotypeData)
    println("\n" * "="^70)
    println("系谱验证")
    println("="^70)
    
    # 找到有基因型的动物
    genotyped_animals = intersect(ped.id, geno.animal_id)
    println("有基因型的动物数: $(length(genotyped_animals))")
    
    # 亲子鉴定
    parent_offspring_results = check_parent_offspring(ped, geno)
    
    println("\n验证完成!")
    
    results = Dict(
        "genotyped_animals" => genotyped_animals,
        "parent_offspring_check" => parent_offspring_results
    )
    
    return results
end

"""
    check_parent_offspring(ped::Pedigree, geno::GenotypeData)

检查亲子关系的一致性

使用Mendelian不一致性检测

# 参数
- `ped::Pedigree`: 系谱数据
- `geno::GenotypeData`: 基因型数据

# 返回
- `DataFrame`: 亲子鉴定结果
"""
function check_parent_offspring(ped::Pedigree, geno::GenotypeData)
    println("\n检查亲子关系...")
    
    # 创建ID映射
    ped_id_to_idx = Dict(ped.id[i] => i for i in 1:ped.n)
    geno_id_to_idx = Dict(geno.animal_id[i] => i for i in 1:geno.n_animals)
    
    results = DataFrame(
        offspring_id = Int[],
        parent_id = Int[],
        parent_type = String[],
        n_markers_compared = Int[],
        n_conflicts = Int[],
        conflict_rate = Float64[]
    )
    
    # 检查每个有基因型的动物
    for i in 1:ped.n
        animal_id = ped.id[i]
        
        # 检查是否有基因型
        if !haskey(geno_id_to_idx, animal_id)
            continue
        end
        
        offspring_geno_idx = geno_id_to_idx[animal_id]
        
        # 检查父亲
        sire_id = ped.sire[i]
        if sire_id != 0 && haskey(geno_id_to_idx, sire_id)
            sire_geno_idx = geno_id_to_idx[sire_id]
            conflicts = count_mendelian_conflicts(
                geno.markers[offspring_geno_idx, :],
                geno.markers[sire_geno_idx, :],
                nothing
            )
            
            n_compared = sum((geno.markers[offspring_geno_idx, :] .!= -9) .& 
                           (geno.markers[sire_geno_idx, :] .!= -9))
            
            push!(results, (
                offspring_id = animal_id,
                parent_id = sire_id,
                parent_type = "sire",
                n_markers_compared = n_compared,
                n_conflicts = conflicts,
                conflict_rate = conflicts / n_compared
            ))
        end
        
        # 检查母亲
        dam_id = ped.dam[i]
        if dam_id != 0 && haskey(geno_id_to_idx, dam_id)
            dam_geno_idx = geno_id_to_idx[dam_id]
            conflicts = count_mendelian_conflicts(
                geno.markers[offspring_geno_idx, :],
                nothing,
                geno.markers[dam_geno_idx, :]
            )
            
            n_compared = sum((geno.markers[offspring_geno_idx, :] .!= -9) .& 
                           (geno.markers[dam_geno_idx, :] .!= -9))
            
            push!(results, (
                offspring_id = animal_id,
                parent_id = dam_id,
                parent_type = "dam",
                n_markers_compared = n_compared,
                n_conflicts = conflicts,
                conflict_rate = conflicts / n_compared
            ))
        end
    end
    
    if nrow(results) > 0
        println("检查的亲子对数: $(nrow(results))")
        println("平均冲突率: $(round(mean(results.conflict_rate), digits=4))")
        
        # 标记可疑的亲子关系（冲突率>1%）
        suspicious = results.conflict_rate .> 0.01
        println("可疑亲子关系数: $(sum(suspicious))")
    end
    
    return results
end

"""
    count_mendelian_conflicts(offspring::Vector{Int8}, 
                             sire::Union{Vector{Int8}, Nothing},
                             dam::Union{Vector{Int8}, Nothing})

计算Mendelian不一致性数量

# 参数
- `offspring::Vector{Int8}`: 后代基因型
- `sire::Union{Vector{Int8}, Nothing}`: 父亲基因型
- `dam::Union{Vector{Int8}, Nothing}`: 母亲基因型

# 返回
- `Int`: 冲突数量
"""
function count_mendelian_conflicts(offspring::Vector{Int8},
                                  sire::Union{Vector{Int8}, Nothing},
                                  dam::Union{Vector{Int8}, Nothing})
    m = length(offspring)
    conflicts = 0
    
    for j in 1:m
        o = offspring[j]
        
        # 跳过缺失值
        if o == -9
            continue
        end
        
        # 检查与父亲的冲突
        if sire !== nothing
            s = sire[j]
            if s != -9
                # 简化的Mendelian检查
                # 如果父亲是纯合AA(-1)，后代不能是纯合BB(1)
                if s == -1 && o == 1
                    conflicts += 1
                elseif s == 1 && o == -1
                    conflicts += 1
                end
            end
        end
        
        # 检查与母亲的冲突
        if dam !== nothing
            d = dam[j]
            if d != -9
                if d == -1 && o == 1
                    conflicts += 1
                elseif d == 1 && o == -1
                    conflicts += 1
                end
            end
        end
    end
    
    return conflicts
end

end # module QualityControl

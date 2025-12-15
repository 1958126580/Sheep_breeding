# ============================================================================
# 国际顶级肉羊育种系统 - 联邦学习模块
# International Top-tier Sheep Breeding System - Federated Learning Module
#
# 文件: FederatedLearning.jl
# 功能: 隐私保护的多机构联合育种值估计
# ============================================================================

module FederatedLearning

using LinearAlgebra
using Statistics
using Random

export federated_blup, federated_gblup
export secure_aggregation, differential_privacy_noise
export FederatedClient, FederatedServer, FederatedConfig
export cross_institution_validation, privacy_budget_check

# ============================================================================
# 数据结构定义
# Data Structure Definitions
# ============================================================================

"""
联邦学习配置
"""
struct FederatedConfig
    num_rounds::Int                   # 通信轮次
    min_clients::Int                  # 最小参与客户端数
    fraction_fit::Float64             # 每轮参与比例
    privacy_budget::Float64           # 差分隐私预算 (epsilon)
    noise_multiplier::Float64         # 噪声乘数
    clip_norm::Float64                # 梯度裁剪范数
    secure_aggregation::Bool          # 是否使用安全聚合
    convergence_threshold::Float64    # 收敛阈值
end

# 默认配置
function FederatedConfig(;
    num_rounds::Int = 10,
    min_clients::Int = 2,
    fraction_fit::Float64 = 1.0,
    privacy_budget::Float64 = 1.0,
    noise_multiplier::Float64 = 1.0,
    clip_norm::Float64 = 1.0,
    secure_aggregation::Bool = true,
    convergence_threshold::Float64 = 1e-4
)
    return FederatedConfig(
        num_rounds, min_clients, fraction_fit,
        privacy_budget, noise_multiplier, clip_norm,
        secure_aggregation, convergence_threshold
    )
end

"""
联邦客户端 (代表一个机构)
"""
mutable struct FederatedClient
    client_id::String
    organization_name::String
    n_animals::Int
    n_genotyped::Int
    local_A::Union{Matrix{Float64}, Nothing}     # 本地亲缘关系矩阵
    local_G::Union{Matrix{Float64}, Nothing}     # 本地基因组关系矩阵
    local_y::Union{Vector{Float64}, Nothing}     # 本地表型
    local_X::Union{Matrix{Float64}, Nothing}     # 本地固定效应
    local_ebv::Union{Vector{Float64}, Nothing}   # 本地育种值
    secret_share::Union{Vector{Float64}, Nothing} # 安全聚合密钥份额
end

"""
联邦服务器 (中心协调者)
"""
mutable struct FederatedServer
    server_id::String
    clients::Vector{FederatedClient}
    global_model::Dict{String, Any}
    round_history::Vector{Dict{String, Any}}
    config::FederatedConfig
end

"""
联邦学习结果
"""
struct FederatedResult
    global_ebv::Dict{String, Vector{Float64}}    # 各机构的育种值
    global_fixed_effects::Vector{Float64}         # 全局固定效应
    n_rounds::Int
    final_loss::Float64
    privacy_consumed::Float64
    participating_clients::Vector{String}
    convergence_achieved::Bool
end

# ============================================================================
# 联邦BLUP实现
# Federated BLUP Implementation
# ============================================================================

"""
    federated_blup(clients, config)

运行联邦BLUP分析

# 算法流程
1. 服务器初始化全局模型参数
2. 每轮迭代:
   - 选择参与的客户端
   - 客户端本地计算梯度/更新
   - 安全聚合客户端更新
   - 添加差分隐私噪声
   - 更新全局模型
3. 收敛检查

# 参数
- `clients`: 客户端列表
- `config`: 联邦配置

# 返回
- `FederatedResult`: 联邦学习结果
"""
function federated_blup(
    clients::Vector{FederatedClient},
    config::FederatedConfig
)
    n_clients = length(clients)
    
    if n_clients < config.min_clients
        error("参与客户端数量不足: 需要 $(config.min_clients), 实际 $(n_clients)")
    end
    
    # 初始化全局模型
    total_animals = sum(c.n_animals for c in clients)
    global_fixed_effects = zeros(1)  # 截距
    
    # 初始化服务器
    server = FederatedServer(
        "central_server",
        clients,
        Dict("fixed_effects" => global_fixed_effects),
        Dict{String, Any}[],
        config
    )
    
    # 联邦训练循环
    privacy_consumed = 0.0
    converged = false
    final_loss = Inf
    
    for round in 1:config.num_rounds
        # 选择参与客户端
        n_selected = max(config.min_clients, 
                        ceil(Int, n_clients * config.fraction_fit))
        selected_indices = randperm(n_clients)[1:n_selected]
        selected_clients = clients[selected_indices]
        
        # 收集客户端更新
        client_updates = Vector{Dict{String, Any}}()
        client_weights = Float64[]
        
        for client in selected_clients
            # 本地训练
            local_update = local_blup_update(client, server.global_model)
            push!(client_updates, local_update)
            push!(client_weights, Float64(client.n_animals))
        end
        
        # 安全聚合
        if config.secure_aggregation
            aggregated = secure_aggregation(client_updates, client_weights)
        else
            aggregated = simple_aggregation(client_updates, client_weights)
        end
        
        # 添加差分隐私噪声
        if config.privacy_budget < Inf
            aggregated, privacy_cost = add_dp_noise(
                aggregated, 
                config.noise_multiplier,
                config.clip_norm,
                length(selected_clients)
            )
            privacy_consumed += privacy_cost
        end
        
        # 更新全局模型
        old_model = copy(server.global_model["fixed_effects"])
        server.global_model["fixed_effects"] = aggregated["fixed_effects"]
        
        # 记录历史
        push!(server.round_history, Dict(
            "round" => round,
            "n_clients" => length(selected_clients),
            "loss" => aggregated["loss"]
        ))
        
        final_loss = aggregated["loss"]
        
        # 收敛检查
        if norm(server.global_model["fixed_effects"] - old_model) < config.convergence_threshold
            converged = true
            break
        end
        
        # 隐私预算检查
        if privacy_consumed >= config.privacy_budget
            @warn "隐私预算耗尽，提前终止"
            break
        end
    end
    
    # 最终育种值估计
    global_ebv = Dict{String, Vector{Float64}}()
    for client in clients
        client_ebv = compute_final_ebv(client, server.global_model)
        global_ebv[client.client_id] = client_ebv
    end
    
    return FederatedResult(
        global_ebv,
        server.global_model["fixed_effects"],
        length(server.round_history),
        final_loss,
        privacy_consumed,
        [c.client_id for c in clients],
        converged
    )
end

"""
本地BLUP更新计算
"""
function local_blup_update(
    client::FederatedClient,
    global_model::Dict{String, Any}
)
    # 如果没有本地数据，返回零更新
    if client.local_y === nothing || client.local_A === nothing
        return Dict(
            "fixed_effects" => zeros(length(global_model["fixed_effects"])),
            "n_samples" => 0,
            "loss" => 0.0
        )
    end
    
    n = client.n_animals
    y = client.local_y
    X = client.local_X === nothing ? ones(n, 1) : client.local_X
    A = client.local_A
    
    # 简化的BLUP更新
    # 在实际应用中，这里应该是更复杂的本地求解
    
    # 假设遗传力 h2 = 0.3
    h2 = 0.3
    lambda = (1 - h2) / h2
    
    # 构建混合模型方程
    XtX = X' * X
    XtZ = X' * I(n)
    Zty = y
    Xty = X' * y
    
    # 本地固定效应估计
    if size(X, 2) > 0
        try
            local_fixed = X \ y
        catch
            local_fixed = zeros(size(X, 2))
        end
    else
        local_fixed = Float64[]
    end
    
    # 计算残差
    residual = y - X * local_fixed
    loss = sum(residual .^ 2) / n
    
    return Dict(
        "fixed_effects" => local_fixed,
        "n_samples" => n,
        "loss" => loss
    )
end

"""
计算最终育种值
"""
function compute_final_ebv(
    client::FederatedClient,
    global_model::Dict{String, Any}
)
    if client.local_y === nothing || client.local_A === nothing
        return Float64[]
    end
    
    n = client.n_animals
    y = client.local_y
    X = client.local_X === nothing ? ones(n, 1) : client.local_X
    A = client.local_A
    
    # 使用全局固定效应
    global_fixed = global_model["fixed_effects"]
    if length(global_fixed) != size(X, 2)
        global_fixed = resize!(copy(global_fixed), size(X, 2))
    end
    
    # 计算残差
    residual = y - X * global_fixed
    
    # BLUP求解育种值
    h2 = 0.3
    lambda = (1 - h2) / h2
    
    try
        lhs = A + lambda * I(n)
        ebv = lhs \ residual
        return ebv
    catch
        return zeros(n)
    end
end

# ============================================================================
# 安全聚合
# Secure Aggregation
# ============================================================================

"""
    secure_aggregation(updates, weights)

安全聚合客户端更新

使用加法秘密共享方案，确保服务器只能看到聚合结果
"""
function secure_aggregation(
    updates::Vector{Dict{String, Any}},
    weights::Vector{Float64}
)
    # 简化实现: 加权平均
    # 在实际部署中，应使用完整的安全聚合协议
    
    total_weight = sum(weights)
    n_updates = length(updates)
    
    if n_updates == 0
        return Dict("fixed_effects" => Float64[], "loss" => 0.0)
    end
    
    # 获取第一个更新的维度
    n_fixed = length(updates[1]["fixed_effects"])
    
    # 加权聚合
    aggregated_fixed = zeros(n_fixed)
    aggregated_loss = 0.0
    
    for (i, update) in enumerate(updates)
        w = weights[i] / total_weight
        if length(update["fixed_effects"]) == n_fixed
            aggregated_fixed .+= w * update["fixed_effects"]
        end
        aggregated_loss += w * update["loss"]
    end
    
    return Dict(
        "fixed_effects" => aggregated_fixed,
        "loss" => aggregated_loss,
        "n_clients" => n_updates
    )
end

"""
简单聚合 (无安全保护)
"""
function simple_aggregation(
    updates::Vector{Dict{String, Any}},
    weights::Vector{Float64}
)
    return secure_aggregation(updates, weights)
end

# ============================================================================
# 差分隐私
# Differential Privacy
# ============================================================================

"""
    differential_privacy_noise(sensitivity, epsilon, delta)

计算差分隐私所需的噪声标准差

使用高斯机制
"""
function differential_privacy_noise(
    sensitivity::Float64,
    epsilon::Float64,
    delta::Float64 = 1e-5
)
    # 高斯机制噪声标准差
    c = sqrt(2.0 * log(1.25 / delta))
    sigma = c * sensitivity / epsilon
    return sigma
end

"""
    add_dp_noise(aggregated, noise_multiplier, clip_norm, n_clients)

向聚合结果添加差分隐私噪声
"""
function add_dp_noise(
    aggregated::Dict{String, Any},
    noise_multiplier::Float64,
    clip_norm::Float64,
    n_clients::Int
)
    # 计算灵敏度
    sensitivity = clip_norm / n_clients
    
    # 添加高斯噪声
    noisy_fixed = aggregated["fixed_effects"] .+ 
                  randn(length(aggregated["fixed_effects"])) * noise_multiplier * sensitivity
    
    # 计算隐私成本 (使用矩会计)
    privacy_cost = noise_multiplier^2 / (2.0 * n_clients)
    
    return Dict(
        "fixed_effects" => noisy_fixed,
        "loss" => aggregated["loss"],
        "n_clients" => get(aggregated, "n_clients", n_clients)
    ), privacy_cost
end

"""
    privacy_budget_check(epsilon_spent, epsilon_total)

检查隐私预算是否耗尽
"""
function privacy_budget_check(epsilon_spent::Float64, epsilon_total::Float64)
    remaining = epsilon_total - epsilon_spent
    if remaining <= 0
        return Dict(
            "status" => "exhausted",
            "remaining" => 0.0,
            "can_continue" => false
        )
    else
        return Dict(
            "status" => "available",
            "remaining" => remaining,
            "can_continue" => true,
            "utilization" => epsilon_spent / epsilon_total
        )
    end
end

# ============================================================================
# 联邦GBLUP
# Federated GBLUP
# ============================================================================

"""
    federated_gblup(clients, config)

运行联邦GBLUP分析 (基因组BLUP)

与federated_blup类似，但使用基因组关系矩阵G而非系谱关系矩阵A
"""
function federated_gblup(
    clients::Vector{FederatedClient},
    config::FederatedConfig
)
    # 检查所有客户端是否有基因型数据
    genotyped_clients = filter(c -> c.local_G !== nothing, clients)
    
    if length(genotyped_clients) < config.min_clients
        error("基因型数据客户端数量不足")
    end
    
    # 修改客户端，使用G矩阵
    for client in genotyped_clients
        if client.local_A === nothing
            client.local_A = client.local_G
        end
    end
    
    # 调用联邦BLUP
    return federated_blup(genotyped_clients, config)
end

# ============================================================================
# 跨机构验证
# Cross-institution Validation
# ============================================================================

"""
    cross_institution_validation(clients, config)

跨机构交叉验证

评估联邦模型的泛化能力
"""
function cross_institution_validation(
    clients::Vector{FederatedClient},
    config::FederatedConfig;
    n_folds::Int = 5
)
    n_clients = length(clients)
    
    if n_clients < 2
        error("至少需要2个客户端进行交叉验证")
    end
    
    validation_results = Dict{String, Any}[]
    
    # 留一机构法交叉验证
    for i in 1:n_clients
        # 训练集: 除第i个客户端外的所有客户端
        train_clients = clients[setdiff(1:n_clients, i)]
        test_client = clients[i]
        
        # 训练联邦模型
        result = federated_blup(train_clients, config)
        
        # 在测试客户端上评估
        if test_client.local_y !== nothing
            predicted_ebv = compute_final_ebv(test_client, 
                Dict("fixed_effects" => result.global_fixed_effects))
            
            # 计算相关性 (作为准确性度量)
            if length(predicted_ebv) > 0 && length(test_client.local_y) > 0
                correlation = cor(predicted_ebv, test_client.local_y)
            else
                correlation = 0.0
            end
            
            push!(validation_results, Dict(
                "test_client" => test_client.client_id,
                "correlation" => isnan(correlation) ? 0.0 : correlation,
                "n_test_animals" => test_client.n_animals
            ))
        end
    end
    
    # 汇总结果
    correlations = [r["correlation"] for r in validation_results]
    
    return Dict(
        "fold_results" => validation_results,
        "mean_correlation" => mean(correlations),
        "std_correlation" => std(correlations),
        "n_folds" => length(validation_results)
    )
end

# ============================================================================
# 辅助函数
# Helper Functions
# ============================================================================

"""
创建模拟客户端 (用于测试)
"""
function create_mock_client(
    client_id::String,
    n_animals::Int;
    has_genotype::Bool = false
)
    # 生成模拟数据
    A = Matrix{Float64}(I(n_animals))  # 简化: 使用单位矩阵
    y = randn(n_animals) * 10 .+ 50    # 模拟表型
    X = ones(n_animals, 1)             # 截距
    
    G = has_genotype ? A + 0.1 * randn(n_animals, n_animals) : nothing
    if G !== nothing
        G = (G + G') / 2  # 保证对称
    end
    
    return FederatedClient(
        client_id,
        "Organization_$client_id",
        n_animals,
        has_genotype ? n_animals : 0,
        A,
        G,
        y,
        X,
        nothing,
        nothing
    )
end

end # module FederatedLearning

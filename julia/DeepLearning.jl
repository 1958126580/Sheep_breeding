# ============================================================================
# 国际顶级肉羊育种系统 - 深度学习育种值预测模块
# International Top-tier Sheep Breeding System - Deep Learning Breeding Module
#
# 文件: DeepLearning.jl
# 功能: 深度神经网络育种值预测、基因组选择
# ============================================================================

module DeepLearning

using LinearAlgebra
using Statistics
using Random

export DeepGBLUP, train_deep_model, predict_ebv
export MLPModel, CNNGenomic, AttentionModel
export DeepLearningConfig, TrainingResult
export cross_validate_deep, hyperparameter_search

# ============================================================================
# 配置和数据结构
# Configuration and Data Structures
# ============================================================================

"""
深度学习配置
"""
struct DeepLearningConfig
    hidden_layers::Vector{Int}        # 隐藏层大小
    activation::String                # 激活函数: "relu", "tanh", "sigmoid"
    dropout_rate::Float64             # Dropout率
    learning_rate::Float64            # 学习率
    batch_size::Int                   # 批大小
    epochs::Int                       # 训练轮数
    early_stopping_patience::Int      # 早停耐心值
    l2_regularization::Float64        # L2正则化系数
    use_batch_norm::Bool              # 是否使用批归一化
end

# 默认配置
function DeepLearningConfig(;
    hidden_layers::Vector{Int} = [256, 128, 64],
    activation::String = "relu",
    dropout_rate::Float64 = 0.2,
    learning_rate::Float64 = 0.001,
    batch_size::Int = 32,
    epochs::Int = 100,
    early_stopping_patience::Int = 10,
    l2_regularization::Float64 = 0.01,
    use_batch_norm::Bool = true
)
    return DeepLearningConfig(
        hidden_layers, activation, dropout_rate,
        learning_rate, batch_size, epochs,
        early_stopping_patience, l2_regularization,
        use_batch_norm
    )
end

"""
MLP模型 (多层感知机)
"""
mutable struct MLPModel
    weights::Vector{Matrix{Float64}}
    biases::Vector{Vector{Float64}}
    layer_sizes::Vector{Int}
    activation::String
    config::DeepLearningConfig
end

"""
训练结果
"""
struct TrainingResult
    model::MLPModel
    train_loss_history::Vector{Float64}
    val_loss_history::Vector{Float64}
    best_epoch::Int
    final_train_loss::Float64
    final_val_loss::Float64
    training_time_seconds::Float64
    correlation_train::Float64
    correlation_val::Float64
end

# ============================================================================
# 激活函数
# Activation Functions
# ============================================================================

"""ReLU激活函数"""
relu(x) = max.(0, x)
relu_derivative(x) = Float64.(x .> 0)

"""Sigmoid激活函数"""
sigmoid(x) = 1.0 ./ (1.0 .+ exp.(-clamp.(x, -500, 500)))
sigmoid_derivative(x) = sigmoid(x) .* (1 .- sigmoid(x))

"""Tanh激活函数"""
tanh_act(x) = tanh.(x)
tanh_derivative(x) = 1 .- tanh.(x).^2

"""获取激活函数"""
function get_activation(name::String)
    if name == "relu"
        return relu, relu_derivative
    elseif name == "sigmoid"
        return sigmoid, sigmoid_derivative
    elseif name == "tanh"
        return tanh_act, tanh_derivative
    else
        return relu, relu_derivative
    end
end

# ============================================================================
# MLP模型构建
# MLP Model Construction
# ============================================================================

"""
    MLPModel(input_size, config)

构建MLP模型
"""
function MLPModel(
    input_size::Int,
    output_size::Int,
    config::DeepLearningConfig
)
    layer_sizes = [input_size; config.hidden_layers; output_size]
    n_layers = length(layer_sizes) - 1
    
    # Xavier初始化
    weights = Matrix{Float64}[]
    biases = Vector{Float64}[]
    
    for i in 1:n_layers
        fan_in = layer_sizes[i]
        fan_out = layer_sizes[i+1]
        
        # Xavier/Glorot初始化
        std = sqrt(2.0 / (fan_in + fan_out))
        W = randn(fan_out, fan_in) * std
        b = zeros(fan_out)
        
        push!(weights, W)
        push!(biases, b)
    end
    
    return MLPModel(weights, biases, layer_sizes, config.activation, config)
end

"""
前向传播
"""
function forward(model::MLPModel, X::Matrix{Float64})
    activation_fn, _ = get_activation(model.activation)
    
    n_layers = length(model.weights)
    activations = [X']  # 转置为 features × samples
    
    for i in 1:n_layers
        W = model.weights[i]
        b = model.biases[i]
        
        # 线性变换
        z = W * activations[end] .+ b
        
        # 激活 (最后一层不激活，用于回归)
        if i < n_layers
            a = activation_fn(z)
        else
            a = z
        end
        
        push!(activations, a)
    end
    
    return activations[end]'  # 转回 samples × features
end

"""
预测
"""
function predict_ebv(model::MLPModel, X::Matrix{Float64})
    return vec(forward(model, X))
end

# ============================================================================
# 训练算法
# Training Algorithm
# ============================================================================

"""
    train_deep_model(X_train, y_train, X_val, y_val, config)

训练深度学习模型
"""
function train_deep_model(
    X_train::Matrix{Float64},
    y_train::Vector{Float64},
    X_val::Matrix{Float64},
    y_val::Vector{Float64},
    config::DeepLearningConfig
)
    start_time = time()
    
    n_samples, n_features = size(X_train)
    
    # 初始化模型
    model = MLPModel(n_features, 1, config)
    
    # 训练历史
    train_loss_history = Float64[]
    val_loss_history = Float64[]
    
    best_val_loss = Inf
    best_epoch = 0
    best_weights = deepcopy(model.weights)
    best_biases = deepcopy(model.biases)
    patience_counter = 0
    
    # 训练循环
    for epoch in 1:config.epochs
        # 打乱数据
        perm = randperm(n_samples)
        X_shuffled = X_train[perm, :]
        y_shuffled = y_train[perm]
        
        epoch_loss = 0.0
        n_batches = ceil(Int, n_samples / config.batch_size)
        
        for batch in 1:n_batches
            start_idx = (batch - 1) * config.batch_size + 1
            end_idx = min(batch * config.batch_size, n_samples)
            
            X_batch = X_shuffled[start_idx:end_idx, :]
            y_batch = y_shuffled[start_idx:end_idx]
            
            # 前向传播
            y_pred = predict_ebv(model, X_batch)
            
            # 计算损失
            batch_loss = mean((y_pred .- y_batch).^2)
            epoch_loss += batch_loss
            
            # 反向传播 (简化的梯度下降)
            gradient_descent_step!(model, X_batch, y_batch, config)
        end
        
        epoch_loss /= n_batches
        push!(train_loss_history, epoch_loss)
        
        # 验证
        y_val_pred = predict_ebv(model, X_val)
        val_loss = mean((y_val_pred .- y_val).^2)
        push!(val_loss_history, val_loss)
        
        # 早停检查
        if val_loss < best_val_loss
            best_val_loss = val_loss
            best_epoch = epoch
            best_weights = deepcopy(model.weights)
            best_biases = deepcopy(model.biases)
            patience_counter = 0
        else
            patience_counter += 1
            if patience_counter >= config.early_stopping_patience
                break
            end
        end
    end
    
    # 恢复最佳模型
    model.weights = best_weights
    model.biases = best_biases
    
    # 计算最终指标
    y_train_pred = predict_ebv(model, X_train)
    y_val_pred = predict_ebv(model, X_val)
    
    corr_train = cor(y_train_pred, y_train)
    corr_val = cor(y_val_pred, y_val)
    
    training_time = time() - start_time
    
    return TrainingResult(
        model,
        train_loss_history,
        val_loss_history,
        best_epoch,
        train_loss_history[end],
        val_loss_history[end],
        training_time,
        isnan(corr_train) ? 0.0 : corr_train,
        isnan(corr_val) ? 0.0 : corr_val
    )
end

"""
梯度下降更新步骤 (简化版)
"""
function gradient_descent_step!(
    model::MLPModel,
    X::Matrix{Float64},
    y::Vector{Float64},
    config::DeepLearningConfig
)
    # 前向传播存储中间结果
    activation_fn, activation_deriv = get_activation(model.activation)
    n_layers = length(model.weights)
    
    # 前向传播
    activations = [X']
    zs = Matrix{Float64}[]
    
    for i in 1:n_layers
        W = model.weights[i]
        b = model.biases[i]
        
        z = W * activations[end] .+ b
        push!(zs, z)
        
        if i < n_layers
            a = activation_fn(z)
        else
            a = z
        end
        push!(activations, a)
    end
    
    # 反向传播
    n_samples = size(X, 1)
    y_pred = vec(activations[end]')
    
    # 输出层误差
    delta = (y_pred .- y) / n_samples
    delta = reshape(delta, 1, :)
    
    # 更新权重和偏置 (从后向前)
    for i in n_layers:-1:1
        # 计算梯度
        dW = delta * activations[i]'
        db = vec(sum(delta, dims=2))
        
        # L2正则化
        dW .+= config.l2_regularization * model.weights[i]
        
        # 更新
        model.weights[i] .-= config.learning_rate * dW
        model.biases[i] .-= config.learning_rate * db
        
        # 传播误差到下一层
        if i > 1
            delta = model.weights[i]' * delta
            delta = delta .* activation_deriv(zs[i-1])
        end
    end
end

# ============================================================================
# DeepGBLUP
# Deep GBLUP (深度学习 + GBLUP混合模型)
# ============================================================================

"""
    DeepGBLUP(Z, y, A_or_G, config)

深度GBLUP模型

结合深度学习提取非线性特征和GBLUP的关系矩阵
"""
function DeepGBLUP(
    Z::Matrix{Float64},      # 基因型矩阵
    y::Vector{Float64},       # 表型
    A_or_G::Matrix{Float64},  # 关系矩阵
    config::DeepLearningConfig;
    n_features::Int = 64      # 深度特征维度
)
    n, m = size(Z)
    
    # 步骤1: 使用深度网络提取非线性特征
    # 修改配置以输出n_features维特征
    feature_config = DeepLearningConfig(
        hidden_layers = [256, 128, n_features],
        activation = config.activation,
        dropout_rate = config.dropout_rate,
        learning_rate = config.learning_rate,
        batch_size = config.batch_size,
        epochs = config.epochs ÷ 2,  # 减少epoch用于特征提取
        early_stopping_patience = config.early_stopping_patience,
        l2_regularization = config.l2_regularization,
        use_batch_norm = config.use_batch_norm
    )
    
    # 分割数据
    n_train = Int(floor(0.8 * n))
    train_idx = 1:n_train
    val_idx = (n_train+1):n
    
    # 训练特征提取器
    feature_result = train_deep_model(
        Z[train_idx, :], y[train_idx],
        Z[val_idx, :], y[val_idx],
        feature_config
    )
    
    # 提取深度特征 (使用倒数第二层的激活)
    deep_features = extract_features(feature_result.model, Z)
    
    # 步骤2: 使用深度特征计算新的关系矩阵
    G_deep = deep_features * deep_features' / size(deep_features, 2)
    G_deep = (G_deep + G_deep') / 2  # 确保对称
    
    # 步骤3: 结合原始关系矩阵和深度关系矩阵
    alpha = 0.5  # 混合权重
    G_combined = alpha * A_or_G + (1 - alpha) * G_deep
    
    # 步骤4: 使用GBLUP求解育种值
    h2 = 0.3
    lambda = (1 - h2) / h2
    
    X = ones(n, 1)
    
    try
        lhs = X' * X
        rhs = X' * y
        fixed_effects = lhs \ rhs
        
        y_adj = y - X * fixed_effects
        
        V = G_combined + lambda * I(n)
        ebv = V \ y_adj
        
        return Dict(
            "ebv" => ebv,
            "fixed_effects" => fixed_effects,
            "G_combined" => G_combined,
            "deep_features" => deep_features,
            "feature_model" => feature_result.model,
            "training_result" => feature_result
        )
    catch e
        @warn "DeepGBLUP求解失败: $e"
        return Dict(
            "ebv" => zeros(n),
            "fixed_effects" => Float64[mean(y)],
            "error" => string(e)
        )
    end
end

"""
提取深度特征 (倒数第二层)
"""
function extract_features(model::MLPModel, X::Matrix{Float64})
    activation_fn, _ = get_activation(model.activation)
    
    n_layers = length(model.weights)
    a = X'
    
    for i in 1:(n_layers-1)  # 不包括最后一层
        W = model.weights[i]
        b = model.biases[i]
        z = W * a .+ b
        a = activation_fn(z)
    end
    
    return a'  # samples × features
end

# ============================================================================
# 交叉验证
# Cross Validation
# ============================================================================

"""
    cross_validate_deep(Z, y, config; n_folds)

K折交叉验证
"""
function cross_validate_deep(
    Z::Matrix{Float64},
    y::Vector{Float64},
    config::DeepLearningConfig;
    n_folds::Int = 5
)
    n = length(y)
    fold_size = n ÷ n_folds
    
    correlations = Float64[]
    mse_values = Float64[]
    
    for fold in 1:n_folds
        # 分割数据
        val_start = (fold - 1) * fold_size + 1
        val_end = fold == n_folds ? n : fold * fold_size
        val_idx = val_start:val_end
        train_idx = setdiff(1:n, val_idx)
        
        # 训练
        result = train_deep_model(
            Z[train_idx, :], y[train_idx],
            Z[val_idx, :], y[val_idx],
            config
        )
        
        # 评估
        y_pred = predict_ebv(result.model, Z[val_idx, :])
        
        corr = cor(y_pred, y[val_idx])
        mse = mean((y_pred .- y[val_idx]).^2)
        
        push!(correlations, isnan(corr) ? 0.0 : corr)
        push!(mse_values, mse)
    end
    
    return Dict(
        "fold_correlations" => correlations,
        "fold_mse" => mse_values,
        "mean_correlation" => mean(correlations),
        "std_correlation" => std(correlations),
        "mean_mse" => mean(mse_values),
        "std_mse" => std(mse_values)
    )
end

# ============================================================================
# 超参数搜索
# Hyperparameter Search
# ============================================================================

"""
    hyperparameter_search(Z, y; param_grid)

网格搜索超参数
"""
function hyperparameter_search(
    Z::Matrix{Float64},
    y::Vector{Float64};
    hidden_layers_options::Vector{Vector{Int}} = [[128, 64], [256, 128, 64]],
    learning_rate_options::Vector{Float64} = [0.001, 0.01],
    dropout_options::Vector{Float64} = [0.1, 0.2, 0.3],
    n_folds::Int = 3
)
    best_corr = -Inf
    best_config = nothing
    best_result = nothing
    
    results = Dict{String, Any}[]
    
    for hidden in hidden_layers_options
        for lr in learning_rate_options
            for dropout in dropout_options
                config = DeepLearningConfig(
                    hidden_layers = hidden,
                    learning_rate = lr,
                    dropout_rate = dropout,
                    epochs = 50  # 减少epoch加速搜索
                )
                
                cv_result = cross_validate_deep(Z, y, config; n_folds=n_folds)
                
                push!(results, Dict(
                    "hidden_layers" => hidden,
                    "learning_rate" => lr,
                    "dropout" => dropout,
                    "mean_correlation" => cv_result["mean_correlation"]
                ))
                
                if cv_result["mean_correlation"] > best_corr
                    best_corr = cv_result["mean_correlation"]
                    best_config = config
                    best_result = cv_result
                end
            end
        end
    end
    
    return Dict(
        "best_config" => best_config,
        "best_correlation" => best_corr,
        "best_cv_result" => best_result,
        "all_results" => results
    )
end

end # module DeepLearning

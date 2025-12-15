# ============================================================================
# 国际顶级肉羊育种系统 - 深度学习GBLUP脚本
# International Top-tier Sheep Breeding System - DeepGBLUP Script
# ============================================================================

using JSON3
using LinearAlgebra
using Statistics
using DeepLearning

"""
    run_analysis(input_data)

运行DeepGBLUP分析
"""
function run_analysis(input_data::Dict)
    try
        # 1. 解析输入数据
        genotype = input_data["genotype"]
        phenotype = input_data["phenotype"]
        config_dict = input_data["config"]
        
        # 转换基因型矩阵 (samples × markers)
        # 假设输入是二维数组列表
        Z = hcat([Vector{Float64}(col) for col in genotype["matrix"]]...)'
        
        # 转换表型向量
        y = Vector{Float64}(phenotype["values"])
        
        # 简单的关系矩阵 (如果未提供，使用G矩阵)
        n, m = size(Z)
        G = Z * Z' / m
        
        # 2. 配置深度学习模型
        config = DeepLearningConfig(
            hidden_layers = Vector{Int}(config_dict["hidden_layers"]),
            activation = String(config_dict["activation"]),
            dropout_rate = Float64(config_dict["dropout_rate"]),
            learning_rate = Float64(config_dict["learning_rate"]),
            batch_size = Int(config_dict["batch_size"]),
            epochs = Int(config_dict["epochs"]),
            early_stopping_patience = Int(config_dict.get("early_stopping_patience", 10)),
            l2_regularization = Float64(config_dict.get("l2_regularization", 0.01)),
            use_batch_norm = Bool(config_dict.get("use_batch_norm", true))
        )
        
        # 3. 运行DeepGBLUP
        result = DeepGBLUP(Z, y, G, config)
        
        # 4. 格式化输出
        output = Dict(
            "status" => "success",
            "ebv" => result["ebv"],
            "fixed_effects" => result["fixed_effects"],
            # 将深度特征转换为列表以便JSON序列化
            "deep_features_sample" => result["deep_features"][1:min(5, end), 1:min(5, end)], # 仅返回部分样本用于预览
            "training_loss" => result["training_result"].final_train_loss,
            "validation_loss" => result["training_result"].final_val_loss,
            "correlation_val" => result["training_result"].correlation_val
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

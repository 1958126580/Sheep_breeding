# ============================================================================
# 国际顶级肉羊育种系统 - Julia模块测试
# International Top-tier Sheep Breeding System - Julia Module Tests
# ============================================================================

using Test
using LinearAlgebra
using Statistics
using Random

# 设置随机种子
Random.seed!(42)

# 加载模块
include("BreedingCore.jl")
include("GWASAnalysis.jl")
include("MultiTraitBLUP.jl")
include("FederatedLearning.jl")
include("DeepLearning.jl")

using .BreedingCore
using .GWASAnalysis
using .MultiTraitBLUP
using .FederatedLearning
using .DeepLearning

# ============================================================================
# GWAS模块测试
# GWAS Module Tests
# ============================================================================

@testset "GWASAnalysis Tests" begin
    # 生成测试数据
    n = 100
    m = 500
    Z = rand([0.0, 1.0, 2.0], n, m)
    y = randn(n) * 5 .+ 50
    
    @testset "Single Marker GWAS" begin
        result = run_single_marker_gwas(y, Z)
        
        @test result.n_samples == n
        @test result.n_snps == m
        @test length(result.pvalues) == m
        @test all(0 .<= result.pvalues .<= 1)
        @test result.lambda_gc > 0
    end
    
    @testset "Lambda GC Calculation" begin
        pvals = rand(1000)
        lambda = calculate_lambda_gc(pvals)
        @test lambda > 0
        @test lambda < 10  # 合理范围
    end
    
    @testset "Manhattan Plot Data" begin
        result = run_single_marker_gwas(y, Z)
        plot_data = manhattan_plot_data(result)
        
        @test haskey(plot_data, "log_pvalues")
        @test haskey(plot_data, "chromosomes")
        @test length(plot_data["log_pvalues"]) == m
    end
    
    @testset "Multiple Testing Correction" begin
        pvals = rand(100)
        
        # Bonferroni
        bonf = multiple_testing_correction(pvals; method="bonferroni")
        @test haskey(bonf, "adjusted_pvalues")
        @test all(bonf["adjusted_pvalues"] .>= pvals)
        
        # FDR
        fdr = multiple_testing_correction(pvals; method="fdr")
        @test haskey(fdr, "adjusted_pvalues")
    end
end

# ============================================================================
# 多性状BLUP测试
# Multi-trait BLUP Tests
# ============================================================================

@testset "MultiTraitBLUP Tests" begin
    n = 50
    t = 3
    
    # 生成测试数据
    Y = randn(n, t) * 10 .+ 50
    A = Matrix{Float64}(I(n))
    X = ones(n, 1)
    
    # 定义模型参数
    G0 = [10.0 2.0 1.0; 2.0 8.0 1.5; 1.0 1.5 5.0]
    R0 = [5.0 0.5 0.2; 0.5 4.0 0.3; 0.2 0.3 3.0]
    
    @testset "Model Creation" begin
        model = create_multitriat_model(
            ["Trait1", "Trait2", "Trait3"],
            G0, R0
        )
        
        @test model.n_traits == 3
        @test length(model.h2) == 3
        @test all(0 .<= model.h2 .<= 1)
    end
    
    @testset "Selection Index" begin
        ebv = randn(n, t)
        weights = [1.0, 0.5, 0.3]
        
        index = calculate_selection_index(ebv, weights, G0)
        
        @test length(index) == n
    end
    
    @testset "Economic Weights" begin
        prices = [100.0, 50.0, 30.0]
        genetic_sds = [2.0, 0.1, 1.5]
        
        weights = economic_weights(
            ["WW", "NLB", "YW"],
            prices,
            genetic_sds;
            standardize=true
        )
        
        @test length(weights) == 3
        @test abs(sum(abs.(weights)) - 1.0) < 0.01
    end
end

# ============================================================================
# 联邦学习测试
# Federated Learning Tests
# ============================================================================

@testset "FederatedLearning Tests" begin
    @testset "Client Creation" begin
        client = create_mock_client("client1", 50)
        
        @test client.client_id == "client1"
        @test client.n_animals == 50
        @test client.local_A !== nothing
        @test client.local_y !== nothing
    end
    
    @testset "Federated Config" begin
        config = FederatedConfig(
            num_rounds=5,
            min_clients=2,
            privacy_budget=1.0
        )
        
        @test config.num_rounds == 5
        @test config.privacy_budget == 1.0
    end
    
    @testset "Privacy Budget Check" begin
        result = privacy_budget_check(0.3, 1.0)
        
        @test result["can_continue"] == true
        @test result["remaining"] ≈ 0.7
        
        exhausted = privacy_budget_check(1.5, 1.0)
        @test exhausted["can_continue"] == false
    end
    
    @testset "Differential Privacy Noise" begin
        sigma = differential_privacy_noise(1.0, 0.5, 1e-5)
        @test sigma > 0
    end
end

# ============================================================================
# 深度学习测试
# Deep Learning Tests
# ============================================================================

@testset "DeepLearning Tests" begin
    n = 100
    m = 50
    
    # 生成测试数据
    X = randn(n, m)
    y = X * randn(m) .+ randn(n) * 0.1
    
    @testset "MLP Model Creation" begin
        config = DeepLearningConfig(
            hidden_layers=[32, 16],
            epochs=10
        )
        
        model = MLPModel(m, 1, config)
        
        @test length(model.weights) == 3  # 2 hidden + 1 output
        @test length(model.biases) == 3
    end
    
    @testset "Forward Pass" begin
        config = DeepLearningConfig(hidden_layers=[32, 16], epochs=5)
        model = MLPModel(m, 1, config)
        
        predictions = predict_ebv(model, X)
        
        @test length(predictions) == n
    end
    
    @testset "Training" begin
        config = DeepLearningConfig(
            hidden_layers=[16, 8],
            epochs=5,
            batch_size=32
        )
        
        n_train = 80
        X_train = X[1:n_train, :]
        y_train = y[1:n_train]
        X_val = X[(n_train+1):end, :]
        y_val = y[(n_train+1):end]
        
        result = train_deep_model(X_train, y_train, X_val, y_val, config)
        
        @test length(result.train_loss_history) > 0
        @test result.best_epoch > 0
    end
    
    @testset "Activation Functions" begin
        x = [-1.0, 0.0, 1.0, 2.0]
        
        @test all(relu(x) .>= 0)
        @test all(0 .<= sigmoid(x) .<= 1)
    end
end

# ============================================================================
# 运行所有测试
# Run All Tests
# ============================================================================

println("\n" * "="^60)
println("所有测试完成!")
println("="^60)

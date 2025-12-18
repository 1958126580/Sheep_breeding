# 算法参考

## 育种算法详细说明

### 目录

1. [BLUP 算法](#blup算法)
2. [GBLUP 算法](#gblup算法)
3. [ssGBLUP 算法](#ssgblup算法)
4. [贝叶斯方法](#贝叶斯方法)
5. [GWAS 分析](#gwas分析)
6. [深度学习方法](#深度学习方法)
7. [最优贡献选择](#最优贡献选择)

---

## BLUP 算法

### Best Linear Unbiased Prediction (最佳线性无偏预测)

BLUP 是动物育种中最常用的遗传评估方法，用于估计个体的育种值。

### 数学模型

**动物模型**:

```
y = Xβ + Za + e
```

其中:

- `y`: 表型观测值向量
- `X`: 固定效应设计矩阵
- `β`: 固定效应向量
- `Z`: 随机效应设计矩阵
- `a`: 育种值向量
- `e`: 残差向量

### 混合模型方程 (MME)

```
┌─────────────┐ ┌───┐   ┌─────┐
│ X'X    X'Z  │ │ β │   │ X'y │
│             │ │   │ = │     │
│ Z'X  Z'Z+A⁻¹λ│ │ a │   │ Z'y │
└─────────────┘ └───┘   └─────┘
```

其中:

- `A`: 加性遗传关系矩阵
- `λ = σ²ₑ/σ²ₐ`: 方差比

### 实现示例

```julia
using LinearAlgebra, SparseArrays

function solve_blup(y, X, Z, A, λ)
    # 构建混合模型方程左侧
    C11 = X' * X
    C12 = X' * Z
    C21 = Z' * X
    C22 = Z' * Z + inv(A) * λ

    # 构建右侧
    rhs1 = X' * y
    rhs2 = Z' * y

    # 求解方程
    LHS = [C11 C12; C21 C22]
    RHS = [rhs1; rhs2]

    sol = LHS \\ RHS

    β = sol[1:size(X,2)]
    a = sol[size(X,2)+1:end]

    return β, a
end
```

### 准确性计算

```julia
function calculate_accuracy(C22_inv, i)
    PEV = C22_inv[i,i]  # 预测误差方差
    accuracy = sqrt(1 - PEV / σ²ₐ)
    return accuracy
end
```

---

## GBLUP 算法

### Genomic BLUP (基因组 BLUP)

GBLUP 使用基因组信息构建关系矩阵，提高育种值估计准确性。

### 基因组关系矩阵 (GRM)

**VanRaden 方法**:

```
G = (M - P)(M - P)' / (2Σpᵢ(1-pᵢ))
```

其中:

- `M`: 基因型矩阵 (n × m)
- `P`: 等位基因频率矩阵
- `pᵢ`: 第 i 个 SNP 的等位基因频率

### 实现

```julia
function calculate_grm(genotypes::Matrix{Int8})
    n, m = size(genotypes)

    # 计算等位基因频率
    p = mean(genotypes, dims=1) / 2

    # 中心化
    M = genotypes .- 2p

    # 计算GRM
    denom = 2 * sum(p .* (1 .- p))
    G = (M * M') / denom

    return G
end
```

### GBLUP 方程

```
y = Xβ + Zg + e
```

其中 `g ~ N(0, Gσ²g)`

---

## ssGBLUP 算法

### Single-Step GBLUP (单步法 GBLUP)

ssGBLUP 整合系谱和基因组信息，同时评估基因分型和未分型个体。

### H 矩阵构建

```
H⁻¹ = A⁻¹ + [0    0   ]
              [0  G⁻¹-A₂₂⁻¹]
```

其中:

- `A`: 系谱关系矩阵
- `G`: 基因组关系矩阵
- `A₂₂`: 基因分型个体的系谱关系矩阵

### 实现

```julia
function build_H_inverse(A_inv, G, genotyped_ids)
    n = size(A_inv, 1)
    H_inv = copy(A_inv)

    # 提取A₂₂
    A22 = A[genotyped_ids, genotyped_ids]
    A22_inv = inv(A22)

    # 计算G⁻¹ - A₂₂⁻¹
    diff = inv(G) - A22_inv

    # 更新H⁻¹
    H_inv[genotyped_ids, genotyped_ids] += diff

    return H_inv
end
```

---

## 贝叶斯方法

### BayesA/B/C/R

贝叶斯方法对 SNP 效应进行不同的先验分布假设。

### BayesA

**模型**:

```
y = μ + Σⱼ xⱼβⱼ + e
βⱼ ~ N(0, σ²βⱼ)
σ²βⱼ ~ χ⁻²(ν, S)
```

### BayesB

**模型**:

```
βⱼ = {0           with probability π
     {N(0, σ²β)   with probability 1-π
```

### 实现 (BayesA)

```julia
function bayes_a(y, X; niter=10000, burnin=5000)
    n, p = size(X)

    # 初始化
    β = zeros(p)
    σ²β = ones(p)
    σ²e = 1.0

    # MCMC采样
    for iter in 1:niter
        # 更新β
        for j in 1:p
            rhs = X[:,j]' * (y - X * β + X[:,j] * β[j])
            lhs = X[:,j]' * X[:,j] + σ²e / σ²β[j]
            β[j] = rand(Normal(rhs/lhs, sqrt(σ²e/lhs)))
        end

        # 更新σ²β
        for j in 1:p
            σ²β[j] = rand(InverseGamma(ν/2 + 0.5,
                                       (ν*S + β[j]^2)/2))
        end

        # 更新σ²e
        e = y - X * β
        σ²e = rand(InverseGamma(n/2, sum(e.^2)/2))
    end

    return β
end
```

---

## GWAS 分析

### 混合线性模型 (MLM)

**模型**:

```
y = Xβ + xⱼαⱼ + Zu + e
```

其中:

- `xⱼ`: 第 j 个 SNP 的基因型
- `αⱼ`: SNP 效应
- `u`: 多基因效应

### 显著性检验

**Wald 检验**:

```
χ² = α̂ⱼ² / Var(α̂ⱼ)
```

**P 值计算**:

```
P = 1 - Φ(|α̂ⱼ| / √Var(α̂ⱼ))
```

### 实现

```julia
function gwas_mlm(y, X, genotypes, K)
    n, m = size(genotypes)
    pvalues = zeros(m)
    effects = zeros(m)

    for j in 1:m
        # 提取SNP基因型
        xⱼ = genotypes[:, j]

        # 拟合混合模型
        model = fit_mixed_model(y, X, xⱼ, K)

        # 计算检验统计量
        effects[j] = model.β_snp
        se = model.se_snp
        z = effects[j] / se
        pvalues[j] = 2 * (1 - cdf(Normal(), abs(z)))
    end

    return effects, pvalues
end
```

### 多重检验校正

**Bonferroni 校正**:

```
α_corrected = α / m
```

**FDR 控制**:

```julia
function benjamini_hochberg(pvalues, α=0.05)
    m = length(pvalues)
    sorted_idx = sortperm(pvalues)
    sorted_p = pvalues[sorted_idx]

    threshold = α * (1:m) / m
    significant = sorted_p .<= threshold

    return sorted_idx[significant]
end
```

---

## 深度学习方法

### CNN 用于基因组预测

**网络架构**:

```
Input (n_snps)
  → Conv1D (64 filters, kernel=5)
  → MaxPool1D (pool=2)
  → Conv1D (128 filters, kernel=3)
  → MaxPool1D (pool=2)
  → Dense (256)
  → Dropout (0.5)
  → Dense (1)
```

### 实现 (Julia Flux.jl)

```julia
using Flux

model = Chain(
    Conv((5,), 1=>64, relu),
    MaxPool((2,)),
    Conv((3,), 64=>128, relu),
    MaxPool((2,)),
    Flatten(),
    Dense(128*n_features, 256, relu),
    Dropout(0.5),
    Dense(256, 1)
)

loss(x, y) = Flux.mse(model(x), y)
opt = ADAM(0.001)

# 训练
for epoch in 1:100
    Flux.train!(loss, params(model), train_data, opt)
end
```

---

## 最优贡献选择

### Optimal Contribution Selection (OCS)

OCS 在最大化遗传进展的同时控制近交系数。

### 目标函数

```
maximize: c'g
subject to: c'Ac ≤ ΔF
           Σcᵢ = n
           0 ≤ cᵢ ≤ 1
```

其中:

- `c`: 贡献向量
- `g`: 育种值向量
- `A`: 关系矩阵
- `ΔF`: 近交增量阈值

### 实现

```julia
using JuMP, Ipopt

function optimal_contribution(g, A, ΔF, n_selected)
    n = length(g)

    model = Model(Ipopt.Optimizer)
    @variable(model, 0 <= c[1:n] <= 1)

    # 目标：最大化遗传进展
    @objective(model, Max, sum(c .* g))

    # 约束：控制近交
    @constraint(model, sum(c[i] * c[j] * A[i,j]
                          for i in 1:n, j in 1:n) <= ΔF)

    # 约束：选择数量
    @constraint(model, sum(c) == n_selected)

    optimize!(model)

    return value.(c)
end
```

---

## 性能优化技巧

### 1. 稀疏矩阵

```julia
using SparseArrays

# 使用稀疏矩阵存储大型关系矩阵
A_sparse = sparse(A)
```

### 2. 并行计算

```julia
using Distributed

# 并行GWAS分析
pvalues = @distributed (vcat) for j in 1:m
    gwas_single_snp(y, X, genotypes[:, j], K)
end
```

### 3. GPU 加速

```julia
using CUDA

# GPU矩阵运算
G_gpu = CuArray(G)
result = G_gpu * G_gpu'
```

---

## 参考文献

1. Henderson, C.R. (1975). Best Linear Unbiased Estimation and Prediction under a Selection Model. _Biometrics_, 31(2), 423-447.

2. VanRaden, P.M. (2008). Efficient Methods to Compute Genomic Predictions. _Journal of Dairy Science_, 91(11), 4414-4423.

3. Legarra, A., et al. (2009). A relationship matrix including full pedigree and genomic information. _Journal of Dairy Science_, 92(9), 4656-4663.

4. Meuwissen, T.H.E., et al. (2001). Prediction of Total Genetic Value Using Genome-Wide Dense Marker Maps. _Genetics_, 157(4), 1819-1829.

5. Kang, H.M., et al. (2010). Variance component model to account for sample structure in genome-wide association studies. _Nature Genetics_, 42(4), 348-354.

---

**更多算法细节请参考源代码：`julia/` 目录**

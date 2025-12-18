# 贡献指南 Contributing Guide

[English](#english-version) | [中文](#中文版本)

---

## 中文版本

感谢您对新星肉羊育种系统的关注！我们欢迎所有形式的贡献。

### 🤝 如何贡献

#### 报告问题 (Bug Reports)

如果您发现了 bug，请通过 [GitHub Issues](https://github.com/1958126580/Sheep_breeding/issues) 报告，并包含：

- 清晰的问题描述
- 复现步骤
- 预期行为 vs 实际行为
- 环境信息（操作系统、Python/Julia 版本等）
- 相关日志或截图

#### 功能建议 (Feature Requests)

我们欢迎新功能建议！请在 Issue 中说明：

- 功能的使用场景
- 预期的实现方式
- 可能的替代方案

#### 代码贡献 (Code Contributions)

1. **Fork 本仓库**
2. **创建特性分支**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **进行开发**
   - 遵循代码规范
   - 添加必要的测试
   - 更新相关文档
4. **提交更改**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
5. **推送到分支**
   ```bash
   git push origin feature/AmazingFeature
   ```
6. **开启 Pull Request**

### 📝 代码规范

#### Python 代码

- 遵循 [PEP 8](https://pep8.org/) 规范
- 使用 `black` 进行代码格式化
- 使用 `flake8` 进行代码检查
- 使用 `mypy` 进行类型检查
- 函数和类必须有文档字符串（中英双语）

```python
def calculate_ebv(pedigree: pd.DataFrame, phenotype: pd.DataFrame) -> np.ndarray:
    """
    计算育种值 (Estimated Breeding Values)
    Calculate Estimated Breeding Values

    参数 Args:
        pedigree: 系谱数据 Pedigree data
        phenotype: 表型数据 Phenotype data

    返回 Returns:
        育种值数组 Array of breeding values
    """
    pass
```

#### Julia 代码

- 遵循 [Julia Style Guide](https://docs.julialang.org/en/v1/manual/style-guide/)
- 函数名使用小写字母和下划线
- 类型名使用驼峰命名法
- 添加详细的文档字符串

```julia
"""
    calculate_ebv(pedigree::DataFrame, phenotype::DataFrame) -> Vector{Float64}

计算育种值 (Estimated Breeding Values)
Calculate Estimated Breeding Values

# 参数 Arguments
- `pedigree::DataFrame`: 系谱数据 Pedigree data
- `phenotype::DataFrame`: 表型数据 Phenotype data

# 返回 Returns
- `Vector{Float64}`: 育种值向量 Vector of breeding values
"""
function calculate_ebv(pedigree::DataFrame, phenotype::DataFrame)
    # Implementation
end
```

### 🧪 测试要求

- 所有新功能必须包含单元测试
- 测试覆盖率应 > 80%
- 确保所有测试通过

```bash
# Python 测试
cd backend
pytest tests/ -v --cov=. --cov-report=html

# Julia 测试
cd julia
julia --project=. test_modules.jl
```

### 📚 文档要求

- 更新相关的 API 文档
- 更新用户手册（如果影响用户使用）
- 在 CHANGELOG.md 中记录更改
- 代码注释使用中英双语

### 🔍 代码审查流程

1. 自动化测试必须通过
2. 至少一位维护者审查代码
3. 解决所有审查意见
4. 合并到主分支

### 📋 提交信息规范

使用清晰的提交信息：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type):**

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例:**

```
feat(breeding): Add ssGBLUP method support

- Implement single-step GBLUP algorithm
- Add GPU acceleration for large datasets
- Update API documentation

Closes #123
```

### 🌟 成为核心贡献者

持续贡献优质代码的开发者将被邀请成为核心贡献者，获得：

- 仓库写权限
- 参与项目决策
- 在 README 中署名

---

## English Version

Thank you for your interest in the NovaBreed Sheep System! We welcome all forms of contributions.

### 🤝 How to Contribute

#### Bug Reports

If you find a bug, please report it via [GitHub Issues](https://github.com/1958126580/Sheep_breeding/issues) with:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment information (OS, Python/Julia version, etc.)
- Relevant logs or screenshots

#### Feature Requests

We welcome feature suggestions! Please describe in the Issue:

- Use case for the feature
- Expected implementation approach
- Possible alternatives

#### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Develop**
   - Follow code standards
   - Add necessary tests
   - Update relevant documentation
4. **Commit changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
5. **Push to branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
6. **Open a Pull Request**

### 📝 Code Standards

#### Python Code

- Follow [PEP 8](https://pep8.org/)
- Use `black` for code formatting
- Use `flake8` for linting
- Use `mypy` for type checking
- Functions and classes must have docstrings (bilingual: Chinese & English)

#### Julia Code

- Follow [Julia Style Guide](https://docs.julialang.org/en/v1/manual/style-guide/)
- Use lowercase with underscores for function names
- Use CamelCase for type names
- Add detailed docstrings

### 🧪 Testing Requirements

- All new features must include unit tests
- Test coverage should be > 80%
- Ensure all tests pass

### 📚 Documentation Requirements

- Update relevant API documentation
- Update user manual (if affecting user experience)
- Record changes in CHANGELOG.md
- Code comments in both Chinese and English

### 🔍 Code Review Process

1. Automated tests must pass
2. At least one maintainer reviews the code
3. Address all review comments
4. Merge to main branch

### 📋 Commit Message Convention

Use clear commit messages following the format above.

### 🌟 Becoming a Core Contributor

Developers who consistently contribute quality code will be invited to become core contributors with:

- Repository write access
- Participation in project decisions
- Credit in README

---

## 📞 联系方式 Contact

- 项目主页 Project Home: https://github.com/1958126580/Sheep_breeding
- 问题反馈 Issues: https://github.com/1958126580/Sheep_breeding/issues
- 邮箱 Email: 1958126580@qq.com

感谢您的贡献！ Thank you for your contributions!

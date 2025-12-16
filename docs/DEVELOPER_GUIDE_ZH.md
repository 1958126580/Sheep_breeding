# 开发者指南

## 开发环境搭建和贡献指南

### 目录

1. [开发环境要求](#开发环境要求)
2. [项目结构](#项目结构)
3. [后端开发](#后端开发)
4. [Julia 计算引擎开发](#julia计算引擎开发)
5. [前端开发](#前端开发)
6. [测试指南](#测试指南)
7. [代码规范](#代码规范)
8. [贡献流程](#贡献流程)

---

## 开发环境要求

### 必需软件

- **Python**: 3.10 或更高版本
- **Julia**: 1.12.2
- **Node.js**: 18.0 或更高版本
- **PostgreSQL**: 14 或更高版本
- **Redis**: 6.0 或更高版本
- **Git**: 2.30 或更高版本

### 推荐工具

- **IDE**: VS Code / PyCharm / Julia VS Code Extension
- **数据库工具**: pgAdmin / DBeaver
- **API 测试**: Postman / Insomnia
- **容器**: Docker Desktop

---

## 项目结构

```
sheep-breeding-system/
├── backend/                 # FastAPI后端
│   ├── api/                # API路由
│   │   └── v1/            # API v1版本
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   ├── tests/             # 测试文件
│   ├── config.py          # 配置文件
│   ├── database.py        # 数据库连接
│   └── main.py            # 应用入口
├── julia/                  # Julia计算引擎
│   ├── BreedingCore.jl    # 核心算法
│   ├── DeepLearning.jl    # 深度学习
│   ├── GWASAnalysis.jl    # GWAS分析
│   └── scripts/           # 分析脚本
├── mobile/                 # React Native移动端
├── docs/                   # 文档
├── k8s/                    # Kubernetes配置
├── database/               # 数据库脚本
└── docker-compose.yml      # Docker编排
```

---

## 后端开发

### 环境设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\\Scripts\\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
cp .env.example .env
# 编辑.env文件配置数据库等信息
```

### 数据库初始化

```bash
# 创建数据库
createdb sheep_breeding

# 运行迁移脚本
python scripts/init_db.py
```

### 启动开发服务器

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 添加新的 API 端点

1. 在 `models/` 中定义数据模型
2. 在 `services/` 中实现业务逻辑
3. 在 `api/v1/` 中创建路由
4. 在 `tests/` 中添加测试

**示例**：添加新的动物管理端点

```python
# models/animal.py
from sqlalchemy import Column, Integer, String, Date
from .base import Base

class Animal(Base):
    __tablename__ = "animals"

    id = Column(Integer, primary_key=True)
    ear_tag = Column(String, unique=True, index=True)
    name = Column(String)
    breed = Column(String)
    birth_date = Column(Date)

# services/animal_service.py
from models.animal import Animal
from services.base import CRUDBase

class AnimalService(CRUDBase[Animal]):
    pass

animal_service = AnimalService(Animal)

# api/v1/animals.py
from fastapi import APIRouter, Depends
from services.animal_service import animal_service

router = APIRouter()

@router.get("/animals")
async def get_animals(skip: int = 0, limit: int = 100):
    return animal_service.get_multi(skip=skip, limit=limit)
```

---

## Julia 计算引擎开发

### 环境设置

```bash
cd julia

# 启动Julia REPL
julia --project=.

# 在Julia REPL中安装依赖
julia> using Pkg
julia> Pkg.instantiate()
julia> Pkg.precompile()
```

### 核心模块说明

#### BreedingCore.jl

- BLUP/GBLUP/ssGBLUP 算法实现
- 遗传关系矩阵构建
- 方差组分估计

#### DeepLearning.jl

- 深度学习育种值预测
- CNN/RNN 模型
- GPU 加速训练

#### GWASAnalysis.jl

- 全基因组关联分析
- 混合线性模型
- 曼哈顿图和 QQ 图生成

### 添加新算法

```julia
# 在BreedingCore.jl中添加新函数
module BreedingCore

export my_new_algorithm

function my_new_algorithm(data::Matrix{Float64})
    # 算法实现
    result = process(data)
    return result
end

end # module
```

### 性能优化

```julia
# 使用多线程
using Base.Threads

@threads for i in 1:n
    # 并行计算
end

# 使用GPU
using CUDA

data_gpu = CuArray(data)
result = gpu_compute(data_gpu)
```

---

## 前端开发

### 环境设置

```bash
cd web-frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 组件开发规范

```typescript
// components/AnimalList.tsx
import React from "react";
import { Table } from "antd";

interface Animal {
  id: number;
  ear_tag: string;
  name: string;
  breed: string;
}

const AnimalList: React.FC = () => {
  const [animals, setAnimals] = useState<Animal[]>([]);

  useEffect(() => {
    fetchAnimals();
  }, []);

  return <Table dataSource={animals} />;
};

export default AnimalList;
```

---

## 测试指南

### 后端测试

```bash
cd backend

# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_animals.py -v

# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html
```

### Julia 测试

```bash
cd julia

# 运行测试
julia --project=. test_modules.jl
```

### 前端测试

```bash
cd web-frontend

# 单元测试
npm test

# E2E测试
npm run test:e2e
```

---

## 代码规范

### Python 代码规范

- 遵循 PEP 8
- 使用 Black 格式化代码
- 使用 type hints
- 函数和类添加 docstring

```python
def calculate_ebv(phenotypes: List[float],
                  pedigree: pd.DataFrame) -> np.ndarray:
    """
    计算估计育种值

    Args:
        phenotypes: 表型数据列表
        pedigree: 系谱数据框

    Returns:
        育种值数组
    """
    # 实现
    pass
```

### Julia 代码规范

- 遵循 Julia Style Guide
- 使用类型注解
- 添加文档字符串

```julia
\"\"\"
    calculate_grm(genotypes::Matrix{Int8})

计算基因组关系矩阵

# Arguments
- `genotypes::Matrix{Int8}`: 基因型矩阵

# Returns
- `Matrix{Float64}`: 基因组关系矩阵
\"\"\"
function calculate_grm(genotypes::Matrix{Int8})
    # 实现
end
```

---

## 贡献流程

### 1. Fork 项目

访问 GitHub 仓库，点击 Fork 按钮

### 2. 克隆到本地

```bash
git clone https://github.com/YOUR_USERNAME/sheep-breeding-system.git
cd sheep-breeding-system
```

### 3. 创建特性分支

```bash
git checkout -b feature/my-new-feature
```

### 4. 开发和测试

- 编写代码
- 添加测试
- 运行测试确保通过
- 更新文档

### 5. 提交更改

```bash
git add .
git commit -m "feat: add new feature description"
```

**提交信息规范**:

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `test`: 测试相关
- `refactor`: 代码重构
- `perf`: 性能优化

### 6. 推送到 Fork

```bash
git push origin feature/my-new-feature
```

### 7. 创建 Pull Request

在 GitHub 上创建 Pull Request，详细描述你的更改

---

## 常见问题

### Q: 如何调试 Julia 代码？

A: 使用 Debugger.jl 包：

```julia
using Debugger
@enter my_function(args)
```

### Q: 如何处理数据库迁移？

A: 使用 Alembic：

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Q: 如何优化查询性能？

A:

1. 添加适当的数据库索引
2. 使用查询优化器
3. 实现缓存机制
4. 使用异步查询

---

## 获取帮助

- 📧 邮箱: 1958126580@qq.com
- 💬 GitHub Issues: https://github.com/1958126580/sheep-breeding-system/issues
- 📖 文档: 查看 docs/ 目录

---

**欢迎贡献！让我们一起打造更好的育种管理系统！**

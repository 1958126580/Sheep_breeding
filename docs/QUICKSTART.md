# Quick Start Guide - 快速入门指南

[English](#english) | [中文](#中文)

---

## English

### 🚀 Quick Start in 5 Minutes

This guide will help you get the NovaBreed Sheep System up and running quickly.

#### Prerequisites

- Docker & Docker Compose (recommended)
- OR: Python 3.10+, Julia 1.12+, PostgreSQL 14+

#### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/1958126580/Sheep_breeding.git
cd Sheep_breeding

# 2. Start all services
docker-compose up -d

# 3. Access the system
# API Documentation: http://localhost:8000/docs
# Backend API: http://localhost:8000
```

That's it! The system is now running.

#### Option 2: Manual Setup

```bash
# 1. Clone the repository
git clone https://github.com/1958126580/Sheep_breeding.git
cd Sheep_breeding

# 2. Set up Python backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 4. Start the backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 5. In another terminal, set up Julia
cd julia
julia --project=. -e 'using Pkg; Pkg.instantiate()'
```

#### First Steps

1. **Access API Documentation**: http://localhost:8000/docs
2. **Create a farm**: POST `/api/v1/farms`
3. **Add animals**: POST `/api/v1/animals`
4. **Record data**: Use health, reproduction, growth endpoints
5. **Run breeding value estimation**: POST `/api/v1/breeding-values/runs`

#### Example API Call

```python
import requests

# Create a farm
response = requests.post(
    "http://localhost:8000/api/v1/farms",
    json={
        "code": "FARM001",
        "name": "Demo Farm",
        "farm_type": "breeding",
        "capacity": 1000
    }
)
print(response.json())
```

#### Need Help?

- 📖 [Full User Manual](USER_MANUAL_ZH.md)
- 🔧 [Installation Guide](INSTALLATION_ZH.md)
- 🚀 [Deployment Guide](DEPLOYMENT_ZH.md)
- 💬 [GitHub Issues](https://github.com/1958126580/Sheep_breeding/issues)

---

## 中文

### 🚀 5 分钟快速开始

本指南帮助您快速启动新星肉羊育种系统。

#### 前置要求

- Docker & Docker Compose（推荐）
- 或：Python 3.10+、Julia 1.12+、PostgreSQL 14+

#### 方式一：Docker（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/1958126580/Sheep_breeding.git
cd Sheep_breeding

# 2. 启动所有服务
docker-compose up -d

# 3. 访问系统
# API 文档: http://localhost:8000/docs
# 后端 API: http://localhost:8000
```

完成！系统已经运行。

#### 方式二：手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/1958126580/Sheep_breeding.git
cd Sheep_breeding

# 2. 设置 Python 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库凭据

# 4. 启动后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 5. 在另一个终端，设置 Julia
cd julia
julia --project=. -e 'using Pkg; Pkg.instantiate()'
```

#### 第一步操作

1. **访问 API 文档**: http://localhost:8000/docs
2. **创建羊场**: POST `/api/v1/farms`
3. **添加动物**: POST `/api/v1/animals`
4. **记录数据**: 使用健康、繁殖、生长等端点
5. **运行育种值估计**: POST `/api/v1/breeding-values/runs`

#### API 调用示例

```python
import requests

# 创建羊场
response = requests.post(
    "http://localhost:8000/api/v1/farms",
    json={
        "code": "FARM001",
        "name": "示范羊场",
        "farm_type": "breeding",
        "capacity": 1000
    }
)
print(response.json())
```

#### 需要帮助？

- 📖 [完整用户手册](USER_MANUAL_ZH.md)
- 🔧 [安装指南](INSTALLATION_ZH.md)
- 🚀 [部署指南](DEPLOYMENT_ZH.md)
- 💬 [GitHub Issues](https://github.com/1958126580/Sheep_breeding/issues)

---

## 📚 Next Steps

### For Users

- Read the [User Manual](USER_MANUAL_ZH.md) for detailed feature explanations
- Explore the [API Documentation](API_ZH.md) for all available endpoints
- Check out example workflows in the documentation

### For Developers

- Review the [Developer Guide](DEVELOPER_GUIDE_ZH.md)
- Read the [Contributing Guide](CONTRIBUTING.md)
- Set up your development environment
- Run the test suite: `pytest tests/ -v`

### For Administrators

- Follow the [Deployment Guide](DEPLOYMENT_ZH.md) for production setup
- Configure monitoring and logging
- Set up backup strategies
- Review security best practices

---

## 🎯 Key Features

- **Farm Management** - Complete farm, barn, and animal tracking
- **Health Management** - Health records, vaccinations, treatments
- **Reproduction** - Breeding, pregnancy, lambing management
- **Growth Monitoring** - Weight records and growth curves
- **Breeding Values** - BLUP, GBLUP, ssGBLUP estimation
- **GWAS Analysis** - Genome-wide association studies
- **GPU Acceleration** - High-performance computing
- **Cloud Services** - Data sync and sharing

---

## 📞 Support

- **Documentation**: [Documentation](./)
- **Issues**: https://github.com/1958126580/Sheep_breeding/issues
- **Email**: 1958126580@qq.com

---

**Happy Breeding! 祝您育种顺利！** 🐑

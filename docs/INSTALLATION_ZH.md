# 国际顶级肉羊育种系统 - 安装部署指南

**版本**: 1.0.0  
**更新日期**: 2024 年 12 月

---

## 📋 目录

1. [环境要求](#一环境要求)
2. [Docker 快速部署（推荐）](#二docker快速部署推荐)
3. [手动部署](#三手动部署)
4. [云端/K8s 部署](#四云端k8s部署)
5. [验证安装](#五验证安装)
6. [常见问题](#六常见问题)

---

## 一、环境要求

### 1.1 硬件要求

| 环境类型     | CPU    | 内存  | 硬盘   | GPU（可选）       |
| ------------ | ------ | ----- | ------ | ----------------- |
| **开发环境** | 4 核+  | 8GB+  | 50GB+  | -                 |
| **测试环境** | 8 核+  | 16GB+ | 100GB+ | -                 |
| **生产环境** | 16 核+ | 32GB+ | 500GB+ | NVIDIA GPU (推荐) |

### 1.2 软件要求

#### 必需软件

| 软件               | 最低版本 | 推荐版本                  | 说明         |
| ------------------ | -------- | ------------------------- | ------------ |
| **操作系统**       | -        | Ubuntu 22.04 / Windows 11 | Linux 推荐   |
| **Docker**         | 20.10    | 24.0+                     | 容器运行环境 |
| **Docker Compose** | 2.0      | 2.20+                     | 多容器编排   |
| **Python**         | 3.10     | 3.11                      | 后端语言     |
| **Julia**          | 1.9      | 1.12.2                    | 计算引擎     |
| **PostgreSQL**     | 14       | 15                        | 主数据库     |
| **Redis**          | 6        | 7                         | 缓存服务     |

#### 可选软件

- **Node.js** 18+ (前端开发)
- **Nginx** (生产环境反向代理)
- **Git** (版本控制)

---

## 二、Docker 快速部署（推荐）

### 2.1 准备工作

#### Windows 系统

```powershell
# 1. 安装Docker Desktop
# 下载地址: https://www.docker.com/products/docker-desktop

# 2. 启动Docker Desktop并确认运行
docker --version
docker-compose --version

# 3. 克隆代码
git clone <repository-url>
cd sheep-breeding-system
```

#### Linux 系统

```bash
# 1. 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 2. 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. 将当前用户加入docker组
sudo usermod -aG docker $USER
newgrp docker

# 4. 克隆代码
git clone <repository-url>
cd sheep-breeding-system
```

### 2.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件
nano .env  # 或使用其他编辑器
```

**关键配置项**:

```bash
# 数据库配置
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=sheep_breeding
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# JWT密钥（请生成随机字符串）
SECRET_KEY=your_secret_key_here

# 环境
ENVIRONMENT=production  # development/production

# Julia配置
JULIA_NUM_THREADS=4
JULIA_GPU_ENABLED=false  # 如有GPU设为true
```

### 2.3 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 仅查看后端日志
docker-compose logs -f backend
```

**预期输出**:

```
NAME                    STATUS              PORTS
postgres                Up 30 seconds       0.0.0.0:5432->5432/tcp
redis                   Up 30 seconds       0.0.0.0:6379->6379/tcp
backend                 Up 28 seconds       0.0.0.0:8000->8000/tcp
```

### 2.4 初始化数据库

```bash
# 进入后端容器
docker-compose exec backend bash

# 运行数据库初始化脚本
python scripts/init_db.py

# 创建管理员账户
python scripts/create_admin.py

# 退出容器
exit
```

### 2.5 访问系统

| 服务             | 地址                         | 说明                  |
| ---------------- | ---------------------------- | --------------------- |
| **API 文档**     | http://localhost:8000/docs   | Swagger UI 交互式文档 |
| **API 备用文档** | http://localhost:8000/redoc  | ReDoc 文档            |
| **健康检查**     | http://localhost:8000/health | 系统健康状态          |

---

## 三、手动部署

### 3.1 安装 PostgreSQL

#### Ubuntu/Debian

```bash
# 添加PostgreSQL仓库
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# 安装PostgreSQL 15
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql
```

```sql
-- 在PostgreSQL命令行中执行
CREATE USER sheep_user WITH PASSWORD 'your_password';
CREATE DATABASE sheep_breeding OWNER sheep_user;
GRANT ALL PRIVILEGES ON DATABASE sheep_breeding TO sheep_user;
\q
```

#### Windows

```powershell
# 1. 下载PostgreSQL安装程序
# https://www.postgresql.org/download/windows/

# 2. 运行安装程序，记住设置的密码

# 3. 使用pgAdmin或命令行创建数据库
psql -U postgres

# 在psql中执行
CREATE USER sheep_user WITH PASSWORD 'your_password';
CREATE DATABASE sheep_breeding OWNER sheep_user;
```

### 3.2 安装 Redis

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y redis-server

# 配置Redis
sudo nano /etc/redis/redis.conf
# 设置密码: requirepass your_redis_password

# 重启Redis
sudo systemctl restart redis
sudo systemctl enable redis
```

#### Windows

```powershell
# 使用WSL或下载Windows版本
# https://github.com/microsoftarchive/redis/releases
```

### 3.3 安装 Python 环境

```bash
# 安装Python 3.11
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip

# 创建项目目录
cd /opt
sudo mkdir sheep-breeding-system
sudo chown $USER:$USER sheep-breeding-system
cd sheep-breeding-system

# 克隆代码
git clone <repository-url> .

# 创建虚拟环境
cd backend
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4 安装 Julia

```bash
# 下载Julia 1.12.2
wget https://julialang-s3.julialang.org/bin/linux/x64/1.12/julia-1.12.2-linux-x86_64.tar.gz

# 解压
tar -xzf julia-1.12.2-linux-x86_64.tar.gz

# 移动到系统目录
sudo mv julia-1.12.2 /opt/julia

# 创建符号链接
sudo ln -s /opt/julia/bin/julia /usr/local/bin/julia

# 验证安装
julia --version

# 安装Julia依赖
cd ../julia
julia --project=. -e 'using Pkg; Pkg.instantiate()'
```

### 3.5 配置环境变量

```bash
# 创建.env文件
cd ../backend
cp .env.example .env

# 编辑配置
nano .env
```

**配置内容**:

```bash
DATABASE_URL=postgresql://sheep_user:your_password@localhost:5432/sheep_breeding
REDIS_URL=redis://:your_redis_password@localhost:6379/0
SECRET_KEY=your_secret_key_here
JULIA_PROJECT_PATH=/opt/sheep-breeding-system/julia
```

### 3.6 初始化数据库

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行数据库迁移
python scripts/init_db.py

# 创建管理员
python scripts/create_admin.py
```

### 3.7 启动服务

```bash
# 启动后端服务
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 或使用Gunicorn（生产环境）
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

---

## 四、生产环境部署

### 4.1 云端/Kubernetes 部署 (SaaS)

对于需要大规模运行或提供 SaaS 服务的场景，我们提供了详细的 Kubernetes 部署指南。请参考 [DEPLOYMENT.md](DEPLOYMENT.md) 文档。

### 4.2 单机生产环境部署 (Nginx)

### 4.2.1 使用 Nginx 反向代理

```bash
# 安装Nginx
sudo apt install -y nginx

# 创建配置文件
sudo nano /etc/nginx/sites-available/sheep-breeding
```

**Nginx 配置**:

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL证书配置
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 日志
    access_log /var/log/nginx/sheep-breeding-access.log;
    error_log /var/log/nginx/sheep-breeding-error.log;

    # 客户端上传大小限制
    client_max_body_size 100M;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态文件
    location /static {
        alias /opt/sheep-breeding-system/backend/static;
        expires 30d;
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/sheep-breeding /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

### 4.2 配置 SSL 证书（Let's Encrypt）

```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 4.3 配置 Systemd 服务

```bash
# 创建服务文件
sudo nano /etc/systemd/system/sheep-breeding.service
```

**服务配置**:

```ini
[Unit]
Description=Sheep Breeding System Backend
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/sheep-breeding-system/backend
Environment="PATH=/opt/sheep-breeding-system/backend/venv/bin"
ExecStart=/opt/sheep-breeding-system/backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl start sheep-breeding
sudo systemctl enable sheep-breeding

# 查看状态
sudo systemctl status sheep-breeding
```

### 4.4 配置防火墙

```bash
# 使用UFW
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# 查看状态
sudo ufw status
```

---

## 五、验证安装

### 5.1 健康检查

```bash
# 检查API健康状态
curl http://localhost:8000/health

# 预期输出
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "julia": "available"
}
```

### 5.2 运行测试

```bash
# 进入后端目录
cd backend

# 激活虚拟环境
source venv/bin/activate

# 运行测试
python run_all_tests.py

# 或使用pytest
pytest tests/ -v
```

### 5.3 访问 API 文档

打开浏览器访问: `http://localhost:8000/docs`

应该看到 Swagger UI 界面，显示所有 API 端点。

---

## 六、常见问题

### 6.1 数据库连接失败

**问题**: `could not connect to server: Connection refused`

**解决方案**:

```bash
# 检查PostgreSQL是否运行
sudo systemctl status postgresql

# 检查端口
sudo netstat -tulpn | grep 5432

# 检查配置
sudo nano /etc/postgresql/15/main/postgresql.conf
# 确保 listen_addresses = '*'

# 检查防火墙
sudo ufw allow 5432/tcp
```

### 6.2 Julia 包安装失败

**问题**: `ERROR: Package not found`

**解决方案**:

```bash
# 清理Julia包缓存
julia -e 'using Pkg; Pkg.gc()'

# 重新安装
cd julia
julia --project=. -e 'using Pkg; Pkg.resolve(); Pkg.instantiate()'
```

### 6.3 内存不足

**问题**: 系统运行缓慢或崩溃

**解决方案**:

```bash
# 增加swap空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久启用
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 6.4 Docker 容器无法启动

**问题**: `Error starting userland proxy`

**解决方案**:

```bash
# 重启Docker
sudo systemctl restart docker

# 清理未使用的容器和镜像
docker system prune -a

# 重新构建
docker-compose down
docker-compose up -d --build
```

---

## 📞 获取帮助

- **文档**: [完整文档](docs/USER_MANUAL_ZH.md)
- **API 参考**: http://localhost:8000/docs
- **问题反馈**: GitHub Issues
- **技术支持**: support@example.com

---

**安装完成后，建议阅读 [用户使用手册](docs/USER_MANUAL_ZH.md) 了解系统功能。**

# 部署指南

## 生产环境部署说明

### 目录

1. [部署架构](#部署架构)
2. [Docker 部署](#docker部署)
3. [Kubernetes 部署](#kubernetes部署)
4. [数据库配置](#数据库配置)
5. [安全配置](#安全配置)
6. [监控和日志](#监控和日志)
7. [备份和恢复](#备份和恢复)
8. [性能优化](#性能优化)

---

## 部署架构

### 推荐架构

```
┌─────────────────────────────────────────┐
│         Load Balancer (Nginx)           │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐          ┌────▼───┐
│ Web    │          │  API   │
│ Server │          │ Server │
│ (×3)   │          │  (×3)  │
└───┬────┘          └────┬───┘
    │                    │
    └──────────┬─────────┘
               │
    ┌──────────▼──────────┐
    │                     │
┌───▼────┐          ┌────▼───┐
│ Julia  │          │ Redis  │
│ Worker │          │ Cache  │
│ (×2)   │          └────────┘
└───┬────┘
    │
┌───▼────────┐
│ PostgreSQL │
│  Cluster   │
└────────────┘
```

---

## Docker 部署

### 1. 环境准备

```bash
# 安装Docker和Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# 数据库配置
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=sheep_breeding
POSTGRES_USER=breeding_user
POSTGRES_PASSWORD=your_secure_password

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# 应用配置
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Julia配置
JULIA_NUM_THREADS=8
JULIA_GPU_ENABLED=true
```

### 3. 启动服务

```bash
# 构建镜像
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 检查服务状态
docker-compose ps
```

### 4. 初始化数据库

```bash
# 运行数据库迁移
docker-compose exec backend python scripts/init_db.py

# 创建管理员用户
docker-compose exec backend python scripts/create_admin.py
```

---

## Kubernetes 部署

### 1. 前置要求

- Kubernetes 集群 (v1.24+)
- kubectl 配置完成
- Helm 3.0+
- 持久化存储 (PV/PVC)

### 2. 创建命名空间

```bash
kubectl create namespace sheep-breeding
```

### 3. 配置 Secrets

```bash
# 创建数据库密码
kubectl create secret generic postgres-secret \\
  --from-literal=password=your_db_password \\
  -n sheep-breeding

# 创建应用密钥
kubectl create secret generic app-secret \\
  --from-literal=secret-key=your_secret_key \\
  -n sheep-breeding
```

### 4. 部署 PostgreSQL

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: sheep-breeding
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:14
          env:
            - name: POSTGRES_DB
              value: sheep_breeding
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: postgres-storage
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 100Gi
```

### 5. 部署后端 API

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
  namespace: sheep-breeding
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend-api
  template:
    metadata:
      labels:
        app: backend-api
    spec:
      containers:
        - name: api
          image: your-registry/sheep-breeding-backend:latest
          ports:
            - containerPort: 8000
          env:
            - name: POSTGRES_HOST
              value: postgres
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
          resources:
            requests:
              memory: "2Gi"
              cpu: "1000m"
            limits:
              memory: "4Gi"
              cpu: "2000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
```

### 6. 部署 Julia 计算节点

```yaml
# julia-worker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: julia-worker
  namespace: sheep-breeding
spec:
  replicas: 2
  selector:
    matchLabels:
      app: julia-worker
  template:
    metadata:
      labels:
        app: julia-worker
    spec:
      containers:
        - name: worker
          image: your-registry/sheep-breeding-julia:latest
          env:
            - name: JULIA_NUM_THREADS
              value: "16"
          resources:
            requests:
              memory: "8Gi"
              cpu: "4000m"
              nvidia.com/gpu: 1
            limits:
              memory: "16Gi"
              cpu: "8000m"
              nvidia.com/gpu: 1
```

### 7. 配置 Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sheep-breeding-ingress
  namespace: sheep-breeding
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - api.sheep-breeding.com
      secretName: sheep-breeding-tls
  rules:
    - host: api.sheep-breeding.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: backend-api
                port:
                  number: 8000
```

### 8. 应用配置

```bash
# 应用所有配置
kubectl apply -f k8s/

# 检查部署状态
kubectl get pods -n sheep-breeding
kubectl get services -n sheep-breeding
kubectl get ingress -n sheep-breeding
```

---

## 数据库配置

### PostgreSQL 优化

```sql
-- postgresql.conf 优化参数

-- 内存配置
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 64MB

-- 并发配置
max_connections = 200
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8

-- 检查点配置
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

-- 查询优化
random_page_cost = 1.1
effective_io_concurrency = 200
```

### 创建索引

```sql
-- 关键索引
CREATE INDEX idx_animals_ear_tag ON animals(ear_tag);
CREATE INDEX idx_animals_farm_id ON animals(farm_id);
CREATE INDEX idx_phenotypes_animal_id ON phenotypes(animal_id);
CREATE INDEX idx_phenotypes_trait_date ON phenotypes(trait_name, measure_date);
CREATE INDEX idx_genotypes_animal_id ON genotypes(animal_id);
```

---

## 安全配置

### 1. HTTPS 配置

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.sheep-breeding.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 防火墙规则

```bash
# UFW配置
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. 密钥管理

使用环境变量或密钥管理服务（如 HashiCorp Vault）存储敏感信息。

---

## 监控和日志

### Prometheus 监控

```yaml
# prometheus-config.yaml
scrape_configs:
  - job_name: "backend-api"
    static_configs:
      - targets: ["backend:8000"]
    metrics_path: "/metrics"
```

### Grafana 仪表板

导入预配置的仪表板：

- API 性能监控
- 数据库性能
- 系统资源使用

### 日志聚合

使用 ELK Stack 收集和分析日志：

```yaml
# filebeat.yml
filebeat.inputs:
  - type: container
    paths:
      - "/var/lib/docker/containers/*/*.log"

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

---

## 备份和恢复

### 数据库备份

```bash
# 每日自动备份
0 2 * * * /usr/local/bin/backup-db.sh

# backup-db.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
pg_dump -h localhost -U breeding_user sheep_breeding | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# 保留最近30天的备份
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

### 数据恢复

```bash
# 恢复数据库
gunzip < backup_20241216.sql.gz | psql -h localhost -U breeding_user sheep_breeding
```

---

## 性能优化

### 1. 应用层缓存

```python
from redis import Redis
from functools import lru_cache

redis_client = Redis(host='redis', port=6379)

@lru_cache(maxsize=1000)
def get_animal_ebv(animal_id):
    # 缓存育种值查询
    cache_key = f"ebv:{animal_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    result = calculate_ebv(animal_id)
    redis_client.setex(cache_key, 3600, json.dumps(result))
    return result
```

### 2. 数据库连接池

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

### 3. 异步任务队列

使用 Celery 处理耗时任务：

```python
from celery import Celery

celery_app = Celery('tasks', broker='redis://redis:6379/0')

@celery_app.task
def calculate_breeding_values(trait_name):
    # 异步计算育种值
    result = run_blup_analysis(trait_name)
    return result
```

---

## 故障排查

### 常见问题

1. **数据库连接失败**

   - 检查防火墙规则
   - 验证数据库凭据
   - 检查连接池配置

2. **Julia 计算超时**

   - 增加 worker 数量
   - 优化算法参数
   - 启用 GPU 加速

3. **内存不足**
   - 增加容器内存限制
   - 优化数据批处理大小
   - 使用稀疏矩阵

---

## 联系支持

- 📧 技术支持: 1958126580@qq.com
- 📖 文档: https://github.com/1958126580/Sheep_breeding/tree/main/docs
- 🐛 问题反馈: https://github.com/1958126580/Sheep_breeding/issues

---

**祝部署顺利！**

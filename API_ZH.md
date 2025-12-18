# API 文档

## RESTful API 接口文档

### 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

---

## 认证接口

### 用户登录

**POST** `/auth/login`

**请求体**:

```json
{
  "username": "string",
  "password": "string"
}
```

**响应**:

```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 种羊管理 Animal Management

### 获取种羊列表

**GET** `/animals`

**查询参数**:

- `skip` (int): 跳过记录数，默认 0
- `limit` (int): 返回记录数，默认 100
- `breed` (string): 品种筛选
- `sex` (string): 性别筛选 (male/female)

**响应**:

```json
{
  "total": 150,
  "items": [
    {
      "id": 1,
      "ear_tag": "SH2024001",
      "name": "优秀001",
      "breed": "杜泊羊",
      "sex": "male",
      "birth_date": "2023-03-15",
      "sire_id": null,
      "dam_id": null,
      "farm_id": 1,
      "status": "active"
    }
  ]
}
```

### 创建种羊记录

**POST** `/animals`

**请求体**:

```json
{
  "ear_tag": "SH2024002",
  "name": "优秀002",
  "breed": "萨福克羊",
  "sex": "female",
  "birth_date": "2024-01-20",
  "sire_id": 1,
  "dam_id": 2,
  "farm_id": 1
}
```

### 获取单个种羊详情

**GET** `/animals/{animal_id}`

### 更新种羊信息

**PUT** `/animals/{animal_id}`

### 删除种羊记录

**DELETE** `/animals/{animal_id}`

---

## 表型数据 Phenotype Data

### 记录表型数据

**POST** `/phenotypes`

**请求体**:

```json
{
  "animal_id": 1,
  "trait_name": "体重",
  "trait_value": 45.5,
  "measure_date": "2024-06-15",
  "age_days": 180,
  "unit": "kg"
}
```

### 获取表型数据

**GET** `/phenotypes`

**查询参数**:

- `animal_id` (int): 动物 ID
- `trait_name` (string): 性状名称
- `start_date` (date): 开始日期
- `end_date` (date): 结束日期

---

## 基因组数据 Genomic Data

### 上传基因型数据

**POST** `/genotypes/upload`

**请求体** (multipart/form-data):

- `file`: VCF/PLINK 格式文件
- `format`: "vcf" | "plink"
- `description`: 数据描述

### 获取基因型数据

**GET** `/genotypes/{animal_id}`

### SNP 质控

**POST** `/genotypes/qc`

**请求体**:

```json
{
  "min_maf": 0.01,
  "max_missing": 0.1,
  "min_call_rate": 0.9
}
```

---

## 育种值估计 Breeding Value Estimation

### 提交 BLUP 分析任务

**POST** `/breeding-values/blup`

**请求体**:

```json
{
  "trait_name": "体重",
  "model_type": "animal_model",
  "fixed_effects": ["sex", "farm"],
  "random_effects": ["animal"],
  "use_genomic": false
}
```

**响应**:

```json
{
  "task_id": "uuid-string",
  "status": "pending",
  "created_at": "2024-12-16T10:00:00Z"
}
```

### 获取分析结果

**GET** `/breeding-values/results/{task_id}`

**响应**:

```json
{
  "task_id": "uuid-string",
  "status": "completed",
  "results": [
    {
      "animal_id": 1,
      "ebv": 2.5,
      "accuracy": 0.85,
      "rank": 1
    }
  ]
}
```

### 提交 GBLUP 分析

**POST** `/breeding-values/gblup`

### 提交 ssGBLUP 分析

**POST** `/breeding-values/ssgblup`

---

## GWAS 分析 GWAS Analysis

### 提交 GWAS 任务

**POST** `/gwas/analyze`

**请求体**:

```json
{
  "trait_name": "体重",
  "method": "mlm",
  "significance_threshold": 5e-8,
  "maf_threshold": 0.05
}
```

---

## 选种决策 Selection Decision

### 获取选种候选

**GET** `/selection/candidates`

**查询参数**:

- `trait_name` (string): 目标性状
- `top_n` (int): 返回前 N 名
- `min_accuracy` (float): 最小准确性

### 最优贡献选择 (OCS)

**POST** `/selection/ocs`

**请求体**:

```json
{
  "trait_name": "体重",
  "target_inbreeding": 0.05,
  "n_selected": 20
}
```

---

## 健康管理 Health Management

### 记录健康事件

**POST** `/health/records`

**请求体**:

```json
{
  "animal_id": 1,
  "event_type": "vaccination",
  "event_date": "2024-06-01",
  "description": "口蹄疫疫苗",
  "veterinarian": "张医生"
}
```

### 获取健康记录

**GET** `/health/records`

---

## 繁殖管理 Reproduction Management

### 记录配种

**POST** `/reproduction/matings`

**请求体**:

```json
{
  "sire_id": 1,
  "dam_id": 2,
  "mating_date": "2024-05-01",
  "method": "natural"
}
```

### 记录产羔

**POST** `/reproduction/births`

---

## 物联网数据 IoT Data

### 上传传感器数据

**POST** `/iot/sensor-data`

**请求体**:

```json
{
  "device_id": "SENSOR001",
  "animal_id": 1,
  "data_type": "temperature",
  "value": 38.5,
  "timestamp": "2024-12-16T10:30:00Z"
}
```

---

## 云端服务 Cloud Services

### 启动数据同步

**POST** `/cloud/sync/start`

### 获取同步状态

**GET** `/cloud/sync/status/{task_id}`

---

## 错误码说明

| 错误码 | 说明               |
| ------ | ------------------ |
| 400    | 请求参数错误       |
| 401    | 未授权，需要登录   |
| 403    | 禁止访问，权限不足 |
| 404    | 资源不存在         |
| 422    | 数据验证失败       |
| 500    | 服务器内部错误     |

---

## 在线 API 文档

访问 `http://localhost:8000/docs` 可查看完整的交互式 API 文档（Swagger UI）。

访问 `http://localhost:8000/redoc` 可查看 ReDoc 格式的 API 文档。

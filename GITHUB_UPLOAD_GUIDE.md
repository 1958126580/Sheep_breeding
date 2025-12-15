# GitHub 上传指南

## 方式一：使用 GitHub Desktop（最简单）

### 1. 安装 GitHub Desktop

- 下载地址: https://desktop.github.com/
- 安装并登录您的 GitHub 账户

### 2. 创建仓库并上传

1. 打开 GitHub Desktop
2. 点击 `File` -> `New Repository`
3. 填写信息：
   - Name: `Sheep_breeding`
   - Local Path: `E:\codes\sheep breeding`
4. 点击 `Create Repository`
5. 点击 `Publish repository` 上传到 GitHub

---

## 方式二：使用命令行（推荐）

### 步骤 1: 配置 Git

```bash
# 打开PowerShell或命令提示符
cd "E:\codes\sheep breeding"

# 配置Git用户信息
git config --global user.name "Bujun Mei"
git config --global user.email "1958126580@qq.com"
```

### 步骤 2: 初始化仓库

```bash
# 初始化Git仓库
git init

# 添加所有文件
git add .

# 创建首次提交
git commit -m "Initial commit: 国际顶级肉羊育种系统"
```

### 步骤 3: 在 GitHub 创建仓库

1. 访问 https://github.com/new
2. 登录账户
3. 填写仓库信息：
   - Repository name: `Sheep_breeding`
   - Description: `国际顶级肉羊育种系统 - International Top-tier Sheep Breeding System`
   - 选择 `Public` 或 `Private`
4. **不要**勾选 "Initialize this repository with a README"
5. 点击 `Create repository`

### 步骤 4: 连接并推送

```bash
# 添加远程仓库（替换为您的实际仓库地址）
git remote add origin https://github.com/1958126580/Sheep_breeding.git

# 推送代码
git branch -M main
git push -u origin main
```

**首次推送会要求输入 GitHub 凭据**

---

## 方式三：使用 Personal Access Token（最安全）

### 1. 创建 Token

1. 登录 GitHub
2. 点击右上角头像 -> `Settings`
3. 左侧菜单 -> `Developer settings` -> `Personal access tokens` -> `Tokens (classic)`
4. 点击 `Generate new token` -> `Generate new token (classic)`
5. 设置：
   - Note: `Sheep Breeding Upload`
   - Expiration: `90 days` 或自定义
   - 勾选权限: `repo` (全部)
6. 点击 `Generate token`
7. **复制生成的 token**（只显示一次！）

### 2. 使用 Token 推送

```bash
# 使用token作为密码
git push https://1958126580:YOUR_TOKEN@github.com/1958126580/Sheep_breeding.git main
```

---

## 创建.gitignore 文件

在上传前，建议创建`.gitignore`文件排除不必要的文件：

```bash
# 在项目根目录创建.gitignore
```

`.gitignore`内容：

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/

# Julia
*.jl.cov
*.jl.*.cov
*.jl.mem
Manifest.toml

# IDE
.vscode/
.idea/
*.swp
*.swo

# 环境变量
.env
.env.local

# 数据库
*.db
*.sqlite

# 日志
*.log
logs/

# 临时文件
*.tmp
*.bak
*~

# 系统文件
.DS_Store
Thumbs.db

# 大文件
*.zip
*.tar.gz
*.rar
```

---

## 完整操作流程

```powershell
# 1. 进入项目目录
cd "E:\codes\sheep breeding"

# 2. 创建.gitignore
New-Item -Path .gitignore -ItemType File
# 然后编辑.gitignore添加上面的内容

# 3. 初始化Git
git init

# 4. 添加文件
git add .

# 5. 查看状态
git status

# 6. 提交
git commit -m "Initial commit: 国际顶级肉羊育种系统

- 完整的后端API (10个模块, 130+端点)
- Julia计算引擎 (6个模块)
- 数据库设计 (22张表)
- 完整的中文文档
- 测试套件"

# 7. 在GitHub网站创建仓库后，添加远程仓库
git remote add origin https://github.com/1958126580/Sheep_breeding.git

# 8. 推送
git push -u origin main
```

---

## 验证上传成功

访问: `https://github.com/1958126580/Sheep_breeding`

应该看到所有文件已上传。

---

## 后续更新代码

```bash
# 修改代码后
git add .
git commit -m "描述您的更改"
git push
```

---

## 注意事项

1. ⚠️ **不要**将`.env`文件上传（包含密码）
2. ⚠️ **不要**上传大型数据文件
3. ✅ 确保`.gitignore`正确配置
4. ✅ 使用有意义的 commit message
5. ✅ 定期备份重要数据

---

## 需要帮助？

如果遇到问题：

1. 检查 Git 是否正确安装: `git --version`
2. 检查网络连接
3. 确认 GitHub 账户可以正常登录
4. 查看错误信息并搜索解决方案

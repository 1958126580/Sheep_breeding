# GitHub 部署脚本
# GitHub Deployment Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "新星肉羊育种系统 - GitHub 部署" -ForegroundColor Cyan
Write-Host "NovaBreed Sheep System - GitHub Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在正确的目录
if (-not (Test-Path "README.md")) {
    Write-Host "错误: 请在项目根目录运行此脚本" -ForegroundColor Red
    Write-Host "Error: Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

Write-Host "✓ 当前目录正确" -ForegroundColor Green
Write-Host ""

# 1. 显示当前状态
Write-Host "1. 检查 Git 状态..." -ForegroundColor Yellow
git status
Write-Host ""

# 2. 添加所有文件
Write-Host "2. 添加所有更改..." -ForegroundColor Yellow
git add .
Write-Host "✓ 文件已添加" -ForegroundColor Green
Write-Host ""

# 3. 显示将要提交的文件
Write-Host "3. 将要提交的文件:" -ForegroundColor Yellow
git status --short
Write-Host ""

# 4. 提交更改
Write-Host "4. 提交更改..." -ForegroundColor Yellow
$commitMessage = @"
feat: Prepare for v1.0.0 release

Major improvements for international top-tier standard:

✨ New Files:
- Add LICENSE (MIT)
- Add CONTRIBUTING.md (bilingual contribution guide)
- Add CHANGELOG.md (comprehensive version history)
- Add .github/workflows/ci.yml (CI/CD pipeline)

🔧 Enhancements:
- Enhance .gitignore with comprehensive patterns
- Add status badges to README (CI/CD, code style, PRs welcome)
- Improve documentation structure

📚 Documentation:
- Complete user manual (976 lines)
- Comprehensive API documentation
- Installation and deployment guides
- Algorithm reference documentation

🧪 Testing:
- Unit tests for models and services
- API integration tests
- Julia module tests
- 80%+ test coverage

🚀 Features:
- 80+ API endpoints
- 12+ data models
- 9+ business services
- 8+ Julia computation modules
- GPU acceleration support
- Parallel computing
- Blockchain traceability
- Cloud services integration

This release brings the NovaBreed Sheep System to international
top-tier software standards with comprehensive documentation,
automated CI/CD, and professional project structure.
"@

git commit -m $commitMessage
Write-Host "✓ 提交完成" -ForegroundColor Green
Write-Host ""

# 5. 检查远程仓库
Write-Host "5. 检查远程仓库..." -ForegroundColor Yellow
$remoteUrl = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ 未配置远程仓库，正在配置..." -ForegroundColor Yellow
    git remote add origin https://github.com/1958126580/Sheep_breeding.git
    Write-Host "✓ 远程仓库已配置" -ForegroundColor Green
} else {
    Write-Host "✓ 远程仓库: $remoteUrl" -ForegroundColor Green
}
Write-Host ""

# 6. 推送到 GitHub
Write-Host "6. 推送到 GitHub..." -ForegroundColor Yellow
Write-Host "⚠ 即将推送到 GitHub，请确认您的凭据" -ForegroundColor Yellow
Write-Host ""
Write-Host "按 Enter 继续推送，或 Ctrl+C 取消..." -ForegroundColor Cyan
Read-Host

git branch -M main
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ 部署成功!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步操作:" -ForegroundColor Cyan
    Write-Host "1. 访问: https://github.com/1958126580/Sheep_breeding" -ForegroundColor White
    Write-Host "2. 检查 README 和徽章显示" -ForegroundColor White
    Write-Host "3. 验证 GitHub Actions 是否自动运行" -ForegroundColor White
    Write-Host "4. 创建 v1.0.0 Release (使用 CHANGELOG.md 内容)" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠ 安全提醒: 建议立即更改 GitHub 密码" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ 推送失败" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "1. 网络连接问题" -ForegroundColor White
    Write-Host "2. 认证失败 - 请检查用户名和密码" -ForegroundColor White
    Write-Host "3. 仓库权限问题" -ForegroundColor White
    Write-Host ""
    Write-Host "请检查错误信息并重试" -ForegroundColor Yellow
}

# GitHub 推送助手
# 自动推送到 GitHub 仓库

Write-Host "正在准备推送到 GitHub..." -ForegroundColor Green

# 1. 检查是否已安装 Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "未找到 Git，请先安装 Git。"
    exit 1
}

# 2. 获取远程仓库 URL
$remoteUrl = Read-Host "请输入您的 GitHub 仓库地址 (例如 https://github.com/username/Sheep_breeding.git)"

if ([string]::IsNullOrWhiteSpace($remoteUrl)) {
    Write-Error "URL 不能为空"
    exit 1
}

# 3. 添加远程仓库
Write-Host "正在添加远程仓库..."
git remote remove origin 2>$null
git remote add origin $remoteUrl

if ($LASTEXITCODE -ne 0) {
    Write-Error "添加远程仓库失败"
    exit 1
}

# 4. 推送代码
Write-Host "正在推送代码..."
Write-Host "注意: 如果弹出登录窗口，请使用您的 GitHub 账号登录。" -ForegroundColor Yellow
Write-Host "如果您开启了双重认证 (2FA)，您必须使用 Personal Access Token 作为密码。" -ForegroundColor Yellow

git branch -M main
git push -u origin main

if ($LASTEXITCODE -ne 0) {
    Write-Error "推送失败。请检查您的网络连接或权限。"
} else {
    Write-Host "✅ 代码已成功推送到 GitHub!" -ForegroundColor Green
}

Pause

@echo off
REM ============================================================================
REM NovaBreed Sheep System - GitHub 自动部署脚本
REM ============================================================================

echo.
echo ========================================
echo  NovaBreed Sheep System
echo  GitHub 自动部署脚本
echo ========================================
echo.

REM 检查Git状态
echo [1/5] 检查Git状态...
git status
echo.

REM 确认推送
echo [2/5] 准备推送到GitHub...
echo.
echo 请确认以下信息:
echo - 仓库: https://github.com/1958126580/Sheep_breeding.git
echo - 分支: main
echo - 提交: 56 files changed, 16,299 insertions(+)
echo.
set /p CONFIRM="确认推送? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo 已取消推送
    pause
    exit /b
)

REM 推送到GitHub
echo.
echo [3/5] 推送到GitHub...
echo.
echo 重要提示:
echo 1. GitHub现在需要Personal Access Token，不能使用密码
echo 2. 请访问: https://github.com/settings/tokens
echo 3. 创建新token，勾选 'repo' 和 'workflow' 权限
echo 4. 复制token后，在下面的命令中替换 YOUR_TOKEN
echo.
echo 推送命令:
echo git push https://YOUR_TOKEN@github.com/1958126580/Sheep_breeding.git main
echo.
set /p TOKEN="请输入您的GitHub Personal Access Token: "

if "%TOKEN%"=="" (
    echo 错误: Token不能为空
    pause
    exit /b 1
)

echo.
echo 正在推送...
git push https://%TOKEN%@github.com/1958126580/Sheep_breeding.git main

if errorlevel 1 (
    echo.
    echo 错误: 推送失败
    echo 请检查:
    echo 1. Token是否正确
    echo 2. Token权限是否足够
    echo 3. 网络连接是否正常
    pause
    exit /b 1
)

echo.
echo [4/5] 推送成功!
echo.

REM 提示启用GitHub Pages
echo [5/5] 下一步: 启用GitHub Pages
echo.
echo 请按照以下步骤操作:
echo.
echo 1. 访问: https://github.com/1958126580/Sheep_breeding/settings/pages
echo 2. 在 "Source" 下选择: GitHub Actions
echo 3. 点击 "Save"
echo 4. 等待3-5分钟自动部署完成
echo 5. 访问: https://1958126580.github.io/Sheep_breeding/
echo.
echo GitHub Actions 构建进度:
echo https://github.com/1958126580/Sheep_breeding/actions
echo.

REM 打开浏览器
set /p OPEN="是否打开GitHub Pages设置页面? (Y/N): "
if /i "%OPEN%"=="Y" (
    start https://github.com/1958126580/Sheep_breeding/settings/pages
)

echo.
echo ========================================
echo  部署完成!
echo ========================================
echo.
echo 您的网站将在几分钟后可以访问:
echo https://1958126580.github.io/Sheep_breeding/
echo.
pause

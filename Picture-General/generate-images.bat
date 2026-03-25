@echo off
REM 豆包图片生成批处理脚本
REM 使用方法：generate-images.bat <prompt-file> [output-dir]

REM 检查是否安装了Node.js
where node >nul 2>nul
if errorlevel 1 (
    echo ❌ 错误：未找到 Node.js，请先安装 Node.js
    echo 下载地址：https://nodejs.org/
    pause
    exit /b 1
)

REM 检查.env文件是否存在
if not exist .env (
    echo ⚠️  未找到 .env 文件，请复制 .env.example 为 .env 并填写你的豆包API密钥
    pause
    exit /b 1
)

REM 加载.env环境变量
for /f "tokens=1,* delims==" %%a in (.env) do (
    if not "%%a"=="" if not "%%a:~0,1%"=="#" set %%a=%%b
)

REM 检查API密钥
if "%DOUBO_API_KEY%"=="" (
    echo ❌ 错误：DOUBO_API_KEY 为空，请在 .env 文件中设置你的API密钥
    pause
    exit /b 1
)

REM 运行生成脚本
node image-generator.js %*

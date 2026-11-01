@echo off
rem 启动「图片网格标线与分割工具」
rem 在 cmd 中直接运行 run.cmd，或在 PowerShell 中运行 .\run.cmd，也可双击执行
chcp 65001 >nul
cd /d "%~dp0"

rem 进入 venv 环境并启动程序（py10power 是 PowerShell 脚本，经 powershell 调用）
powershell -Command "py10power; python image_grid_tool.py"

if errorlevel 1 (
    echo.
    echo 程序异常退出
    pause
)

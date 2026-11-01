@echo off

rem  run image split tool
chcp 65001 >nul
cd /d "%~dp0"

rem
powershell -Command "py10power; python image_grid_tool.py"

if errorlevel 1 (
    echo.
    echo progrom error exit.
    pause
)

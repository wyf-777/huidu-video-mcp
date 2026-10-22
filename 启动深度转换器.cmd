@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 没有找到虚拟环境：.venv\Scripts\python.exe
    echo 请先在当前目录执行：python -m venv .venv
    pause
    exit /b 1
)

echo 正在启动深度视频转换器...
echo 网页会自动打开：http://127.0.0.1:7860/
echo 使用期间请保留此窗口；停止时按 Ctrl+C。
echo.

".venv\Scripts\python.exe" "groovin_depth_converter.py"

echo.
echo 转换器已停止。如上方出现错误，请保留窗口内容。
pause

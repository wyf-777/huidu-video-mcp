@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo [错误] 未找到 Python 环境，请按 README.md 完成首次安装。
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "web_launcher.py"

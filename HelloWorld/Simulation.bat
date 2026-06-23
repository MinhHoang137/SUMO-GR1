@echo off
chcp 65001 >nul

set "VENV=%~dp0.venv"
set "VENV_PY=%VENV%\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [LOI] Khong tim thay .venv. Hay chay install.bat truoc.
    echo.
    pause
    exit /b 1
)

"%VENV_PY%" "%~dp0launcher.py"

echo.
if errorlevel 1 (
    echo [LOI] launcher.py thoat voi loi (xem thong bao o tren^).
) else (
    echo [OK] launcher.py da ket thuc.
)
pause

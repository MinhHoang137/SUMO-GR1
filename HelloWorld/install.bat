@echo off
chcp 65001 >nul
echo ============================================================
echo   SUMO-GR1: Cai dat goi Python can thiet (vao .venv)
echo ============================================================
echo.

set FAILED=0

:: ---- 1. Kiem tra Python ----------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay Python 3.14.
    echo.
    echo        Tai Python 3.14 tai:
    echo        https://www.python.org/downloads/release/python-3140/
    echo.
    echo        Khi cai dat: tich "Add python.exe to PATH"
    echo        Neu may co nhieu phien ban, kiem tra PATH uu tien Python 3.14.
    set FAILED=1
)
if "%FAILED%"=="1" goto :end

:: Kiem tra dung phien ban 3.14
python -c "import sys; v=sys.version_info; exit(0 if v.major==3 and v.minor>=14 else 1)" >nul 2>&1
if errorlevel 1 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [TIM THAY] %%v
    echo.
    echo [LOI] He thong yeu cau Python 3.14+.
    echo       Phien ban tren khong hop le.
    echo.
    echo       Tai Python 3.14 tai:
    echo       https://www.python.org/downloads/release/python-3140/
    echo.
    echo       Sau khi cai, mo "Environment Variables" ^> System Variables ^> Path
    echo       va dam bao thu muc Python 3.14 xep TREN cac phien ban cu.
    set FAILED=1
)
if "%FAILED%"=="1" goto :end

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v

:: ---- 2. Tao virtual environment neu chua co --------------------
echo.
set "VENV=%~dp0.venv"
if not exist "%VENV%\Scripts\python.exe" (
    echo [*] Tao virtual environment tai .venv ...
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo [LOI] Khong tao duoc .venv.
        set FAILED=1
    )
    if not "%FAILED%"=="1" echo [OK] .venv da tao xong.
) else (
    echo [OK] .venv da ton tai, dung lai.
)
if "%FAILED%"=="1" goto :end

:: ---- 3. Nang cap pip -------------------------------------------
echo.
echo [*] Nang cap pip...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip --quiet

:: ---- 4. Cai eclipse-sumo vao venv ------------------------------
echo.
echo [*] Cai dat eclipse-sumo (bao gom SUMO + traci + sumolib)...
echo     Co the mat vai phut lan dau tai...
"%VENV%\Scripts\python.exe" -m pip install eclipse-sumo
if errorlevel 1 (
    echo.
    echo [LOI] Cai dat that bai. Kiem tra ket noi mang va thu lai.
    set FAILED=1
)
if "%FAILED%"=="1" goto :end

:: ---- 4b. Dang ky sumo/tools vao sys.path cua venv ---------------
:: eclipse-sumo dat traci trong sumo/tools/ nhung khong tu them vao sys.path.
:: Tao file .pth de Python tim thay "import traci" ma khong can SUMO global.
echo.
echo [*] Dang ky sumo/tools vao .venv (cho import traci)...
"%VENV%\Scripts\python.exe" -c "import sumo, os, site; p=os.path.join(sumo.SUMO_HOME,'tools'); [open(os.path.join(s,'sumo_tools.pth'),'w').write(p+'\n') for s in site.getsitepackages() if os.path.isdir(s)]; print('[OK] Da dang ky:', p)"
if errorlevel 1 (
    echo [LOI] Khong dang ky duoc sumo/tools.
    set FAILED=1
)
if "%FAILED%"=="1" goto :end

:: ---- 5. Cai Microsoft Visual C++ Redistributable ---------------
echo.
echo [*] Kiem tra Visual C++ Redistributable...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Version >nul 2>&1
if not errorlevel 1 (
    echo [OK] Visual C++ Redistributable da co san.
    goto :skip_vc
)
echo [*] Chua co, dang tai va cai dat...
curl -L -o "%TEMP%\vc_redist.x64.exe" "https://aka.ms/vs/17/release/vc_redist.x64.exe"
if errorlevel 1 (
    echo [CANH BAO] Khong tai duoc VC++ Redist.
    echo            Neu sumo-gui bao loi DLL, hay cai thu cong tu:
    echo            https://aka.ms/vs/17/release/vc_redist.x64.exe
    goto :skip_vc
)
"%TEMP%\vc_redist.x64.exe" /install /quiet /norestart
if errorlevel 1 (
    echo [CANH BAO] Cai VC++ Redist that bai (co the can quyen Admin^).
) else (
    echo [OK] Visual C++ Redistributable da cai xong.
)
del "%TEMP%\vc_redist.x64.exe" >nul 2>&1
:skip_vc

:: ---- 6. Xac nhan ------------------------------------------------
echo.
echo [*] Kiem tra import traci...
"%VENV%\Scripts\python.exe" -c "import traci; print('[OK] traci', traci.__version__)"
if errorlevel 1 (
    echo [LOI] import traci that bai sau khi cai.
    set FAILED=1
)
if "%FAILED%"=="1" goto :end

"%VENV%\Scripts\python.exe" -c "import sumo; print('[OK] SUMO_HOME:', sumo.SUMO_HOME)"

echo.
echo ============================================================
echo   Hoan tat! De chay he thong:
echo     1. Chay:  Simulation.bat  (tu dong dung .venv)
echo     2. Mo Unity build va ket noi
echo ============================================================

:end
echo.
pause

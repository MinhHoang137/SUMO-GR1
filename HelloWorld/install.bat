@echo off
chcp 65001 >nul
echo ============================================================
echo   SUMO-GR1: Cai dat goi Python can thiet
echo ============================================================
echo.

:: ---- 1. Kiem tra Python ----------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay Python.
    echo        Tai Python 3.10+ tai: https://www.python.org/downloads/
    echo        Nho tich "Add Python to PATH" khi cai dat.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v

:: ---- 2. Nang cap pip --------------------------------------------
echo.
echo [*] Nang cap pip...
python -m pip install --upgrade pip --quiet

:: ---- 3. Cai eclipse-sumo ----------------------------------------
echo.
echo [*] Cai dat eclipse-sumo (bao gom SUMO + traci + sumolib)...
echo     Co the mat vai phut lan dau tai...
python -m pip install eclipse-sumo
if errorlevel 1 (
    echo.
    echo [LOI] Cai dat that bai. Kiem tra ket noi mang va thu lai.
    pause
    exit /b 1
)

:: ---- 4. Cai Microsoft Visual C++ Redistributable (can cho sumo-gui) ----
echo.
echo [*] Kiem tra Visual C++ Redistributable...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Version >nul 2>&1
if not errorlevel 1 (
    echo [OK] Visual C++ Redistributable da co san.
) else (
    echo [*] Chua co, dang tai va cai dat...
    curl -L -o "%TEMP%\vc_redist.x64.exe" "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    if errorlevel 1 (
        echo [CANH BAO] Khong tai duoc VC++ Redist. Neu sumo-gui bao loi DLL,
        echo            hay cai thu cong tu: https://aka.ms/vs/17/release/vc_redist.x64.exe
    ) else (
        "%TEMP%\vc_redist.x64.exe" /install /quiet /norestart
        if errorlevel 1 (
            echo [CANH BAO] Cai VC++ Redist that bai (co the can quyen Admin).
        ) else (
            echo [OK] Visual C++ Redistributable da cai xong.
        )
        del "%TEMP%\vc_redist.x64.exe" >nul 2>&1
    )
)

:: ---- 5. Xac nhan ------------------------------------------------
echo.
echo [*] Kiem tra import traci...
python -c "import traci; print('[OK] traci', traci.VERSION)"
if errorlevel 1 (
    echo [LOI] import traci that bai sau khi cai.
    pause
    exit /b 1
)

python -c "import sumo; print('[OK] SUMO_HOME:', sumo.SUMO_HOME)"

:: ---- 6. Tom tat --------------------------------------------------
echo.
echo ============================================================
echo   Hoan tat! De chay he thong:
echo     1. Chay:  python launcher.py
echo     2. Mo Unity build va ket noi
echo ============================================================
echo.
pause

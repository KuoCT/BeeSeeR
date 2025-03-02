@echo off
setlocal

:: 設定虛擬環境路徑
set VENV_DIR=%~dp0SnapOCR_env
set ACTIVATE_SCRIPT=%VENV_DIR%\Scripts\activate.bat
set INIT_FLAG=%VENV_DIR%\init.flag
set INIT_CPU_FLAG=%VENV_DIR%\init_cpu.flag
set REQUIREMENT_FLAG=%VENV_DIR%\requirement.flag

:: 檢查 Python 是否已安裝
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: 檢查虛擬環境是否已存在，若不存在則建立
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: 確保虛擬環境已正確建立
if not exist "%ACTIVATE_SCRIPT%" (
    echo [ERROR] Virtual environment setup failed. Missing activate script.
    pause
    exit /b 1
)

:: 啟動虛擬環境
call "%ACTIVATE_SCRIPT%"

:: 檢查 Python 是否來自虛擬環境
for /f "delims=" %%i in ('python -c "import sys; print(sys.prefix)"') do set VENV_PYTHON_PATH=%%i
for /f "delims=" %%i in ('python -c "import sys; print(sys.base_prefix)"') do set PYTHON_PATH=%%i

if "%VENV_PYTHON_PATH%"=="%PYTHON_PATH%" (
    echo [ERROR] Virtual environment activation failed.
    pause
    exit /b 1
)

echo If you accidentally installed the CUDA version without an NVIDIA GPU, this script will help uninstall CUDA dependencies!
echo Alternatively, if you have an NVIDIA GPU, you can use this script to reinstall the CUDA version.
echo After the script completes, rerun SnapOCR.bat with the correct settings.

:: 解除安裝torch套件
echo Uninstalling torch packages...
pip uninstall torch torchvision torchaudio -y 2>nul
echo Reset Checkpoint...
del %INIT_FLAG% >nul 2>nul
del %INIT_CPU_FLAG% >nul 2>nul
del %REQUIREMENT_FLAG% >nul 2>nul
echo Torch packages have been uninstalled. Remember to adjust the mode in SnapOCR.bat before running it again!

pause
endlocal
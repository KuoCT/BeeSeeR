@echo off
setlocal

:: 設定模式（0 為正常模式，1 為強制CPU模式）
set mode=0

:: 設定 debug 變數（0 為正常模式，1 為除錯模式）
set debug=1

:: 設定虛擬環境路徑
set VENV_DIR=%~dp0SnapOCR_env
set ACTIVATE_SCRIPT=%VENV_DIR%\Scripts\activate
set GUI=%~dp0GUI.py
set INIT=%~dp0init.py
set INIT_FLAG=%VENV_DIR%\init.flag
set INIT_CPU_FLAG=%VENV_DIR%\init_cpu.flag
set REQUIREMENT_FLAG=%VENV_DIR%\requirement.flag

:: 檢查虛擬環境是否已存在，若不存在則建立
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
) else (
    echo Virtual environment already exists.
)

:: 啟動虛擬環境
echo Activating virtual environment...
call "%ACTIVATE_SCRIPT%"

:: 在除錯模式中重新檢查安裝套件
if %debug%==1 (
    echo Debug mode enabled: Reinstalling required packages...
    del "%REQUIREMENT_FLAG%" >nul 2>&1
)

:: 檢查是否已安裝必要的套件
if not exist "%REQUIREMENT_FLAG%" (
    echo Installing required packages...
    python.exe -m pip install --upgrade pip
    pip install torch==2.6.0+cu118 torchvision==0.21.0+cu118 torchaudio==2.6.0+cu118 --index-url https://download.pytorch.org/whl/cu118
    pip install customtkinter==5.2.2 pyautogui==0.9.54
    pip install surya-ocr==0.13.0
    echo Required packages installed > "%REQUIREMENT_FLAG%"
) else (
    echo Required packages already been installed.
)

:: 檢查是否需要執行 INIT
if "%mode%"=="1" (
    if not exist "%INIT_CPU_FLAG%" (
        echo Running INIT in force-CPU mode...
        python "%INIT%" --force-cpu
        echo Initialized CPU Mode > "%INIT_CPU_FLAG%"

    ) else (
        echo INIT has already been executed in force-CPU mode.
    )
) else (
    if not exist "%INIT_FLAG%" (
        echo Running INIT in normal mode...
        python "%INIT%"
        echo Initialized Normal Mode > "%INIT_FLAG%"
    ) else (
        echo INIT has already been executed in normal mode.
    )
)

:: 啟動 GUI
if "%mode%"=="1" (
    echo Launching GUI in force-CPU mode...
    if "%debug%"=="1" (
        python "%GUI%" --force-cpu
    ) else (
        start "" pythonw "%GUI%" --force-cpu
        exit
    )
) else (
    echo Launching GUI in normal mode...
    if "%debug%"=="1" (
        python "%GUI%"
    ) else (
        start "" pythonw "%GUI%"
        exit
    )
)

endlocal

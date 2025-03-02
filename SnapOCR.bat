@echo off
setlocal

:: 設定模式（0 為兼容模式，1 為強制CPU模式）
set mode=0

:: 設定 debug 變數（0 為背景執行模式，1 為除錯模式）
set debug=1

:: 設定虛擬環境路徑
set VENV_DIR=%~dp0SnapOCR_env
set ACTIVATE_SCRIPT=%VENV_DIR%\Scripts\activate.bat
set GUI=%~dp0GUI.py
set INIT=%~dp0init.py
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
) else (
    echo Virtual environment already exists.
)

:: 確保虛擬環境已正確建立
if not exist "%ACTIVATE_SCRIPT%" (
    echo [ERROR] Virtual environment setup failed. Missing activate script.
    pause
    exit /b 1
)

:: 啟動虛擬環境
echo Activating virtual environment...
call "%ACTIVATE_SCRIPT%"

:: 檢查 Python 是否來自虛擬環境
for /f "delims=" %%i in ('python -c "import sys; print(sys.prefix)"') do set VENV_PYTHON_PATH=%%i
for /f "delims=" %%i in ('python -c "import sys; print(sys.base_prefix)"') do set PYTHON_PATH=%%i
echo Current Python path: %VENV_PYTHON_PATH%
echo System Python path: %PYTHON_PATH%

if "%VENV_PYTHON_PATH%"=="%PYTHON_PATH%" (
    echo [ERROR] Virtual environment activation failed.
    pause
    exit /b 1
)

echo Virtual environment activated successfully.

:: 在除錯模式中重新檢查安裝套件
if %debug%==1 (
    echo Debug mode enabled: Recheck required packages...
    del "%REQUIREMENT_FLAG%" >nul 2>&1
)

:: 檢查是否已安裝必要的套件
if not exist "%REQUIREMENT_FLAG%" (
    echo Installing required packages...
    python.exe -m pip install --upgrade pip
    if "%mode%"=="0" (
        pip install torch==2.6.0+cu118 --index-url https://download.pytorch.org/whl/cu118
    )
    pip install customtkinter==5.2.2 pyautogui==0.9.54 surya-ocr==0.13.0
    echo Required packages installed > "%REQUIREMENT_FLAG%"
)

:: 檢查是否需要執行 INIT
if "%mode%"=="1" (
    if not exist "%INIT_CPU_FLAG%" (
        echo Running INIT in force-CPU mode...
        python "%INIT%" --force-cpu
        if %errorlevel% neq 0 (
            echo [ERROR] INIT failed in CPU mode.
            pause
            exit /b 1
        )
        echo Initialized CPU Mode > "%INIT_CPU_FLAG%"
    ) else (
        echo INIT has already been executed in force-CPU mode.
    )
) else (
    if not exist "%INIT_FLAG%" (
        echo Running INIT in normal mode...
        python "%INIT%"
        if %errorlevel% neq 0 (
            echo [ERROR] INIT failed in normal mode.
            pause
            exit /b 1
        )
        echo Initialized Normal Mode > "%INIT_FLAG%"
    ) else (
        echo INIT has already been executed in normal mode.
    )
)

:: 重製 GUI 啟動訊號
if exist %~dp0GUI_open.flag (del %~dp0GUI_open.flag)

:: 啟動 GUI
if "%mode%"=="1" (
    echo Launching GUI in force-CPU mode...
    if "%debug%"=="1" (
        python "%GUI%" --force-cpu
    ) else (
        start "" pythonw "%GUI%" --force-cpu
        for /L %%i in (1,1,60) do (
            if exist %~dp0GUI_open.flag (
                del %~dp0GUI_open.flag
                exit /b 
            )
            timeout /t 1 /nobreak >nul
        )
        exit
    )
) else (
    echo Launching GUI in normal mode...
    if "%debug%"=="1" (
        python "%GUI%"
    ) else (
        start "" pythonw "%GUI%"
        for /L %%i in (1,1,60) do (
            if exist %~dp0GUI_open.flag (
                del %~dp0GUI_open.flag
                exit /b
            )
            timeout /t 1 /nobreak >nul
        )
        exit
    )
)

:: Only pause if errorlevel is non-zero (indicating an error)
if %errorlevel% neq 0 (
    pause
)
endlocal

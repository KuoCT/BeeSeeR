@echo off
setlocal

:: 設定 Groq API Keys 串接 AI 語言模型
set api_key=

:: 設定模式（0 為兼容模式，1 為強制CPU模式）
set mode=0

:: 設定 debug 變數（0 為背景執行模式，1 為除錯模式）
set debug=1

:: 設定虛擬環境路徑
set VENV_DIR=%~dp0env
set ACTIVATE_SCRIPT=%VENV_DIR%\Scripts\activate.bat
set GUI=%~dp0GUI.py
set MODEL=%~dp0\ocr\model.py
set MODEL_FLAG=%VENV_DIR%\model.flag
set MODEL_CPU_FLAG=%VENV_DIR%\model_cpu.flag
set REQUIREMENT_FLAG=%VENV_DIR%\requirement.flag

:: 設定最大重試次數
set MAX_RETRIES=2
set RETRY_COUNT=0

:: 檢查 Python 是否已安裝
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

:CHECK_ENV
:: 檢查虛擬環境是否存在，若不存在則建立
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment check completed.
)

:: 確保虛擬環境已正確建立
if not exist "%ACTIVATE_SCRIPT%" (
    echo [ERROR] Virtual environment setup failed. Missing activate script.
    goto REINSTALL_ENV
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
    goto REINSTALL_ENV
)

echo Virtual environment check completed.
goto INSTALLATION

:REINSTALL_ENV
:: 檢查是否達到最大重試次數
set /a RETRY_COUNT+=1
echo [WARNING] Attempt to repair virtual environment...
if %RETRY_COUNT% geq %MAX_RETRIES% (
    echo [ERROR] Maximum retry limit reached. Exiting...
    pause
    exit /b 1
)

:: 刪除現有的虛擬環境，然後重新安裝
echo [WARNING] Removing and reinstalling the virtual environment... (Attempt %RETRY_COUNT%/%MAX_RETRIES%)
rmdir /s /q "%VENV_DIR%"
if exist "%VENV_DIR%" (
    echo [ERROR] Failed to remove existing virtual environment.
    pause
    exit /b 1
)

echo Repairing virtual environment...
python -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

:: 重新檢查環境
goto CHECK_ENV

:INSTALLATION
:: 重新檢查安裝套件
if %debug% equ 1 goto RECHECK_INSTALLATION
if %RETRY_COUNT% geq 1 goto RECHECK_INSTALLATION

goto CHECK_INSTALLATION

:RECHECK_INSTALLATION
echo Recheck required packages...
del "%REQUIREMENT_FLAG%" >nul 2>&1

:CHECK_INSTALLATION
:: 檢查是否已安裝必要的套件
if not exist "%REQUIREMENT_FLAG%" (
    echo Installing required packages...
    python.exe -m pip install --upgrade pip
    if %mode% equ 0 (
        pip install torch==2.6.0+cu118 --index-url https://download.pytorch.org/whl/cu118
    )
    pip install customtkinter==5.2.2 pyautogui==0.9.54 surya-ocr==0.13.0 groq==0.18.0
    echo Required packages installed > "%REQUIREMENT_FLAG%"
)

:: 檢查是否需要執行 model.py
if %mode% equ 1 (
    if not exist "%MODEL_CPU_FLAG%" (
        echo Running MODEL in force-CPU mode...
        python "%MODEL%" -c
        if %errorlevel% neq 0 (
            echo [ERROR] MODEL failed in CPU mode.
            pause
            exit /b 1
        )
        echo Initialized CPU Mode > "%MODEL_CPU_FLAG%"
    ) else (
        echo MODEL has already been executed in force-CPU mode.
    )
) else (
    if not exist "%MODEL_FLAG%" (
        echo Running MODEL in normal mode...
        python "%MODEL%"
        if %errorlevel% neq 0 (
            echo [ERROR] MODEL failed in normal mode.
            pause
            exit /b 1
        )
        echo Initialized Normal Mode > "%MODEL_FLAG%"
    ) else (
        echo MODEL has already been executed in normal mode.
    )
)

:: 顯示參數最終執行參數
@REM if %mode% equ 1 (
@REM     echo Run argument: -c -k "%api_key%"
@REM ) else (
@REM     echo Run argument: -k "%api_key%"    
@REM )

:: 重製 GUI 啟動訊號
if exist %~dp0GUI_open.flag (del %~dp0GUI_open.flag)

:: 啟動 GUI
if %mode% equ 1 (
    echo Launching GUI in force-CPU mode...
    if %debug% equ 1 (
        python "%GUI%" -a -c -k "%api_key%"
    ) else (
        start "" pythonw "%GUI%" -c -k "%api_key%"
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
    if %debug% equ 1 (
        python "%GUI%" -a -k "%api_key%" 
    ) else (
        start "" pythonw "%GUI%" -k "%api_key%" 
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

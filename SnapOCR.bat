@echo off
setlocal

:: 設定虛擬環境路徑
set VENV_DIR=%~dp0SnapOCR_env
set ACTIVATE_SCRIPT=%VENV_DIR%\Scripts\activate
set GUI=%~dp0GUI.py
set REQUIREMENTS_FLAG=%VENV_DIR%\installed.flag

:: 設定 debug 變數（1 為啟用除錯模式，0 為正常模式）
set debug=0

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

:: 只有在第一次執行時安裝套件，之後不再檢查
if not exist "%REQUIREMENTS_FLAG%" (
    echo Installing required packages for the first time...
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    pip install customtkinter pyautogui 
    pip install surya-ocr

    :: 建立一個標記文件，代表套件已安裝
    echo Packages installed > "%REQUIREMENTS_FLAG%"
) else (
    echo All required packages are already installed.
)

:: 檢查 debug 模式
if "%debug%"=="1" (
    echo [DEBUG MODE] Executing in debug mode...
    pythonw "%GUI%"
) else (
    start "" pythonw "%GUI%"
    exit
)

endlocal

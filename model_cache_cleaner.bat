@echo off
setlocal
echo ================================
echo Cleaning model cache folders...
echo ================================

:: 清除模型快取資料夾，如果未來模型更新或是使用者想要解除安裝，這個腳本可以將專案殘留的快取檔案刪除

:: Hugging Face model cache - model
set HF_MODEL=%USERPROFILE%\.cache\huggingface\hub\models--kha-white--manga-ocr-base
if exist "%HF_MODEL%" (
    rd /s /q "%HF_MODEL%"
    echo Deleted: %HF_MODEL%
) else (
    echo Folder not found: %HF_MODEL%
)

:: Hugging Face model cache - lock
set HF_LOCK=%USERPROFILE%\.cache\huggingface\hub\.locks\models--kha-white--manga-ocr-base
if exist "%HF_LOCK%" (
    rd /s /q "%HF_LOCK%"
    echo Deleted: %HF_LOCK%
) else (
    echo Folder not found: %HF_LOCK%
)

:: Surya OCR model - detection
set DETECTION=%LOCALAPPDATA%\datalab\datalab\Cache\models\text_detection
if exist "%DETECTION%" (
    rd /s /q "%DETECTION%"
    echo Deleted: %DETECTION%
) else (
    echo Folder not found: %DETECTION%
)

:: Surya OCR model - recognition
set RECOGNITION=%LOCALAPPDATA%\datalab\datalab\Cache\models\text_recognition
if exist "%RECOGNITION%" (
    rd /s /q "%RECOGNITION%"
    echo Deleted: %RECOGNITION%
) else (
    echo Folder not found: %RECOGNITION%
)

echo.
echo All specified model cache paths checked.
pause
endlocal

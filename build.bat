@echo off

:: 記錄開始時間
set start_time=%TIME%

:: 若存在先前的 build 資料夾則刪除
if exist build (rmdir /s /q build)

:: Nuitka 封裝腳本
nuitka ^
--standalone ^
--enable-plugin=tk-inter ^
--include-distribution-metadata=Pillow ^
--include-data-dir=./env/Lib/site-packages/manga_ocr/assets=./manga_ocr/assets ^
--include-data-files=./env/Lib/site-packages/unidic_lite/dicdir\**\*=./unidic_lite/dicdir/ ^
--include-package=transformers.models.vit ^
--nofollow-import-to=torchvision ^
--nofollow-import-to=torchaudio ^
--module-parameter=torch-disable-jit=yes ^
--include-data-dir=./checkpoint=./checkpoint ^
--include-data-dir=./icon=./icon ^
--include-data-dir=./persona=./persona ^
--include-data-dir=./theme=./theme ^
--output-dir=build ^
--windows-icon-from-ico=./icon/logo_dark.ico ^
--windows-console-mode=hide ^
--output-filename=BeeSeeR.exe ^
--jobs=-1 ^
GUI.py

:: 記錄結束時間
set end_time=%TIME%

:: 計算耗時
call :TimeDiff "%start_time%" "%end_time%"

pause
exit /b

:: 計算時間差，並顯示分鐘 + 秒
:TimeDiff
setlocal
set "start=%~1"
set "end=%~2"

:: 分解時、分、秒
for /f "tokens=1-4 delims=:." %%a in ("%start%") do (
    set /a start_seconds=%%a*3600 + %%b*60 + %%c
)
for /f "tokens=1-4 delims=:." %%a in ("%end%") do (
    set /a end_seconds=%%a*3600 + %%b*60 + %%c
)

:: 跨午夜處理
if %end_seconds% LSS %start_seconds% (
    set /a end_seconds+=24*3600
)

:: 總秒數
set /a duration=%end_seconds% - %start_seconds%

:: 分解分鐘 + 秒
set /a minutes=%duration% / 60
set /a seconds=%duration% %% 60

echo.
echo ===== Time elapsed: %minutes% minutes and %seconds% seconds =====
endlocal
exit /b
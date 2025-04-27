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
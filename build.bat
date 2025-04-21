if exist build (rmdir /s /q build)
@REM nuitka ^
@REM --standalone ^
@REM --enable-plugin=tk-inter ^
@REM --module-parameter=torch-disable-jit=yes ^
@REM --include-distribution-metadata=Pillow ^
@REM --include-data-dir=./env/Lib/site-packages/manga_ocr/assets=./manga_ocr/assets ^
@REM --include-data-files=./env/Lib/site-packages/unidic_lite/dicdir\**\*=./unidic_lite/dicdir/ ^
@REM --include-package=transformers.models.vit ^
@REM --include-data-dir=./icon=./icon ^
@REM --include-data-dir=./theme=./theme ^
@REM --include-data-dir=./prompt=./prompt ^
@REM --include-data-dir=./checkpoint=./checkpoint ^
@REM --output-dir=build ^
@REM --windows-icon-from-ico=./icon/logo_dark.ico ^
@REM --output-filename=Debug.exe GUI.py

nuitka ^
--standalone ^
--enable-plugin=tk-inter ^
--module-parameter=torch-disable-jit=yes ^
--include-distribution-metadata=Pillow ^
--include-data-dir=./env/Lib/site-packages/manga_ocr/assets=./manga_ocr/assets ^
--include-data-files=./env/Lib/site-packages/unidic_lite/dicdir\**\*=./unidic_lite/dicdir/ ^
--include-package=transformers.models.vit ^
--include-data-dir=./icon=./icon ^
--include-data-dir=./theme=./theme ^
--include-data-dir=./prompt=./prompt ^
--include-data-dir=./checkpoint=./checkpoint ^
--output-dir=build ^
--windows-icon-from-ico=./icon/logo_dark.ico ^
--windows-console-mode=hide ^
--output-filename=BeeSeeR.exe GUI.py
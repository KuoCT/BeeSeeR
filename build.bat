if exist build (rmdir /s /q build)
nuitka ^
--standalone ^
--enable-plugin=tk-inter ^
--module-parameter=torch-disable-jit=yes ^
--include-distribution-metadata=Pillow ^
--include-data-dir=./icon=./icon ^
--include-data-dir=./theme=./theme ^
--include-data-dir=./prompt_diy=./prompt_diy ^
--include-data-dir=./prompt=./prompt ^
--include-data-dir=./checkpoint=./checkpoint ^
--output-dir=build ^
--windows-icon-from-ico=./icon/logo_dark.ico ^
--output-filename=Debug.exe GUI.py

@REM nuitka ^
@REM --standalone ^
@REM --enable-plugin=tk-inter ^
@REM --module-parameter=torch-disable-jit=yes ^
@REM --include-package=surya ^
@REM --include-package=manga_ocr ^
@REM --include-module=PIL.Image ^
@REM --include-module=PIL.ImageOps ^
@REM --include-data-dir=./icon=./icon ^
@REM --include-data-dir=./theme=./theme ^
@REM --include-data-dir=./prompt_diy=./prompt_diy ^
@REM --include-data-dir=./prompt=./prompt ^
@REM --include-data-dir=./checkpoint=./checkpoint ^
@REM --enable-console-mode=disable ^
@REM --output-dir=build ^
@REM --windows-icon-from-ico=./icon/logo_dark.ico ^
@REM --output-filename=BeeSeeR.exe GUI.py
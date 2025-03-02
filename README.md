# SnapOCR
A screen OCR tool that extracts text using a screenshot-like method.

[中文版說明](./README_zh.md)

## Overview
SnapOCR is a convenient screen Optical Character Recognition (OCR) tool designed to quickly capture text from any area of the screen and copy it to the clipboard.

⚠ **Important Notice:** Since this script utilizes automation features like selecting specific areas of the desktop, I am unsure whether it might trigger anti-cheat programs. If you plan to use it in online games (especially competitive games), proceed at your own risk!

## Use Cases
https://github.com/user-attachments/assets/340bdbb9-ad20-4f22-bf8c-2db590b9c0d9

- **Capture text from the screen for LLMs** (e.g., ChatGPT, Claude) without input limitations.
- **Directly capture text from PC game screens.**
- **Enhance PDF reading experience** by quickly extracting and recognizing text.

## Features
- **One-click text extraction** – No need to manually save screenshots. 
- **Clipboard integration** – Text is automatically copied for easy pasting.
- **Multi-language support** – Adaptable for different OCR needs.  
- **Optimized speed** – Option to enable GPU acceleration for improved performance. 

## Installation
### System Requirements
- **Windows 10+** (Tested on Windows 10 with Python 3.10-3.13)
- **Python 3.10+**
- **NVIDIA GPU (Recommended)** – Uses CUDA acceleration for faster OCR processing.

### Setup & First-Time Run
- Clone the repository to your computer:
   ```bash
   git clone https://github.com/KuoCT/SnapOCR.git
   cd SnapOCR
   ```
   Or download it from [here](https://github.com/KuoCT/SnapOCR/archive/refs/heads/main.zip), then extract it and open the folder.

#### NVIDIA GPU (Recommended)
- Run `SnapOCR.bat` for the initial installation.
- After the first installation, users can freely switch between CUDA and CPU mode by editing `SnapOCR.bat` and setting `mode` to `1`:
   ```bat
   :: 設定模式（0 為正常模式，1 為強制CPU模式）
   set mode=1
   ```
- Set `debug` to `0` to hide the terminal window (recommended once everything is running smoothly):
   ```bat
   :: 設定 debug 變數（0 為正常模式，1 為除錯模式）
   set debug=0
   ```
- Save `SnapOCR.bat` for future use.

#### Other GPUs or CPU only
- Edit `SnapOCR.bat`, set `mode` to `1`, and do not change it.
- Save and run the `SnapOCR.bat` for the initial installation.
- After the first installation, set `debug` to `0` in `SnapOCR.bat` to hide the terminal window (recommended once everything is running smoothly)
- Save `SnapOCR.bat` for future use.

The first run may take some time as required dependencies are automatically installed. Subsequent runs will be faster.

## Usage
1. Launch SnapOCR – Run `SnapOCR.bat`.
2. Click the `Caprure` button – Select any area on the screen.
3. The text will be extracted and automatically copied to the clipboard – Ready to paste anywhere (e.g., ChatGPT).
4. You can find and edit `Prompt.txt` within the folder - this text will be copied along with the extracted text! (If you don’t want to copy the prompt, simply uncheck the prompt checkbox.)

## Credit
A huge thanks to the following open-source projects:
- [Surya](https://github.com/VikParuchuri/surya) – Powerful OCR model by VikParuchuri.
- [PyAutoGUI](https://github.com/asweigart/pyautogui) – Intuitive automation tools by asweigart.
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) – Beautiful and modern UI by TomSchimansky.

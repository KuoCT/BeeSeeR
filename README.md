# SnapOCR
An intuitive GUI-based OCR tool with screenshot-like functionality.

[中文版說明](./README_zh.md)

## Overview
SnapOCR is an **efficient and user-friendly** Optical Character Recognition (OCR) tool, designed for **fast and reliable text extraction** from any part of the screen.

**Important Reminder:** This script involves automation features such as selecting a specific area on the computer desktop. I am not sure if it will trigger anti-cheat programs. If you plan to use it in online games (especially competitive games), you do so at your own risk!

## Use Cases
https://github.com/user-attachments/assets/340bdbb9-ad20-4f22-bf8c-2db590b9c0d9

- **Extract text from the screen for LLMs** (e.g., ChatGPT, Claude) without input limitations.
- **Extracting text directly from PC game screens.**
- **Enhancing PDF reading** by quickly capturing and recognizing text.

## Features
- **One-click text extraction** – No need to save screenshots.  
- **Clipboard integration** – Extracted text is automatically copied for easy pasting.  
- **Supports multiple languages** – Works well with various OCR needs.  
- **Optimized for speed** – Leverages GPU acceleration for faster processing (optional).  

## Installation
### **System Requirements**
- **Windows 10+** (Tested on Windows 10 with Python 3.10-3.13)
- **Python 3.10+**
- **NVIDIA GPU (Recommended)** – For faster OCR processing.

### **Setup & First-Time Run**
- Clone the repository:
   ```bash
   git clone https://github.com/KuoCT/SnapOCR.git
   cd SnapOCR
   ```
#### **NVIDIA GPU (Recommended)**
- Simply run `SnapOCR.bat` for first-time installation.
- After the first run, you can switch between CUDA and CPU mode by editing `SnapOCR.bat` and setting `mode` to `1`:
   ```bat
   :: 設定模式（0 為正常模式，1 為強制CPU模式）
   set mode=1
   ```
- You can also hide the terminal console by setting `debug` to `0`:
   ```bat
   :: 設定 debug 變數（0 為正常模式，1 為除錯模式）
   set debug=0
   ```
- Save `SnapOCR.bat` for future use.

#### **Other GPUs or CPU only**
- Edit `SnapOCR.bat`, set `mode` to `1`, and do not change it.
- Save and run the `SnapOCR.bat` for first-time installation.
- After the first run, you can hide the terminal console by editing `SnapOCR.bat` and setting `debug` to `0`:
   ```bat
   :: 設定 debug 變數（0 為正常模式，1 為除錯模式）
   set debug=0
   ```
- Save `SnapOCR.bat` for future use.

The first launch may take some time as dependencies are installed. Subsequent runs will be faster.

## Usage
1. Launch SnapOCR – Run `SnapOCR.bat.`
2. Click the `Caprure` button – Select any part of the screen.
3. Text is text is extracted and copied to clipboard – Paste it anywhere (e.g., ChatGPT).
4. You can find and edit the text in `Prompt.txt` within the folder. It will be copied to the clipboard as a prompt along with the recognized text! (If you don't want to copy the prompt, simply uncheck the prompt checkbox.)

## Credit
A huge thanks to the following open-source projects:
- [Surya](https://github.com/VikParuchuri/surya) – Powerful OCR model by VikParuchuri.
- [PyAutoGUI](https://github.com/asweigart/pyautogui) – Intuitive automation tools by asweigart.
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) – Beautiful and modern UI by TomSchimansky.

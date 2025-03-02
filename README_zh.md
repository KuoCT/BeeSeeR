# SnapOCR
這是一個直觀的 GUI OCR 工具，用類似螢幕截圖的方法解析文字。

## 概述
SnapOCR是一款高效且易用的光學字符識別（OCR）工具，為快速且可靠地從螢幕上的任何區域提取文字而設計。

**重要提醒:** 這個腳本因為用到選擇電腦桌面特定區域等等的自動化功能，我不確定會不會觸發防外掛程式，如果要在線上遊戲中(特別是競技遊戲)使用要自行承擔後果喔！

## 應用
https://github.com/user-attachments/assets/340bdbb9-ad20-4f22-bf8c-2db590b9c0d9
- 無縫提取文字**供 LLM（大語言模型）使用**（如 ChatGPT、Claude），避免輸入限制。
- 直接**從 PC 遊戲畫面擷取文字**。
- **提升 PDF 閱讀體驗**，快速擷取並識別文字。

## 功能特色
- **一鍵提取文字** – 無需手動儲存截圖。
- **剪貼簿整合** – 文字自動複製，方便粘貼。
- **支援多種語言** – 可適應不同 OCR 需求。
- **最佳化速度** – 可選擇啟用 GPU 加速，以提升處理效率。

## 安裝
### **系統需求**
- **Windows 10** 以上（已在 Windows 10 + Python 3.10 測試）
- **Python 3.10**
- **NVIDIA GPU（選配）** – 建議使用 CUDA 加速提高 OCR 速度。

### **Setup & First-Time Run**
1. 複製存儲庫到電腦
   ```shell
   git clone https://github.com/KuoCT/SnapOCR.git
   cd SnapOCR
   ```
2. 執行 `SnapOCR.bat`
- 首次運行可能需要一些時間，因為會自動安裝所需的依賴項。
- 安裝完成後再次運行將更快。

## 使用方式
1. 啟動 SnapOCR – 執行 `SnapOCR.bat`。
2. 點擊按鈕 – 選擇螢幕上的任何區域。
3. OCR 處理 – 文字將被即時提取。
4. 文字自動複製到剪貼簿 – 可直接貼上到 ChatGPT、Google 翻譯等應用程式中。
5. 在資料夾中可以找到並編輯 `Prompt.txt` 中的文字，它會作為提示詞一起被複製到剪貼簿！(不想要複製提示詞的話取消勾選提示詞的核取方塊即可)

## 致謝
特別感謝以下開源專案的支持：
- [Surya](https://github.com/VikParuchuri/surya) – 由 VikParuchuri 開發的強大 OCR 模型。
- [PyAutoGUI](https://github.com/asweigart/pyautogui) – 由 asweigart 開發的直觀自動化工具。
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) – 由 TomSchimansky 開發的美觀現代 UI 庫。

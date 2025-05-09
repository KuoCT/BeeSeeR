## 環境需求
- **Windows 10+**
- **Python 3.10 - 3.12**
- **NVIDIA GPU（建議）** – 使用 CUDA 加速提高 OCR 速度。

## 下載
- 複製存儲庫到電腦
   ```bash
   git clone https://github.com/KuoCT/BeeSeeR.git
   cd BeeSeeR
   ```

## 首次安裝
### 方案 1: 使用 NVIDIA GPU 加速的 `兼容模式` (推薦使用)
- 執行 `BeeSeeR.bat` 進行首次安裝。
- 首次安裝完成後，使用者可以自由切換成 CPU 模式，只要編輯`BeeSeeR.bat` 設定 `mode` 成 `1`:
   ```bat
   :: 設定模式（0 為兼容模式，1 為強制CPU模式）
   set mode=1
   ```
- 設定 `debug` 成 `0` 可以隱藏 terminal 視窗(確定可以正常運行後使用):
   ```bat
   :: 設定 debug 變數（0 為背景執行模式，1 為除錯模式）
   set debug=0
   ```
- 存檔 `BeeSeeR.bat` 供後續使用。

### 方案 2: 使用 `強制 CPU 模式` (占用空間較小，處理速度較慢，適合沒有 NVIDIA GPU 的使用者)
- 編輯 `BeeSeeR.bat` 設定 `mode` 成 `1`，然後不要更改它。
- 執行 `BeeSeeR.bat` 進行首次安裝。
- 首次安裝完成後，在 `BeeSeeR.bat` 中設定 `debug` 成 `0` 可以隱藏 terminal 視窗(確定可以正常運行後使用)
- 存檔 `BeeSeeR.bat` 供後續使用。

首次運行可能需要一些時間，因為會自動安裝所需的依賴項。**請等到OCR小視窗彈出表示安裝完成。** 🛠 **工具:** `fix.bat` 可以幫你解除安裝 pytorch 相關的套件，需要修改初始安裝成 `兼容模式` 或是 `強制 CPU 模式` 時使用。

## 版本更新
- 先備份你的文件到 `專案資料夾以外的其他地方` (例如你自己做的 prompt, API金鑰, config.json(使用者偏好設定存檔), 聊天紀錄等等...) 
- 在 `BeeSeeR` 資料夾中逐行執行以下命令:
   ```bash
   git fetch origin
   git reset --hard origin/main
   git clean -dfn
   git clean -df
   ```
   若你想要完全回復乾淨狀態重新安裝，繼續執行以下指令(選擇性):
   ```bash
   git clean -dfX
   ```
- 用 `debug=1` 模式啟動 `BeeSeeR.bat` 到程式順利彈出。
- 切回 `debug=0` 繼續使用。

版本更新詳細請參考[更新日誌](./update_log.md)。

## 使用方式
執行 `BeeSeeR.bat`即可。
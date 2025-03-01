import os
import sys
import argparse
import customtkinter as ctk


# 解析命令列參數
parser = argparse.ArgumentParser(description="OCR 模型控制器")
parser.add_argument("--force-cpu", action="store_true", help="強制使用 CPU 模式")
args = parser.parse_args()

# 根據 `--force-cpu` 設置環境變數
if args.force_cpu:
    os.environ["CUDA_VISIBLE_DEVICES"] = "," # 在 Windows 環境中要使用空列表 ","

def run_wincap():
    """啟動 WindowCapture GUI 並取得擷取的螢幕畫面"""
    global WinCap
    import WinCap # 只在需要時載入，減少初始開啟時間
    app = WinCap.WindowCapture()
    app.mainloop()

def on_closing():
    """確保關閉視窗時正常退出"""
    window.destroy() # 關閉 Tkinter 視窗
    sys.exit(0) # 強制結束 Python 程式

# GUI    
# 建立主視窗
window = ctk.CTk()

# 設定關閉視窗的事件監聽
window.protocol("WM_DELETE_WINDOW", on_closing)

# 設定主視窗參數(eg. 大小/標題/縮放)
window.geometry("200x50") # 寬 x 高
window.title("OCR")
window.resizable(True, True)

# 讓視窗保持最上層
window.attributes("-topmost", True) # 新增這行讓視窗顯示在最前面

# 設定主題
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# 設定預設字體、顏色
initial_font = ctk.CTkFont(
    family="Helvetica", 
    size=24, 
    weight="bold"
)

# 建立主視窗框架
window.grid_columnconfigure((0), weight=1)
window.grid_rowconfigure((0), weight=1)

# 建立底板
frame = ctk.CTkFrame(master=window, corner_radius=10)
frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

# 建立底板框架
frame.grid_columnconfigure((0), weight=1)
frame.grid_rowconfigure((0), weight=1)

# 建立按鈕
button = ctk.CTkButton(master=frame, text="Capture", font=initial_font, anchor="c", command=run_wincap)
button.grid(row=0, column=0, sticky="nsew")

# 啟動 GUI
window.mainloop()
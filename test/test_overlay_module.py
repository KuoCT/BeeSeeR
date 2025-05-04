import customtkinter as ctk
import os
import sys

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑
sys.path.append(PATH) # 將路徑加入到系統路徑中

if __name__ == "__main__":
    from ocr.overlay import overlayWindow

    showTEXT = "這是一個不可編輯的文字顯示區域，可以調整透明度，可以縮放字體大小，鎖定視窗後可以複製文字。\n" * 20
    scale_factor = 1.25
    current_theme = "dark"
    coords = (500, 100, 800, 400)
    # coords = None

    # 設定主題
    if current_theme == "dark":
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")

    ctk.set_default_color_theme(os.path.join(PATH, "theme", "nectar.json"))

    root = ctk.CTk() # 創建主視窗
    root.geometry("+1600+100") # 設定主視窗位置
    overlay = overlayWindow(root, showTEXT, coords, scale_factor)
    overlay.deiconify()

    def toggle_theme():
        """切換主題的函數"""
        global current_theme # 使用全域變數
        if current_theme == "dark": # 如果當前主題是深色
            ctk.set_appearance_mode("light") # 切換到淺色主題
            current_theme = "light" # 更新當前主題變數
        else: # 如果當前主題是淺色
            ctk.set_appearance_mode("dark") # 切換到深色主題
            current_theme = "dark" # 更新當前主題變數  

    toggle_theme_bt = ctk.CTkButton(root, text = "切換主題", command = toggle_theme)
    toggle_theme_bt.pack(padx = 10, pady = 10) 

    root.attributes("-topmost", True) # 讓視窗顯示在最前面
    root.mainloop()
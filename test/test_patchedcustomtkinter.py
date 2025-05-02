import customtkinter as ctk
import os
import sys

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑
sys.path.append(PATH) # 將路徑加入到系統路徑中

if __name__ == "__main__":
    import tool.patchedcustomtkinter as pctk # 載入補丁過的 CustomTkinter 元件
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    silence = False # False 開啟 debug 模式

    app = ctk.CTk()
    app.title("Patched CTkTextbox 測試")
    app.geometry("600x600")

    label = ctk.CTkLabel(app, text="請測試輸入法 + Shift 鍵行為：")
    label.pack(pady=10)

    # 測試 CTkTextbox
    textbox = pctk.CTkTextbox(app, width=550, height=200, font=("Arial", 14), silence=silence)
    textbox.pack(padx=20, pady=10)

    # 測試 CTkEntry
    entry = pctk.CTkEntry(app, width=550, font=("Arial", 14), silence=silence)
    entry.pack(padx=20, pady=10)

    # 測試 CTkComboBox
    combo = pctk.CTkComboBox(app, width=550, font=("Arial", 14), values=["選項一", "選項二", "選項三" * 20], silence=silence)
    combo.set("請選擇")
    combo.pack(padx=20, pady=10)

    app.mainloop()

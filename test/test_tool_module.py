import customtkinter as ctk
import os
import sys
import ctypes

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑
sys.path.append(PATH) # 將路徑加入到系統路徑中

if __name__ == "__main__":
    from tool.ModelSetting import ModelSetting
    from tool.APISetting import APISetting
    from tool.PersonaEditor import PersonaEditor
        
    # 獲取螢幕的縮放比例
    def get_scale_factor():
        """使用 Windows API 取得 Windows 設定的縮放比例"""
        try:
            shcore = ctypes.windll.shcore
            return shcore.GetScaleFactorForDevice(0) / 100.0  # 例如 125% → 1.25
        except Exception:
            return 1.0  # 預設 100%
    
    scale_factor = get_scale_factor()
    current_theme = "dark"

    # 設定主題
    if current_theme == "dark":
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")

    ctk.set_default_color_theme(os.path.join(PATH, "theme", "nectar.json"))

    root = ctk.CTk() # 創建主視窗

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 設定視窗大小
    window_width = 230
    window_height = 160

    # 計算視窗位置
    x_position = screen_width - int(window_width * scale_factor) - int(50 * scale_factor)
    y_position = int(50 * scale_factor)

    # 設定視窗位置
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    APISet = APISetting(current_theme) # 創建子視窗
    ModSet = ModelSetting(current_theme) # 創建子視窗
    PerEdit = PersonaEditor(current_theme) # 創建子視窗

    def toggle_theme():
        """切換主題的函數"""
        global current_theme # 使用全域變數
        if current_theme == "dark": # 如果當前主題是深色
            ctk.set_appearance_mode("light") # 切換到淺色主題
            current_theme = "light" # 更新當前主題變數
        else: # 如果當前主題是淺色
            ctk.set_appearance_mode("dark") # 切換到深色主題
            current_theme = "dark" # 更新當前主題變數    

    def pop_ModelSetting(): # 打開子視窗的函數
        ModSet.geometry(f"{ModSet.w}x{ModSet.h}+{root.winfo_x() - int((ModSet.w + 10) * scale_factor)}+{root.winfo_y()}")
        ModSet.deiconify() # 顯示子視窗

    def pop_APISetting(): # 打開子視窗的函數
        APISet.geometry(f"{APISet.w}x{APISet.h}+{root.winfo_x() - int((APISet.w + ModSet.w + 20) * scale_factor)}+{root.winfo_y()}")
        APISet.deiconify() # 顯示子視窗

    def pop_PersonaEditor(): # 打開子視窗的函數
        PerEdit.geometry(f"{PerEdit.w}x{PerEdit.h}+{root.winfo_x() - int((APISet.w + ModSet.w + 20) * scale_factor)}+{root.winfo_y() + int((APISet.h - 50)) * scale_factor}")
        PerEdit.deiconify() # 顯示子視窗

    # 創建按鈕並綁定函數
    pop_ModelSetting_bt = ctk.CTkButton(root, text = "ModelSetting", command = pop_ModelSetting)
    pop_ModelSetting_bt.pack(padx = 10, pady = (10, 0))

    pop_APISetting_bt = ctk.CTkButton(root, text = "APISetting", command = pop_APISetting)
    pop_APISetting_bt.pack(padx = 10, pady = (10, 0))

    pop_PersonaEditor_bt = ctk.CTkButton(root, text = "PersonaEditor", command = pop_PersonaEditor)
    pop_PersonaEditor_bt.pack(padx = 10, pady = (10, 0))

    toggle_theme_bt = ctk.CTkButton(root, text = "切換主題", command = toggle_theme)
    toggle_theme_bt.pack(padx = 10, pady = 10) 

    root.attributes("-topmost", True) # 讓視窗顯示在最前面
    root.mainloop()
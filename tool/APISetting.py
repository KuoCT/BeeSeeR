import customtkinter as ctk
import tool.patchedcustomtkinter as pctk
from PIL import Image
import os
import json
import webbrowser

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑

class APISetting(ctk.CTkToplevel):
    w = 360
    h = 140
    def __init__(
            self, 
            current_theme, 
            width = None, 
            height = None, 
            on_activate = None,
            APPDATA = PATH
        ):
        super().__init__()

        # Callback 函數
        self.on_activate = on_activate

        self.title("API 設定 (顯示金鑰，請勿擷取！)")
        width = width if width is not None else self.w
        height = height if height is not None else self.h
        self.geometry(f"{width}x{height}") # 設定視窗大小
        self.attributes("-topmost", False) # 讓視窗顯示在最前面
        self.after(250, self.iconbitmap, 
                (
                    os.path.join(PATH, "icon", "logo_dark.ico") 
                    if current_theme == "dark" 
                    else os.path.join(PATH, "icon", "logo_light.ico")
                )
        )
        self.withdraw() # 預設隱藏
        self.protocol("WM_DELETE_WINDOW", self.withdraw) # 攔截關閉行為 → 改為隱藏（withdraw）

        # 讀取設定檔案
        self.APPDATA = APPDATA
        self.settings = self.load_config()
        self.google_ocr_key = self.settings.get("google_ocr_key", None) # Google Vision API Key 文字辨識
        self.groq_key = self.settings.get("groq_key", None) # Groq API Key 翻譯 / 聊天 語言模型

        # 圖示
        self.png_select = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "select.png")), size = (20, 20))

        # 區域規劃
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure((0, 1), weight = 1)

        self.f1 = ctk.CTkFrame(self)
        self.f1.grid(row = 0, column = 0, padx = (5, 0), pady = (5, 0), sticky = "nswe")
        self.f1.grid_columnconfigure(0, weight = 1)
        self.f1.grid_rowconfigure(0, weight = 1)

        self.f2 = ctk.CTkFrame(self)
        self.f2.grid(row = 1, column = 0, padx = (5, 0), pady = 5, sticky = "nswe")
        self.f2.grid_columnconfigure(0, weight = 1)
        self.f2.grid_rowconfigure(0, weight = 1)

        self.f3 = ctk.CTkFrame(self)
        self.f3.grid(row = 0, rowspan = 2, column = 1, padx = 5, pady = 5, sticky = "nswe")
        self.f3.grid_columnconfigure(0, weight = 1)
        self.f3.grid_rowconfigure((0, 1), weight = 1)

        # Google Vision API 設定
        self.google_ocr_wd = ctk.CTkLabel(self.f1, text = "圖片文字辨識 - Google Vision API:", anchor = "w")
        self.google_ocr_wd.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = (5, 0), sticky = "nswe")

        self.google_ocr_entry = pctk.CTkEntry(self.f1) # 輸入框
        self.google_ocr_entry.grid(row = 1, column = 0, padx = (5, 0), pady = (0, 5), sticky = "nswe")
        if self.google_ocr_key:  # 如果有舊的 API Key，則填入
            self.google_ocr_entry.insert(0, self.google_ocr_key)

        self.google_ocr_select_all_bt = ctk.CTkButton(self.f1, text = "", image = self.png_select, width = 0,  
                                                      command = lambda: self.select_all(self.google_ocr_entry))
        self.google_ocr_select_all_bt.grid(row = 1, column = 1, padx = 5, pady = (2, 5), sticky = "e") # 全選按鈕

        # groq API 設定
        self.groq_wd = ctk.CTkLabel(self.f2, text = "AI 自動翻譯 / 聊天室 - Groq API:", anchor = "w")
        self.groq_wd.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = (5, 0), sticky = "nswe")

        self.groq_entry = pctk.CTkEntry(self.f2) # 輸入框
        self.groq_entry.grid(row = 1, column = 0, padx = (5, 0), pady = (2, 5), sticky = "nswe")
        if self.groq_key:  # 如果有舊的 API Key，則填入
            self.groq_entry.insert(0, self.groq_key)

        self.groq_select_all_bt = ctk.CTkButton(self.f2, text = "", image = self.png_select, width = 0,
                                                command = lambda: self.select_all(self.groq_entry))
        self.groq_select_all_bt.grid(row = 1, column = 1, padx = 5, pady = (0, 5), sticky = "e") # 全選按鈕

        # 網頁按鈕
        self.groq_confirm_bt = ctk.CTkButton(self.f3, text = "網頁", width = 40, anchor = "c", command = self.open_sites)
        self.groq_confirm_bt.grid(row = 0, column = 0, padx = 5, pady = (5, 0), sticky = "nswe")

        # 載入按鈕
        self.groq_confirm_bt = ctk.CTkButton(self.f3, text = "套用", width = 40, anchor = "c", command = self.confirm_API)
        self.groq_confirm_bt.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = "nswe")

    def load_config(self):
        """讀取設定檔案"""
        if os.path.exists(os.path.join(self.APPDATA, "config.json")):
            with open(os.path.join(self.APPDATA, "config.json"), "r", encoding = "utf-8") as f:
                return json.load(f)
        return {}  # 如果沒有設定檔，回傳空字典
    
    def save_config(self):
        """只有當設定異動時，才更新 config.json"""
        old_config = self.load_config()

        # 準備要寫入的內容
        new_config = {
            "google_ocr_key": self.google_ocr_key,
            "groq_key": self.groq_key
        }

        # 只有內容不同時才寫入
        if old_config != {**old_config, **new_config}:
            old_config.update(new_config)
            with open(os.path.join(self.APPDATA, "config.json"), "w", encoding = "utf-8") as f:
                json.dump(old_config, f, ensure_ascii = False, indent = 4)
            # print("\033[32m[INFO] 設定檔已更新\033[0m")
        else:
            # print("\033[34m[INFO] 設定無變更，跳過寫入\033[0m")
            pass

    def open_sites(self):
        """打開 API 申請網站"""
        webbrowser.open("https://console.groq.com", new = 2)  # new = 2 表示開新分頁
        webbrowser.open("https://console.cloud.google.com", new = 2)

    def select_all(self, entry):
        """全選輸入框內的 API Key"""
        entry.select_range(0, "end")  # 選取所有文字
        entry.focus_set()  # 設定輸入框焦點，確保全選有效

    def confirm_API(self):
        """套用 API Key"""
        # 取得輸入框內的 API Key
        input_google_ocr = self.google_ocr_entry.get().strip()
        input_groq = self.groq_entry.get().strip()

        # 判斷是否有更新
        changed = False

        if input_google_ocr != self.google_ocr_key:
            self.google_ocr_key = input_google_ocr
            changed = True

        if input_groq != self.groq_key:
            self.groq_key = input_groq
            changed = True

        # 若有變動就儲存並 callback
        if changed:
            self.save_config()
            if self.on_activate: self.on_activate()  # Callback 函數
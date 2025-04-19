import customtkinter as ctk
import os
import json

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑

class ModelSetting(ctk.CTkToplevel):
    width = 250
    height = 365
    def __init__(
            self, 
            current_theme, 
            force_cpu,
            width = width, 
            height = height
        ):
        super().__init__()

        ctk.set_default_color_theme(os.path.join(PATH, "theme/nectar.json"))

        self.title("OCR 設定")
        self.geometry(f"{width}x{height}") # 設定視窗大小
        self.attributes("-topmost", True) # 讓視窗顯示在最前面
        self.after(250, self.iconbitmap, 
                (
                    os.path.join(PATH, "icon", "logo_dark.ico") 
                    if current_theme == "dark" 
                    else os.path.join(PATH, "icon", "logo_light.ico")
                )
        )
        self.withdraw() # 預設隱藏

        # 配置設定
        self.settings = self.load_config()
        self.auto_dtype = self.settings.get("auto_dtype", "ON")
        self.dtype = self.settings.get("dtype", None)
        self.langs = self.settings.get("langs", None) 
        self.manga_ocr = self.settings.get("manga_ocr", False) 
        self.text_font = ctk.CTkFont(family = "Helvetica", size = 14, weight = "bold") # 設定字體

        # 區域規劃
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure((0, 1, 2, 3), weight = 0)
        self.grid_rowconfigure((4), weight = 1)

        f1 = ctk.CTkFrame(self)
        f1.grid(row = 0, column = 0, padx = 5, pady = (5, 0), sticky = "nswe")
        f1.grid_columnconfigure(0, weight = 0)
        f1.grid_rowconfigure(0, weight = 1)

        f2 = ctk.CTkFrame(self)
        f2.grid(row = 1, column = 0, padx = 5, pady = (5, 0), sticky = "nswe")
        f2.grid_columnconfigure(0, weight = 0, minsize = 35)
        f2.grid_columnconfigure((1, 2), weight = 1)
        f2.grid_rowconfigure(0, weight = 1)

        f3 = ctk.CTkFrame(self)
        f3.grid(row = 2, column = 0, padx = 5, pady = (5, 0), sticky = "nswe")
        f3.grid_columnconfigure(0, weight = 0, minsize = 35)
        f3.grid_columnconfigure((1, 2), weight = 1)
        f3.grid_rowconfigure(0, weight = 1)

        f4 = ctk.CTkFrame(self)
        f4.grid(row = 3, column = 0, padx = 5, pady = (5, 0), sticky = "nswe")
        f4.grid_columnconfigure(0, weight = 1)
        f4.grid_rowconfigure(0, weight = 1)

        f5 = ctk.CTkFrame(self)
        f5.grid(row = 4, column = 0, padx = 5, pady = 5, sticky = "nswe")
        f5.grid_columnconfigure(0, weight = 1)
        f5.grid_rowconfigure(0, weight = 1)

        # 精度設定
        # 自動/手動按鈕
        auto_dtype_bt = ctk.CTkButton(f1, text = "自動", font = self.text_font, width = 20, anchor = "c", command = None)
        auto_dtype_bt.grid(row = 0, column = 0, padx = (5, 0), pady = 5, sticky = "nsew")

        # 精度切換
        dtype_sw_var = ctk.StringVar(value = "float32" if force_cpu else "float16")
        current_dtype = dtype_sw_var.get()
        dtype_sw = ctk.CTkSwitch(f1, text = "模型精度: 全精度" if current_dtype == "float32" else "模型精度: 半精度", 
                                height = 28, corner_radius = 4, button_length = 10, font = self.text_font,
                                variable = dtype_sw_var, onvalue = "float32", offvalue = "float16", command = None)
        dtype_sw.grid(row = 0, column = 1, padx = 5, pady = 0, sticky = "ns")
        dtype_sw.configure(state = "disabled" if self.auto_dtype == "ON" else "normal")

        if force_cpu: auto_dtype_bt.configure(state = "disabled")
        if self.auto_dtype == "OFF": 
            auto_dtype_bt.configure(fg_color = ["gray60", "gray60"], hover_color = ["#325882", "#A85820"])
            dtype_sw_var.set(self.dtype)
            dtype_sw.configure(text = "模型精度: 全精度" if self.dtype == "float32" else "模型精度: 半精度")
        else: 
            auto_dtype_bt.configure(fg_color = ["#1e8bba", "#C7712D"], hover_color = ["#325882", "#A85820"])
            dtype_sw_var.set("float32" if force_cpu else "float16")
            dtype_sw.configure(fg_color = "gray60", progress_color = "gray60", button_color = "gray60",
                            text = "模型精度: 全精度" if current_dtype == "float32" else "模型精度: 半精度")
            dtype_sw.configure(state = "disabled")

        # Google Vision 開關
        google_ocr_sw_var = ctk.StringVar(value = "OFF")
        google_ocr_sw = ctk.CTkCheckBox(
            f2, text = "Google Vision (多國語言)", height = 28, font = self.text_font, variable = google_ocr_sw_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        google_ocr_sw.grid(row = 0, column = 0, columnspan = 3, padx = 5, pady = (5, 0), sticky = "w")

        # 屬性調整
        feature_wd = ctk.CTkLabel(f2, text = "分析內容偏好: ", font = self.text_font, anchor = "w")
        feature_wd.grid(row = 1, column = 1, columnspan = 2, padx = 5, pady = 0, sticky = "w")

        feature_img_cb_var = ctk.StringVar(value = "OFF")
        feature_img_cb = ctk.CTkCheckBox(
            f2, text = "影像", height = 28, font = self.text_font, variable = feature_img_cb_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        feature_img_cb.grid(row = 2, column = 1, padx = (5, 0), pady = (0, 5), sticky = "w")

        feature_doc_cb_var = ctk.StringVar(value = "OFF")
        feature_doc_cb = ctk.CTkCheckBox(
            f2, text = "文件影像", height = 28, font = self.text_font, variable = feature_doc_cb_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        feature_doc_cb.grid(row = 2, column = 2, padx = (5, 0), pady = (0, 5), sticky = "w")

        # Surya OCR 開關
        surya_ocr_sw_var = ctk.StringVar(value = "OFF")
        surya_ocr_sw = ctk.CTkCheckBox(
            f3, text = "Surya OCR (多國語言)", height = 28, font = self.text_font, variable = surya_ocr_sw_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        surya_ocr_sw.grid(row = 0, column = 0, columnspan = 3, padx = 5, pady = (5, 0), sticky = "w")

        # 限定語言
        langs_wd = ctk.CTkLabel(f3, text = "限定語言 (可複選): ", font = self.text_font, anchor = "w")
        langs_wd.grid(row = 1, column = 1, columnspan = 2, padx = 5, pady = 0, sticky = "w")

        langs_zh_cb_var = ctk.StringVar(value = "OFF")
        langs_zh_cb = ctk.CTkCheckBox(
            f3, text = "中文", height = 28, font = self.text_font, variable = langs_zh_cb_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        langs_zh_cb.grid(row = 2, column = 1, padx = (5, 0), pady = 0, sticky = "w")

        langs_en_cb_var = ctk.StringVar(value = "OFF")
        langs_en_cb = ctk.CTkCheckBox(
            f3, text = "英文", height = 28, font = self.text_font, variable = langs_en_cb_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        langs_en_cb.grid(row = 3, column = 1, padx = (5, 0), pady = 5, sticky = "w")

        langs_ja_cb_var = ctk.StringVar(value = "OFF")
        langs_ja_cb = ctk.CTkCheckBox(
            f3, text = "日文", height = 28, font = self.text_font, variable = langs_ja_cb_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        langs_ja_cb.grid(row = 2, column = 2, padx = 5, pady = 0, sticky = "w")

        langs_ko_cb_var = ctk.StringVar(value = "OFF")
        langs_ko_cb = ctk.CTkCheckBox(
            f3, text = "韓文", height = 28, font = self.text_font, variable = langs_ko_cb_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        langs_ko_cb.grid(row = 3, column = 2, padx = 5, pady = 5, sticky = "w")

        # Manga-OCR 開關
        manga_ocr_sw_var = ctk.StringVar(value = "OFF")
        manga_ocr_sw = ctk.CTkCheckBox(
            f4, text = "Manga-OCR (日文漫畫)", height = 28, font = self.text_font, variable = manga_ocr_sw_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        manga_ocr_sw.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = "w")

        # 初始化 CheckBox 狀態
        if self.langs is not None:
            langs_zh_cb_var.set("ON" if "zh" in self.langs else "OFF")
            langs_en_cb_var.set("ON" if "en" in self.langs else "OFF")
            langs_ja_cb_var.set("ON" if "ja" in self.langs else "OFF")
            langs_ko_cb_var.set("ON" if "ko" in self.langs else "OFF")
        else:
            # 沒設定，全部 OFF
            langs_zh_cb_var.set("OFF")
            langs_en_cb_var.set("OFF")
            langs_ja_cb_var.set("OFF")
            langs_ko_cb_var.set("OFF")

        if self.manga_ocr:
            manga_ocr_sw_var.set("ON")
            langs_wd.configure(text_color = "gray60")
            langs_zh_cb.configure(state = "disabled", border_color = "gray60", fg_color = "gray60")
            langs_en_cb.configure(state = "disabled", border_color = "gray60", fg_color = "gray60")
            langs_ja_cb.configure(state = "disabled", border_color = "gray60", fg_color = "gray60")
            langs_ko_cb.configure(state = "disabled", border_color = "gray60", fg_color = "gray60")

        # 製作捷徑
        make_ink_bt = ctk.CTkButton(f5, text = "打開模型資料夾", font = self.text_font, width = 20, anchor = "c", command = self.open_checkpoint_folder)
        make_ink_bt.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = "sw")

        # 顯示版本號
        version_lab = ctk.CTkLabel(f5, text = "v3.0.0 ", font = self.text_font, anchor = "e", text_color = ["gray60", "gray40"])
        version_lab.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = "se")


    def load_config(self):
        """讀取設定檔案"""
        if os.path.exists(os.path.join(PATH, "config.json")):
            with open(os.path.join(PATH, "config.json"), "r") as f:
                return json.load(f)
        return {}  # 如果沒有設定檔，回傳空字典
    
    def save_config(self):
        """讀取現有設定，更新後再存入 JSON 檔案"""
        config = self.load_config()  # 先載入現有設定

        # 更新設定
        config.update({
            "auto_dtype": self.auto_dtype,
            "langs": self.langs
        })

        # 將更新後的設定存回 JSON
        with open(os.path.join(PATH, "config.json"), "w") as f:
            json.dump(config, f, indent = 4)  # `indent = 4` 讓 JSON 易讀

    def open_checkpoint_folder(self): 
        """打開 checkpoint 資料夾"""
        os.startfile(os.path.join(PATH, "checkpoint"))

if __name__ == "__main__":
    root = ctk.CTk() # 創建主視窗
    root.geometry("200x70+500+100") # 設定主視窗大小和位置
    scale_factor = 1

    # 設定主題
    theme = 0
    if theme == 1:
        ctk.set_appearance_mode("light")
    else:
        ctk.set_appearance_mode("dark")

    app = ModelSetting("dark", False) # 創建子視窗

    def pop_model_setting(): # 打開子視窗的函數
        app.geometry(f"{root.winfo_x() - int((ModelSetting.width + 10) * scale_factor)}+{root.winfo_y()}")
        app.deiconify() # 顯示子視窗

    pop_model_setting_bt = ctk.CTkButton(root, text="打開子視窗", command = pop_model_setting) # 創建按鈕並綁定函數
    pop_model_setting_bt.pack(pady = 20) # 將按鈕添加到主視窗

    root.attributes("-topmost", True) # 讓視窗顯示在最前面
    root.mainloop()
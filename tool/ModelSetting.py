import customtkinter as ctk
import os
import json

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑

class ModelSetting(ctk.CTkToplevel):
    w = 270
    h = 380
    def __init__(
            self, 
            current_theme, 
            force_cpu,
            width = None, 
            height = None,
            on_activate = None
        ):
        super().__init__()

        # Callback 函數
        self.on_activate = on_activate

        self.title("OCR 設定")
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
        self.settings = self.load_config()
        self.auto_dtype = self.settings.get("auto_dtype", "ON")
        self.dtype = self.settings.get("dtype", None)
        self.langs = self.settings.get("langs", None) 
        self.ocr_model = self.settings.get("ocr_model", "surya") 
        self.text_font = ctk.CTkFont(family = "Helvetica", size = 14, weight = "bold") # 設定字體

        # 區域規劃
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure((0, 1, 2), weight = 0)
        self.grid_rowconfigure((3), weight = 1)

        self.f1 = ctk.CTkFrame(self)
        self.f1.grid(row = 0, column = 0, padx = 5, pady = (5, 0), sticky = "nswe")
        self.f1.grid_columnconfigure(0, weight = 0, minsize = 35)
        self.f1.grid_columnconfigure((1, 2), weight = 0)
        self.f1.grid_rowconfigure(0, weight = 1)

        self.f2 = ctk.CTkFrame(self)
        self.f2.grid(row = 1, column = 0, padx = 5, pady = (5, 0), sticky = "nswe")
        self.f2.grid_columnconfigure(0, weight = 0, minsize = 35)
        self.f2.grid_columnconfigure((1, 2), weight = 0)
        self.f2.grid_rowconfigure(0, weight = 1)

        self.f2_1 = ctk.CTkFrame(self.f2)
        self.f2_1.grid(row = 4, column = 1, columnspan = 2, padx = 0, pady = (0, 5), sticky = "nswe")
        self.f2_1.grid_columnconfigure(0, weight = 0)
        self.f2_1.grid_rowconfigure(0, weight = 1)

        self.f3 = ctk.CTkFrame(self)
        self.f3.grid(row = 2, column = 0, padx = 5, pady = (5, 0), sticky = "nswe")
        self.f3.grid_columnconfigure(0, weight = 1)
        self.f3.grid_rowconfigure(0, weight = 1)

        self.f4 = ctk.CTkFrame(self)
        self.f4.grid(row = 3, column = 0, padx = 5, pady = 5, sticky = "nswe")
        self.f4.grid_columnconfigure((0, 1, 2), weight = 1)
        self.f4.grid_rowconfigure(1, weight = 1)

        # Google-OCR 開關
        self.google_ocr_sw_var = ctk.StringVar(value = "OFF")
        self.google_ocr_sw = ctk.CTkCheckBox(
            self.f1, text = "Google Vision-OCR (多國語言)", height = 28, font = self.text_font, variable = self.google_ocr_sw_var, 
            text_color_disabled = ["gray14", "gray84"], onvalue = "ON", offvalue = "OFF", command = self.activate_google_ocr
        )
        self.google_ocr_sw.grid(row = 0, column = 0, columnspan = 3, padx = 5, pady = (5, 0), sticky = "w")

        # 屬性調整
        self.feature_wd = ctk.CTkLabel(self.f1, text = "分析內容偏好: ", font = self.text_font, anchor = "w")
        self.feature_wd.grid(row = 1, column = 1, columnspan = 2, padx = 5, pady = 0, sticky = "w")

        self.feature_img_cb_var = ctk.StringVar(value = "OFF")
        self.feature_img_cb = ctk.CTkCheckBox(
            self.f1, text = "影像", height = 28, font = self.text_font, variable = self.feature_img_cb_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        self.feature_img_cb.grid(row = 2, column = 1, padx = (5, 0), pady = (0, 5), sticky = "w")

        self.feature_doc_cb_var = ctk.StringVar(value = "OFF")
        self.feature_doc_cb = ctk.CTkCheckBox(
            self.f1, text = "文件影像", height = 28, font = self.text_font, variable = self.feature_doc_cb_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        self.feature_doc_cb.grid(row = 2, column = 2, padx = (5, 0), pady = (0, 5), sticky = "w")

        # Surya-OCR 開關
        self.surya_ocr_sw_var = ctk.StringVar(value = "OFF")
        self.surya_ocr_sw = ctk.CTkCheckBox(
            self.f2, text = "Surya-OCR (多國語言)", height = 28, font = self.text_font, variable = self.surya_ocr_sw_var, 
            text_color_disabled = ["gray14", "gray84"], onvalue = "ON", offvalue = "OFF", command = self.activate_surya_ocr
        )
        self.surya_ocr_sw.grid(row = 0, column = 0, columnspan = 3, padx = 5, pady = (5, 0), sticky = "w")

        # 限定語言
        self.langs_wd = ctk.CTkLabel(self.f2, text = "限定語言 (可複選): ", font = self.text_font, anchor = "w")
        self.langs_wd.grid(row = 1, column = 1, columnspan = 2, padx = 5, pady = 0, sticky = "w")

        self.langs_zh_cb_var = ctk.StringVar(value = "OFF")
        self.langs_zh_cb = ctk.CTkCheckBox(
            self.f2, text = "中文", height = 28, font = self.text_font, variable = self.langs_zh_cb_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        self.langs_zh_cb.grid(row = 2, column = 1, padx = (5, 0), pady = 0, sticky = "w")

        self.langs_en_cb_var = ctk.StringVar(value = "OFF")
        self.langs_en_cb = ctk.CTkCheckBox(
            self.f2, text = "英文", height = 28, font = self.text_font, variable = self.langs_en_cb_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        self.langs_en_cb.grid(row = 3, column = 1, padx = (5, 0), pady = 5, sticky = "w")

        self.langs_ja_cb_var = ctk.StringVar(value = "OFF")
        self.langs_ja_cb = ctk.CTkCheckBox(
            self.f2, text = "日文", height = 28, font = self.text_font, variable = self.langs_ja_cb_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        self.langs_ja_cb.grid(row = 2, column = 2, padx = 5, pady = 0, sticky = "w")

        self.langs_ko_cb_var = ctk.StringVar(value = "OFF")
        self.langs_ko_cb = ctk.CTkCheckBox(
            self.f2, text = "韓文", height = 28, font = self.text_font, variable = self.langs_ko_cb_var, 
            onvalue = "ON", offvalue = "OFF", command = None
        )
        self.langs_ko_cb.grid(row = 3, column = 2, padx = 5, pady = 5, sticky = "w")

        # 精度設定
        # 自動/手動按鈕
        self.auto_dtype_bt = ctk.CTkButton(self.f2_1, text = "自動", font = self.text_font, width = 20, height = 25, anchor = "c", command = None)
        self.auto_dtype_bt.grid(row = 0, column = 0, padx = (5, 0), pady = 5, sticky = "ew")

        # 精度切換
        self.dtype_sw_var = ctk.StringVar(value = "float32" if force_cpu else "float16")
        self.current_dtype = self.dtype_sw_var.get()
        self.dtype_sw = ctk.CTkSwitch(self.f2_1, text = "模型精度: 全精度" if self.current_dtype == "float32" else "模型精度: 半精度", 
                                height = 28, corner_radius = 4, button_length = 10, font = self.text_font, 
                                variable = self.dtype_sw_var, onvalue = "float32", offvalue = "float16", command = None)
        self.dtype_sw.grid(row = 0, column = 1, padx = 5, pady = 0, sticky = "ns")
        self.dtype_sw.configure(state = "disabled" if self.auto_dtype == "ON" else "normal")

        # Manga-OCR 開關
        self.manga_ocr_sw_var = ctk.StringVar(value = "OFF")
        self.manga_ocr_sw = ctk.CTkCheckBox(
            self.f3, text = "Manga-OCR (日文漫畫)", height = 28, font = self.text_font, variable = self.manga_ocr_sw_var, 
            text_color_disabled = ["gray14", "gray84"], onvalue = "ON", offvalue = "OFF", command = self.activate_manga_ocr
        )
        self.manga_ocr_sw.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = "w")

        # 打開模型資料夾
        self.make_ink_bt = ctk.CTkButton(self.f4, text = "模型資料夾", font = self.text_font, width = 20, height = 25, anchor = "c", command = self.open_checkpoint_folder)
        self.make_ink_bt.grid(row = 0, column = 0, padx = (5, 0), pady = 5, sticky = "nwe")

        # 製作捷徑
        self.make_ink_bt = ctk.CTkButton(self.f4, text = "製作捷徑", font = self.text_font, width = 20, height = 25, anchor = "c", command = self.make_ink)
        self.make_ink_bt.grid(row = 0, column = 1, padx = (5, 0), pady = 5, sticky = "nwe")

        # 回復初始設定
        self.reset_bt = ctk.CTkButton(self.f4, text = "初始設定", font = self.text_font, width = 20, height = 25, anchor = "c", command = None)
        self.reset_bt.grid(row = 0, column = 2, padx = 5, pady = 5, sticky = "nwe")

        # 顯示版本號
        self.version_lab = ctk.CTkLabel(self.f4, text = "BeeSeeR 版本: v3.0.0 ", font = ctk.CTkFont(family = "Helvetica", size = 12), anchor = "e")
        self.version_lab.grid(row = 1, column = 0, columnspan = 3, padx = 5, pady = (0, 5), sticky = "es")

        # 初始化設定選項狀態 (Surya-OCR: 限定語言設定)
        if self.langs is not None:
            self.langs_zh_cb_var.set("ON" if "zh" in self.langs else "OFF")
            self.langs_en_cb_var.set("ON" if "en" in self.langs else "OFF")
            self.langs_ja_cb_var.set("ON" if "ja" in self.langs else "OFF")
            self.langs_ko_cb_var.set("ON" if "ko" in self.langs else "OFF")
        else:
            # 沒設定，全部 OFF
            self.langs_zh_cb_var.set("OFF")
            self.langs_en_cb_var.set("OFF")
            self.langs_ja_cb_var.set("OFF")
            self.langs_ko_cb_var.set("OFF")

        # 初始化設定選項狀態 (Surya-OCR: 精度切換)
        if force_cpu: self.auto_dtype_bt.configure(state = "disabled")
        if self.auto_dtype == "OFF": 
            self.auto_dtype_bt.configure(fg_color = "gray60", hover_color = ["#325882", "#A85820"])
            self.dtype_sw_var.set(self.dtype)
            self.dtype_sw.configure(text = "模型精度: 全精度" if self.dtype == "float32" else "模型精度: 半精度")
        else: 
            self.auto_dtype_bt.configure(fg_color = ["#1e8bba", "#C7712D"], hover_color = ["#325882", "#A85820"])
            self.dtype_sw_var.set("float32" if force_cpu else "float16")
            self.dtype_sw.configure(fg_color = "gray60", progress_color = "gray60", button_color = "gray60",
                            text = "模型精度: 全精度" if self.current_dtype == "float32" else "模型精度: 半精度")
            self.dtype_sw.configure(state = "disabled")

        # 初始化設定選項狀態 (Google-OCR: 開關)
        if self.ocr_model == "google":
            self.google_ocr_sw_var.set("ON")
            self.f2.configure(fg_color = ["gray88", "gray12"])
            self.f2_1.configure(fg_color = ["gray88", "gray12"])
            self.f3.configure(fg_color = ["gray88", "gray12"])
            self.google_ocr_sw.configure(state = "disabled")

        # 初始化設定選項狀態 (Manga-OCR: 開關)
        if self.ocr_model == "manga":
            self.manga_ocr_sw_var.set("ON")
            self.f1.configure(fg_color = ["gray88", "gray12"])
            self.f2.configure(fg_color = ["gray88", "gray12"])
            self.f2_1.configure(fg_color = ["gray88", "gray12"])
            self.manga_ocr_sw.configure(state = "disabled")

        # 初始化設定選項狀態 (Surya-OCR: 開關)
        if self.ocr_model == "surya":
            self.surya_ocr_sw_var.set("ON")
            self.f1.configure(fg_color = ["gray88", "gray12"])
            self.f3.configure(fg_color = ["gray88", "gray12"])
            self.surya_ocr_sw.configure(state = "disabled")

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
            "langs": self.langs,
            "ocr_model": self.ocr_model
        })

        # 將更新後的設定存回 JSON
        with open(os.path.join(PATH, "config.json"), "w") as f:
            json.dump(config, f, indent = 4)  # `indent = 4` 讓 JSON 易讀

    def activate_google_ocr(self):
        """啟用 Google OCR"""
        self.ocr_model = "google"
        self.f1.configure(fg_color = ["#d9d9e8", "#252930"])
        self.f2.configure(fg_color = ["gray88", "gray12"])
        self.f2_1.configure(fg_color = ["gray88", "gray12"])
        self.f3.configure(fg_color = ["gray88", "gray12"])
        self.google_ocr_sw.configure(state = "disabled")
        self.surya_ocr_sw_var.set("OFF")
        self.manga_ocr_sw_var.set("OFF")
        self.surya_ocr_sw.configure(state = "normal")
        self.manga_ocr_sw.configure(state = "normal")
        if self.on_activate: self.on_activate() # Callback 函數
        self.save_config()

    def activate_surya_ocr(self):
        """啟用 Surya OCR"""
        self.ocr_model = "surya"
        self.f1.configure(fg_color = ["gray88", "gray12"])
        self.f2.configure(fg_color = ["#d9d9e8", "#252930"])
        self.f2_1.configure(fg_color = ["#d9d9e8", "#252930"])
        self.f3.configure(fg_color = ["gray88", "gray12"])
        self.surya_ocr_sw.configure(state = "disabled")
        self.google_ocr_sw_var.set("OFF")
        self.manga_ocr_sw_var.set("OFF")
        self.google_ocr_sw.configure(state = "normal")
        self.manga_ocr_sw.configure(state = "normal")
        if self.on_activate: self.on_activate() # Callback 函數
        self.save_config()

    def activate_manga_ocr(self):
        """啟用 Manga OCR"""
        self.ocr_model = "manga"
        self.f1.configure(fg_color = ["gray88", "gray12"])
        self.f2.configure(fg_color = ["gray88", "gray12"])
        self.f2_1.configure(fg_color = ["gray88", "gray12"])
        self.f3.configure(fg_color = ["#d9d9e8", "#252930"])
        self.manga_ocr_sw.configure(state = "disabled")
        self.google_ocr_sw_var.set("OFF")
        self.surya_ocr_sw_var.set("OFF")
        self.google_ocr_sw.configure(state = "normal")
        self.surya_ocr_sw.configure(state = "normal")
        if self.on_activate: self.on_activate() # Callback 函數
        self.save_config()        

    def open_checkpoint_folder(self): 
        """打開 checkpoint 資料夾"""
        os.startfile(os.path.join(PATH, "checkpoint"))

    def make_ink(self):
        """製作快速啟動捷徑（尋找 BeeSeeR.exe，找不到時 fallback 為 .bat）"""
        from tkinter import filedialog, messagebox
        import win32com.client
        import shutil

        exe_path = shutil.which("BeeSeeR.exe")
        bat_path = None

        if exe_path:
            use_exe = True
            # print(f"找到 BeeSeeR.exe：{exe_path}")
        else:
            use_exe = False
            # messagebox.showinfo("未偵測到 BeeSeeR.exe", "請手動選擇 BeeSeeR.bat 檔案。")
            bat_path = filedialog.askopenfilename(
                filetypes=[("Batch Files", "*.bat")],
                initialdir=PATH,
                title="選擇 BeeSeeR 啟動用 .bat 檔"
            )
            if not bat_path:
                messagebox.showwarning("取消", "未選擇 .bat 檔案")
                return

        # 選取 icon
        icon_dir = os.path.join(PATH, "icon")
        if not os.path.exists(icon_dir):
            icon_dir = PATH  # fallback

        icon_path = filedialog.askopenfilename(
            filetypes=[("Icon Files", "*.ico")],
            initialdir=icon_dir,
            title="選擇 icon 檔"
        )

        if not icon_path:
            messagebox.showwarning("取消", "未選擇 icon 檔案")
            return

        # 選取儲存位置
        save_dir = filedialog.askdirectory(
            initialdir=PATH,
            title="選擇捷徑儲存位置"
        )

        if not save_dir:
            messagebox.showwarning("取消", "未選擇捷徑存放位置")
            return

        shortcut_path = os.path.join(save_dir, "BeeSeeR.lnk")

        def get_cmd_path():
            cmd_in_path = shutil.which("cmd.exe")
            if cmd_in_path:
                return "cmd.exe"
            fallback_path = os.path.join(os.environ["SystemRoot"], "System32", "cmd.exe")
            if os.path.exists(fallback_path):
                return fallback_path
            raise FileNotFoundError("找不到 cmd.exe")

        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(shortcut_path)

            if use_exe:
                shortcut.TargetPath = exe_path
                shortcut.Arguments = ""  # 不需要參數
                shortcut.WorkingDirectory = os.path.dirname(exe_path)
            else:
                shortcut.TargetPath = get_cmd_path()
                shortcut.Arguments = f'/c "{bat_path}"'
                shortcut.WorkingDirectory = os.path.dirname(bat_path)

            shortcut.IconLocation = icon_path
            shortcut.Save()
            messagebox.showinfo("完成", f"捷徑已儲存：\n{shortcut_path}")

        except Exception as e:
            messagebox.showerror("錯誤", f"建立捷徑失敗：{str(e)}") 
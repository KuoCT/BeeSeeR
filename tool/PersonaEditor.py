import customtkinter as ctk
from PIL import Image
import os
import json

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑

class PersonaEditor(ctk.CTkToplevel):
    w = 650
    h = 800
    def __init__(
            self,
            current_theme,
            width = None, 
            height = None,
            APPDATA = PATH
        ):
        super().__init__()

        self.title("人格指令編輯器")
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
        self.persona_file = self.settings.get("persona_file", None) # AI 人格與提示詞
        self.persona_save_path = self.settings.get("persona_save_path", None) # persona 設定檔儲存位置

        # 圖示
        self.png_add = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "add.png")), size = (20, 20))
        self.png_rm = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "rm.png")), size = (20, 20))

        # 區域規劃
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(0, weight = 1)

        self.f1 = ctk.CTkFrame(self)
        self.f1.grid(row = 0, column = 0, padx = 5, pady = (5, 0), sticky = "nswe")
        self.f1.grid_columnconfigure(0, weight = 1)
        self.f1.grid_rowconfigure((0, 2, 4, 6), weight = 0)
        self.f1.grid_rowconfigure((1, 3, 5, 7), weight = 1)

        self.f2 = ctk.CTkFrame(self)
        self.f2.grid(row = 1, column = 0, padx = 5, pady = (5, 0), sticky = "nswe")
        self.f2.grid_columnconfigure((0, 1, 2, 3, 4, 6), weight = 0)
        self.f2.grid_columnconfigure(5, weight = 1)
        self.f2.grid_rowconfigure((0, 1), weight = 0)

        # 顯示指令的文字框
        self.Translator_persona_wd = ctk.CTkLabel(self.f1, text = "• AI 翻譯時 - 人格指令:", height = 0, anchor = "w")
        self.Translator_persona_wd.grid(row = 0, column = 0, padx = 5, pady = (5, 0), sticky = "we")       
        self.Translator_persona_tb = ctk.CTkTextbox(self.f1, wrap = "char", corner_radius = 5)
        self.Translator_persona_tb.grid(row = 1, column = 0, padx = (15, 0), pady = 5, sticky = "nsew")

        self.Chat_persona_wd = ctk.CTkLabel(self.f1, text = "• AI 討論時 - 人格指令:", height = 0, anchor = "w")
        self.Chat_persona_wd.grid(row = 2, column = 0, padx = 5, pady = (5, 0), sticky = "we")
        self.Chat_persona_tb = ctk.CTkTextbox(self.f1, wrap = "char", corner_radius = 5)
        self.Chat_persona_tb.grid(row = 3, column = 0, padx = (15, 0), pady = 5, sticky = "nsew")

        self.Memory_persona_wd = ctk.CTkLabel(self.f1, text = "• AI 記憶時 - 人格指令:", height = 0, anchor = "w")
        self.Memory_persona_wd.grid(row = 4, column = 0, padx = 5, pady = (5, 0), sticky = "we")
        self.Memory_persona_tb = ctk.CTkTextbox(self.f1, wrap = "char", corner_radius = 5)
        self.Memory_persona_tb.grid(row = 5, column = 0, padx = (15, 0), pady = 5, sticky = "nsew")

        self.Prompt_wd = ctk.CTkLabel(self.f1, text = "• OCR → 翻譯 - 提示詞 (Prompt):", height = 0, anchor = "w")
        self.Prompt_wd.grid(row = 6, column = 0, padx = 5, pady = (5, 0), sticky = "we")
        self.Prompt_tb = ctk.CTkTextbox(self.f1, wrap = "char", corner_radius = 5)
        self.Prompt_tb.grid(row = 7, column = 0, padx = (15, 0), pady = 5, sticky = "nsew")

        # 綁定事件
        self.Translator_persona_tb._textbox.bind("<<Modified>>", lambda e: self.sync_textbox_to_persona('Translator_persona', self.Translator_persona_tb))
        self.Chat_persona_tb._textbox.bind("<<Modified>>", lambda e: self.sync_textbox_to_persona('Chat_persona', self.Chat_persona_tb))
        self.Memory_persona_tb._textbox.bind("<<Modified>>", lambda e: self.sync_textbox_to_persona('Memory_persona', self.Memory_persona_tb))
        self.Prompt_tb._textbox.bind("<<Modified>>", lambda e: self.sync_textbox_to_persona('Prompt', self.Prompt_tb))

        # 參數設定
        self.arg1_entry = ctk.CTkEntry(self.f2, height = 0, width = 80)
        self.arg1_entry.grid(row = 0, column = 0, padx = (20, 0), pady = (5, 0), sticky = "ns")
        self.arg1_cb = ctk.CTkComboBox(master = self.f2, height = 25, width = 120, values = [], command = self.sync_textbox_to_persona)
        self.arg1_cb.grid(row = 0, column = 2, padx = (5, 0), pady = (5, 0), sticky = "ns")
        self.arg1_addbt = ctk.CTkButton(self.f2, text = "", image = self.png_add, height = 25, width = 25, 
                                        command = lambda: self.update_combobox(self.arg1_cb, self.arg1_cb, "add"))
        self.arg1_addbt.grid(row = 0, column = 3, padx = (5, 0), pady = (5, 0), sticky = "ns")
        self.arg1_rmbt = ctk.CTkButton(self.f2, text = "", image = self.png_rm, height = 25, width = 25, 
                                       command = lambda: self.update_combobox(self.arg1_cb, self.arg1_cb, "remove"))
        self.arg1_rmbt.grid(row = 0, column = 4, padx = (5, 0), pady = (5, 0), sticky = "ns")

        self.arg2_entry = ctk.CTkEntry(self.f2, height = 0, width = 80)
        self.arg2_entry.grid(row = 1, column = 0, padx = (20, 0), pady = (5, 0), sticky = "ns")
        self.arg2_cb = ctk.CTkComboBox(master = self.f2, height = 25, width = 120, values = [], command = self.sync_textbox_to_persona)
        self.arg2_cb.grid(row = 1, column = 2, padx = (5, 0), pady = (5, 0), sticky = "ns")
        self.arg2_addbt = ctk.CTkButton(self.f2, text = "", image = self.png_add, height = 25, width = 25, 
                                        command = lambda: self.update_combobox(self.arg2_cb, self.arg2_cb, "add"))
        self.arg2_addbt.grid(row = 1, column = 3, padx = (5, 0), pady = (5, 0), sticky = "ns")
        self.arg2_rmbt = ctk.CTkButton(self.f2, text = "", image = self.png_rm, height = 25, width = 25, 
                                       command = lambda: self.update_combobox(self.arg2_cb, self.arg2_cb, "remove"))
        self.arg2_rmbt.grid(row = 1, column = 4, padx = (5, 0), pady = (5, 0), sticky = "ns")

        self.arg3_entry = ctk.CTkEntry(self.f2, height = 0, width = 80)
        self.arg3_entry.grid(row = 2, column = 0, padx = (20, 0), pady = (5, 0), sticky = "ns")
        self.arg3_cb = ctk.CTkComboBox(master = self.f2, height = 25, width = 120, values = [], command = self.sync_textbox_to_persona)
        self.arg3_cb.grid(row = 2, column = 2, padx = (5, 0), pady = (5, 0), sticky = "ns") 
        self.arg3_addbt = ctk.CTkButton(self.f2, text = "", image = self.png_add, height = 25, width = 25, 
                                        command = lambda: self.update_combobox(self.arg3_cb, self.arg3_cb, "add"))
        self.arg3_addbt.grid(row = 2, column = 3, padx = (5, 0), pady = (5, 0), sticky = "ns")
        self.arg3_rmbt = ctk.CTkButton(self.f2, text = "", image = self.png_rm, height = 25, width = 25, 
                                       command = lambda: self.update_combobox(self.arg3_cb, self.arg3_cb, "remove"))
        self.arg3_rmbt.grid(row = 2, column = 4, padx = (5, 0), pady = (5, 0), sticky = "ns")
        
        self.arg4_entry = ctk.CTkEntry(self.f2, height = 0, width = 80)
        self.arg4_entry.grid(row = 3, column = 0, padx = (20, 0), pady = 5, sticky = "ns")
        self.arg4_cb = ctk.CTkComboBox(master = self.f2, height = 25, width = 120, values = [], command = self.sync_textbox_to_persona)
        self.arg4_cb.grid(row = 3, column = 2, padx = (5, 0), pady = 5, sticky = "ns")
        self.arg4_addbt = ctk.CTkButton(self.f2, text = "", image = self.png_add, height = 25, width = 25, 
                                        command = lambda: self.update_combobox(self.arg4_cb, self.arg4_cb, "add"))
        self.arg4_addbt.grid(row = 3, column = 3, padx = (5, 0), pady = 5, sticky = "ns")
        self.arg4_rmbt = ctk.CTkButton(self.f2, text = "", image = self.png_rm, height = 25, width = 25, 
                                       command = lambda: self.update_combobox(self.arg4_cb, self.arg4_cb, "remove"))
        self.arg4_rmbt.grid(row = 3, column = 4, padx = (5, 0), pady = 5, sticky = "ns")

        self.arg_wd1 = ctk.CTkLabel(self.f2, text = "參數:", height = 0, anchor = "w")
        self.arg_wd1.grid(row = 0, column = 1, padx = (5, 0), pady = (5, 0), sticky = "we")
        self.arg_wd2 = ctk.CTkLabel(self.f2, text = "參數:", height = 0, anchor = "w")
        self.arg_wd2.grid(row = 1, column = 1, padx = (5, 0), pady = (5, 0), sticky = "we")
        self.arg_wd3 = ctk.CTkLabel(self.f2, text = "參數:", height = 0, anchor = "w")
        self.arg_wd3.grid(row = 2, column = 1, padx = (5, 0), pady = (5, 0), sticky = "we")
        self.arg_wd4 = ctk.CTkLabel(self.f2, text = "參數:", height = 0, anchor = "w")
        self.arg_wd4.grid(row = 3, column = 1, padx = (5, 0), pady = 5, sticky = "we")

        # 綁定使用者輸入的事件
        self.textboxes = [
            self.Translator_persona_tb,
            self.Chat_persona_tb,
            self.Memory_persona_tb,
            self.Prompt_tb,
        ]
        self.arg1_entry.bind("<Return>", lambda e: self.sync_textbox_to_persona(textboxs = self.textboxes, widget = self.arg1_entry))
        self.arg1_entry.bind("<FocusOut>", lambda e: self.sync_textbox_to_persona(textboxs = self.textboxes, widget = self.arg1_entry))
        self.widget_arg1 = self.arg1_cb._entry
        self.widget_arg1.bind("<Return>", lambda e: self.sync_textbox_to_persona(widget = self.arg1_cb))
        self.widget_arg1.bind("<FocusOut>", lambda e: self.sync_textbox_to_persona(widget = self.arg1_cb))

        self.arg2_entry.bind("<Return>", lambda e: self.sync_textbox_to_persona(textboxs = self.textboxes, widget = self.arg2_entry))
        self.arg2_entry.bind("<FocusOut>", lambda e: self.sync_textbox_to_persona(textboxs = self.textboxes, widget = self.arg2_entry))
        self.widget_arg2 = self.arg2_cb._entry
        self.widget_arg2.bind("<Return>", lambda e: self.sync_textbox_to_persona(widget = self.arg2_cb))
        self.widget_arg2.bind("<FocusOut>", lambda e: self.sync_textbox_to_persona(widget = self.arg2_cb))

        self.arg3_entry.bind("<Return>", lambda e: self.sync_textbox_to_persona(textboxs = self.textboxes, widget = self.arg3_entry))
        self.arg3_entry.bind("<FocusOut>", lambda e: self.sync_textbox_to_persona(textboxs = self.textboxes, widget = self.arg3_entry))
        self.widget_arg3 = self.arg3_cb._entry
        self.widget_arg3.bind("<Return>", lambda e: self.sync_textbox_to_persona(widget = self.arg3_cb))
        self.widget_arg3.bind("<FocusOut>", lambda e: self.sync_textbox_to_persona(widget = self.arg3_cb))

        self.arg4_entry.bind("<Return>", lambda e: self.sync_textbox_to_persona(textboxs = self.textboxes, widget = self.arg4_entry))
        self.arg4_entry.bind("<FocusOut>", lambda e: self.sync_textbox_to_persona(textboxs = self.textboxes, widget = self.arg4_entry))
        self.widget_arg4 = self.arg4_cb._entry
        self.widget_arg4.bind("<Return>", lambda e: self.sync_textbox_to_persona(widget = self.arg4_cb))
        self.widget_arg4.bind("<FocusOut>", lambda e: self.sync_textbox_to_persona(widget = self.arg4_cb))

        # 說明文字框
        self.args_info_tb = ctk.CTkTextbox(self.f2, wrap = "char", height = 0, corner_radius = 5)
        self.args_info_tb.grid(row = 0, rowspan = 4, column = 5, padx = (5, 0), pady = (5, 0), sticky = "nsew")
        info_text = ("◀ 佔位符說明:\n用雙大括弧包住{{佔位符}}，參數選項內的文字將會取代整個{{佔位符}}")
        self.args_info_tb.insert("1.0", info_text)
        self.args_info_tb.configure(state="disabled")

        # 控制按鈕
        self.read_persona_bt = ctk.CTkButton(self.f2, text = "讀取 Persona", width = 0, command = lambda: self.read_persona_file (dialog = True))
        self.read_persona_bt.grid(row = 0, column = 6, padx = 5, pady = (5, 0), sticky = "ew")

        self.save_persona_bt = ctk.CTkButton(self.f2, text = "儲存 Persona", width = 0, command = self.save_persona_file)
        self.save_persona_bt.grid(row = 1, column = 6, padx = 5, pady = (5, 0), sticky = "ew")

        self.save_persona_bt = ctk.CTkButton(self.f2, text = "打開資料夾", width = 0, command = lambda: os.startfile(os.path.join(self.APPDATA, "persona")))
        self.save_persona_bt.grid(row = 3, column = 6, padx = 5, pady = 5, sticky = "ew")

        # 初始化載入人格指令 (persona)
        self.read_persona_file()

    def load_config(self):
        """讀取設定檔案"""
        if os.path.exists(os.path.join(self.APPDATA, "config.json")):
            with open(os.path.join(self.APPDATA, "config.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        return {}  # 如果沒有設定檔，回傳空字典
    
    def save_config(self):
        """只有當設定異動時，才更新 config.json"""
        old_config = self.load_config()

        # 準備要寫入的內容
        new_config = {
            "persona_file": self.persona_file,
            "persona_save_path": self.persona_save_path
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

    def read_persona_file(self, dialog = False):
        """讀取 persona 設定檔，初始化或讓使用者選擇檔案"""
        
        if dialog:
            from tkinter import filedialog, messagebox
            # 跳出檔案選擇對話框
            initial_dir = self.persona_save_path if self.persona_save_path else os.path.join(self.APPDATA, "persona")
            file_path = filedialog.askopenfilename(
                filetypes = [("JSON Files", "*.json")],
                initialdir = initial_dir,
                title = "選擇 persona 設定檔"
            )
            if not file_path:  # 使用者取消
                return
            self.persona_file = file_path  # 記錄檔案路徑
            self.persona_save_path = os.path.dirname(file_path)  # 記錄目錄路徑
            self.save_config()  # 儲存設定檔
        else:
            # 初始化時 → 用設定檔或預設檔案
            if self.persona_file and not os.path.exists(self.persona_file):
                from tkinter import messagebox
                messagebox.showwarning("警告", "找不到 persona 設定檔，將使用預設 persona 檔案開啟。")
                fallback_file = os.path.join(self.APPDATA, "persona", "default_persona_zh.json")
                if not os.path.exists(fallback_file):
                    default_data = {
                        "Translator_persona": "You are a translator. Please translate into {{language}}, adapting for {{locale}}.",
                        "Chat_persona": "You are a friendly AI chat assistant speaking {{language}}.",
                        "Memory_persona": "Store translated pairs (source and translation in {{language}}).",
                        "Prompt": "Translate the following text into {{language}} for {{locale}}:"
                    }
                    os.makedirs(os.path.dirname(fallback_file), exist_ok = True)  # 確保資料夾存在
                    with open(fallback_file, "w", encoding = "utf-8") as f:
                        json.dump(default_data, f, ensure_ascii = False, indent = 4)

                    # 修補完成後提示
                    messagebox.showwarning("警告", "找不到預設 persona 設定檔，已臨時修補設定檔。\n建議至官網下載完整檔案以確保功能完整。")

                # 使用 fallback
                self.persona_file = fallback_file
                self.persona_save_path = os.path.dirname(fallback_file)
                self.save_config()

            if not self.persona_file:
                self.persona_file = os.path.join(self.APPDATA, "persona", "default_persona_zh.json")
                self.persona_save_path = os.path.dirname(self.persona_file)
                self.save_config()

        # 載入 persona
        _, self.persona = self.load_persona(self.persona_file)
        self.apply_args_to_widgets(self.persona) # 將 persona 中的參數設定給 UI

        # 更新 persona
        self.updated_persona, _ = self.load_persona(
            self.persona,
            self.arg1_cb.get(),
            self.arg2_cb.get(),
            self.arg3_cb.get(),
            self.arg4_cb.get()
        )
        self.update_textbox(force_update = True) # 強制更新畫面一次

    def save_persona_file(self):
        """儲存目前的 persona 到 JSON 檔案"""
        from tkinter import filedialog
        # 跳出儲存對話框
        initial_dir = self.persona_save_path if self.persona_save_path else os.path.join(self.APPDATA, "persona")
        file_path = filedialog.asksaveasfilename(
            defaultextension = ".json",
            filetypes = [("JSON Files", "*.json")],
            initialdir = initial_dir,
            title = "儲存 persona 設定檔"
        )
        if not file_path:  # 使用者取消
            return

        # 收集主要 persona 欄位內容
        persona_data = {
            "Translator_persona": self.Translator_persona_tb.get("1.0", "end-1c"),
            "Chat_persona": self.Chat_persona_tb.get("1.0", "end-1c"),
            "Memory_persona": self.Memory_persona_tb.get("1.0", "end-1c"),
            "Prompt": self.Prompt_tb.get("1.0", "end-1c"),
        }

        # 收集 arg1~arg4 的 name 和 options
        arg_mappings = [
            ("arg1", self.arg1_entry, self.arg1_cb),
            ("arg2", self.arg2_entry, self.arg2_cb),
            ("arg3", self.arg3_entry, self.arg3_cb),
            ("arg4", self.arg4_entry, self.arg4_cb),
        ]

        for key, entry_widget, combo_widget in arg_mappings:
            name = entry_widget.get()
            options = combo_widget.cget("values")
            persona_data[key] = {
                "name": name,
                "options": list(options) if isinstance(options, tuple) else options
            }

        # 寫入 JSON 檔案
        with open(file_path, "w", encoding = "utf-8") as f:
            json.dump(persona_data, f, ensure_ascii = False, indent = 4)

        # 記錄儲存路徑
        self.persona_file = file_path
        self.persona_save_path = os.path.dirname(file_path)
        self.save_config()  # 儲存設定檔

    def apply_args_to_widgets(self, persona_data: dict):
        """將 persona 中的 arg1~arg4 設定套用到 UI"""
        arg_mappings = [
            ("arg1", self.arg1_entry, self.arg1_cb),
            ("arg2", self.arg2_entry, self.arg2_cb),
            ("arg3", self.arg3_entry, self.arg3_cb),
            ("arg4", self.arg4_entry, self.arg4_cb),
        ]

        for key, entry_widget, combo_widget in arg_mappings:
            arg = persona_data.get(key, {})
            name = arg.get("name", "")
            options = arg.get("options", [])

            entry_widget.delete(0, "end")
            entry_widget.insert(0, name if name else "")
            combo_widget.configure(values = options)
            combo_widget.set(options[0] if options and options[0] else "")

    def load_persona(self, file_or_data, arg1="", arg2="", arg3="", arg4=""):

        """
        從 JSON 文件或已載入的 dict 變數載入 persona 提示詞，
        並根據參數替換相關的占位符 (例如: {{language}}, {{locale}})。

        Args:
            file_or_data (str or dict): JSON 檔案路徑或已載入的 persona dict。
            language (str): 翻譯語言 (例如: '繁體中文')。
            locale (str): 在地化 (例如: '台灣')。

        Returns:
            tuple: (updated_persona, original_persona)
        """
        # 判斷是檔案路徑還是 dict
        if isinstance(file_or_data, str):
            # 是路徑 → 讀取檔案
            with open(file_or_data, 'r', encoding='utf-8') as f:
                persona = json.load(f)
        elif isinstance(file_or_data, dict):
            # 是 dict → 直接使用
            persona = file_or_data
        else:
            raise ValueError("file_or_data 必須是檔案路徑 (str) 或 persona 字典 (dict)")
        
        # 預設值補齊
        if "arg1" not in persona:
            persona["arg1"] = {
                "name": "language",
                "options": ["繁體中文", "日本語", "English", "한국어"]
            }
        if "arg2" not in persona:
            persona["arg2"] = {
                "name": "locale",
                "options": ["台灣", "日本", "USA", "UK", "대한민국"]
            }
        
        # 建立佔位符對應
        arg_map = {}
        for i, val in enumerate([arg1, arg2, arg3, arg4], start = 1):
            arg_key = f"arg{i}"
            name = persona.get(arg_key, {}).get("name", "")
            if name:
                arg_map[name] = val

        # 替換 {{變數}} 的佔位符
        def replace_placeholders(text):
            for key, val in arg_map.items():
                text = text.replace(f"{{{{{key}}}}}", val)
            return text

        # 替換所有可用的 persona 字串欄位
        updated_persona = {
            k: replace_placeholders(v) if isinstance(v, str) else v
            for k, v in persona.items()
        }

        return updated_persona, persona

    def highlight_placeholders(self, textbox):
        """
        在 CTkTextbox 中 highlight 標示 persona 文字框中的 {{變數名稱}} 佔位符，支援 arg1~arg4 的名稱。

        Args:
            textbox (CTkTextbox): 目標 Textbox 控制項
        """
        text_widget = textbox._textbox  # 取得底層 tk.Text 物件

        # 先刪除已存在的標籤
        # text_widget.tag_delete("highlight")
        text_widget.tag_remove("highlight", "1.0", "end")

        # 設定標籤樣式
        text_widget.tag_configure("highlight", foreground = "#03A9F4")

        # 從 Entry 中取得佔位符名稱（不為空才加入）
        placeholder_names = [
            self.arg1_entry.get().strip(),
            self.arg2_entry.get().strip(),
            self.arg3_entry.get().strip(),
            self.arg4_entry.get().strip()
        ]
        placeholders = [f"{{{{{name}}}}}" for name in placeholder_names if name]

        # 對每個 placeholder 搜尋並標記
        for placeholder in placeholders:
            start_idx = "1.0"
            while True:
                pos = text_widget.search(placeholder, start_idx, stopindex = "end")
                if not pos:
                    break # 沒找到就結束
                end_idx = f"{pos}+{len(placeholder)}c"
                text_widget.tag_add("highlight", pos, end_idx)
                start_idx = end_idx # 繼續往後搜尋

    def update_textbox(self, force_update = False):
        """更新文字框，如果文字框內容與 persona 內容不同才更新"""
        
        def update_textbox_if_needed(textbox, new_content):
            # 取得目前文字框內容
            current_content = textbox.get("1.0", "end-1c")  # 去掉最後的換行符
            if current_content != new_content or force_update:
                # 清空並插入新內容
                textbox.delete("1.0", "end")
                textbox.insert("1.0", new_content)
                self.highlight_placeholders(textbox)  # highlight 占位符

        # 檢查並更新各個 textbox
        update_textbox_if_needed(self.Translator_persona_tb, self.persona['Translator_persona'])
        update_textbox_if_needed(self.Chat_persona_tb, self.persona['Chat_persona'])
        update_textbox_if_needed(self.Memory_persona_tb, self.persona['Memory_persona'])
        update_textbox_if_needed(self.Prompt_tb, self.persona['Prompt'])

    def sync_textbox_to_persona(self, key = None, textbox = None, textboxs = None, widget = None):
        """同步 textbox 編輯內容到 persona 並更新佔位符替換內容"""

        # 若有指定 key 和 textbox，將使用者編輯的內容更新進 persona 原始資料
        if key and textbox: 
            self.persona[key] = textbox.get("1.0", "end-1c")
        else:
            if widget: widget.master.focus_set() # 把焦點移開，讓游標從輸入框消失
            pass

        # 從目前 ComboBox 讀取參數值進行佔位符替換
        self.updated_persona, _ = self.load_persona(
            self.persona,
            self.arg1_cb.get(),
            self.arg2_cb.get(),
            self.arg3_cb.get(),
            self.arg4_cb.get()
        )

        if textbox: 
            self.highlight_placeholders(textbox)  # highlight 占位符
            textbox._textbox.edit_modified(False) # 重設 modified 狀態，避免無限觸發
            
        if textboxs: 
            for textbox in textboxs: 
                self.highlight_placeholders(textbox)  # highlight 占位符
                textbox._textbox.edit_modified(False) # 重設 modified 狀態，避免無限觸發

    def update_combobox(self, entry_widget, combobox_widget, action):
        """
        根據使用者輸入新增或刪除 ComboBox 的選項。
        
        Args:
            entry_widget (CTkEntry): 用戶輸入欄位（新增或刪除的項目）
            combobox_widget (CTkComboBox): 對應的下拉選單
            action (str): 動作類型，可為 "add" 或 "remove"
        """
        value = entry_widget.get().strip()
        if not value:
            return  # 空字串不處理

        current_values = list(combobox_widget.cget("values"))

        if action == "add":
            if value not in current_values:
                current_values.append(value)
                combobox_widget.configure(values = current_values)
                combobox_widget.set(value)  # 自動選取剛新增的值

        elif action == "remove":
            if value in current_values:
                current_values.remove(value)
                combobox_widget.configure(values = current_values)
                # 若當前值就是被刪除的值 → 重設為空
                if combobox_widget.get() == value:
                    combobox_widget.set(current_values[0] if current_values else "")

        # 從目前 ComboBox 讀取參數值進行佔位符替換
        self.sync_textbox_to_persona(widget = combobox_widget)
        self.update_textbox(force_update = True) # 更新顯示的佔位符替換結果
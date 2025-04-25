import customtkinter as ctk
import os
import json

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑

class PersonaEditor(ctk.CTkToplevel):
    w = 630
    h = 750
    def __init__(
            self,
            current_theme,
            width = None, 
            height = None
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
        self.settings = self.load_config()
        self.persona_file = self.settings.get("persona_file", None) # AI 人格與提示詞
        self.persona_save_path = self.settings.get("persona_save_path", None) # persona 設定檔儲存位置
        self.language = self.settings.get("language", ["繁體中文", "日本語", "English", "한국어"]) # 翻譯語言
        self.locale = self.settings.get("locale", ["台灣", "日本", "USA", "UK", "대한민국"]) # 在地化
        self.text_font = ctk.CTkFont(family = "Helvetica", size = 14, weight = "bold") # 設定字體

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
        self.f2.grid_columnconfigure((0, 1, 3), weight = 0)
        self.f2.grid_columnconfigure(2, weight = 1)
        self.f2.grid_rowconfigure((0, 1), weight = 0)

        # 顯示指令的文字框
        self.Translator_persona_wd = ctk.CTkLabel(self.f1, text = "• AI 翻譯時 - 人格指令:", font = self.text_font, height = 0, anchor = "w")
        self.Translator_persona_wd.grid(row = 0, column = 0, padx = 5, pady = (5, 0), sticky = "we")       
        self.Translator_persona_tb = ctk.CTkTextbox(self.f1, font = self.text_font, wrap = "word", corner_radius = 5)
        self.Translator_persona_tb.grid(row = 1, column = 0, padx = (15, 0), pady = 5, sticky = "nsew")

        self.Chat_persona_wd = ctk.CTkLabel(self.f1, text = "• AI 討論時 - 人格指令:", font = self.text_font, height = 0, anchor = "w")
        self.Chat_persona_wd.grid(row = 2, column = 0, padx = 5, pady = (5, 0), sticky = "we")
        self.Chat_persona_tb = ctk.CTkTextbox(self.f1, font = self.text_font, wrap = "word", corner_radius = 5)
        self.Chat_persona_tb.grid(row = 3, column = 0, padx = (15, 0), pady = 5, sticky = "nsew")

        self.Memory_persona_wd = ctk.CTkLabel(self.f1, text = "• AI 記憶時 - 人格指令:", font = self.text_font, height = 0, anchor = "w")
        self.Memory_persona_wd.grid(row = 4, column = 0, padx = 5, pady = (5, 0), sticky = "we")
        self.Memory_persona_tb = ctk.CTkTextbox(self.f1, font = self.text_font, wrap = "word", corner_radius = 5)
        self.Memory_persona_tb.grid(row = 5, column = 0, padx = (15, 0), pady = 5, sticky = "nsew")

        self.Prompt_wd = ctk.CTkLabel(self.f1, text = "• OCR → 翻譯 - 提示詞 (Prompt):", font = self.text_font, height = 0, anchor = "w")
        self.Prompt_wd.grid(row = 6, column = 0, padx = 5, pady = (5, 0), sticky = "we")
        self.Prompt_tb = ctk.CTkTextbox(self.f1, font = self.text_font, wrap = "word", corner_radius = 5)
        self.Prompt_tb.grid(row = 7, column = 0, padx = (15, 0), pady = 5, sticky = "nsew")

        # 綁定事件
        self.Translator_persona_tb._textbox.bind("<<Modified>>", lambda e: self.sync_textbox_to_persona('Translator_persona', self.Translator_persona_tb))
        self.Chat_persona_tb._textbox.bind("<<Modified>>", lambda e: self.sync_textbox_to_persona('Chat_persona', self.Chat_persona_tb))
        self.Memory_persona_tb._textbox.bind("<<Modified>>", lambda e: self.sync_textbox_to_persona('Memory_persona', self.Memory_persona_tb))
        self.Prompt_tb._textbox.bind("<<Modified>>", lambda e: self.sync_textbox_to_persona('Prompt', self.Prompt_tb))

        # 參數設定
        self.language_wd = ctk.CTkLabel(self.f2, text = "language 參數:", font = self.text_font, height = 0, anchor = "e")
        self.language_wd.grid(row = 0, column = 0, padx = (5, 0), pady = (5, 0), sticky = "we")
        self.language_cb = ctk.CTkComboBox(
            master = self.f2, 
            values = self.language,
            command = self.sync_textbox_to_persona
        )
        self.language_cb.grid(row = 0, column = 1, padx = (5, 0), pady = (5, 0), sticky = "we")
        self.language_cb.set(self.language[0])

        self.locale_wd = ctk.CTkLabel(self.f2, text = "locale 參數:", font = self.text_font, height = 0, anchor = "e")
        self.locale_wd.grid(row = 1, column = 0, padx = (5, 0), pady = (5, 0), sticky = "we")  
        self.locale_cb = ctk.CTkComboBox(
            master = self.f2,
            values = self.locale,
            command = self.sync_textbox_to_persona
        )
        self.locale_cb.grid(row = 1, column = 1, padx = (5, 0), pady = 5, sticky = "we")
        self.locale_cb.set(self.locale[0])

        # 綁定使用者輸入的事件
        self.widget_lang = self.language_cb._entry
        self.widget_lang.bind("<Return>", lambda e: self.sync_textbox_to_persona(widget = self.language_cb))
        self.widget_lang.bind("<FocusOut>", lambda e: self.sync_textbox_to_persona(widget = self.locale_cb))

        self.widget_locale = self.locale_cb._entry
        self.widget_locale.bind("<Return>", lambda e: self.sync_textbox_to_persona(widget = self.locale_cb))
        self.widget_locale.bind("<FocusOut>", lambda e: self.sync_textbox_to_persona(widget = self.locale_cb))

        # 說明文字框
        self.args_info_tb = ctk.CTkTextbox(self.f2, font = self.text_font, wrap = "word", height = 0, corner_radius = 5)
        self.args_info_tb.grid(row = 0, rowspan = 2, column = 2, padx = (5, 0), pady = (5, 0), sticky = "nsew")
        info_text = ("說明: 參數選項內的文字會替代指令中 highlight 的文字，使用 {{雙大括弧}} 包住參數即可在任意地方使用")
        self.args_info_tb.insert("1.0", info_text)
        self.args_info_tb.configure(state="disabled")

        # 控制按鈕
        self.read_persona_bt = ctk.CTkButton(self.f2, text = "讀取設定", font = self.text_font, width = 0, command = lambda: self.read_persona_file (dialog = True))
        self.read_persona_bt.grid(row = 0, column = 3, padx = 5, pady = (5, 0), sticky = "ns")

        self.save_persona_bt = ctk.CTkButton(self.f2, text = "儲存設定", font = self.text_font, width = 0, command = self.save_persona_file)
        self.save_persona_bt.grid(row = 1, column = 3, padx = 5, pady = 5, sticky = "ns")

        # 初始化人格指令
        self.read_persona_file()
        self.updated_persona, self.persona = self.load_persona(self.persona_file, self.language_cb.get(), self.locale_cb.get())
        self.update_textbox()

    def load_config(self):
        """讀取設定檔案"""
        if os.path.exists(os.path.join(PATH, "config.json")):
            with open(os.path.join(PATH, "config.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        return {}  # 如果沒有設定檔，回傳空字典
    
    def save_config(self):
        """只有當設定異動時，才更新 config.json"""
        old_config = self.load_config()

        # 準備要寫入的內容
        new_config = {
            "persona_file": self.persona_file,
            "persona_save_path": self.persona_save_path,
            "language": self.language,
            "locale": self.locale
        }

        # 只有內容不同時才寫入
        if old_config != {**old_config, **new_config}:
            old_config.update(new_config)
            with open(os.path.join(PATH, "config.json"), "w", encoding = "utf-8") as f:
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
            initial_dir = self.persona_save_path if self.persona_save_path else os.path.join(PATH, "persona")
            file_path = filedialog.askopenfilename(
                filetypes = [("JSON Files", "*.json")],
                initialdir = initial_dir,
                title = "選擇 persona 設定檔"
            )
            if not file_path:  # 使用者取消
                return
            self.persona_file = file_path  # 記錄檔案路徑
            self.save_config()  # 儲存設定檔

            # 載入 persona 並更新畫面
            self.updated_persona, self.persona = self.load_persona(
                self.persona_file,
                self.language_cb.get(),
                self.locale_cb.get()
            )
            self.update_textbox(force_update = True)  # 強制更新文字框
        else:
            # 初始化時 → 用設定檔或預設檔案
            if self.persona_file and not os.path.exists(self.persona_file):
                from tkinter import messagebox
                messagebox.showwarning("警告", "找不到 persona 設定檔，將使用預設 persona 檔案開啟。")
                fallback_file = os.path.join(PATH, "persona", "default_persona.json")
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
                    messagebox.showwarning("警告", "找不到預設 persona 設定檔，已臨時修補設定檔。\n建議至官網下載完整預設設定檔以確保功能完整。")

                # 使用 fallback
                self.persona_file = fallback_file
                self.save_config()

            if not self.persona_file:
                self.persona_file = os.path.join(PATH, "persona", "default_persona.json")

    def save_persona_file(self):
        """儲存目前的 persona 到 JSON 檔案"""
        from tkinter import filedialog
        # 跳出儲存對話框
        initial_dir = self.persona_save_path if self.persona_save_path else os.path.join(PATH, "persona")
        file_path = filedialog.asksaveasfilename(
            defaultextension = ".json",
            filetypes = [("JSON Files", "*.json")],
            initialdir = initial_dir,
            title = "儲存 persona 設定檔"
        )
        if not file_path:  # 使用者取消
            return

        # 收集四個 textbox 的內容
        persona_data = {
            "Translator_persona": self.Translator_persona_tb.get("1.0", "end-1c"),
            "Chat_persona": self.Chat_persona_tb.get("1.0", "end-1c"),
            "Memory_persona": self.Memory_persona_tb.get("1.0", "end-1c"),
            "Prompt": self.Prompt_tb.get("1.0", "end-1c")
        }

        # 寫入 JSON 檔案
        with open(file_path, "w", encoding = "utf-8") as f:
            json.dump(persona_data, f, ensure_ascii = False, indent = 4)

        # 記錄儲存路徑
        self.persona_save_path = file_path
        self.save_config()  # 儲存設定檔

    def load_persona(self, file_or_data, language, locale):
        """
        從 JSON 文件或已載入的 dict 變數載入 persona 提示詞，
        並根據參數替換語言相關的占位符(例如: {{language}}, {{locale}})。

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

        # 定義占位符替換函數
        def replace_placeholders(text):
            return (text
                    .replace('{{language}}', language)
                    .replace('{{locale}}', locale))

        # 替換 persona 中所有字串
        updated_persona = {key: replace_placeholders(value)
                        for key, value in persona.items()}

        return updated_persona, persona

    def highlight_placeholders(self, textbox):
        """
        在 CTkTextbox 中 highlight {{language}} 和 {{locale}} 占位符。

        Args:
            textbox (CTkTextbox): 目標 Textbox 控制項
        """
        text_widget = textbox._textbox  # 取得底層 tk.Text 物件

        # 先刪除已存在的標籤
        text_widget.tag_delete("highlight")

        # 設定標籤樣式
        text_widget.tag_configure("highlight", foreground = "#03A9F4", font = ctk.CTkFont("Helvetica", 14, "bold"))

        # 搜尋並標記 {{language}} 和 {{locale}}
        for placeholder in ["{{language}}", "{{locale}}"]:
            start_idx = "1.0"
            while True:
                pos = text_widget.search(placeholder, start_idx, stopindex = "end")
                if not pos:
                    break  # 沒找到就結束
                end_idx = f"{pos}+{len(placeholder)}c"
                text_widget.tag_add("highlight", pos, end_idx)
                start_idx = end_idx  # 繼續往後搜尋

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

    def sync_textbox_to_persona(self, key = None, textbox = None, widget = None):
        """同步指定 textbox 的內容到 persona"""
        # 更新 persona
        if key and textbox: 
            self.persona[key] = textbox.get("1.0", "end-1c")
        else:
            if widget: widget.master.focus_set() # 把焦點移開，讓游標從輸入框消失
            pass

        # 重新載入 updated_persona（進行佔位符替換）
        self.updated_persona, _ = self.load_persona(
            self.persona, 
            self.language_cb.get(), 
            self.locale_cb.get()
        )

        if textbox: 
            self.highlight_placeholders(textbox)  # highlight 占位符
            textbox._textbox.edit_modified(False) # 重設 modified 狀態，避免無限觸發
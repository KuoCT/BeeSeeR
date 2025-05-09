import os
import json
import colorama
import markdown
import customtkinter as ctk
import tool.patchedcustomtkinter as pctk
from bs4 import BeautifulSoup
import threading

colorama.init() # 讓文字有顏色

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑

class chatroomWindow(ctk.CTkToplevel):
    def __init__(
            self, 
            current_theme, 
            chat_session = None,
            groq_key = None,
            on_activate = None,
            on_link_persona = None,
            APPDATA = PATH
        ):
        super().__init__()

        # Callbask 函數
        self.on_activate = on_activate # 更新主視窗的 token 計數器
        self.on_link_persona = on_link_persona # 連結 persona 指令集

        # 讀取設定
        self.APPDATA = APPDATA
        self.settings  = self.load_config()
        self.chat_font_size = self.settings.get("chat_font_size", 14) # 文字大小
        self.chat_save_path = self.settings.get("chat_save_path", APPDATA) # 初始化儲存位置
        self.message_font = ctk.CTkFont(size = self.chat_font_size)

        self.updated_persona = None # 初始化 persona
        self.prompt_tokens = 0 # 初始化 token 計數器
        self.completion_tokens = 0 # 初始化 token 計數器
        self.chatlog =  "" # 初始化對話紀錄
        self.user_input = "" # 初始化聊天輸入
        self.groq_key = groq_key
        self.model = "llama-3.3-70b-versatile"
        self.enable_short_term_memory = True
        self.max_history = 3
        self.temperature = 0.6
        self.silent = True
        self.current_theme = current_theme

        if chat_session is None:
            import llm.chat as chat
            self.chat_session = chat.GroqChatSession(
                groq_key = self.groq_key, 
                model = self.model, 
                enable_short_term_memory= self.enable_short_term_memory, 
                max_history = self.max_history, 
                temperature = self.temperature,
                silent = self.silent
            )
        else:
            self.chat_session = chat_session

        # 設定視窗
        self.title("聊天室 / 翻譯紀錄")
        self.geometry("630x750")
        self.attributes("-topmost", False) # 讓視窗顯示在最前面
        self.withdraw() # 聊天室視窗預設隱藏
        self.protocol("WM_DELETE_WINDOW", self.withdraw) # 攔截關閉行為 → 改為隱藏（withdraw）
        self.after( # icon 一致化
            250, 
            self.iconbitmap, 
            os.path.join(PATH, "icon/logo_dark.ico") if current_theme == "dark" else os.path.join(PATH, "icon/logo_light.ico")
        )

        # 設定 Grid 佈局
        self.grid_rowconfigure(0, weight = 20)
        self.grid_rowconfigure(1, weight = 0, minsize = 150)
        self.grid_columnconfigure(0, weight = 1)

        # 訊息泡泡區域
        self.text_f = ctk.CTkScrollableFrame(self, fg_color = ["#d9d9e8", "#252930"])
        self.text_f.grid(row = 0, column = 0, padx = 5, pady = (5, 0), sticky = "nsew")
        self.text_f.grid_rowconfigure(0, weight = 1)
        self.text_f.grid_columnconfigure(0, weight = 1)

        # 打字區域
        self.type_f = ctk.CTkFrame(self, fg_color = ["#d9d9e8", "#252930"])
        self.type_f.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = "nsew")
        self.type_f.grid_rowconfigure((0, 1, 2), weight = 0)
        self.type_f.grid_rowconfigure(3, weight = 1)
        self.type_f.grid_columnconfigure(0, weight = 1)
        self.type_f.grid_columnconfigure(1, weight = 0)

        # 可捲動文字框
        self.textbox = pctk.CTkTextbox(self.type_f, font = self.message_font, wrap = "char", corner_radius = 5, height = 100)
        self.textbox.grid(row = 0, rowspan = 4, column = 0, padx = (5, 0), pady = 5, sticky = "nsew")
        self.textbox.bind("<Return>", self.on_return_key) # 綁定 Enter 鍵

        # 功能按鈕
        self.increase_bt = ctk.CTkButton(
            self.type_f, 
            text = "字放大", 
            width = 60, 
            height = 20, 
            corner_radius = 4,
            command = self.increase_font_size
        )
        self.increase_bt.grid(row = 0, column = 1, padx = 5, pady = (5, 0), sticky = "ns")

        self.decrease_bt = ctk.CTkButton(
            self.type_f, 
            text = "字縮小", 
            width = 60, 
            height = 20, 
            corner_radius = 4,
            command = self.decrease_font_size
        )
        self.decrease_bt.grid(row = 1, column = 1, padx = 5, pady = (2, 0), sticky = "ns")

        self.savelog_bt = ctk.CTkButton(
                    self.type_f, 
                    text = "存檔", 
                    width = 60, 
                    height = 20, 
                    corner_radius = 4,
                    command = self.save_chatlog
                )
        self.savelog_bt.grid(row = 2, column = 1, padx = 5, pady = (2, 0), sticky = "ns")

        self.input_bt = ctk.CTkButton(
            self.type_f, 
            text = "送出", 
            width = 60, 
            height = 20, 
            corner_radius = 4,
            command = self.talk_to_llm
        )
        self.input_bt.grid(row = 3, column = 1, padx = 5, pady = (2, 5), sticky = "ns")
    
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
            "chat_font_size": self.chat_font_size,
            "chat_save_path": self.chat_save_path
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

    def append_chatbubble(self, role, message):
        """新增對話泡泡，支援點擊展開選取視窗"""
        # 根據角色決定顏色與對齊
        if role == "User":
            anchor_side = "e"
            border_width = 2
            wraplength = 420
            color = ["gray90", "gray15"]
            b_fill = "none"
            b_expand = False
        else:
            anchor_side = "c"
            wraplength = 560
            border_width = 0
            color = ["#d9d9e8", "#252930"]
            b_fill = "x"
            b_expand = True

        # 泡泡框框
        bubble_frame = ctk.CTkFrame(
            self.text_f, 
            fg_color = color,
            corner_radius = 10,
            border_width = border_width
        )

        # 對話內容
        text = ctk.CTkLabel(
            bubble_frame, 
            text = self.markdown_to_plaintext(message), 
            font = self.message_font,
            wraplength = wraplength, 
            justify = "left"
        )

        text.pack(anchor = "w", padx = 10, pady = 5)

        # 綁定點擊 → 展開 Toplevel 供選取
        text.bind("<Button-1>", lambda e: self.show_popup(e, message))

        # 對齊左右並加內邊距
        bubble_frame.pack(anchor = anchor_side, pady = 5, padx = (5, 0), fill = b_fill, expand = b_expand)

        # 自動捲動到底部
        self.update_idletasks()  # 確保渲染完成
        self.text_f._parent_canvas.yview_moveto(1.0)

        return bubble_frame

        # # 回傳包含 bubble_frame 與 text 控制項（未來可更新）
        # return {
        #     "frame": bubble_frame,
        #     "label": text,
        #     "role": role
        # }
    
    def replace_chatbubble(self, bubble_obj, new_message):
        """更新指定 chat bubble 的內容文字"""
        if not bubble_obj or "label" not in bubble_obj:
            return

        new_text = self.markdown_to_plaintext(new_message)
        bubble_obj["label"].configure(text = new_text)

        # 自動捲動到底部
        self.update_idletasks()  # 確保渲染完成
        self.text_f._parent_canvas.yview_moveto(1.0)

    def show_popup(self, event, message):
        """點擊時展開 Toplevel 供選取"""
        popup = ctk.CTkToplevel(self)
        popup.title("對話內容")

        # 設定彈出視窗的寬高
        popup_width = 400
        popup_height = 200

        # 計算讓滑鼠點擊位置在視窗中心
        x = event.x_root - popup_width // 2
        y = event.y_root

        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        popup.attributes("-topmost", True) # 讓視窗顯示在最前面
        popup.after(250, popup.iconbitmap, 
                (
                    os.path.join(PATH, "icon", "logo_dark.ico") 
                    if self.current_theme == "dark" 
                    else os.path.join(PATH, "icon", "logo_light.ico")
                )
        )

        textbox = ctk.CTkTextbox(popup, wrap = "char", width = 400, height = 200)
        textbox.pack(padx = 5, pady = 5, fill = "both", expand = True)
        textbox.insert("1.0", message)
        textbox.configure(state="disabled")

    def markdown_to_plaintext(self, md_text):
        """Markdown 轉純文字，保留結構且項目之間僅單換行"""
        # Markdown 轉 HTML
        html = markdown.markdown(md_text)
        soup = BeautifulSoup(html, features = "html.parser")

        # 處理 <li><p> → 插入 • 符號
        for li in soup.find_all("li"):
            p = li.find("p")
            if p:
                p.insert(0, "• ")  # 插入符號
            else:
                li.insert(0, "• ")
            li.append("\n")

        # 段落 <p> 統一加換行（跳過 <li> 內部）
        for p in soup.find_all("p"):
            if not p.find_parent("li"):
                p.append("\n")

        # <br> → \n
        for br in soup.find_all("br"):
            br.replace_with("\n")

        plain_text = soup.get_text()
        return plain_text.strip()
    
    def increase_font_size(self):
        """增加字體大小"""
        self.chat_font_size += 2
        self.message_font.configure(size = self.chat_font_size)
        self.save_config()

    def decrease_font_size(self):
        """減少字體大小"""
        if self.chat_font_size > 10:  # 避免字體過小
            self.chat_font_size -= 2
            self.message_font.configure(size = self.chat_font_size)
            self.save_config()

    def update_all_chat_bubbles_font(self):
        """遍歷所有泡泡區中的 Label，更新其字體大小"""
        for child in self.text_f.winfo_children():
            # child 是 bubble_frame
            for grandchild in child.winfo_children():
                if isinstance(grandchild, ctk.CTkLabel):
                    grandchild.configure(font = ("Helvetica", self.chat_font_size))
           
    def on_return_key(self, event):
        if event.state & 0x0001:  # Shift+Enter 換行
            self.textbox.insert("insert", "\n")
        else:  # 單獨 Enter：送出
            self.talk_to_llm()
        return "break"
        
    # def talk_to_llm(self, event = None):
    #     """輸入文字與模型對話"""
    #     self.on_link_persona() # 連接 persona
    #     persona = self.updated_persona # 傳入 persona
    #     self.user_input = self.textbox.get("0.0", "end").strip()
    #     if self.user_input: # 避免空輸入
    #         self.append_chatbubble(role = "User", message = self.user_input)
    #         self.append_chatlog(role = "User", message = self.user_input)
    #         self.textbox.delete("0.0", "end")  # 清空輸入框內容
    #         print(f"\n\033[33m[INFO] 使用者輸入：\033[0m")
    #         print(self.user_input)
    #         system_prompt = persona["Chat_persona"]
    #         memory_prompt = persona["Memory_persona"]
    #         response, prompt_tokens, completion_tokens = self.chat_session.send_to_groq(
    #             system_prompt, 
    #             memory_prompt, 
    #             user_prompt = None, 
    #             user_input = self.user_input
    #         )
    #         self.prompt_tokens = prompt_tokens
    #         self.completion_tokens = completion_tokens
    #         self.append_chatbubble(role = self.chat_session.model, message = response)
    #         self.append_chatlog(role = self.chat_session.model, message = response)
    #         # 呼叫 callback → 通知主視窗更新 token 顯示
    #         if self.on_activate:
    #             self.on_activate(prompt_tokens, completion_tokens)

    def talk_to_llm(self, event = None):
        """輸入文字與模型對話（非同步）"""
        self.on_link_persona() # 連接 persona
        persona = self.updated_persona # 傳入 persona
        self.user_input = self.textbox.get("0.0", "end").strip()

        if not self.user_input: # 避免空輸入
            return

        self.append_chatbubble(role = "User", message = self.user_input)
        self.append_chatlog(role = "User", message = self.user_input)
        self.textbox.delete("0.0", "end") # 清空輸入框內容
        print(f"\n\033[33m[INFO] 使用者輸入：\033[0m")
        print(self.user_input)

        # 準備傳送資料給 AI 分析，先鎖定輸入防止多次傳入，並且提示 AI 正在思考，等 AI 開始回應後刪除該文字
        # 顯示 AI 處理中提示，並暫存 ID
        self.thinking_bubble = self.append_chatbubble(role = self.chat_session.model, message = "思考中…")


        # 建立背景執行緒處理 send_to_groq
        thread = threading.Thread(
            target = self._background_send_to_groq,
            args = (persona["Chat_persona"], persona["Memory_persona"], self.user_input),
            daemon = True
        )
        thread.start()

    def _background_send_to_groq(self, system_prompt, memory_prompt, user_input):
        """背景執行 send_to_groq，完成後傳回主線程更新 UI"""
        try:
            response, prompt_tokens, completion_tokens = self.chat_session.send_to_groq(
                system_prompt,
                memory_prompt,
                user_prompt = None,
                user_input = user_input
            )
        except Exception as e:
            response, prompt_tokens, completion_tokens = f"[ERROR] 模型回應失敗: {e}", 0, 0

        # 回主線程更新 UI
        self.textbox.after(0, lambda: self._update_ui_with_response(response, prompt_tokens, completion_tokens))

    def _update_ui_with_response(self, response, prompt_tokens, completion_tokens):
        """主線程中更新 UI 元件"""
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

        # 取代 AI 處理中提示
        if hasattr(self, "thinking_bubble"):
            self.thinking_bubble.destroy()
            del self.thinking_bubble

        self.append_chatbubble(role = self.chat_session.model, message = response)
        self.append_chatlog(role = self.chat_session.model, message = response)

        if self.on_activate:
            self.on_activate(prompt_tokens, completion_tokens)
    
    def append_chatlog(self, role, message):
        """將單筆對話追加到 chatlog"""
        # 格式化為 Markdown 格式並加上換行
        log_entry = f"##{' '}{role}:{'  '}\n{message}\n\n"
        self.chatlog += log_entry
    
    def save_chatlog(self):
        """將 chatlog 儲存為 Markdown 檔案"""
        import tkinter.filedialog as fd
        from datetime import datetime
         # 取得當前日期時間字串
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        
        # 組合預設檔名
        default_filename = f"{timestamp}_對話紀錄.md"

        # 調出儲存對話框
        filepath = fd.asksaveasfilename(
            defaultextension = ".md",
            filetypes = [("Markdown files", "*.md"), ("All files", "*.*")],
            title = "Save Chatlog",
            initialfile = default_filename,
            initialdir = self.chat_save_path
        )

        if filepath:  # 若使用者有選擇檔案
            try:
                with open(filepath, 'w', encoding = 'utf-8') as file:
                    file.write(self.chatlog)
                self.chat_save_path = os.path.dirname(filepath) # 記錄新儲存路徑
                self.save_config()
                print(f"\033[32m[INFO] 對話紀錄已儲存至: {filepath}\033[0m")
            except Exception as e:
                print(f"\033[31m[ERROR] 儲存對話紀錄失敗: {e}\033[0m")
        else:
            # print("Save operation cancelled.")
            pass
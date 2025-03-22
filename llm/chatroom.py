import os
import json
import colorama
import markdown
import customtkinter as ctk
from bs4 import BeautifulSoup

colorama.init() # 讓文字有顏色

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json") # 設定檔案名稱
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑

class chatroomWindow(ctk.CTkToplevel):
    def __init__(
            self, 
            current_theme, 
            chat_session = None,
            groq_key = None
        ):
        super().__init__()

        ctk.set_default_color_theme(os.path.join(PATH, "theme/nectar.json"))

        self.settings  = self.load_config()
        self.font_size = 18 # 文字大小
        self.prompt_tokens = 0 # 初始化 token 計數器
        self.completion_tokens = 0 # 初始化 token 計數器
        self.chatlog =  "" # 初始化對話紀錄
        self.user_input = "" # 初始化聊天輸入
        self.message_font = ctk.CTkFont(family = "Helvetica", size = self.font_size, weight = "bold")
        text_fix_font = ctk.CTkFont(family = "Helvetica", size = 16, weight = "bold")

        self.groq_key = groq_key
        self.model = "llama-3.3-70b-versatile"
        self.enable_short_term_memory = True
        self.max_history = 3
        self.temperature = 0.6
        self.silent = True

        if chat_session is None:
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
        self.title("聊天室")
        self.geometry("600x750")
        self.attributes("-topmost", False) # 讓視窗顯示在最前面
        self.after( # icon 一致化
            250, 
            self.iconbitmap, 
            os.path.join(PATH, "icon/logo_dark.ico") if current_theme == "dark" else os.path.join(PATH, "icon/logo_light.ico")
        )

        # 設定 Grid 佈局
        self.grid_rowconfigure(0, weight = 20)
        self.grid_rowconfigure(1, weight = 1, minsize = 50)
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
        self.textbox = ctk.CTkTextbox(self.type_f, font = self.message_font, wrap = "word", corner_radius = 5, height = 100)
        self.textbox.grid(row = 0, rowspan = 4, column = 0, padx = (5, 0), pady = 5, sticky = "nsew")

        # 功能按鈕
        self.increase_bt = ctk.CTkButton(
            self.type_f, 
            text = "字放大", 
            width = 60, 
            height = 20, 
            corner_radius = 4,
            font = text_fix_font, 
            command = None
        )
        self.increase_bt.grid(row = 0, column = 1, padx = 5, pady = (5, 0), sticky = "ns")

        self.decrease_bt = ctk.CTkButton(
            self.type_f, 
            text = "字縮小", 
            width = 60, 
            height = 20, 
            corner_radius = 4,
            font = text_fix_font, 
            command = None
        )
        self.decrease_bt.grid(row = 1, column = 1, padx = 5, pady = (2, 0), sticky = "ns")

        self.savelog_bt = ctk.CTkButton(
                    self.type_f, 
                    text = "存檔", 
                    width = 60, 
                    height = 20, 
                    corner_radius = 4,
                    font = text_fix_font, 
                    command = None
                )
        self.savelog_bt.grid(row = 2, column = 1, padx = 5, pady = (2, 0), sticky = "ns")

        self.input_bt = ctk.CTkButton(
            self.type_f, 
            text = "送出", 
            width = 60, 
            height = 20, 
            corner_radius = 4,
            font = text_fix_font, 
            command = self.talk_to_llm
        )
        self.input_bt.grid(row = 3, column = 1, padx = 5, pady = (2, 5), sticky = "ns")
    
    def load_config(self):
        """讀取設定檔案"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {}  # 如果沒有設定檔，回傳空字典

    def append_chatbubble(self, role, message):
        """新增對話泡泡"""
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
            wraplength = 540
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

        # 對齊左右並加內邊距
        bubble_frame.pack(anchor = anchor_side, pady = 5, padx = (5, 0), fill = b_fill, expand = b_expand)

        # 自動捲動到底部
        self.update_idletasks()  # 確保渲染完成
        self.text_f._parent_canvas.yview_moveto(1.0)

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

        # 段落 <p> 統一加換行（跳過 <li> 內部）
        for p in soup.find_all("p"):
            if not p.find_parent("li"):
                p.append("\n")

        # <br> → \n
        for br in soup.find_all("br"):
            br.replace_with("\n")

        plain_text = soup.get_text()

        return plain_text.strip()
    
    def load_prompt(self, file):
        """ 從文件載入提示詞，並回傳 (絕對路徑, 內容) """
        # 取得目前腳本所在的資料夾
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # 構建絕對路徑
        prompt_path = os.path.join(script_dir, "..", "prompt", file)

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            return content  # 回傳

        except Exception as e:
            print(f"\033[31m[INFO] 找不到 {prompt_path} 文件，將會使用預設的提示詞。\033[0m")
            return None  # 讀取失敗時回傳 None
        
    def talk_to_llm(self):
        """輸入文字與模型對話"""
        self.user_input = self.textbox.get("0.0", "end").strip()
        if self.user_input:  # 避免空輸入
            self.append_chatbubble(role = "User", message = self.user_input)
            self.textbox.delete("0.0", "end")  # 清空輸入框內容
            system_prompt = self.load_prompt("Chat_system_prompt.txt") # 讀取系統提示詞
            memory_prompt = self.load_prompt("Chat_memory_prompt.txt") # 讀取記憶提示詞
            response, prompt_tokens, completion_tokens = self.chat_session.send_to_groq(system_prompt, memory_prompt, user_input = self.user_input)
            self.prompt_tokens = prompt_tokens
            self.completion_tokens = completion_tokens
            self.append_chatbubble(role = "AI", message = response)

    def call_token_usage(self):
        return self.prompt_tokens, self.completion_tokens
    
if __name__ == "__main__":
    import chat
    # 輸入 groq_key
    print("\033[32m[INFO] 請提供Groq API key。\033[0m")
    groq_key = input("\033[33mGroq API key: \033[0m")

    # 設定主題
    theme = 1
    if theme == 1:
        ctk.set_appearance_mode("light")
        chatroom = chatroomWindow("light", groq_key = groq_key)
    else:
        ctk.set_appearance_mode("dark")
        chatroom = chatroomWindow("dark", groq_key = groq_key)

    chatroom.mainloop()
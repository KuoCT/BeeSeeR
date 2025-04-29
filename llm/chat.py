import colorama
from groq import Groq
import json
import re

colorama.init() # 讓文字在命令提示字元中有顏色

class GroqChatSession:
    """管理 Groq API 的對話歷史，以維持上下文記憶，並在過長時自動總結"""
    
    def __init__(
            self, 
            groq_key, 
            model = "llama-3.3-70b-versatile", 
            enable_short_term_memory = True, 
            max_history = 3, 
            temperature = 0.5,
            silent = False
    ):
        self.api_key = groq_key
        self.model = model
        self.client = Groq(api_key = groq_key)
        self.messages = []  # 儲存對話歷史
        self.max_history = max_history * 2  # 限制歷史長度
        self.total_prompt_tokens = 0  # 初始化發送的 token 數
        self.total_completion_tokens = 0  # 初始化 AI 回應的 token 數
        self.enable_short_term_memory = enable_short_term_memory  # 記憶功能開關
        self.temperature = temperature * 2  # 設定 AI 創意度
        self.summaries = [""] # 儲存記憶
        self.silent = silent # 控制輸出
        
        # 初始化
        self.system_prompt = None # 系統提示詞
        self.memory_prompt = None # 記憶提示詞

    def update_config(
            self, 
            model = None, 
            enable_short_term_memory = None, 
            max_history = None, 
            temperature = None
        ):
        """ 更新對話參數，允許透過 GUI 即時調整，避免重複更新 """
        
        # 檢查並更新模型
        if model is not None and model != self.model:
            self.model = model
            # not self.silent and print(f"\033[32m[INFO] 變更 AI 推理模型: {model}\033[0m")
        
        # 檢查並更新短期記憶開關
        if enable_short_term_memory is not None and enable_short_term_memory != self.enable_short_term_memory:
            self.enable_short_term_memory = enable_short_term_memory
            # not self.silent and print(f"\033[32m[INFO] 已修改記憶模組: {enable_short_term_memory}\033[0m")

        # 檢查並更新歷史對話長度
        if max_history is not None and max_history * 2 != self.max_history:
            self.max_history = max_history * 2  # 確保仍然是 2 倍長度
            # not self.silent and print(f"\033[32m[INFO] 已修改歷史長度: {max_history} 輪對話\033[0m")

        # 檢查並更新溫度參數
        if temperature is not None and temperature * 2 != self.temperature:
            self.temperature = temperature * 2
            # not self.silent and print(f"\033[32m[INFO] 已變更模型溫度: {self.temperature}\033[0m")
        
    def add_message(self, role, content):
        """將新的訊息加入對話歷史"""
        self.messages.append({"role": role, "content": content})
    
    def summarize_history(self, recent_conversations, to_summarize):
        """讓 AI 生成對話摘要，並保留最近 max_history 個對話 Pair"""
        not self.silent and print("\033[32m[INFO] 觸發開始壓縮記憶。\033[0m")
        if not self.enable_short_term_memory:
            return  # 如果記憶功能關閉，則不執行

        if not to_summarize:
            return  # 若沒有要摘要的內容則直接返回

        # 轉換為摘要格式
        user_inputs = [pair[0]["content"] for pair in to_summarize]
        ai_responses = [pair[1]["content"] for pair in to_summarize]

        # 讀取 system prompt 內容，若沒有則預設一個
        system_prompt = self.system_prompt
        if system_prompt is None:
            system_prompt = "你是一個智能對話機器人，請用自然、清楚的方式回答問題，輸出語言為**繁體中文**。"
            not self.silent and print("\033[32m[INFO] System prompt文件中沒有內容，使用預設提示詞\033[0m")

        # 讀取 memory prompt 內容，若沒有則預設一個
        memory_prompt = self.memory_prompt
        if memory_prompt is None:
            memory_prompt = (
            "請將以下對話內容整理成摘要，格式如下：\n"
            "- 用戶問題：\n  - (關鍵問題 1)\n  - (關鍵問題 2)...\n"
            "- AI 回應：\n  - (重要回應 1)\n  - (重要回應 2)...\n"
            "- 重要資訊：\n  - (對話中的關鍵資訊)...\n"
            "請保持摘要簡潔，並合併歷史摘要，不超過 250 字。"
        )
            not self.silent and print("\033[32m[INFO] Memory prompt 文件中沒有內容，使用預設提示詞\033[0m")

        # 組合待壓縮的歷史內容
        chat_content = (
            f"Here is the [new conversation content]:\n\nUser Questions:\n{user_inputs}\n\nAI Responses:\n{ai_responses}"
        )

        try:
            # 向 AI 發送請求，產生結構化摘要
            summary_response = self.client.chat.completions.create(
                messages = [
                    {"role": "system", "content": memory_prompt},
                    {"role": "system", "content": "Previous summaries：\n{}".format(self.summaries[-1])},
                    {"role": "user", "content": chat_content},
                ],
                model = self.model,
                temperature = 0.25 # 降低創意度確保摘要更精確
            )
            
            summary = summary_response.choices[0].message.content.strip()

            # 更新 `self.summaries`，確保不累積過長
            self.summaries = [summary]  # 只保留最新的整併後摘要

            # 重建 `self.messages`，包含最新的摘要與對話記錄
            self.messages = [
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": "歷史摘要：\n{}".format(self.summaries[-1])}
            ]

            # 加入最新的對話 Pair (未超過 max_history 的部分)
            for pair in recent_conversations:
                self.messages.extend(pair)

            not self.silent and print("\033[32m[INFO] AI 生成了對話摘要，歷史已壓縮。\033[0m")
            print("\033[32m記憶已更新\033[0m")

        except Exception as e:
            not self.silent and print(f"\033[31m[ERROR] 總結對話時出錯：{e}\033[0m")
            raise Exception(f"錯誤出現在記憶力模組：{e}")  # 拋出異常到 send_to_groq()

    def send_to_groq(self, system_prompt, memory_prompt, user_prompt, user_input):
        """發送對話請求給 Groq API，並在歷史過長時進行摘要"""
        if not self.api_key:
            print("\033[31m[ERROR] GROQ_API_KEY 未提供。\033[0m")
            return "[ERROR] GROQ_API_KEY 未提供。"

        # 更新 system prompt 內容，若沒有則預設一個
        self.system_prompt = system_prompt
        if self.system_prompt is None:
            system_prompt = "你是一個智能對話機器人，請用自然、清楚的方式回答問題，輸出語言為**繁體中文**。"
            not self.silent and print("\033[32m[INFO] System prompt文件中沒有內容，使用預設提示詞\033[0m")

        # 更新 memory prompt 內容，若沒有則預設一個
        self.memory_prompt = memory_prompt
        if self.memory_prompt is None:
            memory_prompt = (
            "請將以下對話內容整理成摘要，格式如下：\n"
            "- 用戶問題：\n  - (關鍵問題 1)\n  - (關鍵問題 2)...\n"
            "- AI 回應：\n  - (重要回應 1)\n  - (重要回應 2)...\n"
            "- 重要資訊：\n  - (對話中的關鍵資訊)...\n"
            "請保持摘要簡潔，並合併歷史摘要，不超過 250 字。"
        )
            not self.silent and print("\033[32m[INFO] Memory prompt 文件中沒有內容，使用預設提示詞\033[0m")

        # 根據是否啟用短期記憶，決定對話歷史
        if self.enable_short_term_memory:
            # 使用完整歷史
            if len(self.messages) == 0:
                self.add_message("system", system_prompt)  # 第一輪對話時加入 system 提示詞
            else:
                # 動態更新 system_prompt（即便歷史存在）
                self.messages[0] = {"role": "system", "content": system_prompt}
            self.add_message("user", user_input) # 新增使用者輸入
        else:
            # 僅使用當前對話，不保存歷史
            self.messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
        ]
            
        def insert_before_last(messages, role, content):
            """建立一份副本，插入訊息在倒數第一筆前，並回傳新列表"""
            new_messages = messages.copy()
            new_messages.insert(-1, {"role": role, "content": content})
            return new_messages

        # 判斷 user_prompt 是否為空（None 或空白字串）
        if user_prompt and user_prompt.strip():
            messages_for_chat = insert_before_last(self.messages, "system", user_prompt)
        else:
            messages_for_chat = self.messages

        # print("\033[32m[INFO] AI 看到的內容:\033[0m")
        # print(json.dumps(messages_for_chat, indent = 2, ensure_ascii = False))

        try:
            chat_completion = self.client.chat.completions.create(
                messages = messages_for_chat,
                model = self.model,
                temperature = self.temperature  # 溫度參數
            )
            response = chat_completion.choices[0].message.content

            # 將 AI 回應加入對話歷史
            if self.enable_short_term_memory:
                self.add_message("assistant", response)

            # 提取「user-assistant 對話 Pair」
            self.conversation_pairs = []
            self.temp_pair = []

            for msg in self.messages:
                if msg["role"] in ["user", "assistant"]:
                    self.temp_pair.append(msg)
                if len(self.temp_pair) == 2:  # 一個 Pair 完整
                    self.conversation_pairs.append(self.temp_pair)
                    self.temp_pair = []
            
            # print("\033[32m[INFO] 過去對話:\033[0m")
            # print(json.dumps(self.conversation_pairs, indent = 2, ensure_ascii = False))

            # 保留最近 max_history 個對話 Pair
            recent_conversations = self.conversation_pairs[-self.max_history // 3:]

            # 需要被摘要的對話（超過 max_history 的部分）
            to_summarize = self.conversation_pairs[:-self.max_history // 3]

            # 當對話長度超過 max_history，讓 AI 進行摘要
            if len(self.conversation_pairs) > self.max_history // 2:
                # 用 Threading 在背景執行摘要
                import threading
                threading.Thread(
                    target=self.summarize_history,
                    args=(recent_conversations, to_summarize),
                    daemon=True  # 設為 daemon，程式結束時自動結束
                ).start()

            # 取得 token 使用資訊
            usage = chat_completion.usage
            prompt_tokens = usage.prompt_tokens  # 輸入的 token
            completion_tokens = usage.completion_tokens  # 回應的 token

            # 更新累計 token 數量
            self.total_prompt_tokens += prompt_tokens
            self.total_completion_tokens += completion_tokens

            # 顯示完整資訊
            # total_tokens = usage.total_tokens  # 總 token 數
            # not self.silent and print("\033[32m[INFO] Token 使用量:\033[0m")
            # not self.silent and print(f"輸入 token: {prompt_tokens}")
            # not self.silent and print(f"回應 token: {completion_tokens}")
            # not self.silent and print(f"本次總共 token: {total_tokens}")
            # not self.silent and print(f"累計輸入 token: {self.total_prompt_tokens}")
            # not self.silent and print(f"累計回應 token: {self.total_completion_tokens}")
            # not self.silent and print(f"累計總 token: {self.total_prompt_tokens + self.total_completion_tokens}")
            # not self.silent and print(f"\033[36m[DEBUG] 當前對話輪數: {len(self.conversation_pairs)}\033[0m")
            # not self.silent and print(f"\033[36m[DEBUG] 最近對話: {recent_conversations}\033[0m")
            # not self.silent and print(f"\033[36m[DEBUG] 需要被摘要的對話: {to_summarize}\033[0m")
            # not self.silent and print("\033[32m[DEBUG] 完整輸出:\033[0m")
            # not self.silent and print(json.dumps(self.messages, indent = 2, ensure_ascii = False))

            # 顯示訊息   
            print(f"\n\033[33m[INFO] 大型語言模型 (LLM) 回應 ({self.model}): \033[0m") # 模型標籤 
            print(response)
            print() # 空行

            # 回傳回應內容及 token 數據
            return self.clean_response(response), prompt_tokens, completion_tokens
        
        except Exception as e:
            error_text = str(e)
            # 預設錯誤代碼與訊息
            code = "未知"
            message = "無法取得錯誤訊息"

            # 嘗試解析錯誤內容
            try:
                if 'Error code:' in error_text:
                    code_part, json_part = error_text.split(' - ', 1)
                    code = code_part.strip().split(':')[1].strip()
                    error_json = json.loads(json_part.replace("'", '"'))
                    message = error_json.get('error', {}).get('message', message)
            except Exception:
                message = error_text  # 若解析失敗，直接顯示原始錯誤

            # 格式化 response 給 GUI
            response = f"[ERROR] 與 AI 連線時出錯:\nCode: {code}\n{message}"
            
            # 同步印出終端錯誤（可選）
            print(f"\033[31m{response}\033[0m")

            return response, 0, 0
        
    def clean_response(self, response):
        """去除 <think>...</think> 與其他標籤"""
        tags_to_remove = ["think"] # 可用`,`加入其他標籤
        for tag in tags_to_remove:
            response = re.sub(fr"<{tag}>.*?</{tag}>", "", response, flags = re.DOTALL)
        return response.strip()
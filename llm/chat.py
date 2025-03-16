import colorama
from groq import Groq
import json

colorama.init() # 讓文字在命令提示字元中有顏色

class GroqChatSession:
    """管理 Groq API 的對話歷史，以維持上下文記憶，並在過長時自動總結"""
    
    def __init__(
            self, 
            groq_key, 
            model = "llama-3.3-70b-versatile", 
            enable_short_term_memory = True, 
            max_history = 3, 
            temperature = 0.6,
            silent = True
    ):
        self.api_key = groq_key
        self.model = model
        self.client = Groq(api_key = groq_key)
        self.messages = []  # 儲存對話歷史
        self.max_history = max_history * 2  # 限制歷史長度
        self.total_prompt_tokens = 0  # 初始化發送的 token 數
        self.total_completion_tokens = 0  # 初始化 AI 回應的 token 數
        self.enable_short_term_memory = enable_short_term_memory  # 記憶功能開關
        self.temperature = temperature  # 設定 AI 創意度
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
            not self.silent and print(f"\033[32m[INFO] 已變更模型為: {model}\033[0m")
        
        # 檢查並更新短期記憶開關
        if enable_short_term_memory is not None and enable_short_term_memory != self.enable_short_term_memory:
            self.enable_short_term_memory = enable_short_term_memory
            not self.silent and print(f"\033[32m[INFO] 已修改記憶模組: {enable_short_term_memory}\033[0m")

        # 檢查並更新歷史對話長度
        if max_history is not None and max_history * 2 != self.max_history:
            self.max_history = max_history * 2  # 確保仍然是 2 倍長度
            not self.silent and print(f"\033[32m[INFO] 已修改歷史長度: {max_history} 輪對話\033[0m")

        # 檢查並更新溫度參數
        if temperature is not None and temperature != self.temperature:
            self.temperature = temperature
            not self.silent and print(f"\033[32m[INFO] 已變更模型溫度: {temperature}\033[0m")
        
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
                temperature = 0.25  # 降低創意度確保摘要更精確
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

    def send_to_groq(self, system_prompt, memory_prompt, user_input):
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
        
        # 模型標籤    
        print(f"\n\033[33m{self.model}: \033[0m")

        try:
            chat_completion = self.client.chat.completions.create(
                messages = self.messages,
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

            # 保留最近 max_history 個對話 Pair
            recent_conversations = self.conversation_pairs[-self.max_history // 3:]

            # 需要被摘要的對話（超過 max_history 的部分）
            to_summarize = self.conversation_pairs[:-self.max_history // 3]

            # 當對話長度超過 max_history，讓 AI 進行摘要
            if len(self.conversation_pairs) > self.max_history // 2:
                self.summarize_history(recent_conversations, to_summarize)

            # 取得 token 使用資訊
            usage = chat_completion.usage
            prompt_tokens = usage.prompt_tokens  # 輸入的 token
            completion_tokens = usage.completion_tokens  # 回應的 token
            total_tokens = usage.total_tokens  # 總 token 數

            # 更新累計 token 數量
            self.total_prompt_tokens += prompt_tokens
            self.total_completion_tokens += completion_tokens

            # 顯示訊息
            print(response)
            print() # 空行

            # 顯示完整資訊
            not self.silent and print("\033[32m[INFO] Token 使用量:\033[0m")
            not self.silent and print(f"輸入 token: {prompt_tokens}")
            not self.silent and print(f"回應 token: {completion_tokens}")
            not self.silent and print(f"本次總共 token: {total_tokens}")
            not self.silent and print(f"累計輸入 token: {self.total_prompt_tokens}")
            not self.silent and print(f"累計回應 token: {self.total_completion_tokens}")
            not self.silent and print(f"累計總 token: {self.total_prompt_tokens + self.total_completion_tokens}")
            not self.silent and print(f"\033[34m[INFO] 當前對話輪數: {len(self.conversation_pairs)}\033[0m")
            not self.silent and print(f"\033[34m[INFO] 最近對話: {recent_conversations}\033[0m")
            not self.silent and print(f"\033[34m[INFO] 需要被摘要的對話: {to_summarize}\033[0m")
            not self.silent and print("\033[32m[INFO] 完整輸出:\033[0m")
            not self.silent and print(json.dumps(self.messages, indent = 2, ensure_ascii = False))

            # 回傳回應內容及 token 數據
            return response, prompt_tokens, completion_tokens
        
        except Exception as e:
            print(f"\033[31m[ERROR] 調用 Groq API 時出錯：{e}\033[0m")
            response = f"[ERROR] 調用 Groq API 時出錯：{e}"
            return response

if __name__ == "__main__":
    import argparse
    import os

    # 命令列參數
    parser = argparse.ArgumentParser(description = "Groq API 設定")
    parser.add_argument("-k", "--groq-key", type = str, metavar = "API_KEY", 
                        help = "設定 Groq API Key（用於 API 連線驗證）")
    parser.add_argument("-m", "--model", type = str, metavar = "MODEL_NAME", default = "llama-3.3-70b-versatile", 
                        help = "設定語言模型，預設為 llama-3.3-70b-versatile")
    parser.add_argument("-sl", "--STM-limit", type = int, metavar = "N", default = 3,
                        help = "短期記憶的最大對話數（多少輪對話後開始壓縮記憶），預設為 3。")
    parser.add_argument("-ns", "--noSTM", action = "store_true",
                        help = "取消使用短期記憶。")
    parser.add_argument("-T", "--temperature", type = float, metavar = "TEMP", 
                        help= "設定 AI 創意度 (0.0 = 最嚴謹, 1.0 = 最具創造性)，預設 0.6", default = 0.6)
    parser.add_argument("--messages", type = str, metavar = "MESSAGES", help = "傳遞對話歷史，格式為 JSON")
    parser.add_argument("--summaries", type = str, metavar = "SUMMARIES", help = "傳遞摘要內容")
    args = parser.parse_args()
    
    # 預設不顯示系統資訊
    debug_mode = False
    show_usage = False

    # 預設變數
    model = "llama-3.3-70b-versatile"
    enable_short_term_memory = True
    max_history = 3
    temperature = 0.6
    total_prompt_tokens = 0  # 初始化發送的 token 數
    total_completion_tokens = 0  # 初始化 AI 回應的 token 數
    system_prompt_file = "Chat_system_prompt.txt"
    memory_prompt_file = "Chat_memory_prompt.txt"
    groq_key = args.groq_key.strip() if args.groq_key else None # 移除多餘空白
    groq_available = True

    def load_prompt(file):
        """ 從文件載入提示詞 """
        # 取得目前腳本所在的資料夾
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # 構建絕對路徑
        prompt_path = os.path.join(script_dir, "..", "prompt", file)

        try:
            with open(prompt_path, "r", encoding = "utf-8") as file:
                return file.read().strip()

        except Exception as e:
            print(f"\033[31m[INFO] 找不到 {prompt_path} 文件，將會使用預設的提示詞。\033[0m")
            return None  # 讀取失敗時返回 None

    # 解析命令列參數
    if args.groq_key:
        groq_key = args.groq_key
    else:
        print("\033[32m[INFO] 請提供Groq API key。\033[0m")
        groq_key = input("\033[33mGroq API key: \033[0m")

    if args.model:
        model = args.model

    if args.noSTM:
        enable_short_term_memory = False  # 停用短期記憶

    if args.STM_limit:
        max_history = args.STM_limit

    # # 如果 API Key 非空，嘗試連線驗證
    # if groq_key:
    #     try:
    #         client = Groq(api_key = groq_key)
    #         test_response = client.chat.completions.create(
    #             model="mixtral-8x7b-32768",
    #             messages=[{"role": "system", "content": "ping"}],  # 測試 API 可用性
    #             max_tokens=10
    #         )
    #         if test_response:
    #             print("\033[32m[INFO] Groq API 連線成功! \033[0m")
    #             groq_available = True
    #         else:
    #             print("\033[31m[INFO] API Key 無效，請確認 Groq API Key。\033[0m")
    #     except Exception as e:
    #         print(f"\033[31m[ERROR] 無法連線到 Groq API：{e}\033[0m")

    def multi_line_input():
        """當使用者輸入 `/m` 時，開啟多行輸入模式"""
        print("\033[36m多行輸入模式，輸入 /s 完成輸入。\033[0m")
        lines = []
        while True:
            try:
                line = input()
                if line.strip().lower() == "/s":  # `/s` 結束多行輸入，返回內容
                    return "\n".join(lines).strip() if lines else ""

                lines.append(line)  # 正常加入內容
            except EOFError:  # 支援 `Ctrl+D`（Linux/macOS）或 `Ctrl+Z`（Windows）
                break

        return "\n".join(lines).strip()
    
    def show_commands():
        """指令列表"""
        print("\n\033[36m[INFO] 指令列表：\033[0m")
        print("\033[33m/m\033[0m        - 進入多行輸入模式")
        print("\033[33m/s\033[0m        - 結束多行輸入模式並送出")
        print("\033[33m/mem\033[0m      - 短期記憶抽出")
        print("\033[33m/bye\033[0m      - 結束對話")
        print("\033[33m/all\033[0m      - 開啟/關閉完整系統輸出")
        print("\033[33m/use\033[0m      - 顯示/隱藏 token 使用量")
        print("\033[33m/?\033[0m        - 顯示此指令列表")
        print() # 空行

    # 創建對話會話
    chat_session = GroqChatSession(groq_key, model, enable_short_term_memory, max_history, temperature, silent = True)

    # 初始化訊息
    print("\n\033[33m<<AI 臨時聊天室>>\033[0m")
    print("\033[36m輸入 /m 進入多行輸入模式， /bye 退出對話(更多指令與說明請輸入 /? 查看)。\033[0m")

    # 傳遞對話內容與記憶
    if args.messages:
        chat_session.messages = json.loads(args.messages)
    if args.summaries:
        chat_session.summaries = json.loads(args.summaries)

    is_multi_line = False  # 初始狀態為單行輸入模式

    while True:
        user_input = input("\033[33m你: \033[0m").strip()

        if user_input.lower() == "/bye":
            print("\033[33m[INFO] 對話結束。\033[0m")
            break
        elif user_input.lower() == "/m":
            user_input = multi_line_input()
            if user_input == "/bye":
                print("\033[33m[INFO] 對話結束。\033[0m")
                break
        elif user_input.lower() == "/all":
            debug_mode = not debug_mode
            print("\033[36m[INFO] 完整系統輸出", "開啟" if debug_mode else "關閉", "。\033[0m")
            continue
        elif user_input.lower() == "/use":
            show_usage = not show_usage
            print("\033[36m[INFO] Token 使用量顯示", "開啟" if show_usage else "關閉", "。\033[0m")
            continue
        elif user_input.lower() == "/?":
            show_commands()
            continue

        if user_input:
            # 讀取提示詞
            system_prompt = load_prompt(system_prompt_file)
            memory_prompt = load_prompt(memory_prompt_file)
            reresponse, prompt_tokens, completion_tokens = chat_session.send_to_groq(system_prompt, memory_prompt, user_input)

            # Debug 模式
            if debug_mode:
                chat_session.silent = False
            else:
                chat_session.silent = True

            # 顯示 token 使用量
            if show_usage:
                # 顯示 token 資訊
                print(f"033[36m[INFO] 輸入 token: {prompt_tokens}\033[0m")
                print(f"033[36m[INFO] 回應 token: {completion_tokens}\033[0m")


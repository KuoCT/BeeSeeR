import os
import sys

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑
sys.path.append(PATH) # 將路徑加入到系統路徑中

if __name__ == "__main__":
    import argparse
    import json
    import llm.chat as chat

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
    user_prompt_file = "User_prompt.txt"
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
        # print("\033[33m/mem\033[0m      - 短期記憶抽出")
        print("\033[33m/bye\033[0m      - 結束對話")
        print("\033[33m/all\033[0m      - 開啟/關閉完整系統輸出")
        print("\033[33m/use\033[0m      - 顯示/隱藏 token 使用量")
        print("\033[33m/?\033[0m        - 顯示此指令列表")
        print() # 空行

    # 創建對話會話
    chat_session = chat.GroqChatSession(groq_key, model, enable_short_term_memory, max_history, temperature, silent = True)

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
            user_prompt = load_prompt(user_prompt_file)
            reresponse, prompt_tokens, completion_tokens = chat_session.send_to_groq(system_prompt, memory_prompt, user_prompt, user_input)

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
import os
import sys
import argparse

# 解析命令列參數
parser = argparse.ArgumentParser(description = "BeeSeeR 控制參數，支援 GPU/CPU 模式選擇及 Groq API 設定")
parser.add_argument("-c", "--force-cpu", action = "store_true", help = "強制使用 CPU 模式（預設為 GPU，如適用）")
parser.add_argument("-a", "--all", action = "store_false", help = "完整輸出模式 (只在終端機中生效)")
args = parser.parse_args()

# 根據 `--force-cpu` 設置環境變數
if args.force_cpu:
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # 設定 CUDA 無效化

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__))) # 設定相對路徑

import json
import tkinter as tk
import customtkinter as ctk
from ocr.WinCap import WindowCapture
from ocr.WinCap import MouseTooltip
from ocr.overlay import overlayWindow
from ocr.freeze import FreezeOverlay
import llm.chat as chat
from llm.chatroom import chatroomWindow
import ctypes
import re
import threading
import keyboard
import time

def load_config():
    """讀取設定檔案"""
    if os.path.exists(os.path.join(PATH, "config.json")):
        with open(os.path.join(PATH, "config.json"), "r") as f:
            return json.load(f)
    return {}  # 如果沒有設定檔，回傳空字典

# 定義預設參數
settings  = load_config()
model = settings.get("model", "llama-3.3-70b-versatile")
enable_short_term_memory = settings.get("enable_short_term_memory", True)
silent = args.all
max_history = 3
temperature = 0.6
cb_coords = None # 初始化座標
last_response = None
current_theme = settings.get("theme", "dark")
total_prompt_tokens = 0  # 初始化發送的 token 數
total_completion_tokens = 0  # 初始化 AI 回應的 token 數
system_prompt_file = "AI_system_prompt.txt"
memory_prompt_file = "AI_memory_prompt.txt"
prompt_file = "User_prompt.txt"
prompt_control = True
ost_control = settings.get("ost_control", False)
groq_key = settings.get("groq_key", None)
groq_available = False # 預設 API 狀態為 False
auto_dtype = settings.get("auto_dtype", "ON")
dtype = settings.get("dtype", None)
if args.force_cpu or auto_dtype == "NO": dtype = None
langs = settings.get("langs", None) # 限定語言參數
dialog = None  # 初始化對話框
dialog_api = None  # 初始化 API 對話框
manga_ocr = settings.get("manga_ocr", False)  # 漫畫 OCR 開關
overlay_windows = [] # 加入 overlay_windows 管理清單
overlay_visible = True
toggle_overlay_hotkey = settings.get("toggle_overlay_hotkey", "ctrl+shift+windows+a")
capture_hotkey = settings.get("capture_hotkey", "ctrl+shift+windows+s")
hotkey_enabled = True
# 初使化 OCR 模型
mocr = None
recognition_predictor = None
detection_predictor = None

# 如果 API Key 非空，解鎖 API 功能
if groq_key:
    groq_available = True
    # 驗證機制有機率不過 (棄用)
    # from groq import Groq
    # try:
    #     client = Groq(api_key = groq_key)
    #     test_response = client.chat.completions.create(
    #         model="mixtral-8x7b-32768",
    #         messages=[{"role": "system", "content": "ping"}],  # 測試 API 可用性
    #         max_tokens=10
    #     )
    #     if test_response:
    #         print("\033[32m[INFO] Groq API 連線成功！\033[0m")
    #         groq_available = True
    #     else:
    #         print("\033[31m[INFO] API Key 無效，請確認 Groq API Key。\033[0m")
    # except Exception as e:
    #     print(f"\033[31m[ERROR] 無法連線到 Groq API：{e}\033[0m")

def load_prompt(file):
    """ 從文件載入提示詞，並回傳 (絕對路徑, 內容) """
    # 取得目前腳本所在的資料夾
    script_dir = PATH

    # 構建絕對路徑
    prompt_path = os.path.join(script_dir, "prompt", file)

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        return content # 回傳
        # return prompt_path, content  # 回傳 (絕對路徑, 內容)

    except Exception as e:
        print(f"\033[31m[INFO] 找不到 {prompt_path} 文件，將會使用預設的提示詞。\033[0m")
        return None  # 讀取失敗時回傳 None
        
# 初始化 chat 物件
if groq_available:
    chat_session = chat.GroqChatSession(
        groq_key, 
        model, 
        enable_short_term_memory, 
        max_history, 
        temperature,
        silent
    )

# 螢幕文字辨識
def run_wincap():
    """啟動 WindowCapture 取得螢幕訊息"""
    global manga_ocr, hotkey_enabled

    if not hotkey_enabled:
        return  # 忽略多餘觸發
    
    hotkey_enabled = False  # 禁用快捷鍵

    def receive_coordinates(coords):
        """回呼函數，獲取座標"""
        global cb_coords
        cb_coords = coords
        # print(f"\033[34m[INFO] 即時回傳選取範圍座標: {coords}\033[0m")

    prompt = load_prompt(prompt_file) # 讀取使用者提示詞

    capture_bt.configure(state = "disabled") # 鎖定按鈕防止重複觸發

    # 啟動最初的「載入中...」提示框
    loading_tip = MouseTooltip(window, follow = True)
    loading_tip.update() # 強制畫面更新一次，避免初期不顯示

    def simulate_loop_progress(stop_event):
        """模擬循環動畫：5 格黑框，1 格填滿，直到 stop_event 為 True"""
        frames = []
        total = 5
        for i in range(total):
            frame = ["□"] * total
            frame[i] = "■"
            frames.append("".join(frame))

        idx = 0
        start_time = time.time()  # 記錄動畫開始時間

        while not stop_event.is_set():
            elapsed = time.time() - start_time

            # 額外說明文字（經過10秒後才出現）
            extra_info = ""
            if elapsed > 10:
                extra_info = " \n下載模型約 2 分鐘，取決於網路速度"

            # 更新畫面
            loading_tip.label.configure(
                text = f"下載/快取分析模型 {frames[idx]}{extra_info}"
            )
            loading_tip.update()
            idx = (idx + 1) % total
            time.sleep(0.2)

    def load_model_and_launch():
        """背景載入模型，載入完再啟動 WindowCapture"""
        global mocr, recognition_predictor, detection_predictor

        # 啟動 loading 動畫用的 stop_flag
        stop_event = threading.Event()

        # Manga OCR 模式
        if manga_ocr:
            if not mocr:
                threading.Thread(target = simulate_loop_progress, args = (stop_event,), daemon = True).start()
                from manga_ocr import MangaOcr
                import logging
                logging.getLogger("transformers").setLevel(logging.ERROR)
                mocr = MangaOcr()
            # 清除其他模式
            recognition_predictor = None
            detection_predictor = None

        # Surya 模式
        else:
            if not recognition_predictor and not detection_predictor:
                threading.Thread(target = simulate_loop_progress, args = (stop_event,), daemon = True).start()
                from surya.recognition import RecognitionPredictor
                from surya.detection import DetectionPredictor
                recognition_predictor = RecognitionPredictor(dtype = dtype)
                detection_predictor = DetectionPredictor(dtype = dtype)
            # 清除其他模式
            mocr = None

        # 模型載入完 → 回主執行緒建立 WindowCapture
        def launch_window():
            stop_event.set()  # 結束動畫
            loading_tip.destroy()
            freeze_overlay.show() # 凍結畫面

            app = WindowCapture(
                window,
                prompt_control = prompt_control,
                on_capture = receive_coordinates,
                on_result = handle_result,
                prompt = prompt,
                dtype = dtype,
                langs = langs,
                manga_ocr = manga_ocr,
                mocr = mocr,
                recognition_predictor = recognition_predictor,
                detection_predictor = detection_predictor
            )
            app.deiconify()

        window.after(0, launch_window)

    # 背景執行模型載入
    threading.Thread(target = load_model_and_launch, daemon = True).start()

def estimate_word_count(text: str) -> int:
    """
    粗略估算混合語言（中、日、韓、英文、西文等）中的詞數。
    - 中文/日文漢字：每個字算 1 詞
    - 日文平假名、片假名、韓文字母：每個音節也算 1 詞
    - 拼音語言：單詞算 1 詞
    """
    # 中文、日文、韓文漢字
    cjk_chars = re.findall(r'[\u4E00-\u9FFF\u3400-\u4DBF\uF900-\uFAFF]', text)

    # 日文平假名（ぁ-ん）與片假名（ァ-ン）
    kana_chars = re.findall(r'[\u3040-\u30ff]', text)

    # 韓文字（Hangul）：現代韓文音節
    hangul_chars = re.findall(r'[\uac00-\ud7af]', text)

    # 拉丁語系單詞（含西文變音字母）
    latin_words = re.findall(r'\b[\wÀ-ÖØ-öø-ÿĀ-ſƀ-ȳ]+\b', text)

    return len(cjk_chars) + len(kana_chars) + len(hangul_chars) + len(latin_words)

# AI 自動翻譯 + 螢幕覆蓋顯示結果
def handle_result(prompt_text, extracted_text, final_text, is_dragging):
    """處理 WindowCapture 回傳的結果"""
    global last_response, cb_coords, scale_factor, hotkey_enabled
    freeze_overlay.hide() # 解除凍結畫面
    hotkey_enabled = True  # 重啟快捷鍵

    ext = extracted_text # 取得辨識後文字
    user_prompt = prompt_text
    user_input = ext

    if isinstance(ext, str) and ext.strip():
        print("\033[33m[INFO] 文字辨識結果：\033[0m")
        print(ext)
        if not ost_control: capture_bt.configure(state="normal") # 解鎖按鈕
    else:
        print("\033[31m[INFO] 無法獲取文字辨識結果。\033[0m")
        # 顯示短暫提示：無法獲取文字辨識結果
        tooltip = MouseTooltip(window, follow = False, text = "無法獲取文字辨識結果")
        tooltip.update()  # 強制顯示一次，避免閃爍
        tooltip.after(1000, tooltip.destroy)  # 1 秒後自動銷毀
        capture_bt.configure(state = "normal") # 解鎖按鈕
        return

    # 自動翻譯
    if groq_available and ost_control and isinstance(ext, str) and ext.strip() and is_dragging:
        # 粗略統計單詞數
        word_count = estimate_word_count(ext)
        print(f"[INFO] OCR 分析結果: {word_count} 單字")
        word_threshold = 1000  # 可自行調整單字上限

        if word_count > word_threshold:
            from tkinter import messagebox
            confirm = messagebox.askyesno(
                "OCR 內容過長警告",
                f"OCR 內容過長（約 {word_count} 單詞），可能是辨識錯誤造成的大量雜訊。\n"
                "系統已自動將辨識內容儲存至剪貼簿，可貼上檢查內容是否正確。\n\n"
                "是否仍要送出進行 AI 翻譯？"
            )
            if not confirm:
                return  # 使用者選擇取消，不進行翻譯
            
        # 顯示提示（主線）
        loading_tip = MouseTooltip(window, follow=True, text="AI 處理中...")
        loading_tip.update()

        def translate_in_background():
            global last_response

            try:
                # 讀取提示詞與發送至 Groq
                system_prompt = load_prompt(system_prompt_file)
                memory_prompt = load_prompt(memory_prompt_file)
                response, prompt_tokens, completion_tokens = chat_session.send_to_groq(
                    system_prompt, memory_prompt, user_prompt, user_input
                )
                last_response = response
            except Exception as e:
                print(f"[ERROR] AI 請求失敗: {e}")
                response = "[錯誤] 無法取得 AI 回應。"
                prompt_tokens, completion_tokens = 0, 0
                last_response = response

            def update_ui():
                global total_prompt_tokens, total_completion_tokens
                # 關閉提示
                loading_tip.destroy()

                # 更新 token 計數器
                total_prompt_tokens += prompt_tokens
                total_completion_tokens += completion_tokens
                t_input_wd.configure(text=f"● 輸入: {prompt_tokens}")
                t_output_wd.configure(text=f"● 輸出: {completion_tokens}")
                t_in_total_wd.configure(text=f"● 累計輸入: {total_prompt_tokens}")
                t_out_total_wd.configure(text=f"● 累計輸出: {total_completion_tokens}")

                # 更新 chatroom
                chatroom.append_chatbubble(role = "User", message = user_input)
                chatroom.append_chatbubble(role = chat_session.model, message = last_response)
                chatroom.append_chatlog(role = "User", message = user_input)
                chatroom.append_chatlog(role = chat_session.model, message = last_response)

                # 按鈕狀態
                resetchat_bt.configure(text = "AI 重製/記憶刪除", fg_color = ["#1e8bba", "#C7712D"])

                # 顯示 overlay
                overlay = overlayWindow(window, last_response, cb_coords, scale_factor)
                overlay_windows.append(overlay)
                overlay.deiconify()

                # 翻譯完成並顯示 overlay 後再解鎖按鈕
                capture_bt.configure(state="normal")

            # 回到主線更新畫面
            window.after(0, update_ui)

        # 背景執行 AI 翻譯任務
        threading.Thread(target = translate_in_background, daemon = True).start()

def update_token_display(prompt_tokens, completion_tokens):
    """更新主視窗 token 顯示"""
    # 更新 token 計數器
    global total_prompt_tokens
    global total_completion_tokens
    
    total_prompt_tokens += prompt_tokens
    total_completion_tokens += completion_tokens

    t_input_wd.configure(text=f"● 輸入: {prompt_tokens}")
    t_output_wd.configure(text=f"● 輸出: {completion_tokens}")
    t_in_total_wd.configure(text=f"● 累計輸入: {total_prompt_tokens}")
    t_out_total_wd.configure(text=f"● 累計輸出: {total_completion_tokens}")

    # 還原按鈕
    resetchat_bt.configure(text = "AI 重製/記憶刪除", fg_color = ["#1e8bba", "#C7712D"])

def set_OCR_config():
    """設定 OCR 設定"""
    global dialog
    if dialog:
        dialog.destroy()  # 關閉舊視窗
    dialog = ctk.CTkToplevel()
    dialog.title("OCR 設定")
    dialog.geometry(f"240x220+{window.winfo_x() - int(250 * scale_factor)}+{window.winfo_y()}")
    dialog.attributes("-topmost", True) # 讓視窗顯示在最前面
    # dialog.grab_set() # 鎖定對話框
    dialog.after(250, dialog.iconbitmap, 
                (
                    os.path.join(PATH, "icon", "logo_dark.ico") 
                    if current_theme == "dark" 
                    else os.path.join(PATH, "icon", "logo_light.ico")
                )
    )

    def make_ink():
        """製作快速啟動捷徑"""
        from tkinter import filedialog, messagebox
        import win32com.client
        import shutil
        bat_path = filedialog.askopenfilename(
            filetypes = [("Batch Files", "*.bat")], 
            initialdir = PATH,
            title = "選擇 BeeSeeR 程式啟動檔"
        )
        if not bat_path:
            messagebox.showwarning("取消", "未選擇 .bat 檔案")
            return
        
        icon_dir = os.path.join(PATH, "icon")
        if not os.path.exists(icon_dir):
            icon_dir = PATH  # icon 資料夾不存在時 fallback

        icon_path = filedialog.askopenfilename(
            filetypes = [("Icon Files", "*.ico")],
            initialdir = icon_dir,
            title = "選擇一個 icon"
        )

        if not icon_path:
            messagebox.showwarning("取消", "未選擇 icon 檔案")
            return
        
        save_dir = filedialog.askdirectory(
            initialdir = PATH,
            title = "選擇捷徑存放位置"
        )

        if not save_dir:
            messagebox.showwarning("取消", "未選擇捷徑存放位置")
            return
        shortcut_path = os.path.join(save_dir, "BeeSeeR.lnk")

        def get_cmd_path():
            # 檢查 cmd.exe 是否在 PATH 中
            cmd_in_path = shutil.which("cmd.exe")
            if cmd_in_path:
                print(f"找到 cmd.exe 在 PATH：{cmd_in_path}")
                return "cmd.exe"  # 使用簡寫，保持 PATH 彈性

            # fallback 絕對路徑
            fallback_path = os.path.join(os.environ["SystemRoot"], "System32", "cmd.exe")
            if os.path.exists(fallback_path):
                print(f"使用 fallback cmd.exe：{fallback_path}")
                return fallback_path
            else:
                raise FileNotFoundError("找不到 cmd.exe，請確認系統是否正常。")

        # 組合參數
        arguments = f'/c "{bat_path}"'

        # 建立捷徑
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(shortcut_path)
            shortcut.TargetPath = get_cmd_path()
            shortcut.Arguments = arguments
            shortcut.WorkingDirectory = os.path.dirname(bat_path)
            shortcut.IconLocation = icon_path
            shortcut.Save()
            messagebox.showinfo("完成", f"捷徑已儲存：\n{shortcut_path}")  
        except Exception as e:
            messagebox.showerror("錯誤", f"建立捷徑失敗：{str(e)}") 

    def toggle_auto_dtype():
        """dtype 自動/手動切換"""
        global auto_dtype, dtype
        if auto_dtype == "ON":
            auto_dtype = "OFF"
            dtype = current_dtype
            dtype_sw.configure(state = "normal")
            auto_dtype_bt.configure(fg_color = "gray60", hover_color = ["#325882", "#A85820"])
            dtype_sw.configure(
                fg_color = ["#325882", "#A85820"],
                progress_color = ["gray70", "gray60"],
                button_color = ["#1e8bba", "#C7712D"]
            )
        else:
            auto_dtype = "ON"
            dtype = None # 自動偵測
            dtype_sw_var.set(current_dtype)
            dtype_sw.configure(state = "disabled", text = "辨識模型: 全精度" if current_dtype == "float32" else "辨識模型: 半精度")
            auto_dtype_bt.configure(fg_color = ["#1e8bba", "#C7712D"], hover_color = ["#325882", "#A85820"])
            dtype_sw.configure(fg_color = "gray60", progress_color = "gray60", button_color = "gray60")
        save_config()

    def toggle_dtype():
        """dtype 切換"""
        global dtype
        if dtype == "float32":
            dtype = "float16"
            dtype_sw.configure(text = "辨識模型: 半精度")
        else:
            dtype = "float32"
            dtype_sw.configure(text = "辨識模型: 全精度")
        save_config()

    def update_langs():
        """根據 Checkbox 狀態更新 self.langs"""
        global langs
        selected = []

        if langs_zh_cb_var.get() == "ON":
            selected.append("zh")
        if langs_en_cb_var.get() == "ON":
            selected.append("en")
        if langs_ja_cb_var.get() == "ON":
            selected.append("ja")
        if langs_ko_cb_var.get() == "ON":
            selected.append("ko")

        # 如果有選取語言，更新 self.langs，否則設為 None
        langs = selected if selected else None
        save_config()

    def toggle_manga_ocr():
        """漫畫 OCR 開關"""
        global manga_ocr
        if manga_ocr_sw_var.get() == "ON":
            manga_ocr = True
            langs_zh_cb.configure(state = "disabled", border_color = "gray60", fg_color = "gray60")
            langs_en_cb.configure(state = "disabled", border_color = "gray60", fg_color = "gray60")
            langs_ja_cb.configure(state = "disabled", border_color = "gray60", fg_color = "gray60")
            langs_ko_cb.configure(state = "disabled", border_color = "gray60", fg_color = "gray60")

        else:
            manga_ocr = False
            langs_zh_cb.configure(state = "normal", border_color = ["#3E454A", "#4F5151"], fg_color = ["#56778c", "#c7712d"])
            langs_en_cb.configure(state = "normal", border_color = ["#3E454A", "#4F5151"], fg_color = ["#56778c", "#c7712d"])
            langs_ja_cb.configure(state = "normal", border_color = ["#3E454A", "#4F5151"], fg_color = ["#56778c", "#c7712d"])
            langs_ko_cb.configure(state = "normal", border_color = ["#3E454A", "#4F5151"], fg_color = ["#56778c", "#c7712d"])
        save_config()
    
    # 區域規劃
    dialog.grid_columnconfigure(0, weight = 1)
    dialog.grid_rowconfigure((0, 1), weight = 0)
    dialog.grid_rowconfigure((2), weight = 1)

    f1 = ctk.CTkFrame(dialog)
    f1.grid(row = 0, column = 0, padx = 5, pady = (10, 0), sticky = "nswe")
    f1.grid_columnconfigure(0, weight = 0)
    f1.grid_rowconfigure(0, weight = 1)

    f2 = ctk.CTkFrame(dialog)
    f2.grid(row = 1, column = 0, padx = 5, pady = (0, 0), sticky = "nswe")
    f2.grid_columnconfigure((0, 1), weight = 1)
    f2.grid_rowconfigure(0, weight = 1)

    f3 = ctk.CTkFrame(dialog)
    f3.grid(row = 2, column = 0, padx = 5, pady = (0, 5), sticky = "nswe")
    f3.grid_columnconfigure(0, weight = 1)
    f3.grid_rowconfigure((0), weight = 1)

    # 自動/手動按鈕
    auto_dtype_bt = ctk.CTkButton(f1, text = "自動", font = text_font, width = 20, anchor = "c", command = toggle_auto_dtype)
    auto_dtype_bt.grid(row = 0, column = 0, padx = (5, 0), pady = 0, sticky = "nsew")

    # 精度設定
    dtype_sw_var = ctk.StringVar(value = "float32" if args.force_cpu else "float16")
    current_dtype = dtype_sw_var.get()
    dtype_sw = ctk.CTkSwitch(f1, text = "辨識模型: 全精度" if current_dtype == "float32" else "辨識模型: 半精度", 
                             height = 28, corner_radius = 4, button_length = 10, font = text_font,
                             variable = dtype_sw_var, onvalue = "float32", offvalue = "float16", command = toggle_dtype)
    dtype_sw.grid(row = 0, column = 1, padx = 5, pady = 0, sticky = "ns")
    dtype_sw.configure(state = "disabled" if auto_dtype == "ON" else "normal")

    if args.force_cpu: auto_dtype_bt.configure(state = "disabled")
    if auto_dtype == "OFF": 
        auto_dtype_bt.configure(fg_color = ["gray60", "gray60"], hover_color = ["#325882", "#A85820"])
        dtype_sw_var.set(dtype)
        dtype_sw.configure(text = "辨識模型: 全精度" if dtype == "float32" else "辨識模型: 半精度")
    else: 
        auto_dtype_bt.configure(fg_color = ["#1e8bba", "#C7712D"], hover_color = ["#325882", "#A85820"])
        dtype_sw_var.set("float32" if args.force_cpu else "float16")
        dtype_sw.configure(fg_color = "gray60", progress_color = "gray60", button_color = "gray60",
                           text = "辨識模型: 全精度" if current_dtype == "float32" else "辨識模型: 半精度")
        dtype_sw.configure(state = "disabled")

    # 限定語言模式
    langs_wd = ctk.CTkLabel(f2, text = "限定語言(可複選): ", font = text_font, anchor = "w")
    langs_wd.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = (5, 0), sticky = "w")

    langs_zh_cb_var = ctk.StringVar(value = "OFF")
    langs_zh_cb = ctk.CTkCheckBox(
        f2, text = "中文", height = 28, font = text_font, variable = langs_zh_cb_var, 
        onvalue = "ON", offvalue = "OFF", command = update_langs
    )
    langs_zh_cb.grid(row = 1, column = 0, padx = (5, 0), pady = 0, sticky = "w")

    langs_en_cb_var = ctk.StringVar(value = "OFF")
    langs_en_cb = ctk.CTkCheckBox(
        f2, text = "英文", height = 28, font = text_font, variable = langs_en_cb_var, 
        onvalue = "ON", offvalue = "OFF", command = update_langs
    )
    langs_en_cb.grid(row = 2, column = 0, padx = (5, 0), pady = (5, 0), sticky = "w")

    langs_ja_cb_var = ctk.StringVar(value = "OFF")
    langs_ja_cb = ctk.CTkCheckBox(
        f2, text = "日文", height = 28, font = text_font, variable = langs_ja_cb_var, 
        onvalue = "ON", offvalue = "OFF", command = update_langs
    )
    langs_ja_cb.grid(row = 1, column = 1, padx = 5, pady = 0, sticky = "w")

    langs_ko_cb_var = ctk.StringVar(value = "OFF")
    langs_ko_cb = ctk.CTkCheckBox(
        f2, text = "韓文", height = 28, font = text_font, variable = langs_ko_cb_var, 
        onvalue = "ON", offvalue = "OFF", command = update_langs
    )
    langs_ko_cb.grid(row = 2, column = 1, padx = 5, pady = (5, 0), sticky = "w")

    # 支援 manga-ocr 
    manga_ocr_sw_var = ctk.StringVar(value = "OFF")
    manga_ocr_sw = ctk.CTkCheckBox(
        f2, text = "漫畫 OCR (只支援日文)", height = 28, font = text_font, variable = manga_ocr_sw_var, 
        onvalue = "ON", offvalue = "OFF", command = toggle_manga_ocr
    )
    manga_ocr_sw.grid(row = 3, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = "w")

    # 初始化 CheckBox 狀態
    if langs is not None:
        langs_zh_cb_var.set("ON" if "zh" in langs else "OFF")
        langs_en_cb_var.set("ON" if "en" in langs else "OFF")
        langs_ja_cb_var.set("ON" if "ja" in langs else "OFF")
        langs_ko_cb_var.set("ON" if "ko" in langs else "OFF")
    else:
        # 沒設定，全部 OFF
        langs_zh_cb_var.set("OFF")
        langs_en_cb_var.set("OFF")
        langs_ja_cb_var.set("OFF")
        langs_ko_cb_var.set("OFF")

    if manga_ocr:
        manga_ocr_sw_var.set("ON")
        langs_zh_cb.configure(state = "disabled", border_color = "gray60", fg_color = "gray60")
        langs_en_cb.configure(state = "disabled", border_color = "gray60", fg_color = "gray60")
        langs_ja_cb.configure(state = "disabled", border_color = "gray60", fg_color = "gray60")
        langs_ko_cb.configure(state = "disabled", border_color = "gray60", fg_color = "gray60")

    # 製作捷徑
    make_ink_bt = ctk.CTkButton(f3, text = "製作快速啟動捷徑", font = text_font, width = 20, anchor = "c", command = make_ink)
    make_ink_bt.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = "ws")

    # 顯示版本號
    version_lab = ctk.CTkLabel(f3, text = "v2.1.4", font = text_font, anchor = "e", text_color = ["gray60", "gray40"])
    version_lab.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = "es")

def save_config():
    """讀取現有設定，更新後再存入 JSON 檔案"""
    config = load_config()  # 先載入現有設定

    # 更新設定
    config.update({
        "groq_key": groq_key,
        "ost_control": ost_control,
        "theme": current_theme,
        "model": model,
        "enable_short_term_memory": enable_short_term_memory,
        "auto_dtype": auto_dtype,
        "dtype": dtype,
        "langs": langs,
        "manga_ocr": manga_ocr,
        "toggle_overlay_hotkey": toggle_overlay_hotkey,
        "capture_hotkey": capture_hotkey
    })

    # 將更新後的設定存回 JSON
    with open(os.path.join(PATH, "config.json"), "w") as f:
        json.dump(config, f, indent = 4)  # `indent = 4` 讓 JSON 易讀

def prompt_sw():
    """控制 Prompt 開關"""
    sw = prompt_cb_var.get()
    global prompt_control
    prompt_control = True if sw == "ON" else False
    print(f"\033[33m[INFO] Prompt 開關: {sw}\033[0m")

def ost_sw():
    """控制 AI 自動翻譯開關"""
    sw = ost_cb_var.get()
    global ost_control
    ost_control = True if sw == "ON" else False
    save_config()
    print(f"\033[33m[INFO] AI 自動翻譯開關: {sw}\033[0m")

def restart_app():
    """重新啟動應用程式"""
    python = sys.executable  # 取得當前 Python 解釋器的路徑
    os.execl(python, python, *sys.argv)  # 重新執行當前腳本

def get_API():
    """獲取 API 並儲存"""
    global dialog_api
    if dialog_api:
        dialog_api.destroy()  # 關閉舊視窗
    dialog_api = ctk.CTkToplevel()
    dialog_api.title("輸入 API Key")
    dialog_api.geometry(f"400x40+{window.winfo_x() - int(410 * scale_factor)}+{window.winfo_y()}")
    dialog_api.grid_columnconfigure(1, weight = 1)
    dialog_api.grid_rowconfigure(0, weight = 0)
    dialog_api.attributes("-topmost", True) # 讓視窗顯示在最前面
    # dialog_api.grab_set() # 鎖定對話框
    dialog_api.after(250, dialog_api.iconbitmap, 
                    (
                        os.path.join(PATH, "icon/logo_dark.ico") 
                        if current_theme == "dark" 
                        else os.path.join(PATH, "icon/logo_light.ico")
                    )
    )

    def select_all():
        """全選輸入框內的 API Key"""
        entry.select_range(0, "end")  # 選取所有文字
        entry.focus_set()  # 設定輸入框焦點，確保全選有效

    def confirm_API():
        """送出 API Key"""
        global groq_key
        user_input = entry.get().strip()

        if user_input != groq_key:
            groq_key = user_input  # 更新 API Key
            save_config()  # 儲存到 JSON
            from tkinter import messagebox
            # 顯示警告並詢問是否重啟
            response = messagebox.askyesno("系統提示", "API Key 已更新，需要重新啟動應用程式才會生效。\n是否立即重新啟動？")
            if response:  # 如果使用者選擇 "是"
                restart_app()  # 重新啟動應用程式

        dialog_api.destroy()  # 關閉對話框

    # 標題文字
    API_wd = ctk.CTkLabel(dialog_api, text = "API Key:", font = text_font, anchor = "w")
    API_wd.grid(row = 0, column = 0, padx = (5, 0), pady = 5, sticky = "nswe")

    # 輸入框
    entry = ctk.CTkEntry(dialog_api)
    entry.grid(row = 0, column = 1, padx = (5, 0), pady = 5, sticky = "nswe")
    if groq_key:  # 如果有舊的 API Key，則填入
        entry.insert(0, groq_key)

    # 全選按鈕
    confirm_API_bt = ctk.CTkButton(dialog_api, text = "[ ]", font = text_font, width = 20, anchor = "c", command = select_all)
    confirm_API_bt.grid(row = 0, column = 2, padx = (5, 0), pady = 5, sticky = "e")

    # 載入按鈕
    confirm_API_bt = ctk.CTkButton(dialog_api, text = "套用", font = text_font, width = 40, anchor = "c", command = confirm_API)
    confirm_API_bt.grid(row = 0, column = 3, padx = 5, pady = 5, sticky = "e")

def toggle_theme():
    """切換 Light/Dark 模式"""
    global current_theme, chatroom, dialog, dialog_api # 確保使用的是全域變數
    if current_theme == "dark":
        current_theme = "light"
        ctk.set_appearance_mode(current_theme)  # 切換為 Light 模式
        window.iconbitmap(os.path.join(PATH, "icon", "logo_light.ico"))
        chatroom.iconbitmap(os.path.join(PATH, "icon", "logo_light.ico"))
        if dialog and dialog.winfo_exists(): dialog.iconbitmap(os.path.join(PATH, "icon", "logo_light.ico"))
        if dialog_api and dialog_api.winfo_exists(): dialog_api.iconbitmap(os.path.join(PATH, "icon", "logo_light.ico"))
    else:
        current_theme = "dark"
        ctk.set_appearance_mode(current_theme)  # 切換為 Dark 模式
        window.iconbitmap(os.path.join(PATH, "icon", "logo_dark.ico"))
        chatroom.iconbitmap(os.path.join(PATH, "icon", "logo_dark.ico"))
        if dialog and dialog.winfo_exists(): dialog.iconbitmap(os.path.join(PATH, "icon", "logo_dark.ico"))
        if dialog_api and dialog_api.winfo_exists(): dialog_api.iconbitmap(os.path.join(PATH, "icon", "logo_dark.ico"))
    save_config()

def open_prompt_folder():
    """打開 prompt 資料夾"""
    os.startfile(os.path.join(PATH, "prompt"))

def toggle_memory():
    """切換 AI 短期記憶力"""
    global enable_short_term_memory
    if enable_short_term_memory:
        enable_short_term_memory = False
        mem_cb_var.set("OFF")
        mem_limit_sd.configure(state = "disabled", button_color = ["#939BA2", "#AAB0B5"], progress_color = ["#939BA2", "#AAB0B5"])
        mem_limit_wd.configure(text_color = ["gray60", "gray40"])
    else:
        enable_short_term_memory = True
        mem_cb_var.set("ON")
        mem_limit_sd.configure(state = "normal", button_color = ["#1e8bba", "#C06E2F"], progress_color = ["#1e8bba", "#C06E2F"])
        mem_limit_wd.configure(text_color = ["gray14", "#D4D2CF"])
    save_config()

    if groq_available:
        chat_session.update_config(enable_short_term_memory = enable_short_term_memory) # 更新 chat_session 內部設定

def set_max_history(value):
    """設定 AI 記憶長度與歷史壓縮"""
    global max_history
    max_history = int(value) # 取整數
    mem_limit_wd.configure(text = f"記憶限制器: {max_history} 輪對話")
    if groq_available:
        chat_session.update_config(max_history = max_history) # 更新 chat_session 內部設定

def set_temperature(value):
    """設定 AI 創意力"""
    global temperature
    temperature = round(float(value), 2)  # 保留小數點後 2 位給模型使用
    display_temp = int(temperature * 100)  # 轉換為百分比的整數顯示
    temperature_wd.configure(text = f"AI 創意力: {display_temp} %")  # 顯示整數百分比
    if groq_available:
        chat_session.update_config(temperature = temperature) # 更新 chat_session 內部設定

def reset_chat():
    """重置當前對話的輸入輸出，以及歷史模型記憶"""
    chat_session.messages = []  # 清空對話歷史
    chat_session.summaries = [""]  # 重置摘要

    # 重置當前輸入輸出 token 計數
    t_input_wd.configure(text = "● 輸入: 0")
    t_output_wd.configure(text = "● 輸出: 0")

    # 更改按鈕外觀作為信號（變色或改變文字）
    resetchat_bt.configure(text = "已重製", fg_color = "firebrick")
    print("\033[32m[INFO] 已重置 AI，等待新輸入。\033[0m")

def set_model(choice):
    """變更 AI 模型"""
    global model
    model = choice  # 更新全域變數 `model`
    
    if groq_available:
        chat_session.update_config(model = model)  # 更新 chat_session 內部設定
    
    save_config()

    # 把焦點移開，讓游標從輸入框消失
    model_change_op.master.focus_set()

def pop_chatroom():
    """打開聊天室"""
    chatroom.geometry(f"630x750+{window.winfo_x() - int(640 * scale_factor)}+{window.winfo_y()}")
    chatroom.deiconify()

# 獲取螢幕資訊
def get_refresh_rate():
    """ 透過 Windows API 獲取真實的螢幕刷新率 """
    user32 = ctypes.windll.user32
    hdc = user32.GetDC(0)
    refresh_rate = ctypes.windll.gdi32.GetDeviceCaps(hdc, 116)  # 116 = VREFRESH (垂直刷新率)
    user32.ReleaseDC(0, hdc)
    return refresh_rate

# 設定動畫參數
START_HEIGHT = 195
START_WIDTH = 200
END_HEIGHT = 695
ANIMATION_DURATION = 700  # 總動畫時間 (毫秒)
refresh_rate = get_refresh_rate()
FRAME_RATE = round(1000 / refresh_rate)  # 同步幀率
TOTAL_FRAMES = ANIMATION_DURATION // FRAME_RATE  # 計算總幀數
is_expanded = False  # 初始化視窗狀態

# 貝茲曲線函數 (Cubic Bezier)
def cubic_bezier(t, p0, p1, p2, p3):
    """ Cubic Bezier 曲線計算公式 """
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3

def ease_in_out_bezier(progress):
    """ 使用 Cubic Bezier 計算 ease 軌跡 """
    return cubic_bezier(progress, 0, 0.5, -0.5, 1)  # 參數可調整平滑程度

def get_low_y():
    """ 固定一個底部的 y 座標，計算新的 y1 """
    current_y = window.winfo_y()
    current_window_height = END_HEIGHT if is_expanded else START_HEIGHT
    return current_y - current_window_height

# 視窗動畫
def smooth_expand(target_height, frame = 0):
    """ 平滑展開視窗 (使用貝茲曲線) """
    if frame > TOTAL_FRAMES:
        return  # 動畫結束

    progress = frame / TOTAL_FRAMES  # 取得 0~1 之間的進度
    ease_value = ease_in_out_bezier(progress)  # 使用貝茲曲線計算平滑進度
    new_height = int(START_HEIGHT + (target_height - START_HEIGHT) * ease_value)

    current_width = int(window.winfo_width() / scale_factor)
    current_x = window.winfo_x()
    current_y = window.winfo_y()

    window.geometry(f"{current_width}x{new_height}+{current_x}+{current_y}")
    window.after(FRAME_RATE, lambda: smooth_expand(target_height, frame + 1))

def smooth_collapse(target_height, frame = 0):
    """ 平滑縮小視窗 (使用 Bezier 緩動) """
    if frame > TOTAL_FRAMES:
        return  # 動畫結束

    progress = frame / TOTAL_FRAMES
    ease_value = ease_in_out_bezier(progress)
    new_height = int(END_HEIGHT - (END_HEIGHT - target_height) * ease_value)
    
    current_width = int(window.winfo_width() / scale_factor)
    current_x = window.winfo_x()
    current_y = window.winfo_y()

    window.geometry(f"{current_width}x{new_height}+{current_x}+{current_y}")
    window.after(FRAME_RATE, lambda: smooth_collapse(target_height, frame + 1))

def toggle_window_size():
    """ 切換視窗大小 (平滑展開/收縮) """
    global is_expanded
    if is_expanded:
        f2.grid_remove()  # 收起時隱藏 f2
        smooth_collapse(START_HEIGHT)
        setting_bt.configure(text="▼ 展開額外功能")
    else:
        smooth_expand(END_HEIGHT)
        setting_bt.configure(text="▲ 收起額外功能")
        window.after(ANIMATION_DURATION, lambda: f2.grid())  # 動畫結束後才顯示 f2
    is_expanded = not is_expanded

def toggle_overlay_visibility(event = None):
    """切換所有 overlay 顯示與隱藏狀態"""
    global overlay_visible

    if overlay_visible:
        # 隱藏所有 overlay
        for ov in overlay_windows:
            try:
                ov.withdraw() # 隱藏
            except:
                pass # 保險處理，避免 overlay 被關閉後報錯
        overlay_visible = False
    else:
        # 顯示所有 overlay
        for ov in overlay_windows:
            try:
                ov.deiconify() # 顯示
            except:
                pass # 保險處理，避免 overlay 被關閉後報錯
        overlay_visible = True
    save_config()
    

# GUI    
window = ctk.CTk() # 建立主視窗
freeze_overlay = FreezeOverlay(window)
# freeze_overlay.show()
# freeze_overlay.hide()
if groq_available:
    chatroom = chatroomWindow(current_theme, chat_session, groq_key, token_update_callback = update_token_display) # 建立聊天室視窗
    chatroom.withdraw() # 聊天室視窗預設隱藏
    chatroom.protocol("WM_DELETE_WINDOW", chatroom.withdraw) # 攔截關閉行為 → 改為隱藏（withdraw）

# 獲取螢幕的寬高和縮放比例
def get_scale_factor():
    """使用 Windows API 取得 Windows 設定的縮放比例"""
    try:
        shcore = ctypes.windll.shcore
        return shcore.GetScaleFactorForDevice(0) / 100.0  # 例如 125% → 1.25
    except Exception:
        return 1.0  # 預設 100%

scale_factor = get_scale_factor()
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

# 設定視窗大小
window_width = START_WIDTH
window_height = START_HEIGHT

# 計算視窗位置
x_position = screen_width - int(window_width * scale_factor) - int(50 * scale_factor)
y_position = int(50 * scale_factor)

# 設定視窗位置
window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

# 設定標題與屬性
window.title("BCR")
window.resizable(True, True)
window.iconbitmap(
    os.path.join(PATH, "icon", "logo_dark.ico") 
    if current_theme == "dark" 
    else os.path.join(PATH, "icon", "logo_light.ico")
)
appid = 'KuoCT.Miffon.BeeSeeR.BCR'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

# 讓視窗保持最上層
window.attributes("-topmost", True) # 讓視窗顯示在最前面
window.attributes("-disabled", False)

# 設定主題
ctk.set_appearance_mode(current_theme)
ctk.set_default_color_theme(os.path.join(PATH, "theme", "nectar.json"))

# 設定預設字體、顏色
title_font = ctk.CTkFont(family = "Helvetica", size = 24, weight = "bold")
text_font = ctk.CTkFont(family = "Helvetica", size = 14, weight = "bold")

# 建立主視窗框架
window.grid_columnconfigure(0, weight = 1)
window.grid_rowconfigure(0, weight = 0)
window.grid_rowconfigure(1, weight = 1)

# 建立底板 (初始APP)
f1 = ctk.CTkFrame(master = window, corner_radius = 10)
f1.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = "new")
f1.grid_columnconfigure((0), weight = 1)
f1.grid_rowconfigure((0), weight = 1)

# 螢幕截圖按鈕
capture_bt = ctk.CTkButton(master = f1, text = "Capture", font = title_font, height = 70,
                           anchor = "c", command = run_wincap)
capture_bt.bind("<Button-3>", lambda e: set_OCR_config())
capture_bt.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = "swe")

# User Prompt 開關
prompt_cb_var = tk.StringVar(master = f1, value = "ON")
prompt_cb = ctk.CTkCheckBox(master = f1, text = "複製 Prompt (提示詞)", font = text_font,
                           variable = prompt_cb_var, onvalue = "ON", offvalue = "OFF",
                           command = prompt_sw)
prompt_cb.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = "w")

# AI 自動翻譯
ost_cb_var = tk.StringVar(master = f1, value = "OFF" if not ost_control else "ON")
ost_cb = ctk.CTkCheckBox(master = f1, text = "AI 自動翻譯", font = text_font,
                           variable = ost_cb_var, onvalue = "ON", offvalue = "OFF",
                           command = ost_sw)
ost_cb.grid(row = 2, column = 0, padx = 5, pady = 5, sticky = "w")

API_bt = ctk.CTkButton(master = f1, text = "API", font = text_font, width = 40,
                           anchor = "c", command = get_API)
API_bt.grid(row = 2, column = 0, padx = 5, pady = 5, sticky = "e")

# 展開額外功能按鈕
setting_bt = ctk.CTkButton(master = f1, text = "▼ 展開額外功能", font = text_font,
                           anchor = "c", command = toggle_window_size)
setting_bt.grid(row = 3, column = 0, padx = 5, pady = 5, sticky = "we")

# 建立底板 (額外功能)
f2 = ctk.CTkFrame(master = window, corner_radius = 10)
f2.grid(row = 1, column = 0, padx = 5, pady = 8, sticky = "nswe")
f2.grid_columnconfigure((0), weight = 1)
f2.grid_rowconfigure((0), weight = 0)
f2.grid_rowconfigure((15), weight = 1)
f2.grid_remove()  # 預設隱藏 f2

# 擴充功能
theme_bt = ctk.CTkButton(master = f2, text = "主題切換", font = text_font, height = 28,
                           anchor = "c", command = toggle_theme)
theme_bt.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = "we")

pfolder_bt = ctk.CTkButton(master = f2, text = "Prompt 資料夾", font = text_font, height = 28,
                           anchor = "c", command = open_prompt_folder)
pfolder_bt.grid(row = 1, column = 0, padx = 5, pady = (0, 5), sticky = "we")

chatroom_bt = ctk.CTkButton(
    master = f2, text = "AI 聊天室/紀錄", font = text_font, height = 28, anchor = "c", 
    command = lambda: pop_chatroom()
)
chatroom_bt.grid(row = 2, column = 0, padx = 5, pady = (0, 5), sticky = "we")

resetchat_bt = ctk.CTkButton(master = f2, text = "重製 AI 記憶", font = text_font, height = 28,
                           anchor = "c", command = reset_chat)
resetchat_bt.grid(row = 3, column = 0, padx = 5, pady = (0, 5), sticky = "we")

# 水平線 1
sep1 = ctk.CTkFrame(master = f2, fg_color = "gray", height = 2)
sep1.grid(row = 4, column = 0, padx = 5, pady = 5, sticky = "we")

# AI 記憶模塊
mem_cb_var = tk.StringVar(master = f2, value = "OFF" if not enable_short_term_memory else "ON")
mem_cb = ctk.CTkCheckBox(master = f2, text = "短期記憶力", font = text_font,
                           variable = mem_cb_var, onvalue = "ON", offvalue = "OFF",
                           command = toggle_memory)
mem_cb.grid(row = 5, column = 0, padx = 5, pady = 5, sticky = "w")

# AI 記憶壓縮器
mem_limit_wd = ctk.CTkLabel(master = f2, text = "記憶壓縮器: 3 輪對話", font = text_font, anchor = "w", height = 10)
mem_limit_wd.grid(row = 6, column = 0, padx = 5, pady = 5, sticky = "we")
mem_limit_sd = ctk.CTkSlider(master = f2, from_ = 2, to = 10, number_of_steps = 200, height = 20,
                               command = set_max_history)
mem_limit_sd.set(max_history)  # 設定滑桿初始值
mem_limit_sd.grid(row = 7, column = 0, padx = 5, pady = (0, 5), sticky = "we")

# AI 創意力滑桿
temperature_wd = ctk.CTkLabel(master = f2, text = "AI 創意力: 60 %", font = text_font, anchor = "w", height = 10)
temperature_wd.grid(row = 8, column = 0, padx = 5, pady = 5, sticky = "we")
temperature_sd = ctk.CTkSlider(master = f2, from_ = 0.0, to = 1.0, number_of_steps = 200, height = 20,
                               command = set_temperature)
temperature_sd.set(temperature)  # 設定滑桿初始值
temperature_sd.grid(row = 9, column = 0, padx = 5, pady = (0, 5), sticky = "we")

# Token 計數
token_wd = ctk.CTkLabel(master = f2, text = "Token 計數器", font = text_font, anchor = "w", height = 10)
token_wd.grid(row = 10, column = 0, padx = 5, pady = (20, 5), sticky = "we")
t_input_wd = ctk.CTkLabel(master = f2, text = "● 輸入: 0", font = text_font, anchor = "w", height = 10)
t_input_wd.grid(row = 11, column = 0, padx = (10, 5), pady = 2, sticky = "we")
t_output_wd = ctk.CTkLabel(master = f2, text = "● 輸出: 0", font = text_font, anchor = "w", height = 10)
t_output_wd.grid(row = 12, column = 0, padx = (10, 5), pady = 2, sticky = "we")
t_in_total_wd = ctk.CTkLabel(master = f2, text = "● 累計輸入: 0", font = text_font, anchor = "w", height = 10)
t_in_total_wd.grid(row = 13, column = 0, padx = (10, 5), pady = 2, sticky = "we")
t_out_total_wd = ctk.CTkLabel(master = f2, text = "● 累計輸出: 0", font = text_font, anchor = "w", height = 10)
t_out_total_wd.grid(row = 14, column = 0, padx = (10, 5), pady = (2, 5), sticky = "we")

# 模型切換器
model_change_wd = ctk.CTkLabel(master = f2, text = "目前使用的 AI 模型", font = text_font, anchor = "w", height = 10)
model_change_wd.grid(row = 15, column = 0, padx = 5, pady = (15, 5), sticky = "swe")
model_change_op = ctk.CTkComboBox(
    master = f2, 
    values = ["llama-3.3-70b-versatile", "llama-3.3-70b-specdec", "llama-3.1-8b-instant", "gemma2-9b-it"], 
    command = set_model
)
model_change_op.set(model)
model_change_op.grid(row = 16, column = 0, padx = 5, pady = (0, 5), sticky = "we")

# 綁定使用者輸入的事件
entry_widget = model_change_op._entry
entry_widget.bind("<Return>", lambda e: set_model(model_change_op.get())) # 傳入當前輸入的模型名稱
entry_widget.bind("<FocusOut>", lambda e: set_model(model_change_op.get()))

# 若 groq 不可用則禁用相關功能
if not groq_available:
    API_bt.configure(fg_color = ["gray60", "gray50"], hover_color = ["gray40", "gray40"])
    ost_cb.configure(state = "disabled")
    ost_cb_var.set("OFF") 
    chatroom_bt.configure(state = "disabled")
    resetchat_bt.configure(state = "disabled")
    temperature_sd.configure(state = "disabled", button_color = ["#939BA2", "#AAB0B5"], progress_color = ["#939BA2", "#AAB0B5"])
    mem_cb_var.set("OFF") 
    mem_cb.configure(state = "disabled")
    model_change_op.configure(state = "disabled")
    temperature_wd.configure(text_color = ["gray60", "gray40"])
    token_wd.configure(text_color = ["gray60", "gray40"])
    t_input_wd.configure(text_color = ["gray60", "gray40"])
    t_output_wd.configure(text_color = ["gray60", "gray40"])
    t_in_total_wd.configure(text_color = ["gray60", "gray40"])
    t_out_total_wd.configure(text_color = ["gray60", "gray40"])
    model_change_wd.configure(text_color = ["gray60", "gray40"])

if mem_cb_var.get() == "OFF":
    mem_limit_sd.configure(state = "disabled", button_color = ["#939BA2", "#AAB0B5"], progress_color = ["#939BA2", "#AAB0B5"])
    mem_limit_wd.configure(text_color = ["gray60", "gray40"])

def HotkeyConverter(hotkey):
    """
    將 <Key-a> 或 <Control-Alt-F> 類格式轉成 keyboard 套件用格式
    """
    if not hotkey.startswith("<") or not hotkey.endswith(">"):
        return hotkey.lower()

    content = hotkey[1:-1]  # 移除 <>
    parts = content.split("-")

    keyboard_parts = []
    shift_needed = False
    key_found = None

    replacements = {
        "control": "ctrl",
        "return": "enter",
        "escape": "esc",
        "space": "space",
        "prior": "page up",
        "next": "page down",
        "backspace": "backspace",
        "delete": "delete",
        "tab": "tab",
        "shift": "shift",
        "alt": "alt",
        "meta": "windows",
        "key": "",  # 移除 key 前綴
    }

    for part in parts:
        part_stripped = part.lower()

        # 跳過空字串（可能是 'key' 被去除後）
        if not part_stripped:
            continue

        # 大寫字母處理（可能需要 shift）
        if len(part) == 1 and part.isalpha():
            if part.isupper():
                shift_needed = True
                key_found = part.lower()
            else:
                key_found = part.lower()
        else:
            mapped = replacements.get(part_stripped, part_stripped)
            keyboard_parts.append(mapped)

    # 加入 shift 修飾（若需要且未已存在）
    if shift_needed and "shift" not in keyboard_parts:
        keyboard_parts.append("shift")

    if key_found:
        keyboard_parts.append(key_found)

    return "+".join(keyboard_parts)

# 設定快捷鍵
keyboard.add_hotkey(HotkeyConverter(capture_hotkey), lambda: window.after(10, run_wincap)) # 螢幕截圖 (全域)
keyboard.add_hotkey(HotkeyConverter(toggle_overlay_hotkey), toggle_overlay_visibility) # 隱藏懸浮窗 (全域)
capture_bt.bind("<Control-Button-1>", toggle_overlay_visibility) # 隱藏懸浮窗

# 產生 config 檔案
save_config()

# 啟動 GUI
if __name__ == "__main__":
    with open(os.path.join(PATH, "GUI_open.flag"), "w") as f:
        f.write("GUI_is_opened")
    print("\033[32m[INFO] BeeSeeR GUI 已啟動，系統正常運行\033[0m")
    window.mainloop()
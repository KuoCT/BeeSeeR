import portalocker
import os
import sys
import argparse

# 解析命令列參數
parser = argparse.ArgumentParser(description = "BeeSeeR 控制參數")
parser.add_argument("-c", "--force-cpu", action = "store_true", help = "強制使用 CPU 模式")
parser.add_argument("-a", "--all", action = "store_false", help = "完整輸出模式 (debug 參數)")
parser.add_argument("-b", "--background", action = "store_true", help = "背景執行模式參數 (只在.bat腳本執行時有效)")
args = parser.parse_args()

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__))) # 設定相對路徑

# 判斷是否為 Nuitka 環境
is_nuitka = "__compiled__" in globals()

# 將需要讀取/寫入的文件另存到 LOCALAPPDATA 
if is_nuitka: 
    # print("執行檔模式")
    APPDATA = os.path.join(os.getenv("LOCALAPPDATA"), "BeeSeeR")
    import shutil
    def copy_files(src, dst):
        """
        複製資料夾(src)到指定位置(dst):
        - 只針對最上層檔案
        - 若目標檔案不存在或需要更新則複製
        """
        if not os.path.exists(dst): os.makedirs(dst, exist_ok = True)

        for file_name in os.listdir(src):
            src_file = os.path.join(src, file_name)
            dst_file = os.path.join(dst, file_name)

            # 確保只處理檔案（忽略子資料夾）
            if not os.path.isfile(src_file):
                continue

            try:
                if is_file_updated(src_file, dst_file):
                    shutil.copy2(src_file, dst_file)
            except Exception as e:
                # print(f"無法複製 {src_file}: {e}")
                pass

    def is_file_updated(file1, file2):
        """比較兩個檔案的大小不同或來源較新回傳 True，否則回傳 False"""
        # 先比大小，不同直接回傳 True
        if os.path.getsize(file1) != os.path.getsize(file2):
            return True

        # 比對修改時間（如果來源更新才更新）
        if os.path.getmtime(file1) > os.path.getmtime(file2):
            return True

        # 如果都沒有變動，回傳 False
        return False
    
    copy_files(os.path.join(PATH, "persona"), os.path.join(APPDATA, "persona"))
else:
    # print("開發者模式")
    APPDATA = PATH  # 如果是腳本使用當前目錄

# 檢查是否已經有執行中的程式
lock_file_path = os.path.join(os.getenv("TEMP"), "beeseer.lock")
lock_file = open(lock_file_path, "w")

try:
    # 嘗試獲取檔案鎖
    portalocker.lock(lock_file, portalocker.LOCK_EX | portalocker.LOCK_NB)
except portalocker.exceptions.LockException:
    import tkinter as tk
    from tkinter import messagebox
    if args.background:
        with open(os.path.join(APPDATA, "GUI_open.flag"), "w") as f:
            f.write("GUI_is_opened")
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("偵測到重複執行", "BeeSeeR 正在運行中，無須重複啟動程式。")
    sys.exit(0)

# 根據 `--force-cpu` 設置環境變數
if args.force_cpu:
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # 設定 CUDA 無效化

import json
import tkinter as tk
import customtkinter as ctk
import threading
from ocr.WinCap import WindowCapture
from ocr.WinCap import MouseTooltip
from ocr.overlay import overlayWindow
from ocr.freeze import FreezeOverlay
from tool.ModelSetting import ModelSetting
from tool.APISetting import APISetting
from tool.PersonaEditor import PersonaEditor
import llm.chat as chat
from llm.chatroom import chatroomWindow
import ctypes
import re
import keyboard
import time

# >> Nuitka 補丁 ==============================================================

import transformers.image_utils
from PIL import Image

# 修補 transformers 缺少的 Resampling 屬性（舊 Pillow 不支援）
if not hasattr(transformers.image_utils, "PILImageResampling"):
    transformers.image_utils.PILImageResampling = Image.Resampling
    # print("\033[32m[INFO] 手動補上 PILImageResampling\033[0m")

# 避免 transformers 執行 inspect.getsource() 導致的錯誤
os.environ["TRANSFORMERS_NO_DOCSTRINGS"] = "1"  # 優雅處理 (無效)
try: # 再加一層防禦：如果 decorator 還是跑進來就 patch 掉
    import transformers.utils.doc
    transformers.utils.doc.get_docstring_indentation_level = lambda func: 4
except Exception as e:
    print("[警告] 無法 patch transformers docstring 函式：", e)

# << Nuitka 補丁 ==============================================================

def load_config():
    """讀取設定檔案"""
    if os.path.exists(os.path.join(APPDATA, "config.json")):
        with open(os.path.join(APPDATA, "config.json"), "r", encoding = "utf-8") as f:
            return json.load(f)
    return {}  # 如果沒有設定檔，回傳空字典

# 定義全域變數
settings  = load_config() # 讀取設定檔案
toggle_overlay_hotkey = settings.get("toggle_overlay_hotkey", "ctrl+shift+windows+a") # 快捷鍵: 切換 overlay 顯示/隱藏
capture_hotkey = settings.get("capture_hotkey", "ctrl+shift+windows+s") # 快捷鍵: Capture
current_theme = settings.get("theme", "dark") # 讀取主題設定
ocr_model = settings.get("ocr_model", "surya") # 選擇 OCR 模型
langs = settings.get("langs", None) # Surya-OCR: 限定語言
auto_dtype = settings.get("auto_dtype", "ON") # Surya-OCR: 自動選擇模型精度
dtype = settings.get("dtype", None) # Surya-OCR: 手動選擇模型精度
google_ocr_key = settings.get("google_ocr_key", None) # Google Vision API Key 文字辨識
groq_key = settings.get("groq_key", None) # Groq API Key 翻譯 / 聊天 語言模型
ost_control = settings.get("ost_control", False) # on-screen translation (AI 自動翻譯)
model = settings.get("model", "llama-3.3-70b-versatile") # 預設語言模型 
enable_short_term_memory = settings.get("enable_short_term_memory", True) # 短期記憶開關
prompt_copy = settings.get("prompt_copy", True) # 複製提示詞控制開關
# ============================================================================
mocr = None # 初始化 OCR 模型
recognition_predictor = None # 初始化 OCR 模型
detection_predictor = None # 初始化 OCR 模型
silent = args.all # 語言模型靜默模式
max_history = 3 # 短期記憶長度
temperature = 0.5 # AI 創意力
cb_coords = None # 初始化座標
last_response = None # 初始化 AI 回應
total_prompt_tokens = 0  # 初始化發送的 token 數
total_completion_tokens = 0  # 初始化 AI 回應的 token 數
groq_available = False # AI 自動翻譯功能，預設為鎖定
dialog = None  # 初始化對話框
dialog_api = None  # 初始化 API 對話框
overlay_windows = [] # 加入 overlay_windows 管理清單
overlay_visible = True # 初始化 overlay 顯示狀態
hotkey_enabled = True # 初始化快捷鍵狀態
# ============================================================================
if args.force_cpu or auto_dtype == "NO": dtype = None # 強制 CPU 計算時使用自動模型精度

# 如果 API Key 非空，解鎖 AI 自動翻譯功能
if groq_key:
    groq_available = True
        
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

def receive_coordinates(coords):
    """Callback 函數，獲取座標"""
    global cb_coords
    cb_coords = coords
    print(f"\033[36m[INFO] 即時回傳選取範圍座標: {coords}\033[0m")

# 螢幕文字辨識
def run_wincap(coords = None):
    """啟動 WindowCapture 取得螢幕訊息"""
    global ocr_model, hotkey_enabled

    if not hotkey_enabled:
        return  # 忽略重複觸發
    
    hotkey_enabled = False  # 禁用快捷鍵

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

        while not stop_event.is_set():
            # 更新畫面
            loading_tip.label.configure(
                text = f"載入分析模型 {frames[idx]}"
            )
            loading_tip.update()
            idx = (idx + 1) % total
            time.sleep(0.2)

    def load_model_and_launch():
        """背景載入模型，載入完再啟動 WindowCapture"""
        global mocr, recognition_predictor, detection_predictor

        # 啟動 loading 動畫用的 stop_flag
        stop_event = threading.Event()

        # 統一的錯誤處理函式
        def handle_model_not_found():
            global hotkey_enabled
            stop_event.set()  # 結束動畫
            loading_tip.destroy()
            capture_bt.configure(state = "normal")  # 解鎖按鈕
            hotkey_enabled = True  # 恢復快捷鍵

            # 延遲 100 毫秒再建立 tooltip，讓 window 回穩
            def show_tooltip():
                tooltip = MouseTooltip(window, follow = False, text = "找不到模型文件")
                tooltip.update()
                tooltip.after(1000, tooltip.destroy)

            window.after(100, show_tooltip)

        # OCR 模型選擇
        # Manga-OCR 模式
        if ocr_model == "manga":
            if not mocr:
                threading.Thread(target = simulate_loop_progress, args = (stop_event,), daemon = True).start()
                from manga_ocr import MangaOcr
                import logging
                logging.getLogger("transformers").setLevel(logging.ERROR)
                checkpoint_path = os.path.join(PATH, "checkpoint", "manga-ocr")
                if not os.path.exists(checkpoint_path): # 檢查 checkpoint 資料夾是否存在
                    handle_model_not_found()
                    return
                mocr = MangaOcr(pretrained_model_name_or_path = checkpoint_path)
            # 清除其他模式
            recognition_predictor = None
            detection_predictor = None

        # Surya-OCR 模式
        elif ocr_model == "surya":
            if not recognition_predictor and not detection_predictor:
                threading.Thread(target = simulate_loop_progress, args = (stop_event,), daemon = True).start()
                from surya.recognition import RecognitionPredictor
                from surya.detection import DetectionPredictor
                
                checkpoint_path = os.path.join(PATH, "checkpoint", "surya-ocr", "text_recognition")          
                if not os.path.exists(checkpoint_path): # 檢查 checkpoint 資料夾是否存在
                    handle_model_not_found()
                    return
                recognition_predictor = RecognitionPredictor(dtype = dtype, checkpoint = checkpoint_path)

                checkpoint_path = os.path.join(PATH, "checkpoint", "surya-ocr", "text_detection")
                if not os.path.exists(checkpoint_path): # 檢查 checkpoint 資料夾是否存在
                    handle_model_not_found()
                    return
                detection_predictor = DetectionPredictor(dtype = dtype, checkpoint = checkpoint_path)
            # 清除其他模式
            mocr = None

        # Google-OCR 模式
        elif ocr_model == "google":
            # 清除其他模式
            recognition_predictor = None
            detection_predictor = None
            mocr = None

        else:
            raise ValueError("Unsupported OCR model") # 不支援的 OCR 模式

        # 模型載入完 → 回主執行緒建立 WindowCapture
        def launch_window():
            stop_event.set()  # 結束動畫
            loading_tip.destroy()
            freeze_overlay.show() # 凍結畫面

            app = WindowCapture(
                window,
                prompt_copy = prompt_copy,
                on_capture = receive_coordinates,
                on_result = handle_result,
                prompt = PerEdit.updated_persona["Prompt"],
                ocr_model = ocr_model,
                google_ocr_key = google_ocr_key,
                google_ocr_feature = ModSet.google_ocr_feature,
                dtype = dtype,
                langs = langs,
                mocr = mocr,
                recognition_predictor = recognition_predictor,
                detection_predictor = detection_predictor,
                bind = not bool(coords), # 如果有座標，取消滑鼠綁定 (自動操作)     
            )

            if bool(coords):
                app.auto_capture(coords)
            else:
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
        print("\n\033[33m[INFO] 光學字元辨識 (OCR) 結果：\033[0m")
        print(ext)
        if not ost_control: capture_bt.configure(state = "normal") # 解鎖按鈕
    else:
        print("\033[31m[INFO] 無法獲取文字辨識結果。\033[0m")
        # 顯示短暫提示：無法獲取文字辨識結果
        tooltip = MouseTooltip(window, follow = False, text = "無法獲取文字辨識結果")
        tooltip.update()  # 強制顯示一次，避免閃爍
        tooltip.after(1000, tooltip.destroy)  # 1 秒後自動銷毀
        capture_bt.configure(state = "normal") # 解鎖按鈕
        return

    # 自動翻譯
    # ext = "text "*2000 # 測試
    if groq_available and ost_control and isinstance(ext, str) and ext.strip() and is_dragging:
        # 粗略統計單詞數
        word_count = estimate_word_count(ext)
        print(f"\033[36m[INFO] OCR 結果分析: {word_count} 單字\033[0m")
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
                capture_bt.configure(state = "normal") # 解鎖按鈕
                return  # 使用者選擇取消，不進行翻譯

        def translate_in_background():
            global last_response

            try:
                # 讀取提示詞與發送至 Groq
                persona = PerEdit.updated_persona
                system_prompt = persona["Translator_persona"]
                memory_prompt = persona["Memory_persona"]
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

                # 顯示翻譯結果 overlay 
                overlay = overlayWindow(window, last_response, cb_coords, scale_factor, run_again, APPDATA = APPDATA)
                overlay_windows.append(overlay)
                overlay.deiconify()

                # 更新 token 計數器
                total_prompt_tokens += prompt_tokens
                total_completion_tokens += completion_tokens
                t_input_wd.configure(text=f"• 輸入: {prompt_tokens}")
                t_output_wd.configure(text=f"• 輸出: {completion_tokens}")
                t_in_total_wd.configure(text=f"• 累計輸入: {total_prompt_tokens}")
                t_out_total_wd.configure(text=f"• 累計輸出: {total_completion_tokens}")

                # 更新 chatroom
                chatroom.append_chatbubble(role = "User", message = user_input)
                chatroom.append_chatbubble(role = chat_session.model, message = last_response)
                chatroom.append_chatlog(role = "User", message = user_input)
                chatroom.append_chatlog(role = chat_session.model, message = last_response)

                # 按鈕狀態
                resetchat_bt.configure(text = "AI 重置 / 記憶刪除", fg_color = ["#1e8bba", "#C7712D"])

                # 解鎖按鈕
                capture_bt.configure(state = "normal")

            # 回到主線更新畫面
            window.after(0, update_ui)

        # 顯示提示（主線）
        loading_tip = MouseTooltip(window, follow=True, text="AI 處理中...")
        loading_tip.update()

        # 背景執行 AI 翻譯任務
        threading.Thread(target = translate_in_background, daemon = True).start()

def run_again(coords):
    """Callback 函數，再翻譯一次"""
    run_wincap(coords)

def update_token_display(prompt_tokens, completion_tokens):
    """更新主視窗 token 顯示"""
    # 更新 token 計數器
    global total_prompt_tokens
    global total_completion_tokens
    
    total_prompt_tokens += prompt_tokens
    total_completion_tokens += completion_tokens

    t_input_wd.configure(text=f"• 輸入: {prompt_tokens}")
    t_output_wd.configure(text=f"• 輸出: {completion_tokens}")
    t_in_total_wd.configure(text=f"• 累計輸入: {total_prompt_tokens}")
    t_out_total_wd.configure(text=f"• 累計輸出: {total_completion_tokens}")

    # 還原按鈕
    resetchat_bt.configure(text = "AI 重置 / 記憶刪除", fg_color = ["#1e8bba", "#C7712D"])

def open_ModelSetting():
    """開啟模型設定視窗"""
    ModSet.geometry(f"{ModSet.w}x{ModSet.h}+{window.winfo_x() - int((ModSet.w + 10) * scale_factor)}+{window.winfo_y()}")
    ModSet.deiconify()

def update_ModelSetting():
    """更新模型設定"""
    global capture_hotkey, toggle_overlay_hotkey, auto_dtype, dtype, langs, ocr_model
    ocr_model = ModSet.ocr_model
    langs = ModSet.langs
    auto_dtype = ModSet.auto_dtype
    dtype = ModSet.dtype
    capture_hotkey = ModSet.capture_hotkey
    toggle_overlay_hotkey = ModSet.toggle_overlay_hotkey

def open_APISetting():
    """開啟 API 設定視窗"""
    APISet.geometry(f"{APISet.w}x{APISet.h}+{window.winfo_x() - int((APISet.w + ModSet.w + 20) * scale_factor)}+{window.winfo_y()}")
    APISet.deiconify()

def update_APISetting():
    """更新 API 設定"""
    global google_ocr_key, groq_key
    google_ocr_key = APISet.google_ocr_key
    groq_key = APISet.groq_key
    restart_app()

def open_chatroom():
    """打開聊天室"""
    chatroom.geometry(f"650x750+{window.winfo_x() - int(660 * scale_factor)}+{window.winfo_y()}")
    chatroom.deiconify()

def link_persona():
    """將人格指令連結到聊天室"""
    chatroom.updated_persona = PerEdit.updated_persona  # 更新聊天室的 persona 變數

def open_PersonaEditor(): # 打開子視窗的函數
    PerEdit.geometry(f"{PerEdit.w}x{PerEdit.h}+{window.winfo_x() - int((APISet.w + ModSet.w + 20) * scale_factor)}+{window.winfo_y() + int((APISet.h - 50)) * scale_factor}")
    PerEdit.deiconify() # 顯示子視窗

def restart_app():
    """根據是否被打包，選擇適當的重啟方式"""
    from tkinter import messagebox
    import subprocess
    # 顯示警告並詢問是否重啟
    response = messagebox.askyesno("系統提示", "設定已更新，需要重新啟動應用程式才會生效。\n是否立即重新啟動？")
    if response:  # 如果使用者選擇 "是"
        try:
            # 釋放程式鎖
            lock_file.close()
        except Exception as e:
            messagebox.showerror("錯誤", f"無法釋放或刪除鎖：{e}")
            return

        exe = sys.executable
        try:
            # 安全釋放鎖（很重要）
            lock_file.close()
        except Exception as e:
            print(f"\033[31m[ERROR] 無法釋放或刪除鎖：{e}\033[0m")

        if is_nuitka:  # 判斷是否為打包環境
            # 打包環境，直接執行自身 (sys.executable 就是 .exe 檔)
            subprocess.Popen([exe], creationflags = subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            # 開發環境，執行 Python + 參數
            subprocess.Popen([exe, *sys.argv])

        sys.exit(0)

def save_config():
    """只有當設定異動時，才更新 config.json"""
    old_config = load_config()
    
    # 準備要寫入的內容
    new_config = {
        "ost_control": ost_control,
        "theme": current_theme,
        "model": model,
        "enable_short_term_memory": enable_short_term_memory,
        "prompt_copy": prompt_copy
    }
    
    # 只有內容不同時才寫入
    if old_config != {**old_config, **new_config}:
        old_config.update(new_config)
        with open(os.path.join(APPDATA, "config.json"), "w", encoding = "utf-8") as f:
            json.dump(old_config, f, ensure_ascii = False, indent = 4)
        # print("\033[32m[INFO] 設定檔已更新\033[0m")
    else:
        # print("\033[34m[INFO] 設定無變更，跳過寫入\033[0m")
        pass

# 產生 config 檔案
save_config()

def prompt_sw():
    """控制 Prompt 開關"""
    sw = prompt_cb_var.get()
    global prompt_copy
    prompt_copy = True if sw == "ON" else False
    save_config()
    # print(f"\033[33m[INFO] Prompt 開關: {sw}\033[0m")

def ost_sw():
    """控制 AI 自動翻譯開關"""
    sw = ost_cb_var.get()
    global ost_control
    ost_control = True if sw == "ON" else False
    save_config()
    # print(f"\033[33m[INFO] AI 自動翻譯開關: {sw}\033[0m")

def toggle_theme():
    """切換 Light/Dark 模式"""
    global current_theme, chatroom, dialog, dialog_api # 確保使用的是全域變數
    if current_theme == "dark":
        current_theme = "light"
        ctk.set_appearance_mode(current_theme)  # 切換為 Light 模式
        window.iconbitmap(os.path.join(PATH, "icon", "logo_light.ico"))
        if chatroom and chatroom.winfo_exists(): 
            chatroom.iconbitmap(os.path.join(PATH, "icon", "logo_light.ico"))
            chatroom.current_theme = "light"
        if ModSet and ModSet.winfo_exists(): ModSet.iconbitmap(os.path.join(PATH, "icon", "logo_light.ico"))
        if APISet and APISet.winfo_exists(): APISet.iconbitmap(os.path.join(PATH, "icon", "logo_light.ico"))
        if PerEdit and PerEdit.winfo_exists(): PerEdit.iconbitmap(os.path.join(PATH, "icon", "logo_light.ico"))
    else:
        current_theme = "dark"
        ctk.set_appearance_mode(current_theme)  # 切換為 Dark 模式
        window.iconbitmap(os.path.join(PATH, "icon", "logo_dark.ico"))
        if chatroom and chatroom.winfo_exists(): 
            chatroom.iconbitmap(os.path.join(PATH, "icon", "logo_dark.ico"))
            chatroom.current_theme = "dark"
        if ModSet and ModSet.winfo_exists(): ModSet.iconbitmap(os.path.join(PATH, "icon", "logo_dark.ico"))
        if APISet and APISet.winfo_exists(): APISet.iconbitmap(os.path.join(PATH, "icon", "logo_dark.ico"))
        if PerEdit and PerEdit.winfo_exists(): PerEdit.iconbitmap(os.path.join(PATH, "icon", "logo_dark.ico"))
    save_config()

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
    t_input_wd.configure(text = "• 輸入: 0")
    t_output_wd.configure(text = "• 輸出: 0")

    # 更改按鈕外觀作為信號（變色或改變文字）
    resetchat_bt.configure(text = "已重置", fg_color = "firebrick")
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

# 獲取螢幕資訊
def get_refresh_rate():
    """ 透過 Windows API 獲取真實的螢幕刷新率 """
    user32 = ctypes.windll.user32
    hdc = user32.GetDC(0)
    refresh_rate = ctypes.windll.gdi32.GetDeviceCaps(hdc, 116)  # 116 = VREFRESH (垂直刷新率)
    user32.ReleaseDC(0, hdc)
    return refresh_rate

# 設定動畫參數
START_HEIGHT = 200
START_WIDTH = 200
END_HEIGHT = 720
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

# 儲存目前快捷鍵
current_hotkeys = {}  # 全域熱鍵記錄 dict

def set_hotkey(name, key_combo, callback):
    """
    設定或更新熱鍵
    name: 任意命名此熱鍵的識別名
    key_combo: 例如 "ctrl+alt+x"
    callback: 被觸發的函數
    """
    global current_hotkeys
    # 移除舊的熱鍵
    if name in current_hotkeys:
        try:
            keyboard.remove_hotkey(current_hotkeys[name])
            # print(f"[INFO] 熱鍵 {name} 移除成功")
        except Exception as e:
            # print(f"[WARN] 移除熱鍵 {name} 失敗：{e}")
            pass

    try:
        # 註冊新的熱鍵
        hotkey_id = keyboard.add_hotkey(key_combo, callback)
        current_hotkeys[name] = hotkey_id
        # print(f"[INFO] 熱鍵 {name} 設定為：{key_combo}")
    except Exception as e:
        # print(f"[ERROR] 設定熱鍵 {name} 時失敗：{e}")
        raise

def update_hotkey(name):
    """修改快捷鍵"""
    global capture_hotkey, toggle_overlay_hotkey
    if name == "capture":
        capture_hotkey = ModSet.capture_hotkey
        set_hotkey("capture", capture_hotkey, lambda: window.after(10, run_wincap)) # 螢幕截圖 (全域)
    elif name == "toggle_overlay":
        toggle_overlay_hotkey = ModSet.toggle_overlay_hotkey
        set_hotkey("toggle_overlay", toggle_overlay_hotkey, toggle_overlay_visibility) # 隱藏懸浮窗 (全域)
    else:
        pass
    
# GUI ===========================================================================================================================
ctk.set_appearance_mode(current_theme)
ctk.set_default_color_theme(os.path.join(PATH, "theme", "nectar.json"))

window = ctk.CTk() # 主視窗 (root)
freeze_overlay = FreezeOverlay(window) # 模擬螢幕凍結的 overlay (toplevel)
APISet = APISetting(current_theme, on_activate = update_APISetting, APPDATA = APPDATA) # API 設定視窗 (toplevel)
ModSet = ModelSetting(current_theme, on_activate = update_ModelSetting, on_restart = restart_app, on_update_hotkey = update_hotkey, APPDATA = APPDATA) # OCR 模型設定視窗 (toplevel)
PerEdit = PersonaEditor(current_theme, APPDATA = APPDATA) # 人格指令編輯器 (toplevel)
if groq_available:
    chatroom = chatroomWindow(current_theme, chat_session, groq_key, on_activate = update_token_display, on_link_persona = link_persona, APPDATA = APPDATA) # 聊天室 / 翻譯紀錄 (toplevel)
else:
    chatroom = None

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

# 設定字型大小
title_font = ctk.CTkFont(size = 24)

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
capture_bt.bind("<Button-3>", lambda e: open_ModelSetting())
capture_bt.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = "swe")

# 複製 Prompt 開關
prompt_cb_var = tk.StringVar(master = f1, value = "ON" if prompt_copy else "OFF")
prompt_cb = ctk.CTkCheckBox(master = f1, text = "複製提示詞 (Prompt)",
                           variable = prompt_cb_var, onvalue = "ON", offvalue = "OFF",
                           command = prompt_sw)
prompt_cb.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = "w")

# AI 自動翻譯
ost_cb_var = tk.StringVar(master = f1, value = "OFF" if not ost_control else "ON")
ost_cb = ctk.CTkCheckBox(master = f1, text = "AI 自動翻譯",
                           variable = ost_cb_var, onvalue = "ON", offvalue = "OFF",
                           command = ost_sw)
ost_cb.grid(row = 2, column = 0, padx = 5, pady = 5, sticky = "w")

API_bt = ctk.CTkButton(master = f1, text = "API", width = 0,
                           anchor = "c", command = open_APISetting)
API_bt.grid(row = 2, column = 0, padx = 5, pady = 5, sticky = "e")

# 展開額外功能按鈕
setting_bt = ctk.CTkButton(master = f1, text = "▼ 展開額外功能",
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
theme_bt = ctk.CTkButton(master = f2, text = "主題切換", height = 28,
                           anchor = "c", command = toggle_theme)
theme_bt.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = "we")

Persona_bt = ctk.CTkButton(master = f2, text = "Persona 指令", height = 28,
                           anchor = "c", command = open_PersonaEditor)
Persona_bt.grid(row = 1, column = 0, padx = 5, pady = (0, 5), sticky = "we")

chatroom_bt = ctk.CTkButton(
    master = f2, text = "聊天室 / 翻譯紀錄", height = 28, anchor = "c", 
    command = lambda: open_chatroom()
)
chatroom_bt.grid(row = 2, column = 0, padx = 5, pady = (0, 5), sticky = "we")

resetchat_bt = ctk.CTkButton(master = f2, text = "AI 重置 / 記憶刪除", height = 28,
                           anchor = "c", command = reset_chat)
resetchat_bt.grid(row = 3, column = 0, padx = 5, pady = (0, 5), sticky = "we")

# 水平線 1
sep1 = ctk.CTkFrame(master = f2, fg_color = "gray", height = 2)
sep1.grid(row = 4, column = 0, padx = 5, pady = 5, sticky = "we")

# AI 記憶模塊
mem_cb_var = tk.StringVar(master = f2, value = "OFF" if not enable_short_term_memory else "ON")
mem_cb = ctk.CTkCheckBox(master = f2, text = "短期記憶力",
                           variable = mem_cb_var, onvalue = "ON", offvalue = "OFF",
                           command = toggle_memory)
mem_cb.grid(row = 5, column = 0, padx = 5, pady = 5, sticky = "w")

# AI 記憶壓縮器
mem_limit_wd = ctk.CTkLabel(master = f2, text = "記憶壓縮器: 3 輪對話", anchor = "w", height = 10)
mem_limit_wd.grid(row = 6, column = 0, padx = 5, pady = 5, sticky = "we")
mem_limit_sd = ctk.CTkSlider(master = f2, from_ = 2, to = 10, number_of_steps = 200, height = 20,
                               command = set_max_history)
mem_limit_sd.set(max_history)  # 設定滑桿初始值
mem_limit_sd.grid(row = 7, column = 0, padx = 5, pady = (0, 5), sticky = "we")

# AI 創意力滑桿
temperature_wd = ctk.CTkLabel(master = f2, text = f"AI 創意力: {int(temperature * 100)} %", anchor = "w", height = 10)
temperature_wd.grid(row = 8, column = 0, padx = 5, pady = 5, sticky = "we")
temperature_sd = ctk.CTkSlider(master = f2, from_ = 0.0, to = 1.0, number_of_steps = 200, height = 20,
                               command = set_temperature)
temperature_sd.set(temperature)  # 設定滑桿初始值
temperature_sd.grid(row = 9, column = 0, padx = 5, pady = (0, 5), sticky = "we")

# Token 計數
token_wd = ctk.CTkLabel(master = f2, text = "Token 計數器", anchor = "w", height = 10)
token_wd.grid(row = 10, column = 0, padx = 5, pady = (20, 5), sticky = "we")
t_input_wd = ctk.CTkLabel(master = f2, text = "• 輸入: 0", anchor = "w", height = 10)
t_input_wd.grid(row = 11, column = 0, padx = (10, 5), pady = 2, sticky = "we")
t_output_wd = ctk.CTkLabel(master = f2, text = "• 輸出: 0", anchor = "w", height = 10)
t_output_wd.grid(row = 12, column = 0, padx = (10, 5), pady = 2, sticky = "we")
t_in_total_wd = ctk.CTkLabel(master = f2, text = "• 累計輸入: 0", anchor = "w", height = 10)
t_in_total_wd.grid(row = 13, column = 0, padx = (10, 5), pady = 2, sticky = "we")
t_out_total_wd = ctk.CTkLabel(master = f2, text = "• 累計輸出: 0", anchor = "w", height = 10)
t_out_total_wd.grid(row = 14, column = 0, padx = (10, 5), pady = (2, 5), sticky = "we")

# 模型切換器
model_change_wd = ctk.CTkLabel(master = f2, text = "目前使用的 AI 模型", anchor = "w", height = 10)
model_change_wd.grid(row = 15, column = 0, padx = 5, pady = (15, 5), sticky = "swe")
model_change_op = ctk.CTkComboBox(
    master = f2, 
    values = [
        "llama-3.3-70b-versatile", 
        "compound-beta-mini", 
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "deepseek-r1-distill-llama-70b",
        "qwen-qwq-32b",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "Llama3-70B-8192", 
        "llama-3.1-8b-instant", 
        "gemma2-9b-it"
    ], 
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

# 初始化快捷鍵
set_hotkey("capture", capture_hotkey, lambda: window.after(10, run_wincap)) # 螢幕截圖 (全域)
set_hotkey("toggle_overlay", toggle_overlay_hotkey, toggle_overlay_visibility) # 隱藏懸浮窗 (全域)
capture_bt.bind("<Control-Button-1>", toggle_overlay_visibility) # 隱藏懸浮窗 (綁定)

def on_exit():
    try:
        lock_file.close()  # 釋放 lock 檔案
    except:
        pass
    window.destroy()
    window.quit()

window.protocol("WM_DELETE_WINDOW", on_exit) # 關閉視窗時停止程式

# 啟動 GUI
if __name__ == "__main__":
    if args.background:
        with open(os.path.join(APPDATA, "GUI_open.flag"), "w") as f:
            f.write("GUI_is_opened")
    print("\033[32m[INFO] BeeSeeR GUI 已啟動，系統正常運行\033[0m")
    window.mainloop()
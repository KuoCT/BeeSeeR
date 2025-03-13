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

import json
import tkinter as tk
import customtkinter as ctk
from ocr.WinCap import WindowCapture
from ocr.overlay import overlayWindow
import llm.chat as chat
from groq import Groq
import ctypes
import subprocess

def load_config():
    """讀取設定檔案"""
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {}  # 如果沒有設定檔，回傳空字典

# 定義預設參數
settings  = load_config()
model = settings.get("model", "llama-3.3-70b-versatile")
enable_short_term_memory = settings.get("enable_short_term_memory", False)
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

# 如果 API Key 非空，嘗試連線驗證
if groq_key:
    try:
        client = Groq(api_key = groq_key)
        test_response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "system", "content": "ping"}],  # 測試 API 可用性
            max_tokens=10
        )
        if test_response:
            print("\033[32m[INFO] Groq API 連線成功！\033[0m")
            groq_available = True
        else:
            print("\033[31m[INFO] API Key 無效，請確認 Groq API Key。\033[0m")
    except Exception as e:
        print(f"\033[31m[ERROR] 無法連線到 Groq API：{e}\033[0m")

def load_prompt(file):
    """ 從文件載入提示詞，並回傳 (絕對路徑, 內容) """
    # 取得目前腳本所在的資料夾
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 構建絕對路徑
    prompt_path = os.path.join(script_dir, "prompt", file)

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        return prompt_path, content  # 回傳 (絕對路徑, 內容)

    except Exception as e:
        print(f"\033[31m[INFO] 找不到 {prompt_path} 文件，將會使用預設的提示詞。\033[0m")
        return prompt_path, None  # 讀取失敗時仍回傳絕對路徑，但內容為 None
        
# 初始化提示詞
prompt_path, prompt = load_prompt(prompt_file)
system_prompt_path, system_prompt = load_prompt(system_prompt_file) # 讀取系統提示詞
memory_prompt_path, memory_prompt = load_prompt(memory_prompt_file) # 讀取記憶提示詞

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

# 螢幕文字辨識 + AI 自動翻譯 + 螢幕覆蓋顯示結果
def run_wincap():
    """啟動 WindowCapture 取得螢幕訊息"""

    def receive_coordinates(coords):
        """回呼函數，獲取座標"""
        global cb_coords
        cb_coords = coords
        # print(f"\033[34m[INFO] 即時回傳選取範圍座標: {coords}\033[0m")

    app = WindowCapture(prompt_control = prompt_control, on_capture = receive_coordinates, prompt = prompt)
    app.mainloop()
    # prompt = app.get_prompt_text()
    # ext = app.get_extracted_text()
    user_input = app.get_final_text()
    if user_input:
        print("\033[33m[INFO] 文字辨識結果：\033[0m")
        print(user_input)
    else:
        print("\033[31m[INFO] 無法獲取文字辨識結果。\033[0m")

    # 自動翻譯
    if groq_available and ost_control and user_input:
        global last_response
        global system_prompt
        global system_prompt_path
        global memory_prompt
        global memory_prompt_path
        system_prompt_path, system_prompt = load_prompt(system_prompt_file) # 讀取系統提示詞
        memory_prompt_path, memory_prompt = load_prompt(memory_prompt_file) # 讀取記憶提示詞
        response, prompt_tokens, completion_tokens = chat_session.send_to_groq(system_prompt, memory_prompt, user_input)
        last_response = response

        # 更新 token 計數器
        global total_prompt_tokens
        global total_completion_tokens
        # 更新累計 token 數量
        total_prompt_tokens += prompt_tokens
        total_completion_tokens += completion_tokens
        t_input_wd.configure(text = f"● 輸入: {prompt_tokens}")
        t_output_wd.configure(text = f"● 輸出: {completion_tokens}")
        t_in_total_wd.configure(text = f"● 累計輸入: {total_prompt_tokens}")
        t_out_total_wd.configure(text = f"● 累計輸出: {total_completion_tokens}")

        # 還原按鈕
        resetchat_bt.configure(text = "AI 重製/記憶刪除", fg_color = ["#1e8bba", "#C7712D"])

        # 螢幕覆蓋顯示
        overlay = overlayWindow(last_response, cb_coords)
        overlay.mainloop()


def save_config():
    """讀取現有設定，更新後再存入 JSON 檔案"""
    config = load_config()  # 先載入現有設定

    # 更新設定
    config.update({
        "groq_key": groq_key,
        "ost_control": ost_control,
        "theme": current_theme,
        "model": model,
        "enable_short_term_memory": enable_short_term_memory
    })

    # 將更新後的設定存回 JSON
    with open("config.json", "w") as f:
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
    dialog = ctk.CTkToplevel()
    dialog.title("輸入 API Key")
    dialog.geometry(f"400x40+{window.winfo_x() - 410}+{window.winfo_y()}")
    dialog.grid_columnconfigure(1, weight = 1)
    dialog.grid_rowconfigure(0, weight = 0)
    dialog.attributes("-topmost", True) # 讓視窗顯示在最前面
    dialog.grab_set()
    dialog.after(250, dialog.iconbitmap, "icon/logo_dark.ico" if current_theme == "dark" else "icon/logo_light.ico")

    def select_all():
        """全選輸入框內的 API Key"""
        entry.select_range(0, "end")  # 選取所有文字
        entry.focus_set()  # 設定輸入框焦點，確保全選有效

    def confirm_API():
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

        dialog.destroy()  # 關閉對話框

    # 標題文字
    API_wd = ctk.CTkLabel(dialog, text = "API Key:", font = text_font, anchor = "w")
    API_wd.grid(row = 0, column = 0, padx = (5, 0), pady = 5, sticky = "nswe")

    # 輸入框
    entry = ctk.CTkEntry(dialog)
    entry.grid(row = 0, column = 1, padx = (5, 0), pady = 5, sticky = "nswe")
    if groq_key:  # 如果有舊的 API Key，則填入
        entry.insert(0, groq_key)

    # 全選按鈕
    confirm_API_bt = ctk.CTkButton(dialog, text = "[ ]", font = text_font, width = 20, anchor = "c", command = select_all)
    confirm_API_bt.grid(row = 0, column = 2, padx = (5, 0), pady = 5, sticky = "e")

    # 載入按鈕
    confirm_API_bt = ctk.CTkButton(dialog, text = "確定", font = text_font, width = 40, anchor = "c", command = confirm_API)
    confirm_API_bt.grid(row = 0, column = 3, padx = 5, pady = 5, sticky = "e")

def toggle_theme():
    """切換 Light/Dark 模式"""
    global current_theme  # 確保使用的是全域變數
    if current_theme == "dark":
        current_theme = "light"
        ctk.set_appearance_mode(current_theme)  # 切換為 Light 模式
        window.iconbitmap("icon/logo_light.ico")
    else:
        current_theme = "dark"
        ctk.set_appearance_mode(current_theme)  # 切換為 Dark 模式
        window.iconbitmap("icon/logo_dark.ico")
    save_config()

def open_prompt_folder():
    """打開 prompt 資料夾"""
    os.startfile(os.path.join(os.getcwd(), "prompt"))

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
    resetchat_bt.configure(text = "已重製", fg_color= "firebrick")
    print("\033[32m[INFO] 已重置 AI，等待新輸入。\033[0m")

def set_model(choice):
    """變更 AI 模型"""
    global model
    model = choice  # 更新全域變數 `model`
    
    if groq_available:
        chat_session.update_config(model = model)  # 更新 chat_session 內部設定
    
    save_config()

process = None # 初始化記錄 Popen 進程  

def pop_chatroom(groq_available, groq_key, model, max_history, enable_short_term_memory, temperature, chat_session):
    """依現在的設定打開一個新的聊天室"""
    global process
    # 若已有正在運行的進程，先終結它
    if process and process.poll() is None:
        # print(f"終止舊進程 (PID: {process.pid})")
        process.terminate()  # 嘗試優雅終止
        try:
            process.wait(timeout=3)  # 等待 3 秒
        except subprocess.TimeoutExpired:
            # print("舊進程未能及時終結，強制殺死")
            process.kill()  # 強制終止

    # 建構程式碼
    CMD = ["env/Scripts/python", "llm/chat.py"]

    if groq_available:
        CMD.extend(["-k", groq_key])  # 加入 "-k" 參數

    CMD.extend(["-m", model])
    CMD.extend(["-sl", str(max_history)])  # max_history 轉換為字串
    if not enable_short_term_memory:
        CMD.append("-ns")  # `-ns` 是 flag，不需要額外的值
    CMD.extend(["-T", str(temperature)])  # temperature 轉換為字串

    # 如果有對話歷史，轉換成 JSON 並加入
    if chat_session.messages:
        CMD.extend(["--messages", json.dumps(chat_session.messages)])

    # 如果摘要不為空，轉換成 JSON 並加入
    if chat_session.summaries and chat_session.summaries != [""]:
        CMD.extend(["--summaries", json.dumps(chat_session.summaries)])

    # 執行 subprocess，確保使用虛擬環境，並設定 `cwd` 以確保執行位置正確
    process = subprocess.Popen(CMD)

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

# GUI    
# 建立主視窗
window = ctk.CTk()

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
window.iconbitmap("icon/logo_dark.ico" if current_theme == "dark" else "icon/logo_light.ico")
appid = 'KuoCT.BeeSeeR.BCR.v2.0.2'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

# 讓視窗保持最上層
window.attributes("-topmost", True) # 讓視窗顯示在最前面

# 設定主題
ctk.set_appearance_mode(current_theme)
ctk.set_default_color_theme("theme/nectar.json")

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
capture_bt.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = "swe")

# User Prompt 開關
prompt_cb_var = tk.StringVar(master = f1, value = "ON")
prompt_cb = ctk.CTkCheckBox(master = f1, text = "Prompt (提示詞)", font = text_font,
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
f2.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), weight = 0)
f2.grid_remove()  # 預設隱藏 f2

# 擴充功能
theme_bt = ctk.CTkButton(master = f2, text = "主題切換", font = text_font, height = 28,
                           anchor = "c", command = toggle_theme)
theme_bt.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = "we")

pfolder_bt = ctk.CTkButton(master = f2, text = "Prompt 資料夾", font = text_font, height = 28,
                           anchor = "c", command = open_prompt_folder)
pfolder_bt.grid(row = 1, column = 0, padx = 5, pady = (0, 5), sticky = "we")

chatroom_bt = ctk.CTkButton(master = f2, text = "AI 聊天室 (實驗)", font = text_font, height = 28, anchor = "c", 
                            command = lambda: pop_chatroom(groq_available, groq_key, model, max_history, enable_short_term_memory, temperature, chat_session))
chatroom_bt.grid(row = 2, column = 0, padx = 5, pady = (0, 5), sticky = "we")

resetchat_bt = ctk.CTkButton(master = f2, text = "重製對話/記憶", font = text_font, height = 28,
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
model_change_wd.grid(row = 15, column = 0, padx = 5, pady = (20, 5), sticky = "we")
model_change_op = ctk.CTkOptionMenu(
    master = f2, 
    values = ["llama-3.3-70b-versatile", "llama-3.3-70b-specdec", "llama-3.1-8b-instant", "gemma2-9b-it"], 
    command = set_model)
model_change_op.set(model)
model_change_op.grid(row = 16, column = 0, padx = 5, pady = (0, 5), sticky = "we")

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

# 啟動 GUI
if __name__ == "__main__":
    with open("GUI_open.flag", "w") as f:
        f.write("GUI_is_opened")
    print("\033[32m[INFO] BeeSeeR GUI 已啟動，系統正常運行\033[0m")
    window.mainloop()
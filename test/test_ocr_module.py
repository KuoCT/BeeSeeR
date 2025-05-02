import customtkinter as ctk
import os
import sys
import ctypes

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑
sys.path.append(PATH) # 將路徑加入到系統路徑中

if __name__ == "__main__":
    from ocr.freeze import FreezeOverlay
    from ocr.WinCap import MouseTooltip
    from ocr.WinCap import WindowCapture
    from ocr.overlay import overlayWindow
    import time
    import threading

    # 獲取螢幕的縮放比例
    def get_scale_factor():
        """使用 Windows API 取得 Windows 設定的縮放比例"""
        try:
            shcore = ctypes.windll.shcore
            return shcore.GetScaleFactorForDevice(0) / 100.0  # 例如 125% → 1.25
        except Exception:
            return 1.0  # 預設 100%
    
    # 預設變量
    scale_factor = get_scale_factor()
    current_theme = "dark"
    ocr_model = "surya"

    cb_coords = None # 初始化座標
    last_response = None # 初始化 AI 回應
    dtype = None # Surya-OCR: 手動選擇模型精度
    prompt_copy = True # 複製提示詞控制開關
    ost_control = False # on-screen translation (AI 自動翻譯)
    overlay_windows = [] # 加入 overlay_windows 管理清單
    hotkey_enabled = True # 初始化快捷鍵狀態
    mocr = None # 初始化 OCR 模型
    recognition_predictor = None # 初始化 OCR 模型
    detection_predictor = None # 初始化 OCR 模型

    # 螢幕文字辨識
    def run_wincap(coords = None):
        """啟動 WindowCapture 取得螢幕訊息"""
        global ocr_model, hotkey_enabled

        if not hotkey_enabled:
            return  # 忽略重複觸發
        
        hotkey_enabled = False  # 禁用快捷鍵

        capture_bt.configure(state = "disabled") # 鎖定按鈕防止重複觸發

        # 啟動最初的「載入中...」提示框
        loading_tip = MouseTooltip(root, follow = True)
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

                # 延遲 100 毫秒再建立 tooltip，讓 root 回穩
                def show_tooltip():
                    tooltip = MouseTooltip(root, follow = False, text = "找不到模型文件")
                    tooltip.update()
                    tooltip.after(1000, tooltip.destroy)

                root.after(100, show_tooltip)

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
                    root,
                    prompt_copy = prompt_copy,
                    on_capture = receive_coordinates,
                    on_result = handle_result,
                    prompt = "[測試] 這段文字是可被複製的 prompt",
                    ocr_model = ocr_model,
                    google_ocr_key = None,
                    google_ocr_feature = "image",
                    dtype = dtype,
                    langs = None,
                    mocr = mocr,
                    recognition_predictor = recognition_predictor,
                    detection_predictor = detection_predictor,
                    bind = not bool(coords), # 如果有座標，取消滑鼠綁定 (自動操作)     
                )

                if bool(coords):
                    app.auto_capture(coords)
                else:
                    app.deiconify()

            root.after(0, launch_window)

        # 背景執行模型載入
        threading.Thread(target = load_model_and_launch, daemon = True).start()
    
    def handle_result(prompt_text, extracted_text, final_text, is_dragging):
        """處理 WindowCapture 回傳的結果"""
        global last_response, cb_coords, scale_factor, hotkey_enabled
        freeze_overlay.hide() # 解除凍結畫面
        hotkey_enabled = True  # 重啟快捷鍵

        ext = extracted_text # 取得辨識後文字

        if isinstance(ext, str) and ext.strip():
            print("\n\033[33m[INFO] 光學字元辨識 (OCR) 結果：\033[0m")
            print(ext)
            if not ost_control: capture_bt.configure(state = "normal") # 解鎖按鈕
        else:
            print("\033[31m[INFO] 無法獲取文字辨識結果。\033[0m")
            # 顯示短暫提示：無法獲取文字辨識結果
            tooltip = MouseTooltip(root, follow = False, text = "無法獲取文字辨識結果")
            tooltip.update()  # 強制顯示一次，避免閃爍
            tooltip.after(1000, tooltip.destroy)  # 1 秒後自動銷毀
            capture_bt.configure(state = "normal") # 解鎖按鈕
            return
        
        last_response = final_text
        
        def show_overlay():
            # 顯示結果 overlay 
            overlay = overlayWindow(root, last_response, cb_coords, scale_factor, run_again)
            overlay_windows.append(overlay)
            overlay.deiconify() # 顯示 overlay 視窗.deiconify()

        # 背景執行
        threading.Thread(target = show_overlay, daemon = True).start()

    def receive_coordinates(coords):
        """Callback 函數，獲取座標"""
        global cb_coords
        cb_coords = coords
        print(f"\033[36m[INFO] 即時回傳選取範圍座標: {coords}\033[0m")

    def run_again(coords):
        """Callback 函數，再次執行"""
        run_wincap(coords)

    # 設定主題
    if current_theme == "dark":
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")

    ctk.set_default_color_theme(os.path.join(PATH, "theme", "nectar.json"))

    root = ctk.CTk() # 創建主視窗
    freeze_overlay = FreezeOverlay(root) # 模擬螢幕凍結的 overlay (toplevel)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 設定視窗大小
    window_width = 230
    window_height = 160

    # 計算視窗位置
    x_position = screen_width - int(window_width * scale_factor) - int(50 * scale_factor)
    y_position = int(50 * scale_factor)

    # 設定視窗位置
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # 設定按鈕
    title_font = ctk.CTkFont(family = "Helvetica", size = 24, weight = "bold")
    capture_bt = ctk.CTkButton(master = root, text = "Capture", font = title_font, height = 70, anchor = "c", command = run_wincap)
    capture_bt.pack(padx = 10, pady = 10) 

    root.attributes("-topmost", True) # 讓視窗顯示在最前面
    root.mainloop()





import io
import tkinter as tk
import pyautogui
import pyperclip # 剪貼簿
import threading
from PIL import Image
from torch.cuda import is_available, empty_cache, ipc_collect

class MouseTooltip(tk.Toplevel):
    def __init__(self, window, follow = True, text = "載入套件..."):
        super().__init__(window)
        self.overrideredirect(True)
        self.attributes("-topmost", True)  # 再次確保 topmost
        self.config(bg="yellow")
        self._is_destroyed = False  # 加入狀態標記

        self.label = tk.Label(
            self,
            text = text,
            font = ("Helvetica", 10),
            bg = "yellow",
            fg = "black",
            highlightthickness = 1,
            highlightbackground = "black",
            anchor = "w",
            justify = "left",
        )
        self.label.pack()
        x, y = pyautogui.position()
        self.geometry(f"+{x + 20}+{y + 20}")

        if follow: self.update_position()
    
    def update_position(self):
        """讓提示框貼著滑鼠位置移動"""
        try:
            if self._is_destroyed or not self.winfo_exists():
                return  # 避免已被銷毀還持續排程
            self.lift()  # 提升視窗層級
            x, y = pyautogui.position()
            self.geometry(f"+{x + 20}+{y + 20}")
            self.after(16, self.update_position) # 60 FPS 更新位置
        except:
            pass  # 避免滑鼠瞬間消失時報錯

class WindowCapture(tk.Toplevel):
    def __init__(
            self, 
            window,
            prompt_copy = True, 
            on_capture = None, 
            on_result = None, 
            prompt = None,
            ocr_model = None,
            google_ocr_key = None,
            google_ocr_feature = None,
            dtype = None, 
            langs = None, 
            mocr = None,
            recognition_predictor = None,
            detection_predictor = None,
            bind = True
        ):
        super().__init__(window)
        self.prompt_copy = prompt_copy
        self.on_capture = on_capture  # 回呼函數
        self.on_result = on_result # 回呼函數
        self.ocr_model = ocr_model if ocr_model else "surya"  # 初始化 OCR 模型
        self.google_ocr_key = google_ocr_key
        self.google_ocr_feature = google_ocr_feature
        self.prompt = prompt
        self.dtype = dtype
        self.langs = langs

        # 初始化辨識結果
        self.prompt_text = None
        self.extracted_text = None
        self.final_text = None

        # 設定全螢幕
        self.withdraw()
        self.attributes('-fullscreen', True)
        self.config(bg="black")
        self.attributes('-alpha', 0.6)
        self.overrideredirect(True)
        self.attributes("-topmost", True) # 讓視窗顯示在最前面
        self.set_transparent_color("green")

        # 創建畫布 (Canvas) 來繪製矩形
        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 綁定滑鼠事件
        if bind: # 如果 bind 為 True 則綁定滑鼠事件
            self.canvas.bind("<ButtonPress-1>", self.start_draw)
            self.canvas.bind("<B1-Motion>", self.update_draw)
            self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

        # 用來存儲當前的矩形
        self.rect_id = None
        self.start_x = 0
        self.start_y = 0
        self.is_dragging = False if bind else True # 用來記錄是否有拖曳 (若 bind 為 False 則直接進入拖曳狀態)
        self.bind("<Escape>", lambda event: self.escape_WinCap())

        # 初始化載入 OCR 套件
        if self.ocr_model == "manga":
            self.mocr = mocr
        else:
            self.recognition_predictor = recognition_predictor
            self.detection_predictor = detection_predictor

        if self.ocr_model == "manga":
            self.text = "[漫畫模式] 拖曳偵測文字，點一下退出"
        elif not bind:
            self.text = "自動操作中..."
        else:
            self.text = "拖曳偵測文字，點一下退出"

        self.tooltip = MouseTooltip(self, text = self.text)

    def set_transparent_color(self, color):
        """讓指定顏色變成透明"""
        self.wm_attributes("-transparentcolor", color)

    def start_draw(self, event):
        """當滑鼠左鍵按下時，開始繪製矩形"""
        self.tooltip.label.config(text = "[漫畫模式] 放開滑鼠開始偵測 / Esc中斷" if self.ocr_model == "manga" else "放開滑鼠開始偵測 / Esc中斷")
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y,
                                                    outline = "white", width = 1, fill = "green")
        self.is_dragging = False # 每次點擊時重置拖曳狀態

    def update_draw(self, event):
        """當滑鼠拖曳時，更新矩形的大小"""
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)
            self.is_dragging = True # 只要有拖曳，就設置為 True

    def stop_draw(self, event):
        """當滑鼠釋放時，結束繪製並擷取螢幕 + OCR 辨識 + 複製到剪貼簿"""
        global device
        device = "CUDA" if is_available() else "CPU" # 偵測裝置
        self.tooltip.withdraw() # 瞬間隱藏提示窗避開截圖

        # 如果沒有拖曳，直接結束視窗
        if not self.is_dragging:
            print("\033[31m[INFO] 偵測到未截圖。\033[0m")
            self.after(0, self.exit_WinCap)
            return

        if self.rect_id:
            x1, y1, x2, y2 = self.canvas.coords(self.rect_id)
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            coordinates = (x1, y1, x2, y2)
            # 透過 callback 回傳座標
            if self.on_capture: self.on_capture(coordinates)

        # 呼叫執行緒來執行 OCR
        ocr_thread = threading.Thread(target = self.perform_ocr_process, args=(coordinates,), daemon = True)
        ocr_thread.start()

    def auto_capture(self, coordinates):
        """自動擷取螢幕畫面並進行 OCR 辨識"""
        global device
        device = "CUDA" if is_available() else "CPU" # 偵測裝置

        # 透過 callback 回傳座標
        if self.on_capture:self.on_capture(coordinates)
        
        # 呼叫執行緒來執行 OCR
        ocr_thread = threading.Thread(target = self.perform_ocr_process, args=(coordinates,), daemon = True)
        ocr_thread.start()

    def perform_ocr_process(self, coordinates):
        """執行擷取 + OCR（背景執行緒）"""
        x1, y1, x2, y2 = coordinates
        width = x2 - x1
        height = y2 - y1

        # 防呆：確保選取範圍合法
        if width <= 0 or height <= 0:
            print("\033[31m[ERROR] 選取範圍無效，寬或高為 0。\033[0m")
            self.is_dragging = False
            self.after(0, self.exit_WinCap)
            return

        # 擷取螢幕畫面
        img_bytes = io.BytesIO()
        screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
        screenshot.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # 讀取影像並進行 OCR
        image = Image.open(img_bytes)
        extracted_text = self.perform_ocr(image, img_bytes)  # OCR 處理

        # 讀取 prompt 內容
        prompt_text = self.prompt if self.prompt else "以下文字為光學字元辨識後的文字結果，若出現瑕疵請輕度修復文字確保用詞貼近原文，使用**繁體中文**完整翻譯文字並適度使用**台灣常用詞辭典**在地化，稍微使語法自然通順。**只輸出翻譯結果**："

        # 合併 prompt 與 OCR 結果
        final_text = f"{prompt_text}\n\n{extracted_text}" if self.prompt_copy else extracted_text
        if extracted_text.strip():
            pyperclip.copy(final_text)
            print("\033[32m[INFO] OCR 辨識結果已複製到剪貼簿。\033[0m")
        else:
            print("\033[31m[INFO] 未偵測到文字內容\033[0m。")

        # 儲存辨識結果
        self.prompt_text = prompt_text
        self.extracted_text = extracted_text
        self.final_text = final_text

        # 清理資源
        image.close()

        # 確保 OCR 完成後關閉視窗（回到 UI 執行緒執行）
        self.after(0, self.exit_WinCap)

    def perform_ocr(self, image, img_bytes):
        """進行 OCR 辨識"""
        if self.ocr_model == "manga":
            """使用 Manga-OCR 進行辨識"""
            self.tooltip.deiconify() # 顯示提示窗
            self.tooltip.label.config(text = "[漫畫模式] 偵測文字...")
            mocr = self.mocr
            predictions = mocr(image)
            # print(predictions) # 測試用
            if predictions:
                return predictions
            return ""
        
        elif self.ocr_model == "surya":           
            """使用 Surya-OCR 進行辨識"""
            self.tooltip.deiconify() # 顯示提示窗
            self.tooltip.label.config(text = "偵測文字...")
            print(f"\033[32m[INFO] 載入 OCR 模型（使用裝置: {device}）...\033[0m")
            recognition_predictor = self.recognition_predictor
            detection_predictor = self.detection_predictor

            langs = self.langs
            predictions = recognition_predictor([image], [langs], detection_predictor)
            # print(predictions) # 測試用

            if predictions and hasattr(predictions[0], 'text_lines'):
                return "\n".join([line.text for line in predictions[0].text_lines])
            return ""
        
        elif self.ocr_model == "google":           
            """使用 Google-OCR 進行辨識"""
            self.tooltip.deiconify() # 顯示提示窗
            self.tooltip.label.config(text = "偵測文字...")

            import base64
            import requests

            if not self.google_ocr_key:
                print("\033[31m[ERROR] Google OCR API Key 未設定。\033[0m")
                return ""
            
            # 將 img_bytes 轉為 base64
            img_bytes.seek(0)
            img_base64 = base64.b64encode(img_bytes.read()).decode("utf-8")

            endpoint = f"https://vision.googleapis.com/v1/images:annotate?key={self.google_ocr_key}"
            feature_type = "TEXT_DETECTION" if self.google_ocr_feature == "image" else "DOCUMENT_TEXT_DETECTION"
            payload = {
                "requests": [
                    {
                        "image": {"content": img_base64},
                        "features": [{"type": feature_type}]
                        # 加入語言提示，例如: `"imageContext": {"languageHints": ["zh-Hant"]}` 可以提升辨識率 (以後再考慮)
                    }
                ]
            }
            try:
                response = requests.post(endpoint, json = payload, timeout = 10)
                response.raise_for_status()
                result = response.json()
                
                if self.google_ocr_feature == "image":
                    annotations = result.get("responses", [{}])[0].get("textAnnotations", [])
                    return annotations[0]["description"] if annotations else ""
                else:
                    full_text = result.get("responses", [{}])[0].get("fullTextAnnotation", {}).get("text", "")
                    return full_text if full_text else ""
                
            except requests.exceptions.RequestException as e:
                import tkinter.messagebox as messagebox
                messagebox.showerror("錯誤", f"Google OCR 請求失敗：{e}")
                print(f"\033[31m[ERROR] Google OCR 請求失敗：{e}\033[0m")
                if e.response is not None:
                    print("\033[33m[DEBUG] 回應內容：\033[0m", e.response.text)
                return ""

        else:
            raise ValueError("Unsupported OCR model") # 不支援的 OCR 模式

    def cleanup_memory(self):
        """釋放記憶體（CUDA 模式釋放 VRAM）"""
        if hasattr(self, "recognition_predictor"):
            del self.recognition_predictor

        if hasattr(self, "detection_predictor"):
            del self.detection_predictor

        if hasattr(self, "mocr"):
            del self.mocr

        if device == "CUDA":
            empty_cache()
            ipc_collect()
            print("\033[32m[INFO] 已釋放 GPU 記憶體。\033[0m")
    
    def exit_WinCap(self):
        """關閉視窗，釋放綁定與資源"""
        # 觸發 callback 回傳果給 on_result
        if self.on_result:
            self.on_result(self.prompt_text, self.extracted_text, self.final_text, self.is_dragging)
        if hasattr(self, 'tooltip') and self.tooltip.winfo_exists():
            self.tooltip._is_destroyed = True  # 告知提示窗不要再 update
            self.tooltip.destroy()
        self.cleanup_memory()
        self.destroy()

    def escape_WinCap(self):
        """中斷操作，釋放綁定與資源"""
        print(f"\033[31m[INFO] 操作被中斷\033[0m")
        self.is_dragging = False  # 重設拖曳狀態
        # 回傳空結果給 on_result（主程式可以根據 is_dragging = False 做處理）
        if self.on_result:
            self.on_result(self.prompt_text, self.extracted_text, self.final_text, self.is_dragging)
        if hasattr(self, 'tooltip') and self.tooltip.winfo_exists():
            self.tooltip._is_destroyed = True  # 告知提示窗不要再 update
            self.tooltip.destroy()
        self.cleanup_memory()
        self.destroy()
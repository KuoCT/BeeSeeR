import io
# import time
import tkinter as tk
import pyautogui
import pyperclip # 剪貼簿
import threading
from PIL import Image
from torch.cuda import is_available, empty_cache, ipc_collect

class MouseTooltip(tk.Toplevel):
    def __init__(self, master, follow = True, text = "載入套件..."):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)  # 再次確保 topmost
        self.config(bg="yellow")

        self.label = tk.Label(
            self,
            text = text,
            font = ("Helvetica", 10),
            bg = "yellow",
            fg = "black",
            highlightthickness = 1,
            highlightbackground = "black"
        )
        self.label.pack()
        x, y = pyautogui.position()
        self.geometry(f"+{x + 20}+{y + 20}")

        if follow: self.update_position()
    
    def update_position(self):
        """讓提示框貼著滑鼠位置移動"""
        try:
            self.lift()  # 提升視窗層級
            x, y = pyautogui.position()
            self.geometry(f"+{x + 20}+{y + 20}")
            self.after(16, self.update_position) # 60 FPS 更新位置
        except:
            pass  # 避免滑鼠瞬間消失時報錯

class WindowCapture(tk.Toplevel):
    def __init__(self, prompt_control = True, on_capture = None, prompt = None, dtype = None, langs = None, manga_ocr = False):
        super().__init__()
        self.prompt_control = prompt_control
        self.on_capture = on_capture  # 回呼函數
        self.prompt = prompt
        self.dtype = dtype
        self.langs = langs
        self.manga_ocr = manga_ocr

        # 初始化辨識結果
        self.prompt_text = None
        self.extracted_text = None
        self.final_text = None

        # 設定全螢幕
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
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.update_draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

        # 用來存儲當前的矩形
        self.rect_id = None
        self.start_x = 0
        self.start_y = 0
        self.is_dragging = False # 用來記錄是否有拖曳
        self.bind("<Escape>", lambda event: self.escape_WinCap())

        self.tooltip = MouseTooltip(self, text = "[漫畫模式] 拖曳偵測文字，點一下退出" if self.manga_ocr else "拖曳偵測文字，點一下退出")

        # 初始化載入套件
        from manga_ocr import MangaOcr
        import logging
        logging.getLogger("transformers").setLevel(logging.ERROR)
        from surya.recognition import RecognitionPredictor
        from surya.detection import DetectionPredictor

    def set_transparent_color(self, color):
        """讓指定顏色變成透明"""
        self.wm_attributes("-transparentcolor", color)

    def start_draw(self, event):
        """當滑鼠左鍵按下時，開始繪製矩形"""
        self.tooltip.label.config(text = "[漫畫模式] 放開滑鼠開始偵測 / Esc中斷" if self.manga_ocr else "放開滑鼠開始偵測 / Esc中斷")
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
            self.exit_WinCap()
            return

        if self.rect_id:
            x1, y1, x2, y2 = self.canvas.coords(self.rect_id)
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            coordinates = (x1, y1, x2, y2)
            # 透過 callback 回傳座標
            if self.on_capture:
                self.on_capture(coordinates)

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
        extracted_text = self.perform_ocr(image)  # OCR 處理

        # 讀取 prompt 內容
        prompt_text = self.prompt if self.prompt else "以下文字為光學字元辨識後的文字結果，若出現瑕疵請輕度修復文字確保用詞貼近原文，使用**繁體中文**完整翻譯文字並適度使用**台灣常用詞辭典**在地化，稍微使語法自然通順。**只輸出翻譯結果**："

        # 合併 prompt 與 OCR 結果
        final_text = f"{prompt_text}\n\n{extracted_text}" if self.prompt_control else extracted_text
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
        self.cleanup_memory()

        # 確保 OCR 完成後關閉視窗（回到 UI 執行緒執行）
        self.after(0, self.exit_WinCap)

    def perform_ocr(self, image):
        """進行 OCR 辨識"""
        if self.manga_ocr:
            from manga_ocr import MangaOcr
            import logging
            logging.getLogger("transformers").setLevel(logging.ERROR)
            """使用 Manga-OCR 進行辨識 (延遲加載)"""
            self.tooltip.deiconify() # 顯示提示窗
            self.tooltip.label.config(text = "[漫畫模式] 偵測文字...")
            mocr = MangaOcr()
            predictions = mocr(image)
            # print(predictions) # 測試用
            if predictions:
                return predictions
            return None
        else:           
            from surya.recognition import RecognitionPredictor
            from surya.detection import DetectionPredictor
            """使用 Surya-OCR 進行辨識 (延遲加載)"""
            self.tooltip.label.config(text = "偵測文字...")
            print(f"\033[32m[INFO] 載入 OCR 模型（使用裝置: {device}）...\033[0m")
            recognition_predictor = RecognitionPredictor(dtype = self.dtype)
            detection_predictor = DetectionPredictor(dtype = self.dtype)

            langs = self.langs
            predictions = recognition_predictor([image], [langs], detection_predictor)
            # print(predictions) # 測試用

            if predictions and hasattr(predictions[0], 'text_lines'):
                return "\n".join([line.text for line in predictions[0].text_lines])
            return None

    def cleanup_memory(self):
        """釋放記憶體（CUDA 模式釋放 VRAM; CPU 模式釋放 DRAM）"""
        if device == "CUDA":
            empty_cache()
            ipc_collect()
            print("\033[32m[INFO] 已釋放 GPU 記憶體。\033[0m")

    def get_prompt_text(self):
        """回傳 Prompt"""
        return self.prompt_text
    
    def get_extracted_text(self):
        """回傳 OCR 結果"""
        return self.extracted_text
    
    def get_final_text(self):
        """回傳合併結果"""
        return self.final_text
    
    def exit_WinCap(self):
        """關閉視窗，釋放綁定與資源"""
        if hasattr(self, 'tooltip') and self.tooltip.winfo_exists():
            self.tooltip.destroy()
        self.destroy()
        self.quit()

    def escape_WinCap(self):
        """中斷操作，釋放綁定與資源"""
        print(f"\033[31m[INFO] 操作被中斷\033[0m")
        self.is_dragging = False  # 重設拖曳狀態
        if hasattr(self, 'tooltip') and self.tooltip.winfo_exists():
            self.tooltip.destroy()
        self.destroy()
        self.quit()

if __name__ == "__main__":
    import os
    prompt_file = "User_prompt.txt"

    def load_prompt(file):
        """ 從文件載入提示詞 """
        # 取得目前腳本所在的資料夾
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # 構建絕對路徑
        prompt_path = os.path.join(script_dir, "..", "prompt", file)

        try:
            with open(prompt_path, "r", encoding = "utf-8") as file:
                return file.read().strip()

        except:
            print(f"\033[31m[INFO] 找不到 {prompt_path} 文件，將會使用預設的提示詞。\033[0m")
            return None  # 讀取失敗時返回 None
    
    def receive_coordinates(coords):
        """回呼函數，獲取座標"""
        global cb_coords
        cb_coords = coords
        print(f"\033[34m[INFO] 即時回傳選取範圍座標: {coords}\033[0m")

    prompt = load_prompt(prompt_file)
    prompt_control = True

    # 啟動最初的「載入中...」提示框
    preload_root = tk.Tk()
    preload_root.withdraw()
    loading_tip = MouseTooltip(preload_root, follow = False)
    preload_root.update() # 強制畫面更新一次，避免初期不顯示

    app = WindowCapture(
        prompt_control = prompt_control, 
        on_capture = receive_coordinates, 
        prompt = prompt
    )
    loading_tip.destroy() # 關閉預載入提示視窗
    app.mainloop()
    # prompt = app.get_prompt_text()
    # ext = app.get_extracted_text()
    user_input = app.get_final_text()
    if user_input:
        print("\033[33m[INFO] 文字辨識結果：\033[0m")
        print(user_input)
    else:
        print("\033[31m[INFO] 無法獲取文字辨識結果。\033[0m")
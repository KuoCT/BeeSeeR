import io
import gc
import tkinter as tk
import pyautogui
import pyperclip # 剪貼簿
from PIL import Image
from torch.cuda import is_available, empty_cache, ipc_collect
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor

class WindowCapture(tk.Toplevel):
    def __init__(self, prompt_control = True, on_capture = None, prompt = None):
        super().__init__()
        self.prompt_control = prompt_control
        self.on_capture = on_capture  # 回呼函數
        self.prompt = prompt

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
        self.bind("<Escape>", lambda event: self.exit_WinCap())
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

        # 初始化 OCR 變數 (延遲加載)
        self.recognition_predictor = None
        self.detection_predictor = None

    def set_transparent_color(self, color):
        """讓指定顏色變成透明"""
        self.wm_attributes("-transparentcolor", color)

    def start_draw(self, event):
        """當滑鼠左鍵按下時，開始繪製矩形"""
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y,
                                                    outline="white", width=1, fill="green")
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

        # 擷取螢幕畫面到記憶體
        img_bytes = io.BytesIO()
        screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
        screenshot.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # 讀取影像並進行 OCR
        image = Image.open(img_bytes)
        extracted_text = self.perform_ocr(image)

        # 讀取 prompt 內容，若沒有則預設一個
        prompt_text = self.prompt
        if self.prompt is None:
            prompt_text = "以下文字為光學字元辨識後的文字結果，若出現瑕疵請輕度修復文字確保用詞貼近原文，使用**繁體中文**完整翻譯文字並適度使用**台灣常用詞辭典**在地化，稍微使語法自然通順。**只輸出翻譯結果**："
            print("\033[32m[INFO] Prompt文件中沒有內容，使用預設提示詞\033[0m")

        # 合併 prompt 與 OCR 結果
        if extracted_text:
            final_text = f"{prompt_text}\n\n{extracted_text}" if self.prompt_control else extracted_text
            pyperclip.copy(final_text)
            print("\033[32m[INFO] OCR 辨識結果已複製到剪貼簿。\033[0m")
        else:
            final_text = None
            print("\033[31m[INFO] 未偵測到文字內容\033[0m。")

        # 儲存辨識結果
        self.prompt_text = prompt_text
        self.extracted_text = extracted_text
        self.final_text = final_text

        # 清理資源
        image.close()
        self.cleanup_memory()  # 釋放記憶體

        # 確保 OCR 執行完畢後再關閉視窗
        self.exit_WinCap()

    def perform_ocr(self, image):
        """使用 Surya-OCR 進行辨識 (延遲加載)"""
        if self.recognition_predictor is None or self.detection_predictor is None:
            print(f"\033[32m[INFO] 載入 OCR 模型（使用裝置: {device}）...\033[0m")
            self.recognition_predictor = RecognitionPredictor()
            self.detection_predictor = DetectionPredictor()

        predictions = self.recognition_predictor([image], [None], self.detection_predictor)

        if predictions and hasattr(predictions[0], 'text_lines'):
            return "\n".join([line.text for line in predictions[0].text_lines])
        return None

    def cleanup_memory(self):
        """釋放記憶體（CUDA 模式釋放 VRAM; CPU 模式釋放 DRAM）"""
        if self.recognition_predictor is not None:
            del self.recognition_predictor
            self.recognition_predictor = None

        if self.detection_predictor is not None:
            del self.detection_predictor
            self.detection_predictor = None

        print("\033[32m[INFO] 已卸載 OCR 模型。\033[0m")

        if device == "CUDA":
            empty_cache()
            ipc_collect()
            print("\033[32m[INFO] 已釋放 GPU 記憶體。\033[0m")
        else:
            gc.collect()
            print("\033[32m[INFO] 已釋放 CPU 記憶體。\033[0m")

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

    app = WindowCapture(
        prompt_control = prompt_control, 
        on_capture = receive_coordinates, 
        prompt = prompt
    )
    app.mainloop()
    # prompt = app.get_prompt_text()
    # ext = app.get_extracted_text()
    user_input = app.get_final_text()
    if user_input:
        print("\033[33m[INFO] 文字辨識結果：\033[0m")
        print(user_input)
    else:
        print("\033[31m[INFO] 無法獲取文字辨識結果。\033[0m")


import io
import tkinter as tk
import pyautogui
import pyperclip  # 剪貼簿
import torch  # 用來釋放 VRAM
from PIL import Image
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor

# 只初始化一次 OCR 模型，避免多次加載
recognition_predictor = RecognitionPredictor()
detection_predictor = DetectionPredictor()

class WindowCapture(tk.Tk):
    def __init__(self):
        super().__init__()

        # 設定全螢幕
        self.attributes('-fullscreen', True)
        self.config(bg="black")
        self.attributes('-alpha', 0.6)
        self.overrideredirect(True)
        self.bind("<Escape>", lambda event: self.exit_without_screenshot())
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
        self.is_dragging = False  # 用來記錄是否有拖曳

    def set_transparent_color(self, color):
        """讓指定顏色變成透明"""
        self.wm_attributes("-transparentcolor", color)

    def start_draw(self, event):
        """當滑鼠左鍵按下時，開始繪製矩形"""
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y,
                                                    outline="white", width=1, fill="green")
        self.is_dragging = False  # 每次點擊時重置拖曳狀態

    def update_draw(self, event):
        """當滑鼠拖曳時，更新矩形的大小"""
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)
            self.is_dragging = True  # 只要有拖曳，就設置為 True

    def stop_draw(self, event):
        """當滑鼠釋放時，結束繪製並擷取螢幕 + OCR 辨識 + 複製到剪貼簿"""
        if not self.is_dragging:
            self.exit_without_screenshot()
            return

        if self.rect_id:
            x1, y1, x2, y2 = self.canvas.coords(self.rect_id)
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        # 擷取螢幕畫面到記憶體
        img_bytes = io.BytesIO()
        screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
        screenshot.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # 讀取影像並進行 OCR
        image = Image.open(img_bytes)
        extracted_text = self.perform_ocr(image)

        # 讀取 Prompt.txt 內容
        prompt_text = ""
        prompt_file = "Prompt.txt"  # 檔案名稱
        try:
            with open(prompt_file, "r", encoding="utf-8") as file:
                prompt_text = file.read().strip()  # 讀取並去除前後空白
        except FileNotFoundError:
            print(f"找不到 {prompt_file}，將只輸出 OCR 結果。")

        # 合併 prompt 與 OCR 結果
        if extracted_text:
            final_text = f"{prompt_text}\n\n{extracted_text}" if prompt_text else extracted_text
            pyperclip.copy(final_text)
            print("OCR 辨識結果已複製到剪貼簿：")
            print(final_text)
        else:
            print("未偵測到文字內容。")

        # 清理資源
        image.close()  # 釋放 PIL 圖像
        self.cleanup_gpu_memory()  # 釋放 GPU 記憶體

        # 關閉視窗
        self.destroy()

    def perform_ocr(self, image):
        """使用 Surya-OCR 進行辨識"""
        global recognition_predictor, detection_predictor
        predictions = recognition_predictor([image], [None], detection_predictor)

        if predictions and hasattr(predictions[0], 'text_lines'):
            return "\n".join([line.text for line in predictions[0].text_lines])
        return None

    def cleanup_gpu_memory(self):
        """釋放 GPU 記憶體"""
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()

    def exit_without_screenshot(self):
        """直接關閉視窗，不進行截圖"""
        self.destroy()

if __name__ == "__main__":
    app = WindowCapture()
    app.mainloop()

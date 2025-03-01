import io
import tkinter as tk
import pyautogui
import pyperclip  # 剪貼簿
from PIL import Image
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor

class WindowCapture(tk.Tk):
    def __init__(self):
        super().__init__()

        # 設定全螢幕
        self.attributes('-fullscreen', True)

        # 設定視窗背景色
        self.config(bg="black")

        # 設定透明度 (0.0 完全透明, 1.0 完全不透明)
        self.attributes('-alpha', 0.6)

        # 設定無邊框模式
        self.overrideredirect(True)

        # 設定按 ESC 鍵可關閉視窗
        self.bind("<Escape>", lambda event: self.exit_without_screenshot())

        # 設定 Windows Layered Window，讓特定顏色變透明
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

        # 初始化 Surya-OCR 模型
        self.recognition_predictor = RecognitionPredictor()
        self.detection_predictor = DetectionPredictor()

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
            # 如果沒有拖曳，則直接離開（不截圖）
            self.exit_without_screenshot()
            return

        if self.rect_id:
            x1, y1, x2, y2 = self.canvas.coords(self.rect_id)
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        # 擷取螢幕畫面到記憶體
        img_bytes = io.BytesIO()  # 建立記憶體 buffer
        screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
        screenshot.save(img_bytes, format="PNG")  # 存入記憶體，不寫入硬碟
        img_bytes.seek(0)  # 重設讀取位置

        # 從記憶體讀取影像
        image = Image.open(img_bytes)

        # 使用 Surya-OCR 進行辨識
        langs = None
        predictions = self.recognition_predictor([image], [langs], DetectionPredictor())
        # print(predictions)

        # 解析 OCRResult 並提取純文字
        # 確保 `predictions` 內有 OCRResult
        if predictions and hasattr(predictions[0], 'text_lines'):
            extracted_text = "\n".join([line.text for line in predictions[0].text_lines])  # 取得所有文字
            pyperclip.copy(extracted_text)  # 複製到剪貼簿
            print("OCR 辨識結果已複製到剪貼簿：")
            print(extracted_text)
        else:
            print("未偵測到文字內容。")

        # 關閉視窗
        self.destroy()

    def exit_without_screenshot(self):
        """直接關閉視窗，不進行截圖"""
        self.destroy()

if __name__ == "__main__":
    app = WindowCapture()
    app.mainloop()

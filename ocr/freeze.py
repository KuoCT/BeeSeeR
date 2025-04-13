import tkinter as tk
from PIL import ImageGrab, ImageTk

class FreezeOverlay:
    """凍結畫面覆蓋：擷取螢幕並覆蓋顯示為全畫面"""
    
    def __init__(self, master):
        self.master = master
        self.overlay = None
        self.label = None
        self.screenshot_tk = None  # 保存 image 避免被 GC

    def show(self):
        """顯示凍結畫面"""
        if self.overlay:
            return  # 已存在就不重複創建

        screenshot = ImageGrab.grab()
        self.overlay = tk.Toplevel(self.master)
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-topmost", False)
        self.overlay.configure(bg="black")

        # 鎖定鍵盤輸入（選配）
        # self.overlay.bind("<Escape>", lambda e: self.hide())

        self.screenshot_tk = ImageTk.PhotoImage(screenshot)
        self.label = tk.Label(self.overlay, image = self.screenshot_tk)
        self.label.pack()

    def hide(self):
        """解除凍結，關閉覆蓋視窗"""
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
            self.label = None
            self.screenshot_tk = None

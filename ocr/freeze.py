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
        self.overlay.withdraw()  # 先隱藏
        self.overlay.attributes("-fullscreen", True)
        self.overlay.configure(bg="black")

        # 顯示圖片
        self.screenshot_tk = ImageTk.PhotoImage(screenshot)
        self.label = tk.Label(self.overlay, image=self.screenshot_tk)
        self.label.pack()

        # 顯示後延遲提升
        def raise_to_front():
            self.overlay.lift()
            self.overlay.attributes("-topmost", True)
            self.overlay.after(100, lambda: self.overlay.attributes("-topmost", False))

        self.overlay.deiconify()  # 顯示視窗
        self.overlay.after(200, raise_to_front)  # 延遲拉到最前面（等待建立完成）

    def hide(self):
        """解除凍結，關閉覆蓋視窗"""
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
            self.label = None
            self.screenshot_tk = None

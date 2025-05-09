import tkinter as tk
import customtkinter as ctk
from PIL import Image
import json
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑

class overlayWindow(ctk.CTkToplevel):
    def __init__(self, master, showTEXT = "", coords = None, scale_factor = None, on_activate = None, APPDATA = PATH):
        super().__init__(master)

        # Callback 函數 
        self.on_activate = on_activate

        # 讀取配置設定
        self.APPDATA = APPDATA
        self.settings  = self.load_config()
        self.font_size = self.settings.get("font_size", 16)
        # self.opacity = self.settings.get("opacity", 0.92)
        self.opacity = 0.92
        self.lock_movement = self.settings.get("lock_movement", False)
        self.hide = self.settings.get("hide", "show")
        self.relocate_mode = self.settings.get("relocate_mode", "center")
        self.scale_factor = scale_factor
        self.showTEXT = showTEXT

        # 載入圖示
        self.png_increase = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "increase.png")), size = (18, 18))
        self.png_decrease = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "decrease.png")), size = (18, 18))
        self.png_lock = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "lock.png")), size = (14, 18))
        self.png_unlock = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "unlock.png")), size = (14, 18))
        self.png_h_adjust = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "h_adjust.png")), size = (18, 18))
        self.png_v_adjust = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "v_adjust.png")), size = (18, 18))
        self.png_center = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "center.png")), size = (18, 18))
        self.png_bottom = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "bottom.png")), size = (18, 18))
        self.png_right = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "right.png")), size = (18, 18))
        self.png_reuse = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "reuse.png")), size = (18, 18))
        self.png_close = ctk.CTkImage(Image.open(os.path.join(PATH, "icon", "close.png")), size = (18, 18))

        # 取得螢幕大小
        self.screen_width = int(self.winfo_screenwidth() * scale_factor)
        self.screen_height = int(self.winfo_screenheight() * scale_factor)

        # 預設視窗大小
        default_width, default_height = 230, 90 
        min_width, min_height = default_width, default_height  # 最小視窗大小

        # 設定視窗標題
        self.title("overlay")

        # 計算視窗位置
        if coords is None:
            width, height = default_width, default_height
            x1, y1 = (self.screen_width - width) // 2, (self.screen_height - height) // 2  # 置中
            self.w = default_width # 儲存原始寬高，給 relocate 使用
            self.h = default_height
        else:
            x1, y1, x2, y2 = coords
            w, h = int((x2 - x1) / scale_factor), int((y2 - y1) / scale_factor)
            width, height = w, int(h + (45 / scale_factor))
            self.w = w # 儲存原始寬高，給 relocate 使用
            self.h = h

            # **確保視窗大小不小於最小尺寸**
            if width < min_width:
                width = min_width
            if height < min_height:
                height = min_height

            # **確保 x1、y1 在螢幕內**
            x1 = max(x1, 0)
            y1 = max(y1, 0)

            # **檢查是否超出螢幕範圍**
            if x1 + width > self.screen_width:  # 若超出右邊界，回彈
                x1 = max(self.screen_width - width, 0)  # 不能小於 0
            if y1 + height > self.screen_height:  # 若超出下邊界，回彈
                y1 = max(self.screen_height - height, 0)  # 不能小於 0

            # **如果視窗大小大於螢幕，強制縮小**
            width = min(width, self.screen_width)
            height = min(height, self.screen_height)

        # 設定視窗大小與位置
        self.geometry(f"{width}x{height}+{x1}+{y1}")
        self.width, self.height, self.x1, self.y1 = width, height, x1, y1 # 存入目前視窗訊息
        self.withdraw()  # 隱藏視窗

        # 初始化調整用變數（避免 AttributeError）
        self.adj_width = None
        self.adj_height = None
        self.adj_x1 = None
        self.adj_y1 = None

        # 設定視窗透明度與無邊框
        self.attributes("-alpha", self.opacity)
        self.overrideredirect(True)  # 移除標題欄

        # 設定預設字型大小
        self.text_font = ctk.CTkFont(size = self.font_size)

        # 讓視窗保持最上層
        self.attributes("-topmost", True) # 讓視窗顯示在最前面

        # 設定視窗完全透明
        self.config(bg = "green")  # 背景設為 key，這個顏色會被透明處理
        self.attributes("-transparentcolor", "green")

        # 設定可拖動視窗
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.on_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        
        # 初始化滑鼠點擊偏移位置
        self._offset_x = 0
        self._offset_y = 0

        # 設定按 ESC 鍵可關閉視窗
        self.bind("<Escape>", lambda event: self.destroy())

        # 設定 Grid 佈局
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

        # 文字區域
        self.text_f = ctk.CTkFrame(self, fg_color = "green", bg_color = "green")
        self.text_f.grid(row = 0, column = 0, padx = 0, pady = 0, sticky = "nsew")  # 避免視窗邊緣閃爍
        self.text_f.grid_rowconfigure(0, weight = 1)
        self.text_f.grid_columnconfigure(0, weight = 1)

        # 可捲動文字框（唯讀但可複製）
        self.textbox = ctk.CTkTextbox(self.text_f, font = self.text_font, wrap = "char", corner_radius = 4)
        self.textbox.insert("1.0", self.showTEXT)
        self.textbox.configure(state="disabled") # 唯讀
        self.textbox.grid(row = 0, column = 0, padx = 0, pady = (0, 0), sticky = "nsew")

        # 控制區域 1
        self.control_f1 = ctk.CTkFrame(self, fg_color = "green", bg_color = "green")
        self.control_f1.grid(row = 1, column = 0, padx = 0, pady = 0, sticky="we")
        self.control_f1.grid_rowconfigure((0, 1), weight = 0)
        self.control_f1.grid_columnconfigure((0,1,2), weight = 0)
        self.control_f1.grid_columnconfigure((3), weight = 1)
        self.control_f1.grid_columnconfigure((4,5,6,7), weight = 0)

        # 字體調整按鈕
        self.increase_bt = ctk.CTkButton(self.control_f1, text = "", width = 0, height = 20, corner_radius = 4,
                                         image = self.png_increase, command = self.increase_font_size)
        self.increase_bt.grid(row = 0, column = 0, padx = (5, 0), pady = 2, sticky = "w")
        self.decrease_bt = ctk.CTkButton(self.control_f1, text = "", width = 0, height = 20, corner_radius = 4,
                                         image = self.png_decrease, command = self.decrease_font_size)
        self.decrease_bt.grid(row = 0, column = 1, padx = (2, 0), pady = 2, sticky = "w")

        # 鎖定按鈕
        self.lock_bt = ctk.CTkButton(self.control_f1, text="", image = self.png_lock if self.lock_movement else self.png_unlock,
                                     width = 0, height = 20, corner_radius = 4,
                                     fg_color="#454240" if self.lock_movement else ["#2FA572", "#2CC985"],
                                     hover_color="#878584" if self.lock_movement else ["#106A43", "#0C955A"],
                                     command = self.toggle_lock)
        self.lock_bt.grid(row = 0, column = 2, padx = (2, 0), pady = 2, sticky="w")
       
        # 視窗調整按鈕
        adj_size = 50 # 預設幅度
        self.resize_v_bt = ctk.CTkButton(
            self.control_f1, text = "", image = self.png_v_adjust, width = 0, height = 20, corner_radius = 4, 
            fg_color = ["#c48971", "#2a6475"], hover_color = ["#ed9744", "#3696b3"],
            command = lambda: self.increase_v_size(adj_size))
        self.resize_v_bt.bind("<Button-3>", lambda e: self.decrease_v_size(adj_size))
        self.resize_v_bt.grid(row = 0, column = 4, padx = (2, 0), pady = 2, sticky="e")

        self.resize_h_bt = ctk.CTkButton(
            self.control_f1, text = "", image = self.png_h_adjust, width = 0, height = 20, corner_radius = 4, 
            fg_color = ["#c48971", "#2a6475"], hover_color = ["#ed9744", "#3696b3"],
            command = lambda: self.increase_h_size(adj_size))
        self.resize_h_bt.bind("<Button-3>", lambda e: self.decrease_h_size(adj_size))
        self.resize_h_bt.grid(row = 0, column = 5, padx = (2, 0), pady = 2, sticky="e")

        self.relocate_bt = ctk.CTkButton(
            self.control_f1, text = "", image = self.png_center, width = 0, height = 20, corner_radius = 4, 
            fg_color = ["#c48971", "#2a6475"], hover_color = ["#ed9744", "#3696b3"],
            command = lambda: self.relocate())
        self.relocate_bt.grid(row = 0, column = 6, padx = (2, 0), pady = 2, sticky="e")
        self.relocate_bt.bind("<Button-3>", lambda e: self.toggle_relocate_mode())

        # 退出按鈕
        self.exit_bt = ctk.CTkButton(self.control_f1, text = "", image = self.png_close, fg_color = "firebrick3", hover_color = "firebrick", 
                                     corner_radius = 4, width = 0, height = 20, command = self.destroy)
        self.exit_bt.grid(row = 0, column = 7, padx = (2, 5), pady = 2, sticky = "e")

        # 隱藏
        self.buttons = [
            self.increase_bt, self.decrease_bt, self.resize_v_bt,
            self.resize_h_bt, self.relocate_bt, self.lock_bt
        ]
        if self.hide == "hide":
            for button in self.buttons:
                button.grid_remove()
        else:
            for button in self.buttons:
                button.grid()

        # 控制區域 2
        self.slider = ctk.CTkToplevel(self)
        self.slider.title("調整透明度")
        self.slider.geometry(f"50x{self.height}+{self.x1 + int(self.width * scale_factor)}+{self.y1}")  # 設定滑桿視窗大小與位置
        self.slider.overrideredirect(True)  # 移除標題欄

        # 確保背景透明
        self.slider.config(bg = "green")  # 背景設為 key，這個顏色會被透明處理
        self.slider.attributes("-transparentcolor", "green")
        self.slider.attributes("-topmost", True)  # 讓視窗顯示在最前面
        self.slider.attributes("-alpha", 1.0)  # 確保滑桿視窗本身不透明
        self.slider.grid_columnconfigure(0, weight = 1)
        self.slider.grid_rowconfigure(0, weight = 1)

        self.slider_f = ctk.CTkFrame(self.slider, fg_color = "green", bg_color = "green") 
        self.slider_f.grid(row = 0, column = 0, padx = 0, pady = 0, sticky="nsew")
        self.slider_f.grid_columnconfigure(0, weight = 1)
        self.slider_f.grid_rowconfigure(0, weight = 10000)
        self.slider_f.grid_rowconfigure(1, weight = 1)
        self.slider_f.grid_rowconfigure(2, weight = 0)
        self.slider_f.grid_rowconfigure(3, weight = 0)
      
        # 透明度調整滑桿
        self.opacity_sd = ctk.CTkSlider(self.slider_f, from_ = 0.0, to = 1.0, number_of_steps = 90, width = 20,
                                            orientation = "vertical", command = self.update_opacity)
        self.opacity_sd.set(self.opacity)  # 設定滑桿初始值
        self.opacity_sd.grid(row = 1, column = 0, padx = 2, pady = (2, 0), sticky = "ns")

        # 再次翻譯按鈕
        self.re_bt = ctk.CTkButton(
            self.slider_f, text = "", image = self.png_reuse, width = 0, height = 20, corner_radius = 4, 
            fg_color = ["#1e8bba", "#C06E2F"], hover_color = ["#325882", "#A85820"],
            command = lambda: self.re_acivate(coords))
        self.re_bt.grid(row = 2, column = 0, padx = 2, pady = (2, 5), sticky = "ns")
        CTkToolTip(self.re_bt, lambda: "重新翻譯選取範圍")

        # 建立 CoordsHighlighter 物件
        self.highlighter = CoordsHighlighter(self, coords, self.scale_factor)

        # 加到 re_bt 上的事件
        self.re_bt.bind("<Enter>", lambda e: self.highlighter.show())
        self.re_bt.bind("<Leave>", lambda e: self.highlighter.hide())

        # 隱藏選項開關
        hide_sw_var = ctk.StringVar(value = self.hide)
        self.hide_sw = ctk.CTkSwitch(self.slider_f, text = "", height = 20, width = 0, corner_radius = 20, button_length = 4,
                                     variable = hide_sw_var, onvalue = "hide", offvalue = "show", command = self.toggle_control_f1)
        self.hide_sw.grid(row = 3, column = 0, padx = (7, 0), pady = (0, 5), sticky = "ns")

        # 初始化視窗位置
        self.update_relocate_button_png()
        self.relocate()
        self.deiconify()  # 顯示視窗

    def increase_font_size(self):
        """增加字體大小"""
        self.font_size += 2
        self.text_font.configure(size = self.font_size)
        self.save_config()

    def decrease_font_size(self):
        """減少字體大小"""
        if self.font_size > 10:  # 避免字體過小
            self.font_size -= 2
            self.text_font.configure(size = self.font_size)
            self.save_config()

    def increase_v_size(self, size: int):
        """增加視窗垂直大小"""
        # 確保變數初始化
        self.adj_width = self.adj_width or self.width
        self.adj_x1 = self.adj_x1 or self.winfo_x()  # 更新為當前視窗位置
        
        # 更新高度與 y1 座標
        self.adj_height = (self.adj_height or self.height) + int(size / self.scale_factor)
        self.adj_y1 = (self.adj_y1 or self.winfo_y()) - size  # 更新為當前視窗位置
        
        self.geometry(f"{self.adj_width}x{self.adj_height}+{self.adj_x1}+{self.adj_y1}")

        # 同步調整滑桿位置
        if hasattr(self, "slider") and self.slider.winfo_exists():
            slider_x = self.adj_x1 + int(self.adj_width * self.scale_factor) # 滑桿仍在右側
            slider_y = self.adj_y1  # 保持相同的 y 座標
            self.slider.geometry(f"50x{self.adj_height}+{slider_x}+{slider_y}")

    def decrease_v_size(self, size: int):
        """增加視窗垂直大小"""
        # 確保變數初始化
        self.adj_width = self.adj_width or self.width
        self.adj_x1 = self.adj_x1 or self.winfo_x()  # 更新為當前視窗位置
        
        # 更新高度與 y1 座標
        self.adj_height = (self.adj_height or self.height) - int(size / self.scale_factor)
        self.adj_y1 = (self.adj_y1 or self.winfo_y()) + size  # 更新為當前視窗位置
        
        self.geometry(f"{self.adj_width}x{self.adj_height}+{self.adj_x1}+{self.adj_y1}")

        # 同步調整滑桿位置
        if hasattr(self, "slider") and self.slider.winfo_exists():
            slider_x = self.adj_x1 + int(self.adj_width * self.scale_factor) # 滑桿仍在右側
            slider_y = self.adj_y1  # 保持相同的 y 座標
            self.slider.geometry(f"50x{self.adj_height}+{slider_x}+{slider_y}")

    def increase_h_size(self, size: int):
        """增加視窗水平大小"""
        # 確保變數初始化
        self.adj_height = self.adj_height or self.height
        self.adj_y1 = self.adj_y1 or self.winfo_y()  # 更新為當前視窗位置

        # 更新寬度與 x1 座標
        self.adj_width = (self.adj_width or self.width) + int(size / self.scale_factor)
        self.adj_x1 = (self.adj_x1 or self.winfo_x()) - size  # 更新為當前視窗位置

        # 更新視窗大小與位置
        self.geometry(f"{self.adj_width}x{self.adj_height}+{self.adj_x1}+{self.adj_y1}")

        # 同步調整滑桿位置
        if hasattr(self, "slider") and self.slider.winfo_exists():
            slider_x = self.adj_x1 + int(self.adj_width * self.scale_factor) # 滑桿仍在右側
            slider_y = self.adj_y1  # 保持相同的 y 座標
            self.slider.geometry(f"50x{self.adj_height}+{slider_x}+{slider_y}")

    def decrease_h_size(self, size: int):
        """減少視窗水平大小"""
        # 確保變數初始化
        self.adj_height = self.adj_height or self.height
        self.adj_y1 = self.adj_y1 or self.winfo_y()  # 更新為當前視窗位置

        # 更新寬度與 x1 座標
        self.adj_width = (self.adj_width or self.width) - int(size / self.scale_factor)
        self.adj_x1 = (self.adj_x1 or self.winfo_x()) + size  # 更新為當前視窗位置

        # 更新視窗大小與位置
        self.geometry(f"{self.adj_width}x{self.adj_height}+{self.adj_x1}+{self.adj_y1}")

        # 同步調整滑桿位置
        if hasattr(self, "slider") and self.slider.winfo_exists():
            slider_x = self.adj_x1 + int(self.adj_width * self.scale_factor) # 滑桿仍在右側
            slider_y = self.adj_y1  # 保持相同的 y 座標
            self.slider.geometry(f"50x{self.adj_height}+{slider_x}+{slider_y}")

    def update_relocate_button_png(self):
        """根據 relocate_mode 更新圖示"""
        png_map = {
            "center": self.png_center,
            "bottom": self.png_bottom,
            "right": self.png_right
        }
        self.relocate_bt.configure(image = png_map[self.relocate_mode])

    def toggle_relocate_mode(self):
        """切換還原模式"""
        modes = ["center", "bottom", "right"]
        current_index = modes.index(self.relocate_mode)
        next_index = (current_index + 1) % len(modes)
        self.relocate_mode = modes[next_index]

        self.update_relocate_button_png()  # 更新按鈕文字
        self.save_config()
    
    def relocate(self):
        """還原視窗大小與位置"""
        # **確保變數完全回歸原始狀態**
        self.adj_width = None
        self.adj_height = None
        self.adj_x1 = None
        self.adj_y1 = None

        # 更新視窗大小與位置
        if self.relocate_mode == "bottom":
            self.geometry(f"{self.width}x{self.height}+{self.x1}+{self.y1 + int(self.h * self.scale_factor)}")
        elif self.relocate_mode == "right":
            self.geometry(f"{self.width}x{self.height}+{(self.x1 + int(self.w * self.scale_factor))}+{self.y1}")
        else:
            self.geometry(f"{self.width}x{self.height}+{self.x1}+{self.y1}")

        # 延遲調整滑桿位置，確保主視窗位置更新完成
        if hasattr(self, "slider") and self.slider.winfo_exists():
            self.after(10, self.update_slider_position)
            
    def update_slider_position(self):
        """更新滑桿位置"""
        slider_x = self.winfo_x() + int(self.width * self.scale_factor)
        slider_y = self.winfo_y()
        self.slider.geometry(f"50x{self.height}+{slider_x}+{slider_y}")

    def toggle_lock(self):
        """切換視窗移動鎖定"""
        self.lock_movement = not self.lock_movement
        self.lock_bt.configure(
            image = self.png_lock if self.lock_movement else self.png_unlock,
            fg_color="#454240" if self.lock_movement else ["#2FA572", "#2CC985"],
            hover_color="#878584" if self.lock_movement else ["#106A43", "#0C955A"]
        )
        self.save_config()  # 每次切換都儲存設定

    def update_opacity(self, value):
        """調整視窗透明度"""
        self.opacity = round(float(value), 2)  # 轉換成浮點數並保留 2 位小數
        self.attributes("-alpha", self.opacity)  # 更新透明度
        # self.save_config()

    def toggle_control_f1(self):
        """控制區的顯示與隱藏"""
        if self.hide == "show":
            self.hide = "hide"
            for button in self.buttons:
                button.grid_remove()
        else:
            self.hide = "show"
            for button in self.buttons:
                button.grid()
        self.save_config()

    def start_move(self, event):
        """記錄滑鼠點擊位置"""
        self._offset_x = event.x
        self._offset_y = event.y

    def on_move(self, event):
        """根據滑鼠移動視窗"""
        if self.lock_movement:
            return
        x = self.winfo_x() + (event.x - self._offset_x)
        y = self.winfo_y() + (event.y - self._offset_y)
        self.geometry(f"+{x}+{y}")

        self.adj_x1 = x
        self.adj_y1 = y

        if hasattr(self, "slider") and self.slider.winfo_exists():
            slider_x = x + int((self.adj_width if self.adj_width is not None else self.width) * self.scale_factor)  # 滑桿視窗放在主視窗右側
            slider_y = y  # 保持相同的 y 座標
            self.slider.geometry(f"+{slider_x}+{slider_y}")

    def stop_move(self, event):
        """釋放滑鼠後，停止移動"""
        self._offset_x = 0
        self._offset_y = 0

    def re_acivate(self, coords):
        """重新翻譯一次"""
        # print(f"重新翻譯一次: {coords}")
        self.withdraw()
        if self.on_activate:
            self.on_activate(coords)
            # 等待 500 毫秒後銷毀
            self.after(500, self.destroy)

    def load_config(self):
        """讀取設定檔案"""
        if os.path.exists(os.path.join(self.APPDATA, "config.json")):
            with open(os.path.join(self.APPDATA, "config.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        return {}  # 如果沒有設定檔，回傳空字典
    
    def save_config(self):
        """只有當設定異動時，才更新 config.json"""
        old_config = self.load_config()

        # 準備要寫入的內容
        new_config = {
            "font_size": self.font_size,
            "lock_movement": self.lock_movement,
            "hide": self.hide,
            "relocate_mode": self.relocate_mode
        }

        # 只有內容不同時才寫入
        if old_config != {**old_config, **new_config}:
            old_config.update(new_config)
            with open(os.path.join(self.APPDATA, "config.json"), "w", encoding = "utf-8") as f:
                json.dump(old_config, f, ensure_ascii = False, indent = 4)
            # print("\033[32m[INFO] 設定檔已更新\033[0m")
        else:
            # print("\033[34m[INFO] 設定無變更，跳過寫入\033[0m")
            pass

    def withdraw(self):
        super().withdraw()
        if hasattr(self, "slider") and self.slider.winfo_exists():
            self.slider.withdraw()

    def deiconify(self):
        super().deiconify()
        if hasattr(self, "slider") and self.slider.winfo_exists():
            self.slider.deiconify()
    
    def destroy(self):
        if hasattr(self, "slider") and self.slider.winfo_exists():
            self.slider.destroy()
        super().destroy()

class CTkToolTip:
    def __init__(self, widget, text_func, delay = 500):
        self.widget = widget
        self.text_func = text_func  # 傳入一個回傳提示文字的函式
        self.tipwindow = None
        self.id = None
        self.delay = delay
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.showtip)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def showtip(self):
        if self.tipwindow:
            return
        x, y, _, _ = self.widget.bbox("insert") or (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.attributes("-topmost", True)  # 再次確保 topmost
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text = self.text_func(),
            font = ("Helvetica", 10),
            bg = "yellow",
            fg = "black",
            highlightthickness = 1,
            highlightbackground = "black",
            anchor = "w",
            justify = "left",)
        label.pack()

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class CoordsHighlighter:
    def __init__(self, master, coords, scale_factor):
        self.master = master
        self.coords = coords
        self.scale_factor = scale_factor
        self.overlay = None

    def show(self):
        if not self.coords:
            return
        
        x1, y1, x2, y2 = self.coords
        width = int((x2 - x1))
        height = int((y2 - y1))
        x = int(x1)
        y = int(y1)

        # 建立透明視窗
        self.overlay = tk.Toplevel(self.master)
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-transparentcolor", "green")
        self.overlay.configure(bg = "green")

        # 設定大小與位置
        self.overlay.geometry(f"{width}x{height}+{x}+{y}")

        # 畫邊框
        canvas = tk.Canvas(self.overlay, width = width, height = height, highlightthickness = 0, bg = "green")
        canvas.pack()
        canvas.create_rectangle(1, 1, width - 2, height - 2, outline = "yellow", width = 2)

    def hide(self):
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
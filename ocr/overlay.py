import customtkinter as ctk
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json") # 設定檔案名稱

class overlayWindow(ctk.CTkToplevel):
    def __init__(self, showTEXT = None, coords = None, scale_factor = 1):
        super().__init__()

        # 讀取配置設定
        self.settings  = self.load_config()
        self.font_size = self.settings.get("font_size", 20)
        self.opacity = self.settings.get("opacity", 0.95)
        self.lock_movement = self.settings.get("lock_movement", False)
        self.hide = self.settings.get("hide", "show")
        self.scale_factor = scale_factor

        # 設定要顯示的文字
        if showTEXT is None:
            showTEXT = "這是一個不可編輯的文字顯示區域，可以調整透明度，可以縮放字體大小，鎖定視窗後可以複製文字。\n" * 20
        self.showTEXT = showTEXT

        # 設定預設顏色 (主題讓主視窗決定)
        base_dir = os.path.dirname(os.path.abspath(__file__))  # 取得 overlay.py 的目錄
        theme_path = os.path.join(base_dir, "..", "theme", "nectar.json")
        ctk.set_default_color_theme(theme_path)

        # 取得螢幕大小
        self.screen_width = int(self.winfo_screenwidth() * scale_factor)
        self.screen_height = int(self.winfo_screenheight() * scale_factor)

        # 預設視窗大小
        default_width, default_height = 500, 90 # 最小視窗大小
        min_width, min_height = default_width, default_height  # 最小視窗大小

        # 設定視窗標題
        self.title("overlay")

        # 計算視窗位置
        if coords is None:
            width, height = default_width, default_height
            x1, y1 = (self.screen_width - width) // 2, (self.screen_height - height) // 2  # 置中
        else:
            x1, y1, x2, y2 = coords
            w, h = int((x2 - x1) / scale_factor), int((y2 - y1) / scale_factor)
            width, height = int(w + (30 / scale_factor)), int(h + (45 / scale_factor)), 

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

        # 初始化調整用變數（避免 AttributeError）
        self.adj_width = None
        self.adj_height = None
        self.adj_x1 = None
        self.adj_y1 = None

        # 設定視窗透明度與無邊框
        self.attributes("-alpha", self.opacity)
        self.overrideredirect(True)  # 移除標題欄

        # 設定預設字體、顏色
        text_font = ctk.CTkFont(family = "Helvetica", size = self.font_size, weight = "bold")
        text_fix_font = ctk.CTkFont(family = "Helvetica", size = 20, weight = "bold")

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
        # self.bind("<Escape>", lambda event: self.destroy())

        # 設定 Grid 佈局
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

        # 文字區域
        self.text_f = ctk.CTkFrame(self, fg_color = "green", bg_color = "green", border_color = "green")
        self.text_f.grid(row = 0, column = 0, padx = 0, pady = 0, sticky = "nsew")  # 避免視窗邊緣閃爍
        self.text_f.grid_rowconfigure(0, weight = 1)
        self.text_f.grid_columnconfigure(0, weight = 1)

        # 可捲動文字框（唯讀但可複製）
        self.textbox = ctk.CTkTextbox(self.text_f, font = text_font, wrap = "word", corner_radius = 4, border_color = "green", border_width = 0.1)
        self.textbox.insert("1.0", self.showTEXT)
        self.textbox.configure(state="disabled") # 唯讀
        self.textbox.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = "nsew")

        # 控制區域 1
        self.control_f1 = ctk.CTkFrame(self, fg_color = "green", bg_color = "green")
        self.control_f1.grid(row = 1, column = 0, padx = 0, pady = 0, sticky="we")
        self.control_f1.grid_rowconfigure(0, weight = 1)
        self.control_f1.grid_columnconfigure(2, weight = 1)

        # 字體調整按鈕
        self.increase_bt = ctk.CTkButton(self.control_f1, text = "字放大", width = 60, corner_radius = 4, border_color = "green", border_width = 0.1,
                                         font = text_fix_font, command = self.increase_font_size)
        self.increase_bt.grid(row = 0, column = 0, padx = (5, 0), pady = 5, sticky = "w")
        self.decrease_bt = ctk.CTkButton(self.control_f1, text = "字縮小", width = 60, corner_radius = 4, border_color = "green", border_width = 0.1,
                                         font = text_fix_font, command = self.decrease_font_size)
        self.decrease_bt.grid(row = 0, column = 1, padx = (5, 0), pady = 5, sticky = "w")
       
        increase_size = 50 # 預設增加幅度
        self.resize_v_bt = ctk.CTkButton(
            self.control_f1, text = "↕", font = text_fix_font, width = 30, corner_radius = 4, border_color = "green", border_width = 0.1,
            fg_color = ["#c48971", "#2a6475"], hover_color = ["#ed9744", "#3696b3"],
            command = lambda: self.increase_v_size(increase_size))
        self.resize_v_bt.grid(row = 0, column = 2, padx = (5, 0), pady = 5, sticky="e")

        self.resize_h_bt = ctk.CTkButton(
            self.control_f1, text = "↔", font = text_fix_font, width = 30, corner_radius = 4, border_color = "green", border_width = 0.1,
            fg_color = ["#c48971", "#2a6475"], hover_color = ["#ed9744", "#3696b3"],
            command = lambda: self.increase_h_size(increase_size))
        self.resize_h_bt.grid(row = 0, column = 3, padx = (5, 0), pady = 5, sticky="e")

        self.resize_r_bt = ctk.CTkButton(
            self.control_f1, text = "⛶", font = text_fix_font, width = 30, corner_radius = 4, border_color = "green", border_width = 0.1,
            fg_color = ["#c48971", "#2a6475"], hover_color = ["#ed9744", "#3696b3"],
            command = lambda: self.undo_size())
        self.resize_r_bt.grid(row = 0, column = 4, padx = (5, 0), pady = 5, sticky="e")

        # 鎖定按鈕
        self.lock_bt = ctk.CTkButton(self.control_f1, text="鎖定中" if self.lock_movement else "可移動", width = 60,
                                     font = text_fix_font, corner_radius = 4, border_color = "green", border_width = 0.1,
                                     fg_color="#454240" if self.lock_movement else ["#2FA572", "#2CC985"],
                                     hover_color="#878584" if self.lock_movement else ["#106A43", "#0C955A"],
                                     command = self.toggle_lock)
        self.lock_bt.grid(row = 0, column = 5, padx = (5, 0), pady = 5, sticky="e")

        # 退出按鈕
        self.exit_bt = ctk.CTkButton(self.control_f1, text = "退出", fg_color = "firebrick3", hover_color = "firebrick", 
                                     corner_radius = 4, width = 60, border_color = "green", border_width = 0.1, 
                                     font = text_fix_font, command = self.safe_destroy)
        self.exit_bt.grid(row = 0, column = 6, padx = 5, pady = 5, sticky = "e")

        # 隱藏
        self.buttons = [
            self.increase_bt, self.decrease_bt, self.resize_v_bt,
            self.resize_h_bt, self.resize_r_bt, self.lock_bt
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
        self.slider_f.grid_rowconfigure(0, weight = 1)
      
        # 透明度調整滑桿
        self.opacity_sd = ctk.CTkSlider(self.slider_f, from_ = 0.0, to = 1.0, number_of_steps = 90, width = 20,
                                            orientation = "vertical", command = self.update_opacity)
        self.opacity_sd.set(self.opacity)  # 設定滑桿初始值
        self.opacity_sd.grid(row = 0, column = 0, padx = 5, pady = (5, 0), sticky = "ns")

        # 隱藏選項按鈕
        hide_bt_var = ctk.StringVar(value = self.hide)
        self.hide_bt = ctk.CTkSwitch(self.slider_f, text = "", height = 28, corner_radius = 4, button_length = 10,
                                     variable = hide_bt_var, onvalue = "hide", offvalue = "show", command = self.toggle_control_f1)
        self.hide_bt.grid(row = 1, column = 0, padx = 5, pady = 5, sticky = "ns")

    def increase_font_size(self):
        """增加字體大小"""
        self.font_size += 2
        self.textbox.configure(font=("Arial", self.font_size))
        self.save_config()

    def decrease_font_size(self):
        """減少字體大小"""
        if self.font_size > 10:  # 避免字體過小
            self.font_size -= 2
            self.textbox.configure(font=("Arial", self.font_size))
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
    
    def undo_size(self):
        """還原視窗大小與位置"""
        # **確保變數完全回歸原始狀態**
        self.adj_width = None
        self.adj_height = None
        self.adj_x1 = None
        self.adj_y1 = None

        # 更新視窗大小與位置
        self.geometry(f"{self.width}x{self.height}+{self.x1}+{self.y1}")

        # 同步調整滑桿位置
        if hasattr(self, "slider") and self.slider.winfo_exists():
            slider_x = self.x1 + int(self.width * self.scale_factor)  # 滑桿仍在右側
            slider_y = self.y1  # 保持相同的 y 座標
            self.slider.geometry(f"50x{self.height}+{slider_x}+{slider_y}")

    def toggle_lock(self):
        """切換視窗移動鎖定"""
        self.lock_movement = not self.lock_movement
        self.lock_bt.configure(
            text="鎖定中" if self.lock_movement else "可移動",
            fg_color="#454240" if self.lock_movement else ["#2FA572", "#2CC985"],
            hover_color="#878584" if self.lock_movement else ["#106A43", "#0C955A"]
        )
        self.save_config()  # 每次切換都儲存設定

    def update_opacity(self, value):
        """調整視窗透明度"""
        self.opacity = round(float(value), 2)  # 轉換成浮點數並保留 2 位小數
        self.attributes("-alpha", self.opacity)  # 更新透明度
        self.save_config()

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

        if hasattr(self, "slider") and self.slider.winfo_exists():
            slider_x = x + int((self.adj_width if self.adj_width is not None else self.width) * self.scale_factor)  # 滑桿視窗放在主視窗右側
            slider_y = y  # 保持相同的 y 座標
            self.slider.geometry(f"+{slider_x}+{slider_y}")

    def stop_move(self, event):
        """釋放滑鼠後，停止移動"""
        self._offset_x = 0
        self._offset_y = 0

    # def on_slider_press(self, event):
    #     """當使用者開始拖曳滑桿時，暫時取消視窗拖動"""
    #     self.unbind("<B1-Motion>")

    # def on_slider_release(self, event):
    #     """當使用者釋放滑桿時，恢復視窗拖動"""
    #     self.bind("<B1-Motion>", self.on_move)

    def load_config(self):
        """讀取設定檔案"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {}  # 如果沒有設定檔，回傳空字典
    
    def save_config(self):
        """讀取現有設定，更新後再存入 JSON 檔案"""
        config = self.load_config()  # 先載入現有設定

        # 更新設定
        config.update({
            "font_size": self.font_size,
            "opacity": self.opacity,
            "lock_movement": self.lock_movement,
            "hide": self.hide
        })

        # 將更新後的設定存回 JSON
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent = 4)  # `indent=4` 讓 JSON 易讀

    def safe_destroy(self):
        """確保關閉視窗時不會有綁定事件錯誤"""
        try:
            # self.withdraw()
            # 檢查 after 事件並取消 (捨棄)
            # after_ids = self.tk.call("after", "info")
            # if isinstance(after_ids, tuple):  # 確保它是 tuple
            #     for after_id in after_ids:
            #         try:
            #             # print(after_id) # 測試用
            #             self.after_cancel(after_id)
            #         except Exception as e:
            #             print(f"\033[31m[WARNING] 無法取消 after 事件 {after_id}: {e}\033[0m")
            # self.unbind("<ButtonPress-1>")
            # self.unbind("<B1-Motion>")
            # self.unbind("<ButtonRelease-1>")
            self.destroy()
            self.quit()
        except Exception as e:
            print(f"\033[31m[INFO] 視窗關閉時發生錯誤: {e}\033[0m")

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    # ctk.set_appearance_mode("dark")
    app = overlayWindow()
    app.mainloop()
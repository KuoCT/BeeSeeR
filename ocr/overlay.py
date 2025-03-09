import customtkinter as ctk
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overlay_config.json") # 設定檔案名稱

class overlayWindow(ctk.CTk):
    def __init__(self, showTEXT = None, TEXTsize = 18, coords = None, opacity = 0.95):
        super().__init__()

        # 讀取配置設定
        self.settings  = self.load_config()
        self.font_size = self.settings.get("font_size", TEXTsize)
        self.opacity = self.settings.get("opacity", opacity)

        # 設定要顯示的文字
        if showTEXT is None:
            showTEXT = "這是一個不可編輯的文字顯示區域，可以調整透明度，可以縮放字體大小，鎖定視窗後可以複製文字。\n" * 20
        self.showTEXT = showTEXT

        # 設定背景顏色
        self.current_theme = "dark"
        base_dir = os.path.dirname(os.path.abspath(__file__))  # 取得 overlay.py 的目錄
        theme_path = os.path.join(base_dir, "..", "theme", "nectar.json")
        ctk.set_appearance_mode(self.current_theme)
        ctk.set_default_color_theme(theme_path)

        # 取得螢幕大小
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()

        # 預設視窗大小
        default_width, default_height = 600, 400
        min_width, min_height = default_width, default_height  # 最小視窗大小

        # 設定視窗標題
        self.title("overlay")

        # 計算視窗位置
        if coords is None:
            width, height = default_width, default_height
            x1, y1 = (self.screen_width - width) // 2, (self.screen_height - height) // 2  # 置中
        else:
            x1, y1, x2, y2 = coords
            width, height = x2 - x1, y2 - y1

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
        # 設定視窗透明度與無邊框
        self.opacity = self.settings.get("opacity", opacity)  # 設定預設透明度
        self.attributes("-alpha", self.opacity)
        self.overrideredirect(True)  # 移除標題欄

        # 設定預設字體、顏色
        self.font_size = self.settings.get("font_size", TEXTsize) # 設定預設字體大小
        text_font = ctk.CTkFont(family = "Helvetica", size = self.font_size, weight = "bold")
        text_fix_font = ctk.CTkFont(family = "Helvetica", size = 20, weight = "bold")

        # 讓視窗保持最上層
        self.attributes("-topmost", True) # 新增這行讓視窗顯示在最前面

        # 設定視窗完全透明
        self.config(bg = "green")  # 背景設為 key，這個顏色會被透明處理
        self.attributes("-transparentcolor", "green")

        # 設定可拖動視窗
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.on_move)
        self.bind("<ButtonRelease-1>", self.stop_move)

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
        self.textbox = ctk.CTkTextbox(self.text_f, font = text_font, wrap = "word", corner_radius = 10)
        self.textbox.insert("1.0", self.showTEXT)
        self.textbox.configure(state="disabled") # 唯讀
        self.textbox.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = "nsew")

        # 控制區域 1
        self.control_f1 = ctk.CTkFrame(self, fg_color = "green", bg_color = "green")
        self.control_f1.grid(row = 1, column = 0, padx = 0, pady = 0, sticky="nsew")
        self.control_f1.grid_rowconfigure(0, weight = 1)
        self.control_f1.grid_columnconfigure((0, 1, 2, 3, 4), weight = 1)

        # 字體調整按鈕
        self.increase_button = ctk.CTkButton(self.control_f1, text = "放大",
                                             font = text_fix_font, command = self.increase_font_size)
        self.increase_button.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = "nsew")
        self.decrease_button = ctk.CTkButton(self.control_f1, text = "縮小",
                                             font = text_fix_font, command = self.decrease_font_size)
        self.decrease_button.grid(row = 0, column = 1, padx = 5, pady = 5, sticky = "nsew")

        # 主題切換按鈕
        self.theme_button = ctk.CTkButton(self.control_f1, text = "主題", font = text_fix_font, 
                                         fg_color = ["#c48971", "#2a6475"], hover_color = ["#ed9744", "#3696b3"],
                                         command = self.toggle_theme)
        self.theme_button.grid(row = 0, column = 2, padx = 5, pady = 5, sticky="nsew")

        # 鎖定按鈕
        self.lock_movement = False  # 預設允許移動
        self.lock_button = ctk.CTkButton(self.control_f1, text = "可移動", font = text_fix_font, 
                                         fg_color = ["#2FA572", "#2FA572"], hover_color = ["#1e754f", "#1e754f"],
                                         command = self.toggle_lock)
        self.lock_button.grid(row = 0, column = 3, padx = 5, pady = 5, sticky="nsew")


        # 退出按鈕
        self.exit_button = ctk.CTkButton(self.control_f1, text = "退出", fg_color = "firebrick3", hover_color = "firebrick",
                                         font = text_fix_font, command = self.safe_destroy)
        self.exit_button.grid(row = 0, column = 4, padx = 5, pady = 5, sticky = "nsew")

        # 控制區域 2
        self.control_f2 = ctk.CTkFrame(self, fg_color = "green", bg_color = "green")
        self.control_f2.grid(row = 0, rowspan = 2, column = 1, padx = 0, pady = 0, sticky="nsew")
        self.control_f2.grid_rowconfigure(0, weight = 1)
        self.control_f2.grid_columnconfigure(0, weight = 1)
        
        # 透明度調整滑桿
        self.opacity_slider = ctk.CTkSlider(self.control_f2, from_ = 0.3, to = 1.0, number_of_steps = 70, width = 20,
                                            orientation = "vertical", command = self.update_opacity)
        self.opacity_slider.set(self.opacity)  # 設定滑桿初始值
        self.opacity_slider.bind("<ButtonPress-1>", self.on_slider_press)
        self.opacity_slider.bind("<ButtonRelease-1>", self.on_slider_release)
        self.opacity_slider.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = "ns")

        # 記錄滑鼠點擊位置
        self._offset_x = 0
        self._offset_y = 0

    def toggle_theme(self):
        """切換 Light/Dark 模式"""
        if self.current_theme == "dark":
            self.current_theme = "light"
            ctk.set_appearance_mode("light")  # 切換為 Light 模式
        else:
            self.current_theme = "dark"
            ctk.set_appearance_mode("dark")  # 切換為 Dark 模式

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

    def toggle_lock(self):
        """切換視窗移動鎖定"""
        self.lock_movement = not self.lock_movement
        self.lock_button.configure(
            text = "鎖定中" if self.lock_movement else "可移動",
            fg_color = "#454240" if self.lock_movement else  ["#2FA572", "#2CC985"],
            hover_color = "#878584" if self.lock_movement else ["#106A43", "#0C955A"]
        )

    def update_opacity(self, value):
        """調整視窗透明度"""
        self.opacity = float(value)  # 轉換成浮點數
        self.attributes("-alpha", self.opacity)  # 更新透明度
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

    def on_slider_press(self, event):
        """當使用者開始拖曳滑桿時，暫時取消視窗拖動"""
        self.unbind("<B1-Motion>")

    def on_slider_release(self, event):
        """當使用者釋放滑桿時，恢復視窗拖動"""
        self.bind("<B1-Motion>", self.on_move)

    def stop_move(self, event):
        """釋放滑鼠後，停止移動"""
        self._offset_x = 0
        self._offset_y = 0

    def save_config(self):
        """儲存設定到 JSON 檔案"""
        with open(CONFIG_FILE, "w") as f:
            json.dump({"font_size": self.font_size, "opacity": self.opacity}, f)

    def load_config(self):
        """讀取設定檔案"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {}

    def safe_destroy(self):
        """確保關閉視窗時不會有綁定事件錯誤"""
        try:
            self.withdraw()
            after_ids = self.tk.call("after", "info")
            if isinstance(after_ids, tuple):  # 確保它是 tuple
                for after_id in after_ids:
                    try:
                        # print(after_id) # 測試用
                        self.after_cancel(after_id)
                    except Exception as e:
                        print(f"\033[31m[WARNING] 無法取消 after 事件 {after_id}: {e}\033[0m")
            self.unbind("<ButtonPress-1>")
            self.unbind("<B1-Motion>")
            self.unbind("<ButtonRelease-1>")
            self.quit()
            # self.destroy()  # 會報錯 can't delete Tcl command!!
        except Exception as e:
            print(f"\033[31m[INFO] 視窗關閉時發生錯誤: {e}\033[0m")

if __name__ == "__main__":
    app = overlayWindow()
    app.mainloop()
    # prompt = app.get_prompt_text()
    # ext = app.get_extracted_text()
    # user_input = app.get_final_text()
    # if user_input:
    #     print("\033[33m[INFO] 文字辨識結果：\033[0m")
    #     print(user_input)
    # else:
    #     print("\033[31m[INFO] 無法獲取文字辨識結果。\033[0m")

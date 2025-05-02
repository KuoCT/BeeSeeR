import customtkinter as ctk

# ↓ 有問題的輸入法符號補丁對照表）
IME_PATCH_KEYCODE_MAP = {
    33: "!",  # shift + 1
    35: "#",  # shift + 3
    36: "$",  # shift + 4
    37: "%",  # shift + 5
    38: "&",  # shift + 7
    41: ")",  # shift + 9
    40: "(",  # shift + 0
    34: '"',  # shift + '
    39: "'",  # ' (key)
    45: "-",  # - (數字鍵)
    46: "."   # . (數字鍵)
}

# ↓ IME 輸入法補丁共用 Mixin，供 CTkTextbox/Entry/ComboBox 使用
class IMEPatchMixin:
    def __init__(self, *args, silence=True, **kwargs):
        super().__init__(*args, **kwargs)

        self.silence = silence  # 控制是否輸出 debug 訊息
        self.ime_active = False  # ← 旗標：下一次輸入當作中文補丁用

        # 綁定鍵盤事件（中文輸入法 IME 補丁）
        self.bind("<KeyPress>", self.on_key_press)

    def _log(self, *args, **kwargs):
        if not self.silence:
            print(*args, **kwargs)

    def on_key_press(self, event):
        """按下按鍵時的補丁"""
        self._log(f"[DEBUG] keysym: {event.keysym}, keycode: {event.keycode}, char: {repr(event.char)}")

        # 偵測 IME 組字觸發（微軟注音等）
        if event.keycode == 229:
            self._log("→ 檢測到 IME 組字開始")
            self.ime_active = True
            return None  # 等下一次真正按鍵再處理

        # 若 ime_active 為 True，執行補丁
        if self.ime_active:
            self._log("→ 組字完成，執行補丁")
            self.ime_active = False
            if self.patch_key_behavior(event):
                return "break" # 阻止本來的輸出

        return None # 輸出原本的文字

    def patch_key_behavior(self, event):
        """根據 keycode / keysym / char 修補中文輸入法導致打不出的符號"""
        if event.keycode in IME_PATCH_KEYCODE_MAP:
            char_to_insert = IME_PATCH_KEYCODE_MAP[event.keycode]
            self._log(f"→ 補丁（keycode）: 插入 {char_to_insert}")
            self.insert("insert", char_to_insert)
            return True

        return False


# ↓ 三個已補丁的元件，直接使用即可
class CTkTextbox(IMEPatchMixin, ctk.CTkTextbox):
    pass

class CTkEntry(IMEPatchMixin, ctk.CTkEntry):
    pass

class CTkComboBox(ctk.CTkComboBox):
    def __init__(self, *args, silence=True, **kwargs):
        super().__init__(*args, **kwargs)

        self.silence = silence  # 控制是否輸出 debug 訊息
        self.ime_active = False  # ← 旗標：下一次輸入當作中文補丁用

        # 將事件綁定到 ComboBox 自身（監聽 key press）
        self.bind("<KeyPress>", self.on_key_press)

    def _log(self, *args, **kwargs):
        if not self.silence:
            print(*args, **kwargs)

    def on_key_press(self, event):
        """按下按鍵時的補丁（針對 ComboBox）"""
        self._log(f"[DEBUG] keysym: {event.keysym}, keycode: {event.keycode}, char: {repr(event.char)}")

        if event.keycode == 229:
            self._log("→ 檢測到 IME 組字開始")
            self.ime_active = True
            return None

        if self.ime_active:
            self._log("→ 組字完成，執行補丁")
            self.ime_active = False
            if self.patch_key_behavior(event):
                return "break"

        return None

    def patch_key_behavior(self, event):
        """ComboBox 用的補丁輸入（使用 entry.insert）"""
        if event.keycode in IME_PATCH_KEYCODE_MAP:
            char_to_insert = IME_PATCH_KEYCODE_MAP[event.keycode]
            self._log(f"→ 補丁（keycode）: 插入 {char_to_insert}")

            # 取得當前游標位置
            index = self._entry.index("insert")

            # 插入字元到游標位置
            self._entry.insert(index, char_to_insert)

            return True

        return False
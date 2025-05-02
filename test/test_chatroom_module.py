import customtkinter as ctk
import os
import sys

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..") # 設定相對路徑
sys.path.append(PATH) # 將路徑加入到系統路徑中

if __name__ == "__main__":
    from tool.PersonaEditor import PersonaEditor
    from llm.chatroom import chatroomWindow

    # 輸入 groq_key
    print("\033[32m[INFO] 請提供Groq API key。\033[0m")
    groq_key = input("\033[33mGroq API key: \033[0m")

    # 設定主題
    current_theme = "dark"

    # 設定主題
    if current_theme == "dark":
        ctk.set_appearance_mode("dark")
    else:
        ctk.set_appearance_mode("light")

    ctk.set_default_color_theme(os.path.join(PATH, "theme", "nectar.json"))

    def toggle_theme():
        """切換主題的函數"""
        global current_theme # 使用全域變數
        if current_theme == "dark": # 如果當前主題是深色
            ctk.set_appearance_mode("light") # 切換到淺色主題
            current_theme = "light" # 更新當前主題變數
        else: # 如果當前主題是淺色
            ctk.set_appearance_mode("dark") # 切換到深色主題
            current_theme = "dark" # 更新當前主題變數

    def link_persona():
        """將人格指令連結到聊天室"""
        chatroom.updated_persona = PerEdit.updated_persona  # 更新聊天室的 persona 變數

    root = ctk.CTk() # 創建主視窗
    PerEdit = PersonaEditor(current_theme) # 創建子視窗
    chatroom = chatroomWindow(current_theme, groq_key = groq_key, on_link_persona = link_persona)
    chatroom.deiconify() # 顯示視窗

    toggle_theme_bt = ctk.CTkButton(root, text = "切換主題", command = toggle_theme)
    toggle_theme_bt.pack(padx = 10, pady = 10) 

    root.attributes("-topmost", True) # 讓視窗顯示在最前面
    root.mainloop()
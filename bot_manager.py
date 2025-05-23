import customtkinter as ctk
import psutil
import subprocess
import os
import webbrowser
import pygetwindow as gw
import time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

BOT_DIR = r"C:\Users\Administrator\Desktop\BotAutoMinecraft"

class BotManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BotAutoMinecraft Manager")
        self.geometry("900x550")
        self.minsize(800, 500)

        self.bots = [f"Vanguard{i:02}" for i in range(1, 31)]
        self.widgets = []

        self.setup_gui()
        self.draw_bots()
        self.update_status_loop()

    def setup_gui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.scroll_frame.pack(fill="both", expand=True)

        headers = ["Bot Name", "Inventory", "Status", "Focus", "Run", "Close", "Edit", "Resource"]
        for i in range(len(headers)):
            self.scroll_frame.grid_columnconfigure(i, weight=1)

        for i, header in enumerate(headers):
            ctk.CTkLabel(self.scroll_frame, text=header, font=("Segoe UI", 14, "bold")).grid(
                row=0, column=i, padx=10, pady=10, sticky="ew"
            )

    def draw_bots(self):
        for i, bot in enumerate(self.bots):
            port = 3000 + i + 1
            row = i + 1

            status_var = ctk.StringVar()
            resource_var = ctk.StringVar()

            status_label = ctk.CTkLabel(self.scroll_frame, textvariable=status_var, font=("Segoe UI", 12, "bold"))
            resource_label = ctk.CTkLabel(self.scroll_frame, textvariable=resource_var, font=("Segoe UI", 12))

            inv_btn = ctk.CTkButton(self.scroll_frame, text=f"{port}", width=60,
                                    command=lambda p=port: webbrowser.open(f"http://localhost:{p}"))
            run_btn = ctk.CTkButton(self.scroll_frame, text="▶", width=40,
                                    command=lambda b=bot: self.run_bot(b))
            close_btn = ctk.CTkButton(self.scroll_frame, text="✖", width=40,
                                      fg_color="red", hover_color="#a00",
                                      command=lambda b=bot: self.close_bot(b))
            focus_btn = ctk.CTkButton(self.scroll_frame, text="🔍", width=40,
                                      command=lambda b=bot: self.focus_bot(b))
            edit_btn = ctk.CTkButton(self.scroll_frame, text="✏", width=40,
                                     fg_color="#FFA726", command=lambda b=bot: self.edit_bot(b))

            ctk.CTkLabel(self.scroll_frame, text=bot).grid(row=row, column=0, padx=5, pady=4, sticky="ew")
            inv_btn.grid(row=row, column=1, padx=5, sticky="ew")
            status_label.grid(row=row, column=2, padx=5, sticky="ew")
            focus_btn.grid(row=row, column=3, padx=5, sticky="ew")
            run_btn.grid(row=row, column=4, padx=5, sticky="ew")
            close_btn.grid(row=row, column=5, padx=5, sticky="ew")
            edit_btn.grid(row=row, column=6, padx=5, sticky="ew")
            resource_label.grid(row=row, column=7, padx=5, sticky="ew")

            self.widgets.append({
                "name": bot,
                "status_var": status_var,
                "status_label": status_label,
                "run_btn": run_btn,
                "resource_var": resource_var
            })

    def update_status_loop(self):
        for bot in self.widgets:
            name = bot["name"]
            run_btn = bot["run_btn"]
            status_label = bot["status_label"]
            resource_var = bot["resource_var"]

            process = self.get_process_by_name(f"{name}.exe")

            if process:
                cpu = process.cpu_percent(interval=0.1)
                mem = process.memory_info().rss / (1024 * 1024)  # MB
                bot["status_var"].set("Online")
                status_label.configure(text_color="#43A047")
                run_btn.configure(fg_color="#66BB6A", hover_color="#558B2F")
                resource_var.set(f"CPU: {cpu:.1f}% | RAM: {mem:.1f}MB")
            else:
                bot["status_var"].set("Offline")
                status_label.configure(text_color="#E53935")
                run_btn.configure(fg_color="#FFCA28", hover_color="#FDD835")
                resource_var.set("")

        self.after(3000, self.update_status_loop)

    def get_process_by_name(self, name):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == name.lower():
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def run_bot(self, bot_name):
        exe_path = os.path.join(BOT_DIR, "node", f"{bot_name}.exe")
        js_path = os.path.join(BOT_DIR, f"{bot_name}.js")
        if os.path.exists(exe_path) and os.path.exists(js_path):
            subprocess.Popen([exe_path, js_path], shell=True)
        else:
            self.popup_message(f"Không tìm thấy {bot_name}.exe hoặc JS!", "red")

    def close_bot(self, bot_name):
        os.system(f"taskkill /f /im {bot_name}.exe")

    def focus_bot(self, bot_name):
        try:
            for win in gw.getWindowsWithTitle(bot_name):
                if bot_name in win.title:
                    time.sleep(0.1)
                    win.restore()
                    win.activate()
                    return
            self.popup_message(f"Không tìm thấy cửa sổ {bot_name}", "#FFA500")
        except Exception as e:
            self.popup_message(f"Lỗi: {str(e)}", "red")

    def edit_bot(self, bot):
        js_file = os.path.join(BOT_DIR, f"{bot}.js")
        if os.path.exists(js_file):
            subprocess.Popen(f'subl "{js_file}"', shell=True)
        else:
            self.popup_message("Không tìm thấy file để mở.", "red")

    def popup_message(self, text, color="red"):
        popup = ctk.CTkToplevel(self)
        popup.geometry("300x60+100+100")
        popup.overrideredirect(True)
        popup.configure(fg_color=color)
        label = ctk.CTkLabel(popup, text=text, text_color="white")
        label.pack(pady=15)
        popup.after(2000, popup.destroy)

if __name__ == "__main__":
    app = BotManager()
    app.mainloop()

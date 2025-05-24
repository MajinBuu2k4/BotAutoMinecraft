import os
import sys
import time
import win32gui
import win32con
import win32api
import pyautogui
import customtkinter as ctk
import pygetwindow as gw
from tkinter import ttk

class SendCommand:
    def __init__(self, selected_bot=None):
        self.root = ctk.CTk()
        self.root.title("Gửi Lệnh Cho Bot")
        self.root.geometry("400x300")  # Tăng chiều cao cửa sổ
        
        # Thiết lập theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        
        # Danh sách bot
        self.bots = [f"Vanguard{i:02}" for i in range(1, 31)]
        
        # Frame chính
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Label cho combobox
        self.label = ctk.CTkLabel(self.main_frame, text="Chọn Bot:", font=("Segoe UI", 14, "bold"))
        self.label.pack(pady=10)
        
        # Combobox để chọn bot
        self.bot_combobox = ctk.CTkComboBox(
            self.main_frame,
            values=self.bots,
            width=200,
            font=("Segoe UI", 12)
        )
        self.bot_combobox.pack(pady=10)
        
        # Nếu có bot được chọn, set giá trị cho combobox
        if selected_bot and selected_bot in self.bots:
            self.bot_combobox.set(selected_bot)
        else:
            self.bot_combobox.set(self.bots[0])
        
        # Frame cho nhập lệnh
        self.command_frame = ctk.CTkFrame(self.main_frame)
        self.command_frame.pack(pady=20, fill="x", padx=20)
        
        # Label cho ô nhập lệnh
        self.command_label = ctk.CTkLabel(
            self.command_frame,
            text="Nhập Lệnh:",
            font=("Segoe UI", 14, "bold")
        )
        self.command_label.pack(pady=(0, 5))
        
        # Entry để nhập lệnh với kích thước lớn hơn
        self.command_entry = ctk.CTkEntry(
            self.command_frame,
            placeholder_text="Nhập lệnh tại đây...",
            font=("Segoe UI", 13),
            height=35,
            width=300
        )
        self.command_entry.pack(fill="x", expand=True, pady=(0, 10))
        
        # Frame cho các nút
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(pady=20)
        
        # Nút Gửi Lệnh
        self.send_btn = ctk.CTkButton(
            self.button_frame,
            text="📝 Gửi Lệnh",
            command=self.send_command,
            width=150,  # Tăng kích thước nút
            height=32,
            font=("Segoe UI", 12)
        )
        self.send_btn.pack(side="left", padx=10)

        # Nút Hidden
        self.hidden_btn = ctk.CTkButton(
            self.button_frame,
            text="🔽 Hidden",
            command=self.hidden_bot,
            width=150,  # Tăng kích thước nút
            height=32,
            font=("Segoe UI", 12),
            fg_color="#E53935",  # Màu đỏ
            hover_color="#C62828"  # Màu đỏ đậm
        )
        self.hidden_btn.pack(side="left", padx=10)
        
        # Bind phím Enter cho entry
        self.command_entry.bind("<Return>", lambda e: self.send_command())
        
        # Focus vào ô nhập lệnh
        self.command_entry.focus()

    def focus_bot(self):
        """Focus vào cửa sổ bot được chọn"""
        bot_name = self.bot_combobox.get()
        try:
            windows = gw.getWindowsWithTitle(bot_name)
            for win in windows:
                if bot_name in win.title:
                    time.sleep(0.1)
                    win.restore()  # Phục hồi cửa sổ nếu đang thu nhỏ
                    win.moveTo(0, 0)  # Di chuyển cửa sổ đến vị trí (0,0)
                    win.activate()  # Focus vào cửa sổ
                    return
            self.show_message(f"Không tìm thấy cửa sổ {bot_name}", "warning")
        except Exception as e:
            self.show_message(f"Lỗi: {str(e)}", "error")

    def send_command(self):
        """Gửi lệnh đến bot được chọn"""
        bot_name = self.bot_combobox.get()
        command = self.command_entry.get()
        
        if not command:
            return
            
        try:
            windows = gw.getWindowsWithTitle(bot_name)
            for win in windows:
                if bot_name in win.title:
                    win.restore()
                    win.moveTo(0, 0)  # Di chuyển cửa sổ đến vị trí (0,0)
                    win.activate()
                    time.sleep(0.5)
                    pyautogui.write(command)
                    pyautogui.press('enter')
                    self.command_entry.delete(0, "end")
                    return
            self.show_message(f"Không tìm thấy cửa sổ {bot_name}", "warning")
        except Exception as e:
            self.show_message(f"Lỗi: {str(e)}", "error")

    def hidden_bot(self):
        """Minimize cửa sổ bot và đóng tool"""
        bot_name = self.bot_combobox.get()
        try:
            # Tìm và minimize cửa sổ bot
            windows = gw.getWindowsWithTitle(bot_name)
            for win in windows:
                if bot_name in win.title:
                    win.minimize()  # Thu nhỏ cửa sổ bot
                    break
            
            # Đóng tool sau 0.5 giây
            self.root.after(500, self.root.destroy)
            
        except Exception as e:
            self.show_message(f"Lỗi: {str(e)}", "error")

    def show_message(self, text, msg_type="info"):
        """Hiển thị thông báo popup"""
        colors = {
            "info": "#2196F3",
            "warning": "#FFA726",
            "error": "#E53935"
        }
        
        popup = ctk.CTkToplevel(self.root)
        popup.geometry("300x60")
        popup.overrideredirect(True)
        
        # Đặt vị trí popup ở giữa cửa sổ chính
        x = self.root.winfo_x() + (self.root.winfo_width() - 300) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 60) // 2
        popup.geometry(f"+{x}+{y}")
        
        popup.configure(fg_color=colors.get(msg_type, colors["info"]))
        
        label = ctk.CTkLabel(
            popup,
            text=text,
            text_color="white",
            font=("Segoe UI", 12)
        )
        label.pack(pady=15)
        
        popup.after(2000, popup.destroy)

    def run(self):
        """Chạy ứng dụng"""
        self.root.mainloop()

if __name__ == "__main__":
    # Kiểm tra xem có tham số bot_name được truyền vào không
    selected_bot = sys.argv[1] if len(sys.argv) > 1 else None
    app = SendCommand(selected_bot)
    app.run() 
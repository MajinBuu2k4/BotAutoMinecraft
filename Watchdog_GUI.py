import customtkinter as ctk
import psutil
import subprocess
import os
import webbrowser
import pygetwindow as gw
import time
import threading
import pystray
from PIL import Image, ImageDraw
import sys
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
import queue
import logging
import json

# ==== Cài đặt ====
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

BOT_DIR = r"C:\Users\Administrator\Desktop\BotAutoMinecraft"
BOTS_DIR = os.path.join(BOT_DIR, "bots")
SHORTCUT_DIR = os.path.join(BOT_DIR, "shortcut")
LOG_FILE = os.path.join(BOT_DIR, "watchdog", "watchdog-output.log")
PROGRESS_LOG_FILE = os.path.join(BOT_DIR, "watchdog", "watchdog-progress-output.log")
PS_SCRIPT = os.path.join(BOT_DIR, "watchdog", "watchdog.ps1")
PROGRESS_PS_SCRIPT = os.path.join(BOT_DIR, "watchdog", "watchdog_progress.ps1")
ICON_PATH = os.path.join(BOT_DIR, "icon.ico")
ERROR_LOG = os.path.join(BOT_DIR, "gui_error.log")
SERVICE_DIR = os.path.join(BOT_DIR, "service")
RUNTIME_DATA_FILE = os.path.join(SERVICE_DIR, "runtime_data.json")
CONFIG_FILE = os.path.join(BOT_DIR, "window_config.json")  # File lưu cấu hình cửa sổ

# Màu sắc cho logs
LOG_COLORS = {
    "success": "#4CAF50",  # Xanh lá đậm
    "error": "#F44336",    # Đỏ tươi
    "warning": "#FFA726",  # Cam
    "info": "#90CAF9",     # Xanh dương nhạt
    "title": "#E0E0E0",    # Xám sáng cho tiêu đề
    "background": "#2B2B2B" # Nền tối
}

# Màu sắc cho trạng thái
STATUS_COLORS = {
    "online": "#43A047",    # Xanh lá
    "offline": "#E53935",   # Đỏ
    "starting": "#FFA726",  # Cam
    "text_online": "white", # Màu chữ cho online
    "text_offline": "white" # Màu chữ cho offline
}

# Thêm logging cho errors
logging.basicConfig(
    filename=ERROR_LOG,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Tooltips và messages
TOOLTIPS = {
    "run": "Khởi động bot",
    "close": "Tắt bot",
    "focus": "Tìm và focus cửa sổ bot",
    "edit": "Mở file script để chỉnh sửa",
    "inventory": "Mở trang web xem inventory",
    "pause": "Tạm dừng/tiếp tục kiểm tra",
    "close_all": "Đóng tất cả bot"
}

class WindowConfig:
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self):
        """Đọc cấu hình từ file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Error loading window config: {str(e)}")
            return {}
    
    def save_config(self):
        """Lưu cấu hình vào file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving window config: {str(e)}")
    
    def save_window_state(self, window_name, geometry):
        """Lưu trạng thái của cửa sổ"""
        self.config[window_name] = geometry
        self.save_config()
    
    def get_window_state(self, window_name, default=None):
        """Lấy trạng thái của cửa sổ"""
        return self.config.get(window_name, default)

# Tạo đối tượng quản lý cấu hình toàn cục
window_config = WindowConfig()

class RuntimeStatsWindow(ctk.CTkToplevel):
    def __init__(self, parent, runtime_data):
        super().__init__(parent)
        self.title("⏱ Thời gian chạy")
        
        # Khôi phục vị trí và kích thước từ cấu hình
        saved_geometry = window_config.get_window_state("runtime_stats")
        if saved_geometry:
            self.geometry(saved_geometry)
        else:
            # Cấu hình mặc định nếu chưa có
            self.geometry("600x800")
            # Căn giữa cửa sổ so với cửa sổ chính
            self.center_window(parent)
        
        # Đặt cửa sổ luôn hiển thị trên cửa sổ chính nhưng cho phép tương tác với cửa sổ chính
        self.transient(parent)  # Giữ lại để cửa sổ luôn ở trên cửa sổ chính
        # Bỏ grab_set() để cho phép tương tác với cửa sổ chính
        
        # Frame chứa danh sách
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        headers = ["Bot", "Thời gian chạy"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                self.scroll_frame, 
                text=header,
                font=("Segoe UI", 14, "bold")
            )
            label.grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Sắp xếp bot theo thời gian chạy giảm dần
        sorted_bots = sorted(runtime_data.items(), key=lambda x: x[1], reverse=True)
        
        # Hiển thị thông tin từng bot
        for i, (bot, runtime) in enumerate(sorted_bots, start=1):
            # Tên bot
            bot_label = ctk.CTkLabel(
                self.scroll_frame,
                text=bot,
                font=("Segoe UI", 12)
            )
            bot_label.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            
            # Thời gian chạy
            time_label = ctk.CTkLabel(
                self.scroll_frame,
                text=self.format_runtime(runtime),
                font=("Segoe UI", 12)
            )
            time_label.grid(row=i, column=1, padx=10, pady=5, sticky="w")
            
            # Thêm màu nền xen kẽ cho dễ đọc
            if i % 2 == 0:
                bot_label.configure(fg_color=("gray85", "gray20"))
                time_label.configure(fg_color=("gray85", "gray20"))
        
        # Bind các sự kiện
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Configure>", self.on_window_configure)
        
        # Focus vào cửa sổ này
        self.focus_force()
    
    def center_window(self, parent):
        """Căn giữa cửa sổ so với cửa sổ chính"""
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        width = 600
        height = 800
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        # Đảm bảo cửa sổ không vượt quá màn hình
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))
        
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_window_configure(self, event=None):
        """Xử lý sự kiện khi cửa sổ thay đổi kích thước hoặc vị trí"""
        if event is not None and event.widget == self:
            # Đợi một chút để tránh lưu quá nhiều
            if hasattr(self, '_save_timer'):
                self.after_cancel(self._save_timer)
            self._save_timer = self.after(500, self.save_window_state)
    
    def save_window_state(self):
        """Lưu trạng thái cửa sổ"""
        window_config.save_window_state("runtime_stats", self.geometry())

    def format_runtime(self, seconds):
        """Định dạng thời gian chạy"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days} ngày")
        if hours > 0 or days > 0:
            parts.append(f"{hours} giờ")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes} phút")
        parts.append(f"{secs} giây")
        
        return " ".join(parts)

class LogWindow(ctk.CTkToplevel):
    def __init__(self, parent, title, log_file, log_type="watchdog"):
        super().__init__(parent)
        self.title(title)
        self.log_file = log_file
        self.log_type = log_type
        
        # Thiết lập màu cho thanh title
        if self.log_type == "watchdog":
            title_color = "#9C27B0"  # Màu tím cho Watchdog Log
        else:
            title_color = "#009688"  # Màu xanh lá cho Progress Log
        
        # Thay đổi màu thanh title (Windows only)
        if sys.platform.startswith('win'):
            self.after(10, lambda: self.set_title_bar_color(title_color))
        
        # Khôi phục vị trí và kích thước từ cấu hình
        saved_geometry = window_config.get_window_state(f"log_{log_type}")
        if saved_geometry:
            self.geometry(saved_geometry)
        else:
            # Cấu hình mặc định nếu chưa có
            self.geometry("800x600")
            # Căn giữa cửa sổ so với cửa sổ chính
            self.center_window(parent)
        
        # Đặt cửa sổ luôn hiển thị trên cửa sổ chính nhưng cho phép tương tác với cửa sổ chính
        self.transient(parent)  # Giữ lại để cửa sổ log luôn ở trên cửa sổ chính
        # Bỏ grab_set() để cho phép tương tác với cửa sổ chính
        
        # Tạo textbox cho log
        self.log_text = ctk.CTkTextbox(
            self,
            wrap="word",
            font=("Consolas", 12),
            fg_color=LOG_COLORS["background"],
            text_color=LOG_COLORS["info"]
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Thêm nút đóng
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        refresh_button = ctk.CTkButton(
            self.button_frame,
            text="🔄 Làm mới",
            command=self.refresh_log,
            width=100,
            fg_color=title_color,  # Sử dụng cùng màu với thanh title
            hover_color=self.adjust_color_brightness(title_color, -20)  # Tối hơn một chút khi hover
        )
        refresh_button.pack(side="left", padx=5)

        close_button = ctk.CTkButton(
            self.button_frame,
            text="Đóng",
            command=self.destroy,
            width=100
        )
        close_button.pack(side="right", padx=5)
        
        # Bind các sự kiện
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Configure>", self.on_window_configure)
        
        # Focus vào cửa sổ này
        self.focus_force()
        
        # Cập nhật log ban đầu
        self.refresh_log()
        
        # Tự động cập nhật log mỗi giây
        self.after(1000, self.auto_refresh)
    
    def set_title_bar_color(self, color):
        """Thay đổi màu thanh title (Windows only)"""
        try:
            import ctypes
            from ctypes import windll, byref, sizeof, c_int
            
            DWMWA_CAPTION_COLOR = 35
            
            # Chuyển đổi màu hex sang RGB
            color = color.lstrip('#')
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            # Chuyển RGB thành BGRA (Windows yêu cầu định dạng này)
            bgra = rgb[2] | (rgb[1] << 8) | (rgb[0] << 16) | (0xFF << 24)
            
            hwnd = windll.user32.GetParent(self.winfo_id())
            value = c_int(bgra)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_CAPTION_COLOR,
                byref(value),
                sizeof(value)
            )
        except Exception as e:
            logging.error(f"Error setting title bar color: {str(e)}")
    
    def adjust_color_brightness(self, color, factor):
        """Điều chỉnh độ sáng của màu"""
        # Chuyển hex sang RGB
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        
        # Điều chỉnh độ sáng
        new_rgb = tuple(max(0, min(255, c + factor)) for c in rgb)
        
        # Chuyển lại thành hex
        return '#{:02x}{:02x}{:02x}'.format(*new_rgb)

    def center_window(self, parent):
        """Căn giữa cửa sổ so với cửa sổ chính"""
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        width = 800
        height = 600
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        # Đảm bảo cửa sổ không vượt quá màn hình
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))
        
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_window_configure(self, event=None):
        """Xử lý sự kiện khi cửa sổ thay đổi kích thước hoặc vị trí"""
        if event is not None and event.widget == self:
            # Đợi một chút để tránh lưu quá nhiều
            if hasattr(self, '_save_timer'):
                self.after_cancel(self._save_timer)
            self._save_timer = self.after(500, self.save_window_state)
    
    def save_window_state(self):
        """Lưu trạng thái cửa sổ"""
        window_config.save_window_state(f"log_{self.log_type}", self.geometry())

    def auto_refresh(self):
        """Tự động cập nhật log nếu cửa sổ còn mở"""
        if self.winfo_exists():
            self.refresh_log()
            self.after(1000, self.auto_refresh)
    
    def refresh_log(self):
        """Cập nhật nội dung log"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, "r", encoding="utf-8") as f:
                    content = f.readlines()
                
                # Lưu vị trí cuộn hiện tại
                current_scroll = self.log_text.yview()[0]
                
                self.log_text.configure(state="normal")
                self.log_text.delete("1.0", "end")
                
                for line in content:
                    if self.log_type == "watchdog":
                        if "OK" in line:
                            self.log_text.insert("end", line, "success")
                        elif "Error" in line or "Exception" in line:
                            self.log_text.insert("end", line, "error")
                        elif "restart" in line.lower():
                            self.log_text.insert("end", line, "warning")
                        else:
                            self.log_text.insert("end", line, "info")
                    else:  # progress log
                        if "✅" in line:
                            self.log_text.insert("end", line, "success")
                        elif "❌" in line:
                            self.log_text.insert("end", line, "error")
                        elif "🛠" in line or "🔄" in line:
                            self.log_text.insert("end", line, "warning")
                        else:
                            self.log_text.insert("end", line, "info")
                
                # Cấu hình màu cho các tag
                self.log_text.tag_config("success", foreground=LOG_COLORS["success"])
                self.log_text.tag_config("error", foreground=LOG_COLORS["error"])
                self.log_text.tag_config("warning", foreground=LOG_COLORS["warning"])
                self.log_text.tag_config("info", foreground=LOG_COLORS["info"])
                
                # Giữ nguyên vị trí cuộn nếu không ở cuối
                if current_scroll > 0.9:
                    self.log_text.see("end")
                else:
                    self.log_text.yview_moveto(current_scroll)
                
                self.log_text.configure(state="disabled")
                
        except Exception as e:
            logging.error(f"Error refreshing log: {str(e)}")

class BotManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BotAutoMinecraft Manager")
        self.iconbitmap(ICON_PATH)
        
        # Thêm lock cho việc khởi động bot
        self.bot_locks = {}
        self.last_start_times = {}
        
        # Khôi phục vị trí và kích thước từ cấu hình
        saved_geometry = window_config.get_window_state("main_window")
        if saved_geometry:
            self.geometry(saved_geometry)
        else:
            self.geometry("1000x650")
        self.center_window()
        
        self.minsize(800, 500)

        self.bots = [f"Vanguard{i:02}" for i in range(1, 31)]
        self.widgets = []
        self.process_cache = {}  # Cache cho processes
        self.cache_timestamp = 0
        self.cache_duration = 2  # Cache 2 giây
        
        # Thêm biến kiểm soát trạng thái kiểm tra
        self.is_checking_paused = False
        
        # Thread pool để xử lý các tác vụ nặng
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.update_queue = queue.Queue()
        
        # Biến để kiểm soát việc cập nhật
        self.is_updating = False
        self.update_counter = 0
        
        # Biến lưu trữ cửa sổ log
        self.watchdog_window = None
        self.progress_window = None
        
        # Đường dẫn đến icon đỏ
        self.red_icon_path = os.path.join(BOT_DIR, "icons", "shiba_do.ico")
        
        # Khởi tạo runtime data
        self.runtime_data = self.load_runtime_data()
        
        self.setup_gui()
        self.draw_bots()
        self.start_update_threads()
        
        # Cập nhật logs và runtime
        self.after(1000, self.update_runtime_display)  # Cập nhật hiển thị runtime mỗi giây
        self.after(1000, self.check_service_status)  # Kiểm tra trạng thái service

        # Kích hoạt ngay lập tức các chức năng kiểm tra khi khởi động
        self.run_watchdog()  # Chạy watchdog ngay lập tức
        self.auto_refresh_progress()  # Bắt đầu kiểm tra progress
        self.auto_refresh_watchdog()  # Bắt đầu kiểm tra watchdog

        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.create_tray_icon()
        
        self.bind("<Configure>", self.on_window_configure)

    def center_window(self):
        """Căn giữa cửa sổ trên màn hình"""
        self.update_idletasks()  # Cập nhật kích thước thực
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_gui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.scroll_frame.pack(fill="both", expand=True)

        # Cấu hình chiều rộng cột
        column_widths = {
            0: (1, 100),  # Bot Name
            1: (1, 80),   # Inventory
            2: (0, 100),  # Status - cố định
            3: (1, 60),   # Focus
            4: (1, 60),   # Run
            5: (1, 60),   # Close
            6: (1, 60),   # Edit
            7: (0, 350)   # Resource - cố định
        }
        
        for col, (weight, minsize) in column_widths.items():
            self.scroll_frame.grid_columnconfigure(col, weight=weight, minsize=minsize)

        headers = ["Bot Name", "Inventory", "Status", "Focus", "Run", "Close", "Edit", "Resource"]
        for i, header in enumerate(headers):
            if i in [2, 7]:  # Status và Resource có chiều rộng cố định
                ctk.CTkLabel(
                    self.scroll_frame,
                    text=header,
                    font=("Segoe UI", 14, "bold"),
                    width=column_widths[i][1]  # Sử dụng chiều rộng từ cấu hình
                ).grid(row=0, column=i, padx=10, pady=10, sticky="w")
            else:
                ctk.CTkLabel(
                    self.scroll_frame,
                    text=header,
                    font=("Segoe UI", 14, "bold")
                ).grid(row=0, column=i, padx=10, pady=10, sticky="ew")

        # Frame chứa các nút điều khiển
        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.pack(pady=5)

        self.run_btn = ctk.CTkButton(self.btn_frame, text="▶ Chạy Watchdog", command=self.run_watchdog)
        self.run_btn.pack(side="left", padx=10)

        # Nút mở cửa sổ Watchdog Log
        self.watchdog_log_btn = ctk.CTkButton(
            self.btn_frame,
            text="📋 Watchdog Log",
            command=self.show_watchdog_log,
            fg_color="#9C27B0",
            hover_color="#7B1FA2"
        )
        self.watchdog_log_btn.pack(side="left", padx=10)

        # Nút mở cửa sổ Progress Log
        self.progress_log_btn = ctk.CTkButton(
            self.btn_frame,
            text="📊 Progress Log",
            command=self.show_progress_log,
            fg_color="#009688",
            hover_color="#00796B"
        )
        self.progress_log_btn.pack(side="left", padx=10)

        # Nút hiển thị thời gian chạy
        self.runtime_btn = ctk.CTkButton(
            self.btn_frame, 
            text="⏱ Thời gian chạy", 
            command=self.show_runtime_stats,
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.runtime_btn.pack(side="left", padx=10)

        # Nút tạm dừng kiểm tra
        self.pause_btn = ctk.CTkButton(
            self.btn_frame, 
            text="⏸ Tạm dừng kiểm tra", 
            command=self.pause_checking,
            fg_color="#FFA726",
            hover_color="#FB8C00"
        )
        self.pause_btn.pack(side="left", padx=10)
        self.bind_tooltip(self.pause_btn, TOOLTIPS["pause"])

        # Label hiển thị trạng thái service
        self.service_status_label = ctk.CTkLabel(
            self.btn_frame,
            text="🔄 Đang kiểm tra service...",
            font=("Segoe UI", 12)
        )
        self.service_status_label.pack(side="left", padx=10)

        # Nút đóng tất cả bot
        self.close_all_btn = ctk.CTkButton(
            self.btn_frame, 
            text="✖ Đóng tất cả", 
            command=self.close_all_bots,
            fg_color="#E53935",
            hover_color="#C62828"
        )
        self.close_all_btn.pack(side="right", padx=10)
        self.bind_tooltip(self.close_all_btn, TOOLTIPS["close_all"])

    def draw_bots(self):
        for i, bot in enumerate(self.bots):
            port = 3000 + i + 1
            row = i + 1

            status_var = ctk.StringVar(value="Offline")  # Giá trị mặc định
            resource_var = ctk.StringVar()

            # Status label với chiều rộng cố định và background color
            status_label = ctk.CTkLabel(
                self.scroll_frame,
                textvariable=status_var,
                font=("Segoe UI", 12, "bold"),
                width=100,
                anchor="center",
                fg_color=STATUS_COLORS["offline"],  # Background color mặc định
                text_color=STATUS_COLORS["text_offline"],  # Màu chữ mặc định
                corner_radius=6  # Bo góc cho đẹp
            )

            resource_label = ctk.CTkLabel(
                self.scroll_frame,
                textvariable=resource_var,
                font=("Segoe UI", 12),
                width=350,
                anchor="w"
            )

            # Thêm tooltips cho các nút
            inv_btn = self.create_button(self.scroll_frame, f"{port}", 60, 
                                       lambda p=port: webbrowser.open(f"http://localhost:{p}"),
                                       tooltip=TOOLTIPS["inventory"])
            
            run_btn = self.create_button(self.scroll_frame, "▶", 40,
                                       lambda b=bot: self.run_bot_async(b),
                                       tooltip=TOOLTIPS["run"])
            
            close_btn = self.create_button(self.scroll_frame, "✖", 40,
                                         lambda b=bot: self.close_bot_async(b),
                                         fg_color="red", hover_color="#a00",
                                         tooltip=TOOLTIPS["close"])
            
            focus_btn = self.create_button(self.scroll_frame, "🔍", 40,
                                         lambda b=bot: self.focus_bot_async(b),
                                         tooltip=TOOLTIPS["focus"])
            
            edit_btn = self.create_button(self.scroll_frame, "✏", 40,
                                        lambda b=bot: self.edit_bot(b),
                                        fg_color="#FFA726",
                                        tooltip=TOOLTIPS["edit"])

            ctk.CTkLabel(self.scroll_frame, text=bot).grid(row=row, column=0, padx=5, pady=4, sticky="ew")
            inv_btn.grid(row=row, column=1, padx=5, sticky="ew")
            status_label.grid(row=row, column=2, padx=5, pady=4, sticky="ew")  # Sử dụng sticky="ew" để căn giữa
            focus_btn.grid(row=row, column=3, padx=5, sticky="ew")
            run_btn.grid(row=row, column=4, padx=5, sticky="ew")
            close_btn.grid(row=row, column=5, padx=5, sticky="ew")
            edit_btn.grid(row=row, column=6, padx=5, sticky="ew")
            resource_label.grid(row=row, column=7, padx=5, pady=4, sticky="w")

            self.widgets.append({
                "name": bot,
                "status_var": status_var,
                "status_label": status_label,
                "run_btn": run_btn,
                "resource_var": resource_var
            })

    def create_button(self, parent, text, width, command, tooltip="", **kwargs):
        """Helper function to create buttons with tooltips"""
        btn = ctk.CTkButton(parent, text=text, width=width, command=command, **kwargs)
        
        if tooltip:
            self.bind_tooltip(btn, tooltip)
        
        return btn

    def bind_tooltip(self, widget, text):
        """Create tooltip for a widget"""
        tooltip = None
        
        def enter(event):
            nonlocal tooltip
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20

            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")

            label = tk.Label(tooltip, text=text, justify='left',
                            background="#2B2B2B", foreground="white",
                            relief='solid', borderwidth=1,
                            font=("Segoe UI", "8", "normal"))
            label.pack()

        def leave(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def get_all_processes_cached(self):
        """Lấy tất cả processes với cache để giảm lag"""
        current_time = time.time()
        
        if current_time - self.cache_timestamp > self.cache_duration:
            try:
                # Chỉ lấy các thuộc tính cần thiết
                processes = {}
                for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                    try:
                        name = proc.info['name'].lower()
                        if name.startswith('vanguard') and name.endswith('.exe'):
                            processes[name] = proc
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                
                self.process_cache = processes
                self.cache_timestamp = current_time
            except Exception:
                pass
        
        return self.process_cache

    def get_process_info(self, bot_name):
        """Lấy thông tin process với cache theo thời gian"""
        processes = self.get_all_processes_cached()
        process_name = f"{bot_name.lower()}.exe"
        
        if process_name in processes:
            try:
                proc = processes[process_name]
                if proc.is_running():
                    create_time = proc.create_time()
                    runtime = time.time() - create_time
                    
                    # Cache CPU/RAM trong 5 giây
                    current_time = time.time()
                    if not hasattr(proc, '_last_resource_check') or \
                       current_time - proc._last_resource_check > 5:
                        try:
                            cpu = proc.cpu_percent()
                            mem = proc.memory_info().rss / (1024 * 1024)
                            proc._cached_cpu = cpu
                            proc._cached_mem = mem
                            proc._last_resource_check = current_time
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            cpu = 0
                            mem = 0
                    else:
                        cpu = getattr(proc, '_cached_cpu', 0)
                        mem = getattr(proc, '_cached_mem', 0)
                    
                    return {
                        'online': True,
                        'runtime': runtime,
                        'cpu': cpu,
                        'memory': mem,
                        'create_time': create_time
                    }
            except Exception as e:
                logging.error(f"Error getting process info for {bot_name}: {str(e)}")
                if process_name in self.process_cache:
                    del self.process_cache[process_name]
        
        return {'online': False}

    def update_bot_status_background(self):
        """Cập nhật trạng thái bot trong background thread"""
        while True:
            try:
                if not self.is_updating:
                    self.is_updating = True
                    updates = []
                    
                    # Đọc runtime data mới nhất từ service
                    self.runtime_data = self.load_runtime_data()
                    
                    for bot in self.widgets:
                        name = bot["name"]
                        info = self.get_process_info(name)
                        
                        # Lấy thời gian chạy từ service
                        info['total_runtime'] = self.runtime_data.get(name, 0)
                        updates.append((bot, info))
                    
                    # Đưa updates vào queue để main thread xử lý
                    self.update_queue.put(updates)
                    self.is_updating = False
                    
                time.sleep(3)  # Cập nhật mỗi 3 giây
            except Exception:
                self.is_updating = False
                time.sleep(5)

    def process_updates_from_queue(self):
        """Xử lý updates từ queue trong main thread"""
        try:
            while not self.update_queue.empty():
                updates = self.update_queue.get_nowait()
                
                for bot_widget, info in updates:
                    name = bot_widget["name"]
                    
                    if info['online']:
                        runtime_str = self.format_runtime(info['runtime'])
                        
                        # Cập nhật status và màu sắc
                        bot_widget["status_var"].set("Online")
                        bot_widget["status_label"].configure(
                            fg_color=STATUS_COLORS["online"],
                            text_color=STATUS_COLORS["text_online"]
                        )
                        bot_widget["run_btn"].configure(fg_color="#66BB6A", hover_color="#558B2F")
                        
                        # Cập nhật thông tin tài nguyên
                        bot_widget["resource_var"].set(
                            f"CPU: {info['cpu']:.1f}% | RAM: {info['memory']:.1f}MB | Runtime: {runtime_str}"
                        )
                    else:
                        total_runtime_str = self.format_total_runtime(info['total_runtime'])
                        
                        # Cập nhật status và màu sắc
                        bot_widget["status_var"].set("Offline")
                        bot_widget["status_label"].configure(
                            fg_color=STATUS_COLORS["offline"],
                            text_color=STATUS_COLORS["text_offline"]
                        )
                        bot_widget["run_btn"].configure(fg_color="#FFCA28", hover_color="#FDD835")
                        
                        # Cập nhật thông tin tài nguyên
                        bot_widget["resource_var"].set(f"CPU: 0.0% | RAM: 0.0MB | Runtime: --")
                
                self.update_counter += 1
                
        except queue.Empty:
            pass
        except Exception as e:
            logging.error(f"Error in process_updates_from_queue: {str(e)}")
        
        # Lên lịch cho lần kiểm tra tiếp theo
        self.after(500, self.process_updates_from_queue)

    def start_update_threads(self):
        """Khởi động các thread cập nhật"""
        # Thread cập nhật trạng thái bot
        update_thread = threading.Thread(target=self.update_bot_status_background, daemon=True)
        update_thread.start()
        
        # Bắt đầu xử lý queue updates
        self.after(1000, self.process_updates_from_queue)

    def format_runtime(self, seconds):
        """Chuyển đổi seconds thành định dạng dễ đọc"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def run_bot_async(self, bot_name):
        """Chạy bot trong thread riêng"""
        self.executor.submit(self.run_bot, bot_name)

    def run_bot(self, bot_name):
        try:
            # Kiểm tra lock và thời gian khởi động gần nhất
            current_time = time.time()
            if bot_name in self.last_start_times:
                time_since_last_start = current_time - self.last_start_times[bot_name]
                if time_since_last_start < 30:  # Không cho phép khởi động lại trong vòng 30 giây
                    logging.warning(f"Bỏ qua yêu cầu khởi động {bot_name}: mới khởi động cách đây {int(time_since_last_start)} giây")
                    return
            
            # Kiểm tra và thiết lập lock
            if bot_name in self.bot_locks and self.bot_locks[bot_name]:
                logging.warning(f"Bỏ qua yêu cầu khởi động {bot_name}: đang trong quá trình khởi động")
                return
                
            self.bot_locks[bot_name] = True
            logging.info(f"=== Bắt đầu kiểm tra khởi động {bot_name} ===")
            
            try:
                # Kiểm tra process
                processes = self.get_all_processes_cached()
                process_name = f"{bot_name.lower()}.exe"
                
                if process_name in processes:
                    try:
                        proc = processes[process_name]
                        if proc.is_running():
                            msg = f"{bot_name} đã đang chạy (PID: {proc.pid})!"
                            logging.info(msg)
                            self.after(0, lambda: self.popup_message(msg, "#FFA726"))
                            return
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        logging.warning(f"Lỗi kiểm tra process {bot_name}: {str(e)}")
                
                # Kiểm tra cửa sổ
                windows = gw.getWindowsWithTitle(bot_name)
                if windows:
                    msg = f"{bot_name} đã có {len(windows)} cửa sổ đang chạy!"
                    logging.warning(msg)
                    self.after(0, lambda: self.popup_message(msg, "#FFA726"))
                    return
                
                # Kiểm tra shortcut
                shortcut_path = os.path.join(SHORTCUT_DIR, f"{bot_name}.lnk")
                if not os.path.exists(shortcut_path):
                    msg = f"Không tìm thấy shortcut {bot_name}.lnk!"
                    logging.error(msg)
                    self.after(0, lambda: self.popup_message(msg, "red"))
                    return
                
                logging.info(f"Chuẩn bị khởi động {bot_name} từ shortcut: {shortcut_path}")
                
                # Khởi động bot
                process = subprocess.Popen(
                    ["cmd", "/c", "start", "", shortcut_path],
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Cập nhật thời gian khởi động gần nhất
                self.last_start_times[bot_name] = current_time
                
                # Đợi và kiểm tra kết quả
                time.sleep(5)  # Đợi lâu hơn để đảm bảo process đã khởi động
                
                if process.poll() is None:
                    msg = f"Đã khởi động {bot_name} thành công"
                    logging.info(msg)
                    self.after(0, lambda: self.popup_message(msg, "#43A047"))
                else:
                    stdout, stderr = process.communicate()
                    error_msg = f"Bot {bot_name} khởi động không thành công. Exit code: {process.returncode}"
                    if stdout:
                        error_msg += f"\nOutput: {stdout.decode('utf-8', errors='ignore')}"
                    if stderr:
                        error_msg += f"\nError: {stderr.decode('utf-8', errors='ignore')}"
                    logging.error(error_msg)
                    self.after(0, lambda: self.popup_message(error_msg, "red"))
                
            finally:
                # Giải phóng lock
                self.bot_locks[bot_name] = False
                
        except Exception as e:
            error_msg = f"Lỗi không xác định khi khởi động {bot_name}: {str(e)}"
            logging.error(error_msg)
            self.after(0, lambda: self.popup_message(error_msg, "red"))
            self.bot_locks[bot_name] = False  # Đảm bảo giải phóng lock trong trường hợp lỗi
        
        finally:
            logging.info(f"=== Kết thúc quá trình khởi động {bot_name} ===\n")

    def close_bot_async(self, bot_name):
        """Đóng bot trong thread riêng"""
        self.executor.submit(self.close_bot, bot_name)

    def close_bot(self, bot_name):
        try:
            subprocess.run(f"taskkill /f /im {bot_name}.exe", shell=True, capture_output=True)
            # Xóa khỏi cache ngay lập tức
            process_name = f"{bot_name.lower()}.exe"
            if process_name in self.process_cache:
                del self.process_cache[process_name]
        except Exception as e:
            self.after(0, lambda: self.popup_message(f"Lỗi đóng {bot_name}: {str(e)}", "red"))

    def focus_bot_async(self, bot_name):
        """Focus bot trong thread riêng"""
        self.executor.submit(self.focus_bot, bot_name)

    def focus_bot(self, bot_name):
        try:
            # Focus vào cửa sổ bot
            windows = gw.getWindowsWithTitle(bot_name)
            bot_window = None
            for win in windows:
                if bot_name in win.title:
                    bot_window = win
                    time.sleep(0.1)
                    win.restore()
                    win.moveTo(0, 0)  # Di chuyển bot về vị trí 0,0
                    win.activate()
                    break
            
            if not bot_window:
                self.after(0, lambda: self.popup_message(f"Không tìm thấy cửa sổ {bot_name}", "#FFA500"))
                return

            # Lấy kích thước cửa sổ bot
            bot_width = bot_window.width
            
            # Mở tool send_command
            send_command_process = subprocess.Popen(
                [sys.executable, os.path.join("tool_quan_ly", "send_command.py"), bot_name],
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            # Đợi một chút để cửa sổ send_command xuất hiện
            time.sleep(1)
            
            # Tìm và di chuyển cửa sổ send_command
            send_command_windows = gw.getWindowsWithTitle("Gửi Lệnh Cho Bot")
            for win in send_command_windows:
                win.moveTo(bot_width, 0)  # Di chuyển sang phải của cửa sổ bot
                break

        except Exception as e:
            self.after(0, lambda: self.popup_message(f"Lỗi: {str(e)}", "red"))

    def edit_bot(self, bot):
        js_file = os.path.join(BOTS_DIR, f"{bot}.js")
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

    def run_watchdog(self):
        def task():
            try:
                if os.path.exists(LOG_FILE):
                    os.remove(LOG_FILE)
                
                # Chạy PowerShell script ẩn
                if sys.platform == "win32":
                    # Cách chạy cho Windows
                    subprocess.Popen(
                        ["powershell.exe", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-NoProfile", "-File", PS_SCRIPT],
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                else:
                    # Cách chạy cho các hệ điều hành khác
                    subprocess.Popen(
                        ["powershell", "-File", PS_SCRIPT],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
            except Exception as e:
                self.after(0, lambda: self.append_to_log(f"Lỗi: {e}", is_error=True))
            finally:
                self.after(0, self.refresh_log)

        self.executor.submit(task)

    def show_watchdog_log(self):
        """Hiển thị cửa sổ Watchdog Log"""
        if self.watchdog_window is None or not self.watchdog_window.winfo_exists():
            self.watchdog_window = LogWindow(
                self,
                "📋 Watchdog Log",
                LOG_FILE,
                "watchdog"
            )
        else:
            self.watchdog_window.focus()

    def show_progress_log(self):
        """Hiển thị cửa sổ Progress Log"""
        if self.progress_window is None or not self.progress_window.winfo_exists():
            self.progress_window = LogWindow(
                self,
                "📊 Progress Log",
                PROGRESS_LOG_FILE,
                "progress"
            )
        else:
            self.progress_window.focus()

    def show_runtime_stats(self):
        """Hiển thị cửa sổ thống kê thời gian chạy"""
        runtime_data = self.load_runtime_data()
        stats_window = RuntimeStatsWindow(self, runtime_data)
        stats_window.focus()

    def on_window_configure(self, event=None):
        """Xử lý sự kiện khi cửa sổ thay đổi kích thước hoặc vị trí"""
        if event is not None and event.widget == self:
            # Đợi một chút để tránh lưu quá nhiều
            if hasattr(self, '_save_timer'):
                self.after_cancel(self._save_timer)
            self._save_timer = self.after(500, self.save_window_state)
    
    def save_window_state(self):
        """Lưu trạng thái cửa sổ"""
        window_config.save_window_state("main_window", self.geometry())

    def hide_to_tray(self):
        self.withdraw()

    def create_tray_icon(self):
        """Tạo icon trong system tray với menu và xử lý double click"""
        if os.path.exists(ICON_PATH):
            self.normal_icon = Image.open(ICON_PATH)
        else:
            self.normal_icon = Image.new("RGB", (64, 64), color="green")
            draw = ImageDraw.Draw(self.normal_icon)
            draw.rectangle((0, 0, 64, 64), fill="green")
            draw.text((10, 20), "Bot", fill="white")

        if os.path.exists(self.red_icon_path):
            self.paused_icon = Image.open(self.red_icon_path)
        else:
            self.paused_icon = Image.new("RGB", (64, 64), color="red")
            draw = ImageDraw.Draw(self.paused_icon)
            draw.rectangle((0, 0, 64, 64), fill="red")
            draw.text((10, 20), "Bot", fill="white")

        self.tray_icon = pystray.Icon(
            "BotManager",
            self.normal_icon,
            "BotAutoMinecraft",
            menu=self.create_tray_menu()
        )
        
        # Xử lý double click
        self.tray_icon.on_activate = self.show_window

        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def create_tray_menu(self):
        """Tạo menu cho system tray icon"""
        return pystray.Menu(
            pystray.MenuItem(
                "Mở giao diện",
                self.show_window,
                default=True  # Làm cho mục này là default action (single click)
            ),
            pystray.MenuItem(
                "Tiếp tục kiểm tra" if self.is_checking_paused else "Tạm dừng kiểm tra",
                self.toggle_pause_from_tray
            ),
            pystray.MenuItem(
                "Thoát",
                self.quit_app
            )
        )

    def toggle_pause_from_tray(self):
        """Xử lý tạm dừng/tiếp tục từ system tray"""
        self.pause_checking()  # Sử dụng lại logic đã có

    def pause_checking(self):
        """Tạm dừng/tiếp tục kiểm tra từ nút trong GUI"""
        self.is_checking_paused = not self.is_checking_paused
        
        if self.is_checking_paused:
            self.pause_btn.configure(
                text="▶ Tiếp tục kiểm tra",
                fg_color="#43A047",
                hover_color="#2E7D32"
            )
            self.tray_icon.icon = self.paused_icon
        else:
            self.pause_btn.configure(
                text="⏸ Tạm dừng kiểm tra",
                fg_color="#FFA726",
                hover_color="#FB8C00"
            )
            self.tray_icon.icon = self.normal_icon
            # Kích hoạt kiểm tra ngay lập tức
            self.refresh_all_logs()
        
        # Cập nhật menu với text mới
        self.tray_icon.menu = self.create_tray_menu()
        
        # Cập nhật lại icon để menu được refresh
        self.tray_icon.update_menu()
        
        self.append_to_log("Đã tạm dừng kiểm tra" if self.is_checking_paused else "Đã tiếp tục kiểm tra")

    def close_all_bots(self):
        """Đóng tất cả bot"""
        def task():
            try:
                # Kích hoạt tạm dừng kiểm tra trước
                if not self.is_checking_paused:
                    self.after(0, self.pause_checking)
                
                # Sau đó đóng tất cả bot
                for bot in self.bots:
                    self.close_bot(bot)
                    time.sleep(0.1)  # Tránh quá tải hệ thống
                self.after(0, lambda: self.append_to_log("Đã đóng tất cả bot"))
            except Exception as e:
                self.after(0, lambda: self.append_to_log(f"Lỗi đóng tất cả bot: {str(e)}", is_error=True))

        self.executor.submit(task)

    def load_runtime_data(self):
        """Đọc dữ liệu thời gian chạy từ file"""
        try:
            if os.path.exists(RUNTIME_DATA_FILE):
                with open(RUNTIME_DATA_FILE, 'r') as f:
                    return json.load(f)
            return {bot: 0 for bot in self.bots}
        except Exception as e:
            logging.error(f"Error loading runtime data: {str(e)}")
            return {bot: 0 for bot in self.bots}

    def update_runtime_display(self):
        """Cập nhật hiển thị thời gian chạy"""
        # Cập nhật hiển thị cho mỗi bot
        for widget in self.widgets:
            bot_name = widget["name"]
            
            # Lấy thông tin CPU/RAM từ process cache
            process_name = f"{bot_name.lower()}.exe"
            if process_name in self.process_cache:
                try:
                    proc = self.process_cache[process_name]
                    if proc.is_running():
                        cpu = proc.cpu_percent()
                        mem = proc.memory_info().rss / (1024 * 1024)
                        current_runtime = time.time() - proc.create_time()
                        runtime_str = self.format_runtime(current_runtime)
                        widget["resource_var"].set(
                            f"CPU: {cpu:.1f}% | RAM: {mem:.1f}MB | Runtime: {runtime_str}"
                        )
                    else:
                        widget["resource_var"].set("Offline")
                except Exception:
                    widget["resource_var"].set("Offline")
            else:
                widget["resource_var"].set("Offline")
        
        # Lên lịch cập nhật tiếp theo
        self.after(1000, self.update_runtime_display)

    def show_window(self):
        self.after(0, self.deiconify)

    def quit_app(self):
        """Thoát ứng dụng"""
        # Xóa icon khỏi system tray ngay lập tức
        self.tray_icon.visible = False
        self.tray_icon.stop()
        
        # Đóng executor và destroy window
        self.executor.shutdown(wait=False)
        self.quit()

    def auto_refresh_progress(self):
        """Tự động chạy watchdog_progress.ps1 để kiểm tra trạng thái"""
        if not self.is_checking_paused:
            def task():
                try:
                    if os.path.exists(PROGRESS_LOG_FILE):
                        os.remove(PROGRESS_LOG_FILE)
                    
                    # Chạy PowerShell script ẩn
                    if sys.platform == "win32":
                        process = subprocess.Popen(
                            ["powershell.exe", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-NoProfile", "-File", PROGRESS_PS_SCRIPT],
                            creationflags=subprocess.CREATE_NO_WINDOW,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        
                        # Đợi script hoàn thành
                        process.wait()
                        
                        # Đọc log và kiểm tra bot nào offline
                        if os.path.exists(PROGRESS_LOG_FILE):
                            with open(PROGRESS_LOG_FILE, 'r', encoding='utf-8') as f:
                                log_content = f.read()
                            
                            # Tìm các bot offline và khởi động lần lượt
                            for bot in self.bots:
                                if f"❌ [{bot}] offline" in log_content:
                                    # Kiểm tra xem bot có đang bị lock không
                                    if bot in self.bot_locks and self.bot_locks[bot]:
                                        logging.info(f"Bỏ qua {bot}: đang trong quá trình khởi động")
                                        continue
                                        
                                    # Kiểm tra thời gian khởi động gần nhất
                                    current_time = time.time()
                                    if bot in self.last_start_times:
                                        time_since_last_start = current_time - self.last_start_times[bot]
                                        if time_since_last_start < 30:
                                            logging.info(f"Bỏ qua {bot}: mới khởi động cách đây {int(time_since_last_start)} giây")
                                            continue
                                    
                                    logging.info(f"Phát hiện {bot} offline, chuẩn bị khởi động")
                                    time.sleep(5)  # Đợi 5 giây trước khi khởi động bot tiếp theo
                                    self.run_bot(bot)
                    else:
                        subprocess.Popen(
                            ["powershell", "-File", PROGRESS_PS_SCRIPT],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                except Exception as e:
                    logging.error(f"Lỗi kiểm tra progress: {str(e)}")
                finally:
                    self.after(0, self.refresh_progress_log)

            self.executor.submit(task)
        
        # Tăng thời gian giữa các lần kiểm tra lên 60 giây
        self.after(60000, self.auto_refresh_progress)  # Chạy lại sau 60 giây

    def refresh_progress_log(self):
        """Đọc và cập nhật progress log"""
        def load_log():
            if os.path.exists(PROGRESS_LOG_FILE):
                try:
                    with open(PROGRESS_LOG_FILE, "r", encoding="utf-8") as f:
                        return f.readlines()
                except Exception as e:
                    logging.error(f"Error reading progress log: {str(e)}")
                    return [f"Lỗi đọc progress log file: {str(e)}\n"]
            return []

        def update_progress_display(content):
            self.progress_window.log_text.configure(state="normal")
            current_content = self.progress_window.log_text.get("1.0", "end-1c")
            new_content = "".join(content)
            
            # Chỉ cập nhật và cuộn xuống nếu có nội dung mới
            if current_content != new_content:
                # Lưu vị trí cuộn hiện tại
                current_scroll = self.progress_window.log_text.yview()[0]
                
                self.progress_window.log_text.delete("1.0", "end")
                for line in content:
                    if "✅" in line:
                        self.progress_window.log_text.insert("end", line, "success")
                    elif "❌" in line:
                        self.progress_window.log_text.insert("end", line, "error")
                    elif "🛠" in line or "🔄" in line:
                        self.progress_window.log_text.insert("end", line, "warning")
                    else:
                        self.progress_window.log_text.insert("end", line, "info")
                
                # Cấu hình màu cho các tag
                self.progress_window.log_text.tag_config("success", foreground=LOG_COLORS["success"])
                self.progress_window.log_text.tag_config("error", foreground=LOG_COLORS["error"])
                self.progress_window.log_text.tag_config("warning", foreground=LOG_COLORS["warning"])
                self.progress_window.log_text.tag_config("info", foreground=LOG_COLORS["info"])
                
                # Chỉ cuộn xuống dưới nếu trước đó đang ở cuối
                if current_scroll > 0.9:  # Nếu đang ở gần cuối (90% trở lên)
                    self.progress_window.log_text.see("end")
                else:  # Giữ nguyên vị trí cuộn
                    self.progress_window.log_text.yview_moveto(current_scroll)
            
            self.progress_window.log_text.configure(state="disabled")

            # Cập nhật trạng thái bot trong grid
            for line in content:
                for widget in self.widgets:
                    if widget["name"] in line:
                        if "OK" in line:
                            widget["status_var"].set("Online")
                            widget["status_label"].configure(text_color=STATUS_COLORS["online"])
                        elif "khởi động" in line:
                            widget["status_var"].set("Starting...")
                            widget["status_label"].configure(text_color=STATUS_COLORS["starting"])
                        else:
                            widget["status_var"].set("Offline")
                            widget["status_label"].configure(text_color=STATUS_COLORS["offline"])

        try:
            content = load_log()
            self.after(0, lambda: update_progress_display(content))
        except Exception as e:
            logging.error(f"Error in refresh_progress_log: {str(e)}")

    def format_total_runtime(self, seconds):
        """Chuyển đổi tổng thời gian chạy thành định dạng dễ đọc"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        
        return " ".join(parts)

    def check_service_status(self):
        """Kiểm tra trạng thái của Runtime Service"""
        try:
            # Kiểm tra service có đang chạy không
            result = subprocess.run(
                ["sc", "query", "BotRuntimeTracker"],
                capture_output=True,
                text=True
            )
            
            if "RUNNING" in result.stdout:
                self.service_status_label.configure(
                    text="✅ Runtime Service đang chạy",
                    text_color="#43A047"
                )
            else:
                self.service_status_label.configure(
                    text="❌ Runtime Service không hoạt động",
                    text_color="#E53935"
                )
        except Exception:
            self.service_status_label.configure(
                text="❌ Không thể kiểm tra Runtime Service",
                text_color="#FFA726"
            )
        
        # Kiểm tra lại sau 5 giây
        self.after(5000, self.check_service_status)

    def refresh_all_logs(self):
        """Làm mới cả 2 loại log"""
        self.refresh_log()
        self.refresh_progress_log()

    def continuous_log_refresh(self):
        """Liên tục cập nhật nội dung của cả hai log"""
        if not self.is_checking_paused:
            self.refresh_log()
            self.refresh_progress_log()
        self.after(1000, self.continuous_log_refresh)  # Lập lịch cho lần cập nhật tiếp theo

    def append_to_log(self, text, is_error=False):
        """Thêm text vào cả 2 log box"""
        tag = "red" if is_error else "green"
        
        self.watchdog_window.log_text.configure(state="normal")
        self.watchdog_window.log_text.insert("end", text + "\n", tag)
        self.watchdog_window.log_text.configure(state="disabled")
        
        self.progress_window.log_text.configure(state="normal")
        self.progress_window.log_text.insert("end", text + "\n", tag)
        self.progress_window.log_text.configure(state="disabled")

    def auto_refresh_watchdog(self):
        """Tự động chạy watchdog.ps1 mỗi 2 phút để kiểm tra log"""
        if not self.is_checking_paused:
            self.run_watchdog()
        self.after(120000, self.auto_refresh_watchdog)  # Chạy lại sau 2 phút

if __name__ == "__main__":
    app = BotManager()
    app.mainloop()
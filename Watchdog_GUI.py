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

# ==== Cài đặt ====
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# Màu sắc cho logs
LOG_COLORS = {
    "success": "#4CAF50",  # Xanh lá đậm
    "error": "#FF5252",    # Đỏ tươi
    "warning": "#FFA726",  # Cam
    "info": "#90CAF9",     # Xanh dương nhạt
    "normal": "#E0E0E0",   # Xám sáng
    "time": "#B39DDB",     # Tím nhạt
    "bot": "#81C784"       # Xanh lá nhạt
}

BOT_DIR = r"C:\Users\Administrator\Desktop\BotAutoMinecraft"
BOTS_DIR = os.path.join(BOT_DIR, "bots")
SHORTCUT_DIR = os.path.join(BOT_DIR, "shortcut")
LOG_FILE = os.path.join(BOT_DIR, "watchdog", "watchdog-output.log")
PROGRESS_LOG_FILE = os.path.join(BOT_DIR, "watchdog", "watchdog-progress-output.log")
PS_SCRIPT = os.path.join(BOT_DIR, "watchdog", "watchdog.ps1")
PROGRESS_PS_SCRIPT = os.path.join(BOT_DIR, "watchdog", "watchdog_progress.ps1")
WATCHDOG_SHORTCUT = os.path.join(BOT_DIR, "watchdog", "watchdog_service.lnk")
PROGRESS_SHORTCUT = os.path.join(BOT_DIR, "watchdog", "watchdog_progress_service.lnk")
ICON_PATH = os.path.join(BOT_DIR, "icon.ico")
ERROR_LOG = os.path.join(BOT_DIR, "gui_error.log")

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

STATUS_COLORS = {
    "online": "#43A047",
    "offline": "#E53935",
    "starting": "#FFA726"
}

class BotManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BotAutoMinecraft Manager")
        self.iconbitmap(ICON_PATH)
        self.geometry("1000x650")
        self.minsize(800, 500)
        
        # Căn giữa cửa sổ
        self.center_window()

        self.bots = [f"Vanguard{i:02}" for i in range(1, 31)]
        self.widgets = []
        self.bot_start_times = {}
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
        
        self.setup_gui()
        self.draw_bots()
        self.start_update_threads()
        self.refresh_log()
        
        # Cập nhật logs thường xuyên
        self.after(1000, self.continuous_log_refresh)  # Cập nhật log mỗi 1 giây
        self.after(10000, self.auto_refresh_progress)  # Kiểm tra progress mỗi 10s
        self.after(120000, self.auto_refresh_watchdog)  # Kiểm tra log mỗi 2 phút

        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.create_tray_icon()

    def center_window(self):
        """Căn giữa cửa sổ trên màn hình"""
        self.update_idletasks()  # Cập nhật kích thước thực của cửa sổ
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

        for i in range(8):
            self.scroll_frame.grid_columnconfigure(i, weight=1)

        headers = ["Bot Name", "Inventory", "Status", "Focus", "Run", "Close", "Edit", "Resource"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(self.scroll_frame, text=header, font=("Segoe UI", 14, "bold")).grid(
                row=0, column=i, padx=10, pady=10, sticky="ew"
            )

        # Frame chứa 2 cột log
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.pack(fill="both", expand=False, padx=10, pady=10)
        
        # Cột bên trái cho watchdog log
        self.left_frame = ctk.CTkFrame(self.log_frame)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0,5))
        
        # Thêm header đẹp hơn cho watchdog log
        header_frame = ctk.CTkFrame(self.left_frame, fg_color="#2D3436")
        header_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(
            header_frame,
            text="🔍 Watchdog Log",
            font=("Segoe UI", 14, "bold"),
            text_color="#E0E0E0"
        ).pack(pady=5)
        
        # Cấu hình watchdog log
        self.watchdog_log = ctk.CTkTextbox(
            self.left_frame,
            wrap="word",
            height=200,
            font=("Consolas", 12),
            fg_color="#1E1E1E",
            text_color="#E0E0E0"
        )
        self.watchdog_log.pack(fill="both", expand=True)
        self.watchdog_log.configure(state="disabled")
        
        # Cột bên phải cho progress log
        self.right_frame = ctk.CTkFrame(self.log_frame)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(5,0))
        
        # Thêm header đẹp hơn cho progress log
        header_frame = ctk.CTkFrame(self.right_frame, fg_color="#2D3436")
        header_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(
            header_frame,
            text="📊 Progress Log",
            font=("Segoe UI", 14, "bold"),
            text_color="#E0E0E0"
        ).pack(pady=5)
        
        # Cấu hình progress log
        self.progress_log = ctk.CTkTextbox(
            self.right_frame,
            wrap="word",
            height=200,
            font=("Consolas", 12),
            fg_color="#1E1E1E",
            text_color="#E0E0E0"
        )
        self.progress_log.pack(fill="both", expand=True)
        self.progress_log.configure(state="disabled")

        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.pack(pady=5)

        self.run_btn = ctk.CTkButton(self.btn_frame, text="▶ Chạy Watchdog", command=self.run_watchdog)
        self.run_btn.pack(side="left", padx=10)

        self.refresh_btn = ctk.CTkButton(self.btn_frame, text="🔄 Làm mới log", command=self.refresh_all_logs)
        self.refresh_btn.pack(side="left", padx=10)

        # Thêm nút tạm dừng kiểm tra
        self.pause_btn = ctk.CTkButton(
            self.btn_frame, 
            text="⏸ Tạm dừng kiểm tra", 
            command=self.pause_checking,
            fg_color="#FFA726",
            hover_color="#FB8C00"
        )
        self.pause_btn.pack(side="left", padx=10)
        self.bind_tooltip(self.pause_btn, TOOLTIPS["pause"])

        # Thêm nút đóng tất cả bot
        self.close_all_btn = ctk.CTkButton(
            self.btn_frame, 
            text="✖ Đóng tất cả", 
            command=self.close_all_bots,
            fg_color="#E53935",
            hover_color="#C62828"
        )
        self.close_all_btn.pack(side="left", padx=10)
        self.bind_tooltip(self.close_all_btn, TOOLTIPS["close_all"])

    def draw_bots(self):
        for i, bot in enumerate(self.bots):
            port = 3000 + i + 1
            row = i + 1

            status_var = ctk.StringVar()
            resource_var = ctk.StringVar()

            status_label = ctk.CTkLabel(self.scroll_frame, textvariable=status_var, font=("Segoe UI", 12, "bold"))
            resource_label = ctk.CTkLabel(self.scroll_frame, textvariable=resource_var, font=("Segoe UI", 12))

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
                    
                    for bot in self.widgets:
                        name = bot["name"]
                        info = self.get_process_info(name)
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
                        create_time = info['create_time']
                        
                        if name not in self.bot_start_times:
                            self.bot_start_times[name] = create_time
                        
                        runtime_str = self.format_runtime(info['runtime'])
                        
                        bot_widget["status_var"].set("Online")
                        bot_widget["status_label"].configure(text_color="#43A047")
                        bot_widget["run_btn"].configure(fg_color="#66BB6A", hover_color="#558B2F")
                        bot_widget["resource_var"].set(
                            f"CPU: {info['cpu']:.1f}% | RAM: {info['memory']:.1f}MB | Runtime: {runtime_str}"
                        )
                    else:
                        if name in self.bot_start_times:
                            del self.bot_start_times[name]
                        
                        bot_widget["status_var"].set("Offline")
                        bot_widget["status_label"].configure(text_color="#E53935")
                        bot_widget["run_btn"].configure(fg_color="#FFCA28", hover_color="#FDD835")
                        bot_widget["resource_var"].set("CPU: 0.0% | RAM: 0.0MB | Runtime: --")
                
                self.update_counter += 1
                
        except queue.Empty:
            pass
        except Exception:
            pass
        
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
        shortcut_path = os.path.join(SHORTCUT_DIR, f"{bot_name}.lnk")
        
        if os.path.exists(shortcut_path):
            try:
                subprocess.Popen(
                    ["cmd", "/c", "start", "", shortcut_path],
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
                )
                self.after(0, lambda: self.popup_message(f"Đã khởi động {bot_name}", "#43A047"))
            except Exception as e:
                self.after(0, lambda: self.popup_message(f"Lỗi khởi động {bot_name}: {str(e)}", "red"))
        else:
            self.after(0, lambda: self.popup_message(f"Không tìm thấy shortcut {bot_name}.lnk!", "red"))

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
            windows = gw.getWindowsWithTitle(bot_name)
            for win in windows:
                if bot_name in win.title:
                    time.sleep(0.1)
                    win.restore()
                    win.activate()
                    return
            self.after(0, lambda: self.popup_message(f"Không tìm thấy cửa sổ {bot_name}", "#FFA500"))
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
                # Sử dụng shortcut thay vì chạy trực tiếp
                subprocess.Popen(
                    ["cmd", "/c", "start", "", WATCHDOG_SHORTCUT],
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            except Exception as e:
                self.after(0, lambda: self.append_to_log(f"Lỗi: {e}", is_error=True))
            finally:
                self.after(0, self.refresh_log)

        self.executor.submit(task)

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

    def refresh_log(self):
        """Đọc và cập nhật watchdog log"""
        def load_log():
            if os.path.exists(LOG_FILE):
                try:
                    with open(LOG_FILE, "r", encoding="utf-8") as f:
                        return f.readlines()
                except Exception as e:
                    logging.error(f"Error reading watchdog log: {str(e)}")
                    return [f"Lỗi đọc watchdog log file: {str(e)}\n"]
            return []

        def update_log_display(content):
            self.watchdog_log.configure(state="normal")
            current_content = self.watchdog_log.get("1.0", "end-1c")
            new_content = "".join(content)
            
            # Chỉ cập nhật nếu nội dung thay đổi
            if current_content != new_content:
                self.watchdog_log.delete("1.0", "end")
                for line in content:
                    # Tách timestamp và nội dung
                    parts = line.split("]", 1) if "]" in line else ["", line]
                    if len(parts) == 2:
                        timestamp = parts[0] + "]"
                        message = parts[1]
                        
                        # Thêm timestamp với màu riêng
                        self.watchdog_log.insert("end", timestamp, "time")
                        
                        # Xác định tag cho phần nội dung
                        if "OK" in message:
                            tag = "success"
                        elif "Error" in message or "Exception" in message:
                            tag = "error"
                        elif "khởi động" in message:
                            tag = "warning"
                        else:
                            tag = "normal"
                        
                        # Thêm nội dung với màu tương ứng
                        self.watchdog_log.insert("end", message, tag)
                    else:
                        self.watchdog_log.insert("end", line, "normal")
                
                # Cấu hình màu cho các tag
                self.watchdog_log.tag_config("time", foreground=LOG_COLORS["time"])
                self.watchdog_log.tag_config("success", foreground=LOG_COLORS["success"])
                self.watchdog_log.tag_config("error", foreground=LOG_COLORS["error"])
                self.watchdog_log.tag_config("warning", foreground=LOG_COLORS["warning"])
                self.watchdog_log.tag_config("normal", foreground=LOG_COLORS["normal"])
                
                # Cuộn xuống cuối
                self.watchdog_log.see("end")
            
            self.watchdog_log.configure(state="disabled")

        try:
            content = load_log()
            self.after(0, lambda: update_log_display(content))
        except Exception as e:
            logging.error(f"Error in refresh_log: {str(e)}")

    def append_to_log(self, text, is_error=False):
        """Thêm text vào cả 2 log box"""
        tag = "red" if is_error else "green"
        
        self.watchdog_log.configure(state="normal")
        self.watchdog_log.insert("end", text + "\n", tag)
        self.watchdog_log.configure(state="disabled")
        
        self.progress_log.configure(state="normal")
        self.progress_log.insert("end", text + "\n", tag)
        self.progress_log.configure(state="disabled")

    def auto_refresh_watchdog(self):
        """Tự động chạy watchdog.ps1 mỗi 2 phút"""
        if not self.is_checking_paused:
            self.run_watchdog()
        self.after(120000, self.auto_refresh_watchdog)

    def hide_to_tray(self):
        self.withdraw()

    def create_tray_icon(self):
        if os.path.exists(ICON_PATH):
            image = Image.open(ICON_PATH)
        else:
            image = Image.new("RGB", (64, 64), color="green")
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, 64, 64), fill="green")
            draw.text((10, 20), "Bot", fill="white")

        self.tray_icon = pystray.Icon("BotManager", image, "BotAutoMinecraft", menu=pystray.Menu(
            pystray.MenuItem("Mở giao diện", lambda: self.show_window()),
            pystray.MenuItem("Thoát", lambda: self.quit_app())
        ))

        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self):
        self.after(0, self.deiconify)

    def quit_app(self):
        self.executor.shutdown(wait=False)
        self.tray_icon.stop()
        self.destroy()

    def auto_refresh_progress(self):
        """Tự động chạy watchdog_progress.ps1 mỗi 10 giây"""
        if not self.is_checking_paused:
            def task():
                try:
                    if os.path.exists(PROGRESS_LOG_FILE):
                        os.remove(PROGRESS_LOG_FILE)
                    # Sử dụng shortcut thay vì chạy trực tiếp
                    subprocess.Popen(
                        ["cmd", "/c", "start", "", PROGRESS_SHORTCUT],
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                except Exception as e:
                    self.after(0, lambda: self.append_to_log(f"Lỗi kiểm tra progress: {e}", is_error=True))
                finally:
                    self.after(0, self.refresh_progress_log)

            self.executor.submit(task)
        self.after(10000, self.auto_refresh_progress)

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
            self.progress_log.configure(state="normal")
            current_content = self.progress_log.get("1.0", "end-1c")
            new_content = "".join(content)
            
            # Chỉ cập nhật nếu nội dung thay đổi
            if current_content != new_content:
                self.progress_log.delete("1.0", "end")
                for line in content:
                    # Tách phần bot name và trạng thái
                    if "[" in line and "]" in line:
                        bot_start = line.find("[")
                        bot_end = line.find("]", bot_start) + 1
                        bot_name = line[bot_start:bot_end]
                        rest_of_line = line[bot_end:]
                        
                        # Thêm tên bot với màu riêng
                        self.progress_log.insert("end", bot_name, "bot")
                        
                        # Xác định tag cho phần trạng thái
                        if "✅" in rest_of_line:
                            tag = "success"
                        elif "❌" in rest_of_line:
                            tag = "error"
                        elif "🛠" in rest_of_line:
                            tag = "warning"
                        else:
                            tag = "info"
                        
                        # Thêm phần còn lại với màu tương ứng
                        self.progress_log.insert("end", rest_of_line, tag)
                    else:
                        self.progress_log.insert("end", line, "normal")
                
                # Cấu hình màu cho các tag
                self.progress_log.tag_config("bot", foreground=LOG_COLORS["bot"])
                self.progress_log.tag_config("success", foreground=LOG_COLORS["success"])
                self.progress_log.tag_config("error", foreground=LOG_COLORS["error"])
                self.progress_log.tag_config("warning", foreground=LOG_COLORS["warning"])
                self.progress_log.tag_config("info", foreground=LOG_COLORS["info"])
                self.progress_log.tag_config("normal", foreground=LOG_COLORS["normal"])
                
                # Cuộn xuống cuối
                self.progress_log.see("end")
            
            self.progress_log.configure(state="disabled")

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

    def pause_checking(self):
        """Tạm dừng/tiếp tục kiểm tra"""
        self.is_checking_paused = not self.is_checking_paused
        if self.is_checking_paused:
            self.pause_btn.configure(text="▶ Tiếp tục kiểm tra", fg_color="#43A047", hover_color="#2E7D32")
            self.append_to_log("Đã tạm dừng kiểm tra")
        else:
            self.pause_btn.configure(text="⏸ Tạm dừng kiểm tra", fg_color="#FFA726", hover_color="#FB8C00")
            self.append_to_log("Đã tiếp tục kiểm tra")
            # Kích hoạt kiểm tra ngay lập tức
            self.refresh_all_logs()

    def close_all_bots(self):
        """Đóng tất cả bot"""
        def task():
            try:
                for bot in self.bots:
                    self.close_bot(bot)
                    time.sleep(0.1)  # Tránh quá tải hệ thống
                self.after(0, lambda: self.append_to_log("Đã đóng tất cả bot"))
            except Exception as e:
                self.after(0, lambda: self.append_to_log(f"Lỗi đóng tất cả bot: {str(e)}", is_error=True))

        self.executor.submit(task)

if __name__ == "__main__":
    app = BotManager()
    app.mainloop()
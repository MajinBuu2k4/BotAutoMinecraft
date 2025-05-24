import os
import json
import time
import psutil
import logging
import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
from datetime import datetime
from pathlib import Path

# Cấu hình đường dẫn
BOT_DIR = r"C:\Users\Administrator\Desktop\BotAutoMinecraft"
SERVICE_DIR = os.path.join(BOT_DIR, "service")
RUNTIME_DATA_FILE = os.path.join(SERVICE_DIR, "runtime_data.json")
SERVICE_LOG_FILE = os.path.join(SERVICE_DIR, "runtime_service.log")

# Cấu hình logging
logging.basicConfig(
    filename=SERVICE_LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class RuntimeTracker:
    def __init__(self):
        self.bots = [f"Vanguard{i:02}" for i in range(1, 31)]
        self.runtime_data = self.load_runtime_data()
        self.bot_start_times = {}
        self.process_cache = {}
        self.cache_timestamp = 0
        self.cache_duration = 2  # Cache 2 giây
        self.is_running = True

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

    def save_runtime_data(self):
        """Lưu dữ liệu thời gian chạy vào file"""
        try:
            # Cập nhật thời gian chạy cho các bot đang hoạt động
            current_time = time.time()
            for bot, start_time in self.bot_start_times.items():
                runtime = current_time - start_time
                self.runtime_data[bot] = runtime  # Lưu thời gian chạy hiện tại

            # Lưu vào file
            with open(RUNTIME_DATA_FILE, 'w') as f:
                json.dump(self.runtime_data, f, indent=4)

            logging.info("Runtime data saved successfully")
        except Exception as e:
            logging.error(f"Error saving runtime data: {str(e)}")

    def get_all_processes(self):
        """Lấy tất cả processes với cache để giảm lag"""
        current_time = time.time()
        
        if current_time - self.cache_timestamp > self.cache_duration:
            try:
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
            except Exception as e:
                logging.error(f"Error getting processes: {str(e)}")
        
        return self.process_cache

    def update_runtime(self):
        """Cập nhật thời gian chạy của các bot"""
        try:
            processes = self.get_all_processes()
            current_time = time.time()
            active_bots = set()

            # Kiểm tra các bot đang chạy
            for bot in self.bots:
                process_name = f"{bot.lower()}.exe"
                if process_name in processes:
                    active_bots.add(bot)
                    if bot not in self.bot_start_times:
                        # Bot mới bắt đầu chạy
                        self.bot_start_times[bot] = current_time
                        logging.info(f"Bot {bot} started")

            # Kiểm tra các bot đã dừng
            for bot in list(self.bot_start_times.keys()):
                if bot not in active_bots:
                    # Bot đã dừng
                    start_time = self.bot_start_times.pop(bot)
                    runtime = current_time - start_time
                    self.runtime_data[bot] = runtime
                    logging.info(f"Bot {bot} stopped. Total runtime: {runtime:.2f} seconds")

            # Lưu dữ liệu định kỳ
            self.save_runtime_data()

        except Exception as e:
            logging.error(f"Error updating runtime: {str(e)}")

    def run(self):
        """Chạy service"""
        logging.info("Runtime tracking service started")
        
        try:
            while self.is_running:
                self.update_runtime()
                time.sleep(1)  # Cập nhật mỗi giây
        except Exception as e:
            logging.error(f"Service error: {str(e)}")
        finally:
            self.save_runtime_data()

    def stop(self):
        """Dừng service"""
        self.is_running = False
        self.save_runtime_data()
        logging.info("Runtime tracking service stopped")

class BotRuntimeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "BotRuntimeTracker"
    _svc_display_name_ = "Bot Runtime Tracker Service"
    _svc_description_ = "Tracks runtime of Vanguard bots and saves data to JSON"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

        # Thiết lập logging
        self.log_dir = Path("C:/Users/Administrator/Desktop/BotAutoMinecraft/service")
        self.log_file = self.log_dir / "runtime_service.log"
        
        logging.basicConfig(
            filename=str(self.log_file),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # File lưu dữ liệu runtime
        self.data_file = Path("C:/Users/Administrator/Desktop/BotAutoMinecraft/service/runtime_data.json")
        
        # Khởi tạo dữ liệu runtime
        self.runtime_data = self.load_runtime_data()
        self.bot_start_times = {}

    def load_runtime_data(self):
        """Đọc dữ liệu runtime từ file"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Error loading runtime data: {str(e)}")
            return {}

    def save_runtime_data(self):
        """Lưu dữ liệu runtime vào file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.runtime_data, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving runtime data: {str(e)}")

    def update_runtime(self):
        """Cập nhật thời gian chạy của các bot"""
        try:
            current_time = time.time()
            bot_processes = {}

            # Lấy tất cả processes của bot
            for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                try:
                    name = proc.info['name'].lower()
                    if name.startswith('vanguard') and name.endswith('.exe'):
                        bot_name = name[:-4].capitalize()  # Chuyển vanguard01.exe thành Vanguard01
                        bot_processes[bot_name] = proc.info['create_time']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Cập nhật thời gian chạy
            for bot_name, create_time in bot_processes.items():
                # Bot mới được khởi động
                if bot_name not in self.bot_start_times:
                    self.bot_start_times[bot_name] = create_time
                    logging.info(f"Bot {bot_name} started")

                # Cập nhật tổng thời gian chạy
                if bot_name not in self.runtime_data:
                    self.runtime_data[bot_name] = 0

                runtime = current_time - self.bot_start_times[bot_name]
                self.runtime_data[bot_name] += runtime
                self.bot_start_times[bot_name] = current_time  # Reset start time

            # Kiểm tra các bot đã tắt
            for bot_name in list(self.bot_start_times.keys()):
                if bot_name not in bot_processes:
                    del self.bot_start_times[bot_name]
                    logging.info(f"Bot {bot_name} stopped")

            # Lưu dữ liệu
            self.save_runtime_data()

        except Exception as e:
            logging.error(f"Error updating runtime: {str(e)}")

    def SvcStop(self):
        """Xử lý khi service bị dừng"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

    def SvcDoRun(self):
        """Main loop của service"""
        try:
            logging.info("Service started")
            while self.running:
                self.update_runtime()
                # Đợi 1 giây hoặc cho đến khi nhận lệnh dừng
                win32event.WaitForSingleObject(self.stop_event, 1000)
        except Exception as e:
            logging.error(f"Service error: {str(e)}")
        finally:
            logging.info("Service stopped")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(BotRuntimeService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(BotRuntimeService) 
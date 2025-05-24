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
import win32security
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

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
    
    # Cấu hình khởi động tự động
    _svc_deps_ = []
    _exe_name_ = sys.executable
    _exe_args_ = os.path.abspath(sys.argv[0])
    _svc_reg_class_ = "WIN32_OWN_PROCESS"
    _svc_start_type_ = win32service.SERVICE_AUTO_START
    _svc_recovery_actions_ = [
        (win32service.SC_ACTION_RESTART, 0),  # Khởi động lại ngay lập tức
        (win32service.SC_ACTION_RESTART, 60000),  # Thử lại sau 1 phút
        (win32service.SC_ACTION_RESTART, 120000)  # Thử lại sau 2 phút
    ]
    _svc_recovery_opts_ = {
        'reset_period': 86400,  # Reset error count sau 1 ngày
        'actions': _svc_recovery_actions_,
        'first': 0,  # Khởi động lại ngay lập tức lần đầu
        'max_tries': len(_svc_recovery_actions_)
    }

    def __init__(self, args):
        try:
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.running = True
            
            # Thiết lập logging
            self.setup_logging()
            
            # Khởi tạo runtime tracker
            self.tracker = RuntimeTracker()
            
            logging.info("Service initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing service: {str(e)}")
            raise

    def setup_logging(self):
        try:
            log_dir = Path(SERVICE_DIR)
            log_file = log_dir / "runtime_service.log"
            
            # Đảm bảo thư mục tồn tại
            os.makedirs(str(log_dir), exist_ok=True)
            
            # Thiết lập logging với rotation
            handler = RotatingFileHandler(
                str(log_file),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            
            logger = logging.getLogger()
            logger.setLevel(logging.INFO)
            logger.addHandler(handler)
            
        except Exception as e:
            print(f"Error setting up logging: {str(e)}")
            raise

    def SvcStop(self):
        try:
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.stop_event)
            self.running = False
            logging.info("Service stop requested")
        except Exception as e:
            logging.error(f"Error stopping service: {str(e)}")

    def SvcDoRun(self):
        try:
            logging.info("Service is starting...")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            
            while self.running:
                try:
                    # Cập nhật runtime data
                    self.tracker.update_runtime()
                    
                    # Đợi 1 giây hoặc cho đến khi nhận lệnh dừng
                    rc = win32event.WaitForSingleObject(self.stop_event, 1000)
                    if rc == win32event.WAIT_OBJECT_0:
                        break
                        
                except Exception as e:
                    logging.error(f"Error in main loop: {str(e)}")
                    # Tiếp tục chạy ngay cả khi có lỗi
                    time.sleep(1)
                    continue
                    
        except Exception as e:
            logging.error(f"Service error: {str(e)}")
            raise
        finally:
            logging.info("Service is stopping...")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, '')
            )

if __name__ == '__main__':
    try:
        if len(sys.argv) == 1:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(BotRuntimeService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            win32serviceutil.HandleCommandLine(BotRuntimeService)
    except Exception as e:
        logging.error(f"Service startup error: {str(e)}")
        raise 
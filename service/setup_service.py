import os
import sys
import argparse
import subprocess
from pathlib import Path

def run_as_admin(cmd):
    """Chạy lệnh với quyền admin"""
    if sys.platform.startswith('win'):
        try:
            return subprocess.run(['runas', '/user:Administrator', cmd], capture_output=True, text=True)
        except Exception as e:
            print(f"Lỗi khi chạy lệnh với quyền admin: {e}")
            return None

def install_service():
    """Cài đặt service"""
    try:
        print("Đang cài đặt Bot Runtime Tracker service...")
        result = subprocess.run(
            ['python', 'runtime_service.py', 'install'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Đã cài đặt service thành công!")
            # Khởi động service
            subprocess.run(['net', 'start', 'BotRuntimeTracker'])
            print("✅ Đã khởi động service!")
        else:
            print("❌ Lỗi khi cài đặt service:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def uninstall_service():
    """Gỡ cài đặt service"""
    try:
        print("Đang gỡ cài đặt Bot Runtime Tracker service...")
        # Dừng service trước
        subprocess.run(['net', 'stop', 'BotRuntimeTracker'], capture_output=True)
        
        result = subprocess.run(
            ['python', 'runtime_service.py', 'remove'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Đã gỡ cài đặt service thành công!")
        else:
            print("❌ Lỗi khi gỡ cài đặt service:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def start_service():
    """Khởi động service"""
    try:
        print("Đang khởi động service...")
        result = subprocess.run(['net', 'start', 'BotRuntimeTracker'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Đã khởi động service thành công!")
        else:
            print("❌ Lỗi khi khởi động service:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def stop_service():
    """Dừng service"""
    try:
        print("Đang dừng service...")
        result = subprocess.run(['net', 'stop', 'BotRuntimeTracker'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Đã dừng service thành công!")
        else:
            print("❌ Lỗi khi dừng service:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def check_status():
    """Kiểm tra trạng thái service"""
    try:
        result = subprocess.run(['sc', 'query', 'BotRuntimeTracker'], capture_output=True, text=True)
        if "RUNNING" in result.stdout:
            print("✅ Service đang chạy")
        elif "STOPPED" in result.stdout:
            print("⏹ Service đã dừng")
        else:
            print("❌ Service chưa được cài đặt")
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra trạng thái: {e}")

if __name__ == "__main__":
    # Đảm bảo script được chạy từ thư mục service
    os.chdir(Path(__file__).parent)
    
    parser = argparse.ArgumentParser(description="Quản lý Bot Runtime Tracker Service")
    parser.add_argument('action', choices=['install', 'uninstall', 'start', 'stop', 'status'],
                      help='Hành động cần thực hiện với service')
    
    args = parser.parse_args()
    
    actions = {
        'install': install_service,
        'uninstall': uninstall_service,
        'start': start_service,
        'stop': stop_service,
        'status': check_status
    }
    
    # Thực hiện hành động
    actions[args.action]() 
# BotAutoMinecraft Manager

Ứng dụng quản lý và theo dõi các bot Minecraft tự động với giao diện đồ họa (GUI) và Windows Service.

## Cấu trúc thư mục

```
BotAutoMinecraft/
├── bots/                   # Thư mục chứa các file script bot (.js)
├── shortcut/              # Thư mục chứa shortcut để chạy bot
├── watchdog/              # Thư mục chứa các script theo dõi bot
│   ├── watchdog.ps1
│   ├── watchdog_progress.ps1
│   ├── watchdog_service.lnk
│   └── watchdog_progress_service.lnk
├── service/               # Thư mục chứa Windows Service theo dõi thời gian chạy
│   ├── runtime_service.py     # File chính của service
│   ├── runtime_data.json      # File lưu thời gian chạy
│   ├── runtime_service.log    # File log của service
│   └── setup_service.py       # Script quản lý service
├── Watchdog_GUI.py       # Giao diện người dùng chính
├── install_service.bat   # Script cài đặt Windows Service
└── window_config.json    # Cấu hình cửa sổ
```

## Tính năng mới

1. **Runtime Tracking Service**
   - Windows Service theo dõi thời gian chạy của từng bot
   - Lưu trữ dữ liệu vào file JSON
   - Tự động khởi động cùng Windows
   - Ghi log hoạt động

2. **Cải tiến GUI**
   - Hiển thị tổng thời gian chạy của từng bot
   - Hiển thị trạng thái service
   - Cửa sổ xem thống kê thời gian chạy
   - Lưu và khôi phục vị trí, kích thước cửa sổ

## Cài đặt

### Yêu cầu
- Windows 10/11
- Python 3.11
- Các thư viện Python: pywin32, customtkinter, psutil, pygetwindow, pystray, Pillow

### Cài đặt Runtime Service
1. Chạy file `install_service.bat` với quyền Administrator
2. Script sẽ tự động:
   - Tìm Python trên máy
   - Cài đặt các package cần thiết
   - Cài đặt và khởi động service

### Quản lý Service
Sử dụng `setup_service.py` trong thư mục service:
```bash
# Kiểm tra trạng thái
python service/setup_service.py status

# Khởi động service
python service/setup_service.py start

# Dừng service
python service/setup_service.py stop

# Gỡ cài đặt service
python service/setup_service.py uninstall
```

## Sử dụng

### Giao diện chính (Watchdog_GUI.py)
- **Danh sách bot**: Hiển thị trạng thái, tài nguyên và thời gian chạy
- **Các nút điều khiển**:
  - 🔄 Chạy Watchdog: Khởi động script theo dõi bot
  - 📋 Watchdog Log: Xem log theo dõi bot
  - 📊 Progress Log: Xem log tiến trình
  - ⏱ Thời gian chạy: Xem thống kê thời gian hoạt động
  - ⏸ Tạm dừng kiểm tra: Tạm dừng/tiếp tục việc kiểm tra bot
  - ✖ Đóng tất cả: Đóng tất cả các bot

### Tính năng ẩn xuống khay hệ thống
- Ứng dụng sẽ ẩn xuống system tray khi đóng cửa sổ
- Click đúp vào icon để hiện lại cửa sổ
- Menu tray có các tùy chọn:
  - Mở giao diện
  - Tạm dừng kiểm tra
  - Thoát

### Các phím tắt
- `ESC`: Đóng cửa sổ log/thống kê

## Xử lý sự cố

### Service không hoạt động
1. Kiểm tra trạng thái: `python service/setup_service.py status`
2. Xem log trong `service/runtime_service.log`
3. Thử khởi động lại: 
   ```bash
   python service/setup_service.py stop
   python service/setup_service.py start
   ```

### GUI không hiển thị thời gian chạy
1. Kiểm tra service có đang chạy không
2. Kiểm tra file `service/runtime_data.json` có tồn tại không
3. Xem log trong `service/runtime_service.log`

## Ghi chú
- Service sẽ tự động khởi động cùng Windows
- Dữ liệu thời gian chạy được lưu trong `service/runtime_data.json`
- Cấu hình cửa sổ được lưu trong `window_config.json`
- Các file log được tự động làm mới khi đạt kích thước lớn 
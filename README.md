# BotAutoMinecraft Manager

Ứng dụng quản lý và giám sát bot Minecraft với giao diện đồ họa. Hỗ trợ quản lý nhiều bot cùng lúc, tự động khởi động lại khi gặp sự cố và theo dõi trạng thái hoạt động.

## Yêu cầu hệ thống

- Windows 10 trở lên
- PowerShell 5.1 trở lên
- Node.js 16.x trở lên
- Python 3.8 trở lên
- AutoHotkey v2 (cho tính năng tự động hóa)

## Cài đặt

### 1. Cài đặt Node.js dependencies

```bash
npm install
```

Các thư viện Node.js cần thiết:
- mineflayer@4.27.0
- mineflayer-pathfinder@2.4.5
- mineflayer-web-inventory@1.8.5
- express@5.1.0
- body-parser@2.2.0
- chalk@5.4.1

### 2. Cài đặt Python dependencies

```bash
pip install customtkinter
pip install psutil
pip install pygetwindow
pip install pystray
pip install pillow
```

### 3. Cấu trúc thư mục

```
BotAutoMinecraft/
├── bots/                  # Thư mục chứa script của các bot
│   └── logs/             # Log của từng bot
├── node/                  # Thư mục chứa các file thực thi của bot
├── watchdog/             # Script giám sát và log của watchdog
├── shortcut/             # Shortcut để khởi động bot
├── Watchdog_GUI.py       # Giao diện quản lý chính
├── Watchdog_GUI.ahk      # Script AutoHotkey
└── icon.ico              # Icon của ứng dụng
```

## Cấu hình

1. Đảm bảo các đường dẫn trong `watchdog/watchdog.ps1` trỏ đến đúng thư mục của bạn
2. Kiểm tra các đường dẫn trong `Watchdog_GUI.py` phù hợp với cấu trúc thư mục của bạn
3. Tạo thư mục `logs` trong thư mục `bots` nếu chưa có

## Sử dụng

### Khởi động ứng dụng

1. Chạy file `Watchdog_GUI.py`:
```bash
python Watchdog_GUI.py
```

### Các tính năng chính

1. **Quản lý Bot**
   - Khởi động/dừng từng bot
   - Xem trạng thái hoạt động
   - Theo dõi tài nguyên sử dụng (CPU, RAM)
   - Focus vào cửa sổ bot cụ thể
   - Chỉnh sửa script của bot

2. **Giám sát tự động**
   - Tự động kiểm tra trạng thái bot mỗi 2 phút
   - Tự động khởi động lại bot khi gặp sự cố
   - Theo dõi log hoạt động
   - Tạm dừng/tiếp tục việc kiểm tra
   - Đóng tất cả bot cùng lúc

3. **Tính năng phụ trợ**
   - Chạy ẩn trong system tray
   - Xem inventory của bot qua web interface
   - Ghi log lỗi để debug

### Các nút chức năng

- **▶ Chạy Watchdog**: Kích hoạt hệ thống giám sát
- **🔄 Làm mới log**: Cập nhật log thủ công
- **⏸ Tạm dừng kiểm tra**: Tạm dừng/tiếp tục việc tự động kiểm tra
- **✖ Đóng tất cả**: Đóng tất cả bot đang chạy

### Theo dõi trạng thái

- **Màu xanh**: Bot đang hoạt động bình thường
- **Màu vàng**: Bot đang khởi động
- **Màu đỏ**: Bot không hoạt động/gặp sự cố

## Xử lý sự cố

1. **Bot không khởi động**
   - Kiểm tra đường dẫn trong file cấu hình
   - Xem log lỗi trong `gui_error.log`
   - Đảm bảo Node.js đang chạy đúng phiên bản

2. **Watchdog không hoạt động**
   - Kiểm tra quyền thực thi PowerShell
   - Xem log trong thư mục `watchdog`

3. **Giao diện không hiển thị đúng**
   - Cập nhật CustomTkinter lên phiên bản mới nhất
   - Kiểm tra file `icon.ico` tồn tại

## Bảo trì

- Kiểm tra và xóa các file log cũ định kỳ
- Cập nhật các thư viện Node.js và Python
- Backup các script bot quan trọng

## Lưu ý

- Không đóng cửa sổ PowerShell đang chạy bot
- Nên để ứng dụng chạy ẩnh thay vì đóng hoàn toàn
- Kiểm tra tài nguyên hệ thống khi chạy nhiều bot
- Đặt tên bot theo định dạng "VanguardXX" 
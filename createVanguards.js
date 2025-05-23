const fs = require('fs');
const path = require('path');

// Đường dẫn đến node.exe gốc
const sourcePath = 'C:\\Program Files\\nodejs\\node.exe';
// Thư mục đích
const destFolder = 'C:\\Users\\Administrator\\Desktop\\node';

// Tạo thư mục nếu chưa có
if (!fs.existsSync(destFolder)) {
    fs.mkdirSync(destFolder, { recursive: true });
}

// Tạo 30 bản sao
for (let i = 1; i <= 30; i++) {
    const fileNumber = String(i).padStart(2, '0'); // 01, 02, ..., 30
    const destFileName = `Vanguard${fileNumber}.exe`;
    const destPath = path.join(destFolder, destFileName);

    // Sao chép file
    fs.copyFileSync(sourcePath, destPath);
    console.log(`Đã tạo: ${destFileName}`);
}

console.log('Hoàn tất sao chép 30 file Vanguard');

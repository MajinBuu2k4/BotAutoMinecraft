const mineflayer = require('mineflayer');
const webInventory = require('mineflayer-web-inventory');
const { pathfinder, Movements, goals: { GoalBlock } } = require('mineflayer-pathfinder');
const fs = require('fs');
const path = require('path');

// ====== CẤU HÌNH BOT ======
const USERNAME = 'Vanguard08';
const INVENTORY_PORT = 3008;
const SERVER_HOST = 'mc.luckyvn.com';
const MINECRAFT_VERSION = '1.18.2';
const LOG_FILE = path.join(__dirname, 'logs', `${USERNAME}.log`);
const MAX_RECONNECT_ATTEMPTS = 10;

let bot;
let checkClockInterval;
let reconnectAttempts = 0;
let loggedIn = false;
let menuOpened = false;
let inGame = false;  // <-- thêm biến này
let webInventoryServerStarted = false;

// ====== GHI LOG "ALIVE" ĐỊNH KỲ ======
const logsDir = path.dirname(LOG_FILE);
if (!fs.existsSync(logsDir)) fs.mkdirSync(logsDir);

setInterval(() => {
  try {
    let state = 'ALIVE';
    if (inGame) {
      state = 'ALIVE-INGAME';
    } else if (menuOpened) {
      state = 'ALIVE-MENU';
    } else if (loggedIn) {
      state = 'ALIVE-LOBBY';
    }
    fs.writeFileSync(LOG_FILE, `${state} ${new Date().toISOString()}`);
  } catch (err) {
    console.error("❗ Không thể ghi log:", err.message);
  }
}, 5000);


// ====== HÀM CHÍNH TẠO BOT ======
function createBot() {
  loggedIn = false;
  menuOpened = false;
  inGame = false;  // reset trạng thái khi tạo bot mới

  bot = mineflayer.createBot({
    host: SERVER_HOST,
    username: USERNAME,
    version: MINECRAFT_VERSION,
  });

  bot.loadPlugin(pathfinder);

  bot.once('spawn', () => {
    reconnectAttempts = 0;
    console.log("🟢 Bot đã vào game, chờ login...");

    const defaultMove = new Movements(bot);
    bot.pathfinder.setMovements(defaultMove);

    if (!webInventoryServerStarted) {
      webInventory(bot, { port: INVENTORY_PORT });
      webInventoryServerStarted = true;
      console.log(`🌐 Xem inventory tại: http://localhost:${INVENTORY_PORT}`);
    }

    checkClockInterval = setInterval(() => {
      if (loggedIn && !menuOpened) {
        const slot4 = bot.inventory.slots[36 + 4];
        if (slot4?.name === 'minecraft:clock') {
          bot.setQuickBarSlot(4);
          bot.activateItem();
        }
      }
    }, 10000);
  });

  // ====== XỬ LÝ MESSAGE ======
  bot.on('message', (message) => {
    const msg = message.toString();
    if (message.toAnsi) console.log(message.toAnsi());
    else console.log(msg);
  
    // Đăng nhập
    if (msg.includes('/login') && !loggedIn) {
      bot.chat('/login Phuc2005');
      loggedIn = true;
      console.log("🔐 Đã gửi lệnh /login");
    }
  
    // Mở menu
    if (msg.includes('Đăng nhập thành công') && !menuOpened) {
      setTimeout(() => {
        console.log("🕹 Dùng đồng hồ mở menu chọn chế độ");
        bot.setQuickBarSlot(4);
        bot.activateItem();
      }, 1000);
    }
  
    if (msg.includes('Bạn đã mở bảng chọn máy chủ!') && !menuOpened) {
      menuOpened = true;
      console.log("📥 Menu mở, chuẩn bị click slot 22 và 34");
  
      setTimeout(() => bot.clickWindow(22, 0, 0), 1000);
      setTimeout(() => {
        bot.clickWindow(34, 0, 0);
        console.log("🎮 Đã chọn máy chủ, chờ vào In-Game...");
      }, 2500);
    }
  
    // ✅ Gán inGame khi vào được server thành công
    if (msg.includes(`${USERNAME} Đã tham gia máy chủ!`)) {
      inGame = true;
      console.log("✅ Bot đã vào In-Game!");
    }
  });
  

  // ====== XỬ LÝ SỰ KIỆN ======
  bot.on('respawn', () => {
    menuOpened = false;
    inGame = false;  // reset khi respawn
    console.log('♻️ Reset trạng thái menu và inGame khi vào sảnh');

    setTimeout(() => {
      const clockSlot = bot.inventory.slots[36 + 4];
      if (clockSlot?.name.includes('clock')) {
        bot.setQuickBarSlot(4);
        console.log('🔁 Cầm lại đồng hồ sau khi vào sảnh');
      }
    }, 2000);
  });

  bot.on('end', () => {
    clearInterval(checkClockInterval);
    reconnectAttempts++;

    console.log(`❌ Mất kết nối (lần thử ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);

    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.log("🛑 Quá số lần reconnect, dừng bot");
      return process.exit(1);
    }

    const delay = Math.min(reconnectAttempts, 10) * 5000;
    console.log(`⌛ Thử kết nối lại sau ${delay / 1000}s...`);

    setTimeout(safeCreateBot, delay);
  });

  bot.on('kicked', (reason) => {
    clearInterval(checkClockInterval);
    console.log("❌ Bị kick:", reason);

    if (reason.includes("đang kết nối") || reason.includes("already connected")) {
      console.log("⚠️ Lỗi session, đợi 20s rồi thử lại...");
      setTimeout(() => {
        reconnectAttempts = 0;
        safeCreateBot();
      }, 20000);
    } else {
      reconnect();
    }
  });

  bot.on('error', err => console.log("⚠️ Lỗi:", err.message));

  // ====== ĐIỀU KHIỂN QUA STDIN ======
  process.stdin.on('data', async data => {
    const input = data.toString().trim();
    if (input === '#dropall') {
      try {
        const dropAllModule = require('../module_rieng/drop_all');
        const viTriModule = require(`../module_rieng/vi_tri_${USERNAME}`);
        console.log('🎯 Bắt đầu thực hiện drop all items...');
        await dropAllModule(bot, viTriModule);
      } catch (err) {
        console.log('❌ Lỗi khi thực hiện drop all:', err.message);
      }
      return;
    }


    if (input.startsWith('#goto')) {
      const [x, y, z] = input.split(' ').slice(1).map(Number);
      if ([x, y, z].some(isNaN)) return console.log("⚠️ Tọa độ không hợp lệ!");
      try {
        console.log(`🧭 Đang đi đến: ${x} ${y} ${z}`);
        await bot.pathfinder.goto(new GoalBlock(x, y, z));
        console.log("✅ Đã đến tọa độ.");
      } catch (err) {
        console.log("⚠️ Lỗi khi đi:", err.message);
      }
      return;
    }

    if (input.startsWith('#look')) {
      const [yawDeg, pitchDeg] = input.split(' ').slice(1).map(Number);
      if ([yawDeg, pitchDeg].some(isNaN)) return console.log("⚠️ Cú pháp không hợp lệ. Ví dụ: #look 90 0");
      try {
        await bot.look(yawDeg * Math.PI / 180, pitchDeg * Math.PI / 180);
        console.log(`👀 Đã quay: yaw ${yawDeg}°, pitch ${pitchDeg}°`);
      } catch (err) {
        console.log("⚠️ Lỗi khi quay:", err.message);
      }
      return;
    }

    if (input === '#vecho') {
      try {
        const modulePath = path.join(__dirname, '..', 'module_rieng', `vi_tri_${USERNAME}.js`);
        if (fs.existsSync(modulePath)) {
          const goToModule = require(modulePath);
          console.log(`🚀 Đang chạy module di chuyển: vi_tri_${USERNAME}.js`);
          await goToModule(bot);
        } else {
          console.log(`⚠️ Không tìm thấy module vi_tri_${USERNAME}.js`);
        }
      } catch (err) {
        console.log(`❌ Lỗi khi gọi module vị trí cho ${USERNAME}:`, err.message);
      }
      return;
    }
    
    if (input.length > 0) {
      bot.chat(input);
      console.log(`⌨️ Gửi chat: ${input}`);
    }
  });
}

// ====== HÀM PHỤ ======
function reconnect() {
  console.log("♻️ Reconnect sau 5s...");
  setTimeout(safeCreateBot, 5000);
}

function safeCreateBot() {
  try {
    createBot();
  } catch (err) {
    console.error("❗ Lỗi tạo bot:", err.message);
    setTimeout(safeCreateBot, 5000);
  }
}

// ====== CHẠY BOT ======
safeCreateBot();

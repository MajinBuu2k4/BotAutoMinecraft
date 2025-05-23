const { goals: { GoalBlock }, Movements } = require('mineflayer-pathfinder');

async function drop_all(bot, returnPositionModule) {
  try {
    // Thiết lập movement để không phá/đặt block
    const movements = new Movements(bot);
    movements.allowParkour = false;
    movements.canDig = false;
    movements.placeCost = Infinity;  // Không cho phép đặt block
    movements.blocksCantBreak.add('*');  // Không cho phép phá bất kỳ block nào
    bot.pathfinder.setMovements(movements);

    // Dùng lệnh /warp afk
    await bot.chat('/warp afk');
    await new Promise(resolve => setTimeout(resolve, 2000)); // Đợi 2 giây để teleport

    // Di chuyển đến vị trí 5 56 108
    console.log('🧭 Đang di chuyển đến 5 56 108...');
    await bot.pathfinder.goto(new GoalBlock(5, 56, 108));
    console.log('✅ Đã đến tọa độ 5 56 108');

    // Quay mặt hướng -90 0
    await bot.look(-90 * Math.PI / 180, 0);
    console.log('👀 Đã quay mặt về hướng yaw=-90°, pitch=0°');

    // Dùng lệnh /drop để được phép drop đồ
    await bot.chat('/drop');
    console.log('🎯 Đã kích hoạt lệnh /drop');

    // Theo dõi chat để phát hiện thông báo dọn dẹp
    let shouldStopDropping = false;
    const messageHandler = (message) => {
      const msg = message.toString();
      console.log('📢 Nhận được message:', msg); // Log để debug

      // Kiểm tra cả hai trường hợp: chữ hoa và chữ thường
      if (msg.includes('Nhân viên sẽ quét dọn vật phẩm') || 
          msg.toLowerCase().includes('nhân viên sẽ quét dọn vật phẩm')) {
        shouldStopDropping = true;
        console.log('⚠️ Phát hiện thông báo dọn dẹp, dừng drop đồ!');
        // Thêm warp về AFK ngay lập tức khi phát hiện thông báo
        bot.chat('/warp afk');
      }
      if (msg.toLowerCase().includes('stop')) {
        shouldStopDropping = true;
        console.log('⚠️ Phát hiện lệnh stop, dừng drop đồ!');
      }
    };
    bot.on('message', messageHandler);

    // Drop tất cả đồ trong inventory
    const inventory = bot.inventory.items();
    for (const item of inventory) {
      if (shouldStopDropping) {
        console.log('🛑 Dừng drop do nhận được tín hiệu dừng');
        break;
      }
      try {
        await bot.tossStack(item);
        console.log(`📦 Đã drop ${item.name}`);
        await new Promise(resolve => setTimeout(resolve, 100)); // Đợi 0.1 giây giữa mỗi lần drop
      } catch (err) {
        console.log(`⚠️ Không thể drop ${item.name}:`, err.message);
      }
    }

    // Gỡ bỏ event listener để tránh memory leak
    bot.removeListener('message', messageHandler);

    // Warp về khu AFK trước khi quay về vị trí
    console.log('🌀 Đang warp về khu AFK...');
    await bot.chat('/warp afk');
    await new Promise(resolve => setTimeout(resolve, 2000)); // Đợi 2 giây để teleport

    // Quay về vị trí của bot tương ứng
    if (returnPositionModule) {
      console.log(`🔄 Đang quay về vị trí của ${returnPositionModule.name}...`);
      await returnPositionModule(bot);
    } else {
      console.log('⚠️ Không có module vị trí được cung cấp, ở lại vị trí hiện tại');
    }

  } catch (err) {
    console.log('⚠️ Lỗi trong quá trình thực hiện drop_all:', err.message);
  }
}

module.exports = drop_all; 
// module_rieng/vi_tri_Vanguard07.js

const { goals: { GoalBlock } } = require('mineflayer-pathfinder');

async function vi_tri_Vanguard07(bot) {
  try {
    console.log('🧭 Đang di chuyển đến -18 55 137...');
    await bot.pathfinder.goto(new GoalBlock(-18, 55, 137));
    console.log('✅ Đã đến tọa độ -18 55 137');
    await bot.look(-90 * Math.PI / 180, 0);
    console.log('👀 Đã quay mặt về hướng yaw=90°, pitch=0°');
  } catch (err) {
    console.log('⚠️ Lỗi khi di chuyển đến Vanguard07:', err.message);
  }
}

module.exports = vi_tri_Vanguard07;
"""快速截图工具：保存当前屏幕到 debug_screenshots/ 目录。

用法：
1. 打开游戏，停留在顾客订单面板
2. 运行此脚本，等待 3 秒（期间切回游戏窗口）
3. 截图保存为 debug_screenshots/customer_orders.png
"""

import time
from pathlib import Path

import pyautogui

SAVE_DIR = Path(__file__).parent / "debug_screenshots"
SAVE_DIR.mkdir(exist_ok=True)

print("将在 3 秒后截图，请切到游戏窗口并停留在顾客订单面板...")
for i in range(3, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

screenshot = pyautogui.screenshot()
filepath = SAVE_DIR / "customer_orders.png"
screenshot.save(filepath)
print(f"截图已保存: {filepath}")
print(f"尺寸: {screenshot.size}")

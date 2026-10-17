"""模板截图辅助工具。

运行后会逐个提示你截取按钮，保存为模板图片。
每个按钮有 3 秒倒计时，请在倒计时结束前把鼠标移到按钮上方。

需要截取的按钮（来自顾客订单流程）：
  1. 交付
  2. 前往制作
  3. 制作
  4. 暂时没货

用法：
    python capture_templates.py
"""

import time
from pathlib import Path

import pyautogui

TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

BUTTONS = ["交付", "前往制作", "制作", "暂时没货"]


def capture_button(name: str) -> None:
    print(f"\n>>> 请在 3 秒内把鼠标移到 [{name}] 按钮上方（悬停即可，不要点击）")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    # 获取鼠标位置，以此为中心截取按钮区域
    x, y = pyautogui.position()
    # 按钮通常 80x40 左右，以鼠标为中心截取 120x60 区域
    region = (x - 60, y - 30, 120, 60)
    img = pyautogui.screenshot(region=region)

    filepath = TEMPLATES_DIR / f"{name}.png"
    img.save(filepath)
    print(f"  已保存模板: {filepath}")


def main() -> None:
    print("=" * 50)
    print("按钮模板截图工具")
    print("=" * 50)
    print("请打开游戏并停留在能看到按钮的界面。")
    print("每个按钮有 3 秒倒计时，把鼠标移到按钮上方即可。")
    print()

    for btn in BUTTONS:
        try:
            capture_button(btn)
        except KeyboardInterrupt:
            print("\n用户中断，已保存的模板不会被删除。")
            break

    print("\n" + "=" * 50)
    print("模板截图完成！已保存到 templates/ 目录：")
    for f in sorted(TEMPLATES_DIR.glob("*.png")):
        print(f"  - {f.name}")
    print("=" * 50)


if __name__ == "__main__":
    main()

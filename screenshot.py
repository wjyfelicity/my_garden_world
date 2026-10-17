import datetime
import os
import time

import pyautogui


class AutoScreenshot:
    def __init__(self, save_dir="screenshots", interval: float = 1.0) -> None:
        """
        初始化截屏工具类

        :param save_dir: 截图保存的目录
        :param interval: 截屏间隔时间（秒）
        """
        self.save_dir = save_dir
        self.interval = interval
        self.running = False

        # 创建保存目录
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        # pyautogui 的安全机制：将鼠标移动到屏幕左上角会触发异常
        # 设置 fail-safe 为 True，防止程序失控
        pyautogui.FAILSAFE = True

    def take_screenshot(self):
        """
        执行一次截屏并保存
        """
        # 获取当前时间戳作为文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(self.save_dir, filename)

        # 使用 pyautogui 截屏
        # pyautogui.screenshot() 返回一个 PIL Image 对象
        screenshot = pyautogui.screenshot()

        # 保存图片
        screenshot.save(filepath)
        print(f"截图已保存: {filepath}")

    def start(self):
        """
        开始自动截屏
        """
        self.running = True
        print(f"开始自动截屏，间隔 {self.interval} 秒。")
        print("提示: 将鼠标移动到屏幕左上角 (0,0) 位置可以紧急停止程序。")

        try:
            while self.running:
                self.take_screenshot()

                # 检查鼠标是否在左上角，用于触发 FAILSAFE 异常从而停止
                # 这里的 position() 调用是 pyautogui 的检查点
                pyautogui.position()

                time.sleep(self.interval)

        except pyautogui.FailSafeException:
            print("\n检测到鼠标在屏幕左上角，触发紧急停止！")
            self.stop()
        except KeyboardInterrupt:
            print("\n检测到 Ctrl+C，正在停止截屏...")
            self.stop()

    def stop(self):
        """
        停止自动截屏
        """
        self.running = False
        print("自动截屏已停止。")


def convert_format() -> None:
    """备选：将所有 .jpg 格式的模板转换为 .png 格式"""
    from pathlib import Path

    from PIL import Image

    for jpg_file in Path("./templates").glob("*.jpg"):
        img = Image.open(jpg_file)
        png_path = jpg_file.with_suffix(".png")
        img.save(png_path)
        print(f"已转换: {jpg_file.name} -> {png_path.name}")


if __name__ == "__main__":
    # 创建截屏工具实例
    # 注意：pyautogui 在某些高分辨率屏幕下可能会有坐标问题，通常不需要额外配置
    tool = AutoScreenshot()

    # 启动
    tool.start()

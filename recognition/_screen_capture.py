"""跨平台屏幕捕获模块。

- Windows: 使用 windows-capture + win32gui（原方案，性能最佳）
- macOS: 使用 pyautogui 截图 + AppleScript (osascript) 获取窗口位置
- 其他平台: 回退为全屏截图

接口与原方案保持一致：
- window_rect: (left, top, right, bottom)
- grab(show, save_dir) -> (PIL.Image, np.ndarray BGR)
"""

import datetime
import platform
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np
from loguru import logger
from PIL import Image

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import win32gui  # type: ignore
    from windows_capture import Frame, InternalCaptureControl, WindowsCapture  # type: ignore


def _find_window_rect_macos(keyword: str) -> tuple[int, int, int, int] | None:
    """通过 AppleScript 查找包含 keyword 的窗口位置。"""
    script = f'''
    tell application "System Events"
        set matched to missing value
        repeat with p in (every process whose visible is true)
            try
                repeat with w in (windows of p)
                    set wname to name of w
                    if wname contains "{keyword}" then
                        set matched to {{position of w, size of w}}
                        exit repeat
                    end if
                end repeat
            end try
            if matched is not missing value then exit repeat
        end repeat
        return matched
    end tell
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5,
        )
        # 输出格式: x, y, width, height
        parts = result.stdout.strip().split(", ")
        if len(parts) == 4:
            x, y, w, h = map(int, parts)
            return (x, y, x + w, y + h)
    except Exception as e:
        logger.warning(f"AppleScript 获取窗口位置失败: {e}")
    return None


def _find_window_rect_windows(keyword: str) -> tuple[int, int, int, int] | None:
    """通过 win32gui 查找包含 keyword 的窗口位置。"""
    handles: list[int] = []

    def callback(hwnd: int, _: list[int]) -> None:
        if keyword in win32gui.GetWindowText(hwnd):
            handles.append(hwnd)

    win32gui.EnumWindows(callback, handles)
    if not handles:
        return None
    return win32gui.GetWindowRect(handles[0])


class _ScreenCapture:
    def __init__(self, keyword: str, save_dir: str = "screenshots2") -> None:
        self.keyword = keyword
        self.window_rect: tuple[int, int, int, int] = (0, 0, 0, 0)
        self.window_title: str = keyword
        self.save_dir = save_dir
        # Retina 屏幕缩放因子：截图物理像素 / 逻辑点。grab() 时自动计算。
        self.scale_factor: float = 1.0

        if IS_WINDOWS:
            self._init_windows()
        else:
            logger.info("非 Windows 平台，使用 pyautogui 跨平台截图方案")

    def _init_windows(self) -> None:
        """Windows 专用：使用 windows-capture 初始化。"""
        self.bgr_buffer: np.ndarray = np.array([])
        self.windows_capture = WindowsCapture(cursor_capture=False, window_name=self.keyword)

        handles: list[int] = []

        def callback(hwnd: int, _: list[int]) -> None:
            if self.keyword in win32gui.GetWindowText(hwnd):
                handles.append(hwnd)

        win32gui.EnumWindows(callback, handles)
        if not handles:
            raise RuntimeError(f"未找到包含{self.keyword}的窗口")
        self.window_rect = win32gui.GetWindowRect(handles[0])
        self.window_title = win32gui.GetWindowText(handles[0])
        logger.info(f"找到窗口: {self.window_title}, rect={self.window_rect}")

        @self.windows_capture.event
        def on_frame_arrived(frame: Frame, capture_control: InternalCaptureControl) -> None:
            frame = frame.convert_to_bgr()
            self.bgr_buffer = frame.frame_buffer.copy()
            capture_control.stop()

        @self.windows_capture.event
        def on_closed() -> None:
            logger.info("The window was closed accidentally. Stopping capture.")

    def _refresh_window_rect(self) -> None:
        """刷新窗口位置（窗口可能移动）。"""
        if IS_WINDOWS:
            rect = _find_window_rect_windows(self.keyword)
        elif platform.system() == "Darwin":
            rect = _find_window_rect_macos(self.keyword)
        else:
            rect = None

        if rect:
            self.window_rect = rect
        else:
            # 找不到窗口时回退为全屏
            import pyautogui

            size = pyautogui.size()
            self.window_rect = (0, 0, size.width, size.height)

    def grab(self, show: bool = False, save_dir: Path | None = None) -> tuple[Image.Image, np.ndarray]:
        """截取窗口图像，返回 (PIL.Image RGB, numpy BGR)。"""
        self._refresh_window_rect()
        left, top, right, bottom = self.window_rect
        width = right - left
        height = bottom - top

        if IS_WINDOWS:
            # Windows 走 windows-capture
            self.windows_capture.start()
            assert self.bgr_buffer.size > 0, "Failed to capture window"
            frame = self.bgr_buffer
            rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb_img)
            self.scale_factor = 1.0
        else:
            # 跨平台回退：pyautogui 截图
            import pyautogui

            pil_img = pyautogui.screenshot(region=(left, top, width, height))
            image = pil_img
            frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            # 计算 Retina 缩放因子：截图物理像素 / 逻辑区域尺寸
            if width > 0 and height > 0:
                self.scale_factor = pil_img.width / width

        if show:
            image.show("Captured Window")
            cv2.imshow("frame", frame)
            cv2.waitKey(0)

        if save_dir:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = save_dir / filename
            image.save(filepath)
            logger.info(f"截图已保存: {filepath}")

        return image, frame

    def start(self, number: int = 5, interval: float = 1.0) -> None:
        save_dir = Path(self.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"开始自动截屏，间隔 {interval} 秒。")
        for _ in range(number):
            self.grab(save_dir=save_dir)
            time.sleep(interval)


screen_capture = _ScreenCapture(keyword="我的花园世界")

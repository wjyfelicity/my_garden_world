"""recognition 包初始化。

图像识别模块（颜色检测）在所有平台可用；
屏幕捕获模块仅在 Windows 平台可用，导入失败时优雅降级。
"""

from ._image_recognition import image_recognition

try:
    from ._screen_capture import screen_capture
except ImportError:
    screen_capture = None  # type: ignore

from .character_recognition import TextRecognition

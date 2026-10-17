import dataclasses
import time
from abc import ABC, abstractmethod

from loguru import logger
import pyautogui

from recognition import screen_capture


class BaseTask(ABC):
    """所有自动化任务的基类"""

    # 是否已实现具体逻辑（子类覆盖），用于 GUI 标记
    implemented: bool = False

    def __init__(self, task_name: str) -> None:
        self.task_name = task_name

    @abstractmethod
    def can_execute(self) -> bool:
        """检查前置条件：比如是否有体力、材料够不够"""
        pass

    @abstractmethod
    def execute(self) -> None:
        """执行具体逻辑"""
        pass

    def click_relative(self, x_center: float, y_center: float, relative: bool = True) -> None:
        """点击屏幕坐标。

        - relative=True: x,y 为窗口内相对坐标 (0~1)
        - relative=False: x,y 为截图上的物理像素坐标，会自动根据 scale_factor 转换为逻辑点
        """
        rect = screen_capture.window_rect
        left, top, right, bottom = rect
        win_w = right - left
        win_h = bottom - top
        scale = getattr(screen_capture, "scale_factor", 1.0)

        if relative:
            abs_x = left + int(x_center * win_w)
            abs_y = top + int(y_center * win_h)
        else:
            # x, y 是截图帧上的物理像素坐标（相对于帧左上角）
            # 转换为屏幕逻辑点坐标：先除以缩放因子，再加上窗口左上角偏移
            abs_x = left + int(x_center / scale)
            abs_y = top + int(y_center / scale)

        logger.debug(f"点击: 原始=({x_center:.1f}, {y_center:.1f}), scale={scale:.1f}, 实际=({abs_x}, {abs_y})")
        pyautogui.click(abs_x, abs_y)
        time.sleep(0.2)  # 避免过快点击

    def close_popup(self) -> bool:
        """查找并点击一个关闭按钮（X），匹配 templates/common/close/ 下任一模板。

        返回 True 表示找到并点击了，False 表示没找到。
        """
        from recognition.character_recognition import text_recognition

        _, frame = screen_capture.grab()
        positions = text_recognition.get_text_positions(frame, subdir="common/close")
        if not positions:
            return False
        # 点击第一个匹配到的关闭按钮
        _, _, center = positions[0]
        logger.info(f"点击关闭按钮 at ({center[0]:.0f}, {center[1]:.0f})")
        self.click_relative(center[0], center[1], relative=False)
        time.sleep(0.3)
        return True

    def close_all_popups(self, max_tries: int = 3) -> int:
        """循环关闭所有弹窗，直到没有关闭按钮为止。

        返回实际关闭的弹窗数量。
        """
        closed = 0
        for _ in range(max_tries):
            if not self.close_popup():
                break
            closed += 1
        if closed > 0:
            logger.info(f"共关闭 {closed} 个弹窗")
        return closed


@dataclasses.dataclass
class _Bonus:
    experience: int = 0  # 经验
    gold_coin: int = 0  # 金币
    flower_shop_coin: int = 0  # 花坊币
    building_material: int = 0  # 建材
    silk_and_satin: int = 0  # 绸缎
    customer_order: int = 0  # 顾客订单
    resident_order: int = 0  # 居民订单
    building_material_order: int = 0  # 建材订单
    silk_and_satin_order: int = 0  # 绸缎订单


bonus = _Bonus()

import time

from loguru import logger

from base_task import BaseTask, bonus
from recognition import screen_capture
from recognition._image_recognition import image_recognition
from recognition.character_recognition import text_recognition


class CustomerOrderTask(BaseTask):
    implemented: bool = True

    def __init__(self) -> None:
        super().__init__("提交顾客订单")

    def can_execute(self) -> bool:
        # TODO: 检查仓库是否集齐订单所需物品，目前直接放行
        return True

    def execute(self):
        logger.info(">>> 执行：截图 -> 检测订单图标 -> 交付/制作")
        self.close_all_popups()  # 先清掉意外弹窗
        _, frame = screen_capture.grab()
        objs = image_recognition.detect_objects(frame)

        if not objs:
            logger.info("本轮未检测到订单图标（绿/黄/红），请确认游戏停留在顾客订单面板")
            time.sleep(2)
            return

        for name, conf, cx, cy in objs:
            if name not in ['green_check', 'yellow_exclamation', 'red_exclamation']:
                continue
            logger.info(f"检测到对象: {name} (置信度{conf:.2f}) at ({cx:.2f}, {cy:.2f})")
            logger.info(f"点击订单 at ({cx:.2f}, {cy:.2f})")
            self.click_relative(cx, cy, relative=False)
            # time.sleep(0.5)
            match name:
                case 'green_check':
                    logger.info("状态：绿色对勾，订单直接可交付")
                    self.green_check_flow()
                case 'yellow_exclamation':
                    logger.info("状态：黄色感叹号，订单缺少材料")
                    self.yellow_exclamation_flow(objs)
                case 'red_exclamation':
                    logger.info("状态：红色感叹号，订单无法完成")
                    self.red_exclamation_flow()

        # 本轮处理完所有检测到的订单后，等待一会儿再重新扫描
        time.sleep(2)

    def recognize_and_click(self, target: str, skip: str = "", repeat: bool = False) -> bool:
        """识别并点击目标文字按钮，返回是否成功点击。"""
        for attempt in range(3):  # 最多重试 3 次
            _, frame = screen_capture.grab()
            positions = text_recognition.get_text_positions(frame, subdir="customer")
            logger.debug(f"识别到文字：{[(t, f'{c:.2f}') for t, c, _ in positions]}")
            for text, _, center in positions:
                if skip and skip in text:
                    continue
                if target not in text:
                    continue
                logger.info(f"点击 {target} at ({center[0]:.0f}, {center[1]:.0f})")
                self.click_relative(center[0], center[1], relative=False)
                if repeat:
                    self.click_relative(center[0], center[1], relative=False)
                return True
            time.sleep(0.5)
        logger.warning(f"未找到按钮: {target}")
        return False

    def green_check_flow(self):
        """绿色对勾：订单可直接交付。"""
        time.sleep(0.5)  # 等待弹窗出现
        if self.recognize_and_click("交付"):
            time.sleep(0.5)
            self.recognize_and_click("点击任意处关闭")
            bonus.customer_order += 1
            logger.info(f"顾客订单已交付，累计完成 {bonus.customer_order} 单")
        else:
            logger.warning("绿色对勾订单：未找到交付按钮，关闭弹窗后跳过")
            self.close_all_popups()

    def yellow_exclamation_flow(self, objs):
        """黄色感叹号：订单缺材料，需制作后交付。"""
        time.sleep(0.5)  # 等待弹窗出现
        if self.recognize_and_click("制作交付"):
            time.sleep(0.5)
            self.recognize_and_click("点击任意处关闭")
            bonus.customer_order += 1
            logger.info(f"顾客订单已制作并交付，累计完成 {bonus.customer_order} 单")
        else:
            logger.warning("黄色感叹号订单：未找到制作交付按钮，关闭弹窗后跳过")
            self.close_all_popups()

    def red_exclamation_flow(self):
        """红色感叹号：订单无法完成，暂时跳过。"""
        logger.info("红色感叹号订单，跳过")

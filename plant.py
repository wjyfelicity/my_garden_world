import time

from loguru import logger

from base_task import BaseTask
from recognition import screen_capture
from recognition.character_recognition import TEMPLATES_DIR, text_recognition

# 模板目录结构（按花分组）：
#   templates/plant/
#   ├── common/            通用：empty_pot / 待浇水状态 / 选择水桶浇水 / 收获
#   └── <花名>/
#       ├── 种子.png       该花的种子按钮
#       └── 成熟状态.png   该花成熟时的样子
PLANT_DIR = TEMPLATES_DIR / "plant"
COMMON_GROUP = "common"

EMPTY_POT = "empty_pot"
WATERING_STATE = "待浇水状态"
SEED_FILE = "种子"
MATURE_FILE = "成熟状态"
WATER_BUTTON = "选择水桶浇水"
HARVEST_BUTTON = "收获"


class PlantFlowerTask(BaseTask):
    implemented: bool = True

    def __init__(self, flower_list: list[str] | None = None) -> None:
        super().__init__("种花")
        # 外部指定的花名列表（来自 GUI 选择），None 表示自动发现全部
        self.flower_list: list[str] | None = flower_list

    @staticmethod
    def discover_flowers() -> list[str]:
        """发现所有可种植的花（存在 templates/plant/<花名>/种子.png）。"""
        if not PLANT_DIR.exists():
            return []
        return sorted(
            sub.name
            for sub in PLANT_DIR.iterdir()
            if sub.is_dir()
            and sub.name != COMMON_GROUP
            and (sub / f"{SEED_FILE}.png").exists()
        )

    def _flower_order(self) -> list[str]:
        """本次种植的优先顺序：优先用外部指定，否则用全部可种植的花。"""
        available = self.discover_flowers()
        if self.flower_list is None:
            return available
        ordered = [f for f in self.flower_list if f in available]
        return ordered or available

    def can_execute(self) -> bool:
        return True

    def execute(self):
        logger.info(">>> 执行：检测土地状态 -> 收获/浇水/种植")
        self.close_all_popups()  # 先清掉意外弹窗

        _, frame = screen_capture.grab()
        positions = text_recognition.get_text_positions(frame, subdir="plant", recursive=True)

        if not positions:
            logger.info("本轮未检测到可处理的土地状态")
            time.sleep(2)
            return

        # 按优先级分类：成熟收获 > 待浇水 > 空地种植
        mature = [(n, c) for n, _, c in positions if n.endswith(f"/{MATURE_FILE}")]
        watering = [c for n, _, c in positions if n == f"{COMMON_GROUP}/{WATERING_STATE}"]
        empty = [c for n, _, c in positions if n == f"{COMMON_GROUP}/{EMPTY_POT}"]

        # 每轮只处理一个动作，处理完重新截图，避免用过期坐标点击
        if mature:
            name, (cx, cy) = mature[0]
            flower = name.split("/")[0]
            logger.info(f"检测到 {flower} 成熟 at ({cx:.0f}, {cy:.0f})，优先收获")
            self.harvest_flow(cx, cy, flower)
        elif watering:
            cx, cy = watering[0]
            logger.info(f"检测到待浇水 at ({cx:.0f}, {cy:.0f})，优先浇水")
            self.water_flow(cx, cy)
        elif empty:
            cx, cy = empty[0]
            logger.info(f"检测到空地 at ({cx:.0f}, {cy:.0f})，开始种植")
            self.plant_seed_flow(cx, cy, self._flower_order())
        else:
            logger.info("本轮无可用动作")

        time.sleep(2)

    def scan(self) -> dict[str, tuple[int, int]]:
        """截屏并返回 {模板名: 中心点} 映射。"""
        _, frame = screen_capture.grab()
        positions = text_recognition.get_text_positions(frame, subdir="plant", recursive=True)
        return {name: center for name, _, center in positions}

    def click_template(self, name: str, retries: int = 3) -> bool:
        """查找并点击指定模板，返回是否成功。"""
        for _ in range(retries):
            found = self.scan()
            if name in found:
                cx, cy = found[name]
                logger.info(f"点击 {name} at ({cx:.0f}, {cy:.0f})")
                self.click_relative(cx, cy, relative=False)
                return True
            time.sleep(0.5)
        logger.warning(f"未找到: {name}")
        return False

    def plant_seed_flow(self, cx: float, cy: float, flowers: list[str]):
        """空地流程：点击空地 -> 按顺序选择第一个有货的种子。"""
        logger.info(f"→ 种植流程：点击空地 -> 选择种子（顺序: {flowers}）")
        self.click_relative(cx, cy, relative=False)
        time.sleep(0.5)

        for _ in range(3):  # 等待种子面板出现
            found = self.scan()
            for flower in flowers:
                key = f"{flower}/{SEED_FILE}"
                if key in found:
                    fx, fy = found[key]
                    logger.info(f"点击种子 {key} at ({fx:.0f}, {fy:.0f})")
                    self.click_relative(fx, fy, relative=False)
                    logger.info(f"✓ 已种植: {flower}")
                    return
            time.sleep(0.5)

        logger.warning("✗ 未找到任何可用种子，关闭弹窗后跳过")
        self.close_all_popups()

    def water_flow(self, cx: float, cy: float):
        """待浇水流程：点击植物 -> 选择水桶浇水。"""
        logger.info("→ 浇水流程：点击植物 -> 选择水桶浇水")
        self.click_relative(cx, cy, relative=False)
        time.sleep(0.5)
        if self.click_template(f"{COMMON_GROUP}/{WATER_BUTTON}"):
            logger.info("✓ 已浇水")
        else:
            logger.warning("✗ 未找到浇水按钮，关闭弹窗后跳过")
            self.close_all_popups()

    def harvest_flow(self, cx: float, cy: float, flower: str):
        """成熟流程：点击成熟植物 -> 收获。"""
        logger.info(f"→ 收获流程：点击 {flower} -> 收获")
        self.click_relative(cx, cy, relative=False)
        time.sleep(0.5)
        if self.click_template(f"{COMMON_GROUP}/{HARVEST_BUTTON}"):
            logger.info(f"✓ 已收获: {flower}")
        else:
            logger.warning("✗ 未找到收获按钮，关闭弹窗后跳过")
            self.close_all_popups()

import time

from loguru import logger

from base_task import BaseTask


class CollectBucketTask(BaseTask):
    def __init__(self):
        super().__init__("收集水桶")

    def can_execute(self) -> bool:
        return False  # TODO: 伪代码，检查水桶

    def execute(self):
        logger.info(">>> 执行：点击水桶 -> 收获 -> 存入仓库")


class CollectPearlTask(BaseTask):
    def __init__(self) -> None:
        super().__init__("收集珍珠")

    def can_execute(self) -> bool:
        return True  # TODO: 伪代码

    def execute(self) -> None:
        # TODO: 伪代码
        logger.info(">>> 执行：点击珍珠面板 -> 雇佣采集 -> 收获")
        time.sleep(2 * 60 * 60)  # 等待2小时

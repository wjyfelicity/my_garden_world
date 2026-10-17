from base_task import BaseTask


class ResidentOrderTask(BaseTask):
    def __init__(self) -> None:
        super().__init__("提交居民订单")

    def can_execute(self) -> bool:
        return False  # TODO: 伪代码

    def execute(self):
        # TODO: 伪代码
        print(">>> 执行：打开居民订单面板 -> 提交")

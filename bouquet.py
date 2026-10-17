from base_task import BaseTask


class AssembleBouquetTask(BaseTask):
    def __init__(self) -> None:
        super().__init__("task_name")

    def can_execute(self) -> bool:
        return False  # TODO: 伪代码

    def execute(self):
        # TODO: 伪代码
        print(">>> 执行：打开花束面板 -> 设定数目 -> 点击组装")


class DisplayBouquetTask(BaseTask):
    def __init__(self) -> None:
        super().__init__("上架花艺")

    def can_execute(self) -> bool:
        return False  # TODO: 伪代码

    def execute(self):
        # TODO: 伪代码
        print(">>> 执行：打开花架面板 -> 上架花艺")

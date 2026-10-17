import traceback

from loguru import logger

from base_task import BaseTask
from bouquet import AssembleBouquetTask, DisplayBouquetTask
from collect import CollectBucketTask, CollectPearlTask
from customer import CustomerOrderTask
from plant import PlantFlowerTask
from resident import ResidentOrderTask


class Automation:
    def __init__(self, tasks: list[BaseTask] | None = None) -> None:
        all_tasks: list[BaseTask] = [
            AssembleBouquetTask(),
            DisplayBouquetTask(),
            CollectBucketTask(),
            CollectPearlTask(),
            CustomerOrderTask(),
            PlantFlowerTask(),
            ResidentOrderTask(),
        ]
        self.tasks: list[BaseTask] = tasks if tasks is not None else all_tasks
        self._running: bool = True

    def stop(self) -> None:
        """请求停止主循环。"""
        self._running = False

    def mainloop(self):
        self._running = True
        while self._running:
            # TODO: 【轮询】伪代码，循环检查每个任务是否可执行，并执行
            for task in self.tasks:
                if not self._running:
                    break
                if task.can_execute():
                    task.execute()
        # 后期考虑：例如种花需要等候，有一定的时间空闲，可以考虑类似IO中的异步或者者多线程的方式来处理等待时间，提升效率

    def run(self) -> None:
        while True:
            try:
                self.mainloop()
            except KeyboardInterrupt:
                cmd = input(">>> Terminated by user. Do you want to restart? (y/N): ")
            except Exception as e:
                logger.error(f"Error details: {e}", exc_info=True)
                traceback.print_exception(e, colorize=True)  # type: ignore
                cmd = input(">>> Error occurred, do you want to restart? (y/N): ")
            except BaseException as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                traceback.print_exception(e, colorize=True)  # type: ignore
                cmd = input(">>> Unexpected error occurred, do you want to restart? (y/N): ")
            if cmd.lower() != 'y':
                logger.info("Exiting...")
                return
            logger.info("Restarting...")

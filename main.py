from automation import Automation
from base_task import BaseTask
from bouquet import AssembleBouquetTask, DisplayBouquetTask
from collect import CollectBucketTask, CollectPearlTask
from customer import CustomerOrderTask
from plant import PlantFlowerTask
from resident import ResidentOrderTask


ALL_TASKS: list[BaseTask] = [
    AssembleBouquetTask(),
    DisplayBouquetTask(),
    CollectBucketTask(),
    CollectPearlTask(),
    CustomerOrderTask(),
    PlantFlowerTask(),
    ResidentOrderTask(),
]


def select_tasks() -> list[BaseTask]:
    """交互式选择要执行的任务。"""
    print("=" * 50)
    print("可选任务列表：")
    print("-" * 50)
    for i, task in enumerate(ALL_TASKS, start=1):
        print(f"  {i}. {task.__class__.__name__}  ({task.task_name})")
    print("-" * 50)
    print("输入任务序号，多个用空格分隔（例如: 1 3 5）")
    print("直接回车 = 执行全部任务")
    print("=" * 50)

    raw = input(">>> 请选择: ").strip()
    if not raw:
        return list(ALL_TASKS)

    try:
        indices = [int(x) for x in raw.split()]
    except ValueError:
        print("输入无效，将执行全部任务。")
        return list(ALL_TASKS)

    selected: list[BaseTask] = []
    for idx in indices:
        if 1 <= idx <= len(ALL_TASKS):
            selected.append(ALL_TASKS[idx - 1])
        else:
            print(f"忽略无效序号: {idx}")

    if not selected:
        print("未选中任何有效任务，将执行全部任务。")
        return list(ALL_TASKS)

    print(f"\n已选择 {len(selected)} 个任务:")
    for task in selected:
        print(f"  - {task.__class__.__name__}")
    return selected


def main() -> None:
    tasks = select_tasks()
    robot = Automation(tasks=tasks)
    robot.run()


if __name__ == '__main__':
    main()

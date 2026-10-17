"""图形化操作面板。

使用 Tkinter（Python 内置）构建，无需额外依赖。
功能：
- 多选任务
- 选择要种的花（多选自适应）
- 启动 / 停止自动化
- 实时日志输出
"""
import queue
import threading
import tkinter as tk
from tkinter import scrolledtext

from loguru import logger

from automation import Automation
from main import ALL_TASKS
from plant import PlantFlowerTask


class GuiLogSink:
    """将 loguru 日志转发到 Tkinter 文本框的 sink。"""

    def __init__(self, log_queue: queue.Queue) -> None:
        self.log_queue = log_queue

    def write(self, message) -> None:
        self.log_queue.put(message)

    def flush(self) -> None:
        pass


class AutomationGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("花园世界自动化")
        self.root.geometry("760x640")

        self.automation: Automation | None = None
        self.worker_thread: threading.Thread | None = None
        self.log_queue: queue.Queue = queue.Queue()
        self.task_vars: list[tk.BooleanVar] = []
        self.flower_vars: dict[str, tk.BooleanVar] = {}

        self._build_ui()
        self._setup_logger()
        self._poll_logs()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        # --- 任务选择区 ---
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)

        tk.Label(top_frame, text="选择要执行的任务：", font=("", 12, "bold")).pack(anchor=tk.W)

        check_frame = tk.Frame(top_frame)
        check_frame.pack(fill=tk.X, pady=5)

        col_count = 2
        for i, task in enumerate(ALL_TASKS):
            # 已实现的任务默认勾选，未实现的默认不勾选
            var = tk.BooleanVar(value=task.implemented)
            self.task_vars.append(var)
            row = i // col_count
            col = i % col_count
            label = f"{task.task_name} ({task.__class__.__name__})"
            if not task.implemented:
                label += "  [未实现]"
            cb = tk.Checkbutton(
                check_frame,
                text=label,
                variable=var,
                fg="gray" if not task.implemented else "black",
            )
            cb.grid(row=row, column=col, sticky=tk.W, padx=10)

        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="全选", command=self._select_all).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="全不选", command=self._select_none).pack(side=tk.LEFT, padx=4)

        # --- 种花选择区 ---
        seed_frame = tk.LabelFrame(self.root, text="种花 - 选择要种的花（可多选，按勾选顺序种植）", padx=10, pady=5)
        seed_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        available_flowers = PlantFlowerTask.discover_flowers()
        if available_flowers:
            self.flower_check_frame = tk.Frame(seed_frame)
            self.flower_check_frame.pack(fill=tk.X)
            cols = 4
            for i, flower in enumerate(available_flowers):
                var = tk.BooleanVar(value=True)
                self.flower_vars[flower] = var
                r, c = divmod(i, cols)
                cb = tk.Checkbutton(self.flower_check_frame, text=flower, variable=var)
                cb.grid(row=r, column=c, sticky=tk.W, padx=8, pady=2)
            tk.Label(
                seed_frame,
                text="提示：勾选多个时，按从左到右的顺序优先种植（库存不足时自动尝试下一种）",
                fg="gray", font=("", 9),
            ).pack(anchor=tk.W, pady=(4, 0))
        else:
            tk.Label(seed_frame, text="未检测到种子模板（templates/plant/<花名>/种子.png）", fg="gray").pack(anchor=tk.W)

        # --- 控制按钮 ---
        ctrl_frame = tk.Frame(self.root, padx=10, pady=5)
        ctrl_frame.pack(fill=tk.X)

        self.start_btn = tk.Button(
            ctrl_frame, text="▶ 启动", command=self._start,
            bg="#4CAF50", fg="white", font=("", 11, "bold"),
            width=12,
        )
        self.start_btn.pack(side=tk.LEFT, padx=4)

        self.stop_btn = tk.Button(
            ctrl_frame, text="■ 停止", command=self._stop,
            bg="#F44336", fg="white", font=("", 11, "bold"),
            width=12, state=tk.DISABLED,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=4)

        self.status_label = tk.Label(ctrl_frame, text="状态：未运行", fg="gray", font=("", 11))
        self.status_label.pack(side=tk.LEFT, padx=20)

        # --- 日志区 ---
        log_frame = tk.LabelFrame(self.root, text="运行日志", padx=5, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _setup_logger(self) -> None:
        logger.add(GuiLogSink(self.log_queue), format="{time:HH:mm:ss} | {level:<8} | {message}")

    def _poll_logs(self) -> None:
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_text.insert(tk.END, msg)
            self.log_text.see(tk.END)
        self.root.after(100, self._poll_logs)

    def _select_all(self) -> None:
        for var in self.task_vars:
            var.set(True)

    def _select_none(self) -> None:
        for var in self.task_vars:
            var.set(False)

    def _get_selected_flowers(self) -> list[str]:
        """按勾选顺序返回选中的花名列表。"""
        return [flower for flower, var in self.flower_vars.items() if var.get()]

    def _get_selected_tasks(self):
        selected = []
        for task, var in zip(ALL_TASKS, self.task_vars):
            if var.get():
                # 如果是种花任务，传入选中的花名列表
                if isinstance(task, PlantFlowerTask):
                    flowers = self._get_selected_flowers()
                    task.flower_list = flowers if flowers else None
                selected.append(task)
        return selected

    def _start(self) -> None:
        tasks = self._get_selected_tasks()
        if not tasks:
            logger.warning("请至少选择一个任务")
            return

        self.automation = Automation(tasks=tasks)
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="状态：运行中", fg="#4CAF50")
        logger.info(f"启动自动化，已选任务: {[t.task_name for t in tasks]}")

        def run_worker():
            try:
                self.automation.mainloop()
            except Exception as e:
                logger.error(f"运行出错: {e}")
            finally:
                self.root.after(0, self._on_stopped)

        self.worker_thread = threading.Thread(target=run_worker, daemon=True)
        self.worker_thread.start()

    def _stop(self) -> None:
        if self.automation:
            logger.info("正在停止...")
            self.automation.stop()

    def _on_stopped(self) -> None:
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="状态：已停止", fg="#F44336")
        logger.info("自动化已停止")

    def _on_close(self) -> None:
        if self.automation:
            self.automation.stop()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    AutomationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

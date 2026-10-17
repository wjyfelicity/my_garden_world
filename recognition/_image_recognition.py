"""基于 OpenCV 模板匹配的图标识别模块。

替代原来的 YOLO 模型方案和 HSV 颜色检测方案，直接用模板图片做 matchTemplate，
准确率最高、不会误检。

图标模板放置在 templates/ 目录下，文件名即识别类别名：
    templates/green_check.png       （绿色对勾）
    templates/yellow_exclamation.png  （黄色感叹号）
    templates/red_exclamation.png     （红色感叹号，可选）
"""

from pathlib import Path

import cv2
import numpy as np
from cv2.typing import MatLike
from PIL import Image

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "icons"

# 需要识别的图标类别（按此顺序匹配）
ICON_NAMES = ["green_check", "yellow_exclamation", "red_exclamation"]

# 模板匹配相似度阈值
MATCH_THRESHOLD = 0.8


class _ImageRecognition:
    def __init__(self, model: str | None = None) -> None:
        # 不再加载 YOLO 模型，仅保留参数以兼容旧调用方式
        self.model = None
        self._template_cache: dict[str, np.ndarray] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """加载图标模板，缓存到内存。"""
        if not TEMPLATES_DIR.exists():
            return
        for name in ICON_NAMES:
            tpl_path = TEMPLATES_DIR / f"{name}.png"
            if tpl_path.exists():
                tpl = cv2.imread(str(tpl_path), cv2.IMREAD_COLOR)
                if tpl is not None:
                    self._template_cache[name] = tpl

    def detect_objects(
        self, image: MatLike | Image.Image, show: bool = False
    ) -> list[tuple[str, float, float, float]]:
        """检测图像中的图标，返回 [(name, conf, cx, cy), ...]。

        与原 YOLO 版本接口保持一致。
        """
        if image is None:
            return []

        # 统一转为 OpenCV 的 BGR numpy 数组
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        objs: list[tuple[str, float, float, float]] = []

        for name, tpl in self._template_cache.items():
            th, tw = tpl.shape[:2]
            ih, iw = image.shape[:2]
            if th > ih or tw > iw:
                continue

            result = cv2.matchTemplate(image, tpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val >= MATCH_THRESHOLD:
                cx = max_loc[0] + tw // 2
                cy = max_loc[1] + th // 2
                objs.append((name, float(max_val), float(cx), float(cy)))

        if show:
            annotated = image.copy()
            for name, conf, cx, cy in objs:
                cv2.circle(annotated, (int(cx), int(cy)), 10, (0, 255, 0), 2)
                cv2.putText(
                    annotated, f"{name}({conf:.2f})", (int(cx) + 12, int(cy)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2,
                )
            cv2.imshow("template_match", annotated)
            cv2.waitKey(0)

        return objs


image_recognition = _ImageRecognition()

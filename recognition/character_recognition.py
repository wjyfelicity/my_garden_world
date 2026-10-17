"""文字识别模块。

主方案：OpenCV 模板匹配（matchTemplate）—— 对固定按钮文字准确率高、速度快。
回退方案：RapidOCR —— 当模板不存在时使用。

模板图片放置在 templates/ 目录下，文件名即匹配的目标文字，例如：
    templates/交付.png
    templates/前往制作.png
    templates/制作.png
    templates/暂时没货.png
"""

from pathlib import Path

import cv2
import numpy as np
from cv2.typing import MatLike
from loguru import logger
from PIL import Image

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
# 模板匹配相似度阈值，低于此值认为未匹配到
MATCH_THRESHOLD = 0.8


class TextRecognition:
    def __init__(self) -> None:
        # 缓存结构: {subdir: {name: template_array}}
        self._template_cache: dict[str, dict[str, np.ndarray]] = {}
        self._ocr_engine = None  # 懒加载 OCR，仅在模板匹配不可用时初始化

    def _load_templates(self, subdir: str = "", recursive: bool = False) -> dict[str, np.ndarray]:
        """加载 templates/<subdir>/ 目录下的模板图片，缓存到内存。

        - subdir="" 表示加载 templates/ 根目录下的模板
        - subdir="customer" 加载 templates/customer/ 下的模板
        - recursive=True 时递归加载子目录，模板名用相对路径（如 "粉鹤芋/种子"）
        """
        cache_key = f"{subdir}::{'r' if recursive else 'f'}"
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        tpl_dir = TEMPLATES_DIR / subdir if subdir else TEMPLATES_DIR
        if not tpl_dir.exists():
            logger.warning(f"模板目录不存在: {tpl_dir}，将使用 OCR 回退")
            self._template_cache[cache_key] = {}
            return {}

        templates: dict[str, np.ndarray] = {}
        tpl_paths = tpl_dir.rglob("*.png") if recursive else tpl_dir.glob("*.png")
        for tpl_path in tpl_paths:
            # 递归模式用相对路径作为模板名，非递归模式仅用文件名
            if recursive:
                name = tpl_path.relative_to(tpl_dir).with_suffix("").as_posix()
            else:
                name = tpl_path.stem
            tpl = cv2.imread(str(tpl_path), cv2.IMREAD_COLOR)
            if tpl is not None:
                templates[name] = tpl
                logger.info(f"加载模板 [{subdir or 'root'}]: {name} ({tpl.shape[1]}x{tpl.shape[0]})")

        if not templates:
            logger.warning(f"模板目录为空: {tpl_dir}，将使用 OCR 回退")
        self._template_cache[cache_key] = templates
        return templates

    def _get_ocr_engine(self):
        """懒加载 RapidOCR 引擎。"""
        if self._ocr_engine is None:
            from rapidocr_onnxruntime import RapidOCR

            self._ocr_engine = RapidOCR()
        return self._ocr_engine

    def get_text_positions(
        self,
        image: MatLike | Image.Image,
        subdir: str = "",
        show: bool = False,
        recursive: bool = False,
    ) -> list[tuple[str, float, tuple[int, int]]]:
        """识别图像中的文字位置，返回 [(text, conf, (cx, cy)), ...]。

        - subdir: 指定从 templates/<subdir>/ 加载模板，默认加载根目录
        - recursive: 是否递归加载子目录模板（模板名带相对路径前缀）
        """
        if image is None:
            return []

        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # 优先模板匹配
        templates = self._load_templates(subdir, recursive=recursive)
        if templates:
            return self._match_templates(image, templates, show=show)

        # 回退 OCR
        return self._ocr_recognize(image, show=show)

    def _match_templates(
        self, image: np.ndarray, templates: dict[str, np.ndarray], show: bool = False
    ) -> list[tuple[str, float, tuple[int, int]]]:
        """在图像中匹配所有模板，返回每个匹配的中心点。"""
        results: list[tuple[str, float, tuple[int, int]]] = []

        for name, tpl in templates.items():
            th, tw = tpl.shape[:2]
            ih, iw = image.shape[:2]
            # 模板比图像还大，跳过
            if th > ih or tw > iw:
                continue

            result = cv2.matchTemplate(image, tpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val >= MATCH_THRESHOLD:
                cx = max_loc[0] + tw // 2
                cy = max_loc[1] + th // 2
                results.append((name, float(max_val), (cx, cy)))
                if show:
                    logger.info(f"模板匹配: '{name}' 置信度={max_val:.2f} at ({cx}, {cy})")

        if show:
            annotated = image.copy()
            for name, conf, (cx, cy) in results:
                cv2.circle(annotated, (cx, cy), 10, (0, 255, 0), 2)
                cv2.putText(
                    annotated, f"{name}({conf:.2f})", (cx + 12, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
                )
            cv2.imshow("template_match", annotated)
            cv2.waitKey(0)

        return results

    def _ocr_recognize(
        self, image: np.ndarray, show: bool = False
    ) -> list[tuple[str, float, tuple[int, int]]]:
        """OCR 回退方案。"""
        engine = self._get_ocr_engine()
        result, _ = engine(image)
        if not result:
            return []

        positions: list[tuple[str, float, tuple[int, int]]] = []
        for box, text, conf in result:
            x_center = int((box[0][0] + box[2][0]) / 2)
            y_center = int((box[0][1] + box[2][1]) / 2)
            positions.append((text, float(conf), (x_center, y_center)))
            if show:
                logger.info(f"OCR: '{text}' 置信度={conf:.2f} at ({x_center}, {y_center})")

        if show:
            annotated = image.copy()
            for box, text, conf in result:
                cv2.rectangle(annotated, tuple(box[0]), tuple(box[2]), (0, 255, 0), 2)
                cv2.putText(annotated, text, tuple(box[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.imshow("ocr_result", annotated)
            cv2.waitKey(0)

        return positions


text_recognition = TextRecognition()

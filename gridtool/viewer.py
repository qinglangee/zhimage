# -*- coding: utf-8 -*-
"""单图查看弹窗：滚轮缩放，底部实时显示缩放比例。"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton,
)

from .image_utils import load_pixmap


class ImageViewerDialog(QDialog):
    """点击预览图后弹出的独立查看窗口。

    - 滚轮向上放大、向下缩小（以 1.25 倍步进）
    - 底部状态栏实时显示缩放比例
    - 「适应窗口」恢复按窗口大小缩放，「原始大小」恢复 100%
    """

    MIN_SCALE = 0.02
    MAX_SCALE = 40.0
    ZOOM_STEP = 1.25

    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.setWindowTitle(f"查看图片 - {self.path.name}")
        self.resize(900, 700)

        self.pixmap = load_pixmap(self.path)
        self.scale = 1.0
        self.fit_mode = True  # 初始为适应窗口

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: #202020;")
        self.scroll.setWidget(self.image_label)
        layout.addWidget(self.scroll, 1)

        # 底部状态栏：缩放比例 + 操作按钮
        bottom = QHBoxLayout()
        self.zoom_label = QLabel()
        self.zoom_label.setStyleSheet("font-weight: bold;")
        bottom.addWidget(self.zoom_label, 1)

        fit_btn = QPushButton("适应窗口")
        fit_btn.clicked.connect(self.fit_to_window)
        original_btn = QPushButton("原始大小")
        original_btn.clicked.connect(self.actual_size)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(fit_btn)
        bottom.addWidget(original_btn)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

        self._apply()

    # ---------- 缩放逻辑 ----------

    def _fit_scale(self) -> float:
        viewport = self.scroll.viewport().size()
        w = max(viewport.width() - 4, 1)
        h = max(viewport.height() - 4, 1)
        return min(w / self.pixmap.width(), h / self.pixmap.height())

    def fit_to_window(self):
        self.fit_mode = True
        self._apply()

    def actual_size(self):
        self.fit_mode = False
        self.scale = 1.0
        self._apply()

    def wheelEvent(self, event):
        if self.pixmap.isNull():
            return
        factor = self.ZOOM_STEP if event.angleDelta().y() > 0 else 1 / self.ZOOM_STEP
        base = self._fit_scale() if self.fit_mode else self.scale
        new_scale = min(max(base * factor, self.MIN_SCALE), self.MAX_SCALE)
        self.fit_mode = False
        self.scale = new_scale
        self._apply()
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.fit_mode:
            self._apply()

    # ---------- 显示刷新 ----------

    def _apply(self):
        scale = self._fit_scale() if self.fit_mode else self.scale
        scale = min(max(scale, self.MIN_SCALE), self.MAX_SCALE)
        width = max(1, round(self.pixmap.width() * scale))
        height = max(1, round(self.pixmap.height() * scale))
        self.image_label.setPixmap(
            self.pixmap.scaled(
                width, height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        if not self.fit_mode:
            self.scale = scale
        self.zoom_label.setText(
            f"缩放比例： {scale * 100:.1f}%"
            f"　|　原始尺寸： {self.pixmap.width()}×{self.pixmap.height()}"
        )

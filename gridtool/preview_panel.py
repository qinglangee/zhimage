# -*- coding: utf-8 -*-
"""拖拽区与多图预览面板。点击缩略图弹出单图查看窗口。"""

from pathlib import Path

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout, QScrollArea, QFrame,
)

from .image_utils import load_pixmap
from .viewer import ImageViewerDialog


class DropArea(QFrame):
    """支持拖入图片文件的文件列表区域。"""

    def __init__(self, on_files):
        super().__init__()
        self.on_files = on_files
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(74)
        self.setStyleSheet("""
            DropArea {
                border: 2px dashed #8b98a8;
                border-radius: 8px;
                background: palette(alternate-base);
            }
        """)
        layout = QVBoxLayout(self)
        self.label = QLabel("将图片文件拖到这里\n也可以点击下方「添加图片」")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.label)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                paths.append(Path(url.toLocalFile()))
        self.on_files(paths)
        event.acceptProposedAction()


class ClickableLabel(QLabel):
    """可点击的图片标签，点击时发出 clicked 信号。"""

    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class PreviewPanel(QWidget):
    """可滚动的多图片预览面板。点击缩略图弹出查看窗口。"""

    def __init__(self, title):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        self.heading = QLabel(title)
        self.heading.setStyleSheet("font-weight: bold;")
        outer.addWidget(self.heading)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid.setSpacing(10)
        self.scroll.setWidget(self.container)
        outer.addWidget(self.scroll, 1)

    def clear(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def set_images(self, entries):
        """
        entries: [(Path, optional description)]
        """
        self.clear()
        if not entries:
            empty = QLabel("暂无图片")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(empty, 0, 0)
            return

        columns = 3
        for index, entry in enumerate(entries):
            path = entry[0]
            description = entry[1] if len(entry) > 1 else path.name
            self.grid.addWidget(
                self._make_card(path, description),
                index // columns, index % columns,
            )

    def _make_card(self, path: Path, description: str) -> QWidget:
        card = QWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(5, 5, 5, 5)
        card_layout.setSpacing(4)

        image_label = ClickableLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setMinimumSize(150, 115)
        image_label.setMaximumSize(240, 180)
        image_label.setCursor(Qt.CursorShape.PointingHandCursor)
        image_label.setStyleSheet(
            "background: palette(base); border: 1px solid palette(mid);"
        )
        try:
            pixmap = load_pixmap(path)
            image_label.setPixmap(
                pixmap.scaled(
                    QSize(230, 165),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            image_label.setToolTip("点击查看大图")
            image_label.clicked.connect(
                lambda checked=False, p=path: self.open_viewer(p)
            )
        except Exception as exc:
            image_label.setText(f"无法预览\n{exc}")

        name_label = QLabel(description)
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setToolTip(str(path))
        name_label.setMaximumWidth(240)

        card_layout.addWidget(image_label)
        card_layout.addWidget(name_label)
        card.setStyleSheet(
            "QWidget { border: 1px solid palette(mid); border-radius: 5px; }"
        )
        return card

    def open_viewer(self, path: Path):
        ImageViewerDialog(path, self).exec()

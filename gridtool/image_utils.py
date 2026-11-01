# -*- coding: utf-8 -*-
"""图片加载与 Pillow <-> Qt 转换工具。"""

from pathlib import Path

from PIL import Image, ImageOps
from PySide6.QtGui import QPixmap, QImage

SUPPORTED = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tif", ".tiff"}


def pil_to_pixmap(image: Image.Image) -> QPixmap:
    """将 Pillow 图片转换为 Qt Pixmap，用于预览。"""
    rgba = image.convert("RGBA")
    data = rgba.tobytes("raw", "RGBA")
    qimage = QImage(data, rgba.width, rgba.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimage.copy())


def load_pixmap(path: Path) -> QPixmap:
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        return pil_to_pixmap(im)

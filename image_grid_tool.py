#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片网格标线 / 分割工具
依赖：pip install PySide6 Pillow
运行：python image_grid_tool.py

代码结构（gridtool 包）：
- image_utils   图片加载与 Qt 转换工具
- processing    网格标线 / 分割的核心图像处理逻辑
- viewer        单图查看弹窗（滚轮缩放、显示缩放比例）
- preview_panel 拖拽区与多图预览面板
- main_window   主窗口
"""

import sys

from PySide6.QtWidgets import QApplication

from gridtool.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

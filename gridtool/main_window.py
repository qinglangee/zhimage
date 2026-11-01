# -*- coding: utf-8 -*-
"""主窗口：文件选择、参数设置、预览与处理调度。"""

from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QLineEdit,
    QFileDialog, QSpinBox, QCheckBox, QColorDialog, QHBoxLayout, QVBoxLayout,
    QGridLayout, QGroupBox, QMessageBox, QSplitter, QFormLayout,
    QApplication,
)

from .config import load_config, save_config
from .image_utils import SUPPORTED
from .preview_panel import DropArea, PreviewPanel
from .processing import process_image


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图片网格标线与分割工具")
        self.resize(1180, 820)

        self.source_files = []
        self.output_files = []
        self.line_color = "#ff3030"

        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)

        # 文件输入
        file_group = QGroupBox("图片文件")
        file_layout = QVBoxLayout(file_group)
        self.drop_area = DropArea(self.add_files)
        file_layout.addWidget(self.drop_area)

        file_buttons = QHBoxLayout()
        add_btn = QPushButton("添加图片")
        add_btn.clicked.connect(self.choose_files)
        remove_btn = QPushButton("清空列表")
        remove_btn.clicked.connect(self.clear_files)
        self.files_label = QLabel("尚未选择图片")
        file_buttons.addWidget(add_btn)
        file_buttons.addWidget(remove_btn)
        file_buttons.addWidget(self.files_label, 1)
        file_layout.addLayout(file_buttons)
        main.addWidget(file_group)

        # 参数设置
        settings = QGroupBox("网格与输出设置")
        settings_layout = QGridLayout(settings)

        grid_box = QGroupBox("网格")
        grid_form = QFormLayout(grid_box)
        self.rows = QSpinBox()
        self.rows.setRange(1, 500)
        self.rows.setValue(5)
        self.cols = QSpinBox()
        self.cols.setRange(1, 500)
        self.cols.setValue(7)
        grid_form.addRow("行数：", self.rows)
        grid_form.addRow("列数：", self.cols)

        margin_box = QGroupBox("四边 Margin（像素）")
        margin_grid = QGridLayout(margin_box)
        self.margin_top = self.make_margin_spin()
        self.margin_bottom = self.make_margin_spin()
        self.margin_left = self.make_margin_spin()
        self.margin_right = self.make_margin_spin()
        margin_grid.addWidget(QLabel("上："), 0, 0)
        margin_grid.addWidget(self.margin_top, 0, 1)
        margin_grid.addWidget(QLabel("下："), 0, 2)
        margin_grid.addWidget(self.margin_bottom, 0, 3)
        margin_grid.addWidget(QLabel("左："), 1, 0)
        margin_grid.addWidget(self.margin_left, 1, 1)
        margin_grid.addWidget(QLabel("右："), 1, 2)
        margin_grid.addWidget(self.margin_right, 1, 3)

        line_box = QGroupBox("分隔线")
        line_form = QFormLayout(line_box)
        self.line_width = QSpinBox()
        self.line_width.setRange(1, 30)
        self.line_width.setValue(2)
        self.color_button = QPushButton()
        self.update_color_button()
        self.color_button.clicked.connect(self.choose_color)
        self.endpoints_check = QCheckBox("只画端点（3px）")
        self.endpoints_check.setChecked(False)
        line_form.addRow("线宽：", self.line_width)
        line_form.addRow("颜色：", self.color_button)
        line_form.addRow("", self.endpoints_check)

        output_box = QGroupBox("输出")
        output_layout = QVBoxLayout(output_box)
        self.split_check = QCheckBox("分割图片（不勾选则只输出标线图片）")
        self.split_check.setChecked(False)
        output_layout.addWidget(self.split_check)
        output_dir_row = QHBoxLayout()
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("选择输出目录（默认：首张图片目录下的 output）")
        browse_output = QPushButton("浏览…")
        browse_output.clicked.connect(self.choose_output_dir)
        output_dir_row.addWidget(self.output_dir, 1)
        output_dir_row.addWidget(browse_output)
        output_layout.addLayout(output_dir_row)

        settings_layout.addWidget(grid_box, 0, 0)
        settings_layout.addWidget(margin_box, 0, 1)
        settings_layout.addWidget(line_box, 0, 2)
        settings_layout.addWidget(output_box, 1, 0, 1, 3)
        main.addWidget(settings)

        # 预览选项和执行
        action_row = QHBoxLayout()
        self.show_source_check = QCheckBox("显示源图片")
        self.show_source_check.setChecked(True)
        self.show_output_check = QCheckBox("显示输出图片")
        self.show_output_check.setChecked(True)
        self.show_source_check.toggled.connect(self.toggle_source_preview)
        self.show_output_check.toggled.connect(self.toggle_output_preview)
        action_row.addWidget(self.show_source_check)
        action_row.addWidget(self.show_output_check)
        action_row.addStretch(1)
        self.process_button = QPushButton("开始处理")
        self.process_button.setMinimumWidth(130)
        self.process_button.clicked.connect(self.process_images)
        action_row.addWidget(self.process_button)
        main.addLayout(action_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.source_preview = PreviewPanel("源图片", on_delete=self.remove_source)
        self.output_preview = PreviewPanel("输出图片")
        splitter.addWidget(self.source_preview)
        splitter.addWidget(self.output_preview)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main.addWidget(splitter, 1)

        self.statusBar().showMessage("就绪")
        self.apply_settings(load_config())

    # ---------- 配置持久化 ----------

    def collect_settings(self) -> dict:
        return {
            "rows": self.rows.value(),
            "cols": self.cols.value(),
            "margin_top": self.margin_top.value(),
            "margin_bottom": self.margin_bottom.value(),
            "margin_left": self.margin_left.value(),
            "margin_right": self.margin_right.value(),
            "line_width": self.line_width.value(),
            "line_color": self.line_color,
            "endpoints_only": self.endpoints_check.isChecked(),
            "split": self.split_check.isChecked(),
            "output_dir": self.output_dir.text().strip(),
            "show_source": self.show_source_check.isChecked(),
            "show_output": self.show_output_check.isChecked(),
            "source_files": [str(p) for p in self.source_files],
        }

    def apply_settings(self, settings: dict):
        if not settings:
            return
        self.rows.setValue(settings.get("rows", self.rows.value()))
        self.cols.setValue(settings.get("cols", self.cols.value()))
        self.margin_top.setValue(settings.get("margin_top", 0))
        self.margin_bottom.setValue(settings.get("margin_bottom", 0))
        self.margin_left.setValue(settings.get("margin_left", 0))
        self.margin_right.setValue(settings.get("margin_right", 0))
        self.line_width.setValue(settings.get("line_width", self.line_width.value()))
        self.line_color = settings.get("line_color", self.line_color)
        self.update_color_button()
        self.endpoints_check.setChecked(bool(settings.get("endpoints_only", False)))
        self.split_check.setChecked(bool(settings.get("split", False)))
        self.output_dir.setText(settings.get("output_dir", ""))
        self.show_source_check.setChecked(bool(settings.get("show_source", True)))
        self.show_output_check.setChecked(bool(settings.get("show_output", True)))
        # 恢复上次添加且仍然存在的图片
        restored = [Path(p) for p in settings.get("source_files", [])
                    if Path(p).is_file()]
        if restored:
            self.add_files(restored)

    def closeEvent(self, event):
        save_config(self.collect_settings())
        super().closeEvent(event)

    @staticmethod
    def make_margin_spin():
        spin = QSpinBox()
        spin.setRange(0, 100000)
        spin.setValue(0)
        spin.setSuffix(" px")
        return spin

    def update_color_button(self):
        self.color_button.setText(self.line_color)
        self.color_button.setStyleSheet(
            f"QPushButton {{ background-color: {self.line_color}; color: white; }}"
        )

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.line_color = color.name()
            self.update_color_button()

    def choose_files(self):
        filenames, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff)"
        )
        self.add_files([Path(name) for name in filenames])

    def add_files(self, paths):
        added = 0
        known = {p.resolve() for p in self.source_files}
        for path in paths:
            if path.is_dir():
                candidates = sorted(
                    p for p in path.iterdir()
                    if p.is_file() and p.suffix.lower() in SUPPORTED
                )
            else:
                candidates = [path]
            for candidate in candidates:
                if candidate.is_file() and candidate.suffix.lower() in SUPPORTED:
                    try:
                        resolved = candidate.resolve()
                        if resolved not in known:
                            # 验证文件是否为可读取图片
                            with Image.open(candidate) as im:
                                im.verify()
                            self.source_files.append(candidate)
                            known.add(resolved)
                            added += 1
                    except Exception:
                        pass

        self.update_source_preview()
        self.files_label.setText(f"已选择 {len(self.source_files)} 张图片")
        if added:
            self.statusBar().showMessage(f"新增 {added} 张图片", 4000)

    def clear_files(self):
        self.source_files.clear()
        self.output_files.clear()
        self.files_label.setText("尚未选择图片")
        self.source_preview.set_images([])
        self.output_preview.set_images([])
        self.statusBar().showMessage("已清空")

    def remove_source(self, path: Path):
        """从源文件列表删除单个文件。"""
        self.source_files = [p for p in self.source_files if p != path]
        if self.source_files:
            self.files_label.setText(f"已选择 {len(self.source_files)} 张图片")
        else:
            self.files_label.setText("尚未选择图片")
        self.update_source_preview()
        self.statusBar().showMessage(f"已删除 {path.name}", 4000)

    def choose_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir.setText(directory)

    def toggle_source_preview(self, checked):
        self.source_preview.setVisible(checked)
        self.update_source_preview()

    def toggle_output_preview(self, checked):
        self.output_preview.setVisible(checked)
        if checked:
            self.update_output_preview()

    def update_source_preview(self):
        if self.show_source_check.isChecked():
            self.source_preview.set_images([(p, p.name) for p in self.source_files])

    def update_output_preview(self):
        if self.show_output_check.isChecked():
            self.output_preview.set_images([(p, p.name) for p in self.output_files])

    def output_directory(self):
        entered = self.output_dir.text().strip()
        if entered:
            return Path(entered).expanduser()
        if self.source_files:
            return self.source_files[0].parent / "output"
        return Path.cwd() / "output"

    def _process_one(self, source: Path, base_output: Path):
        return process_image(
            source, base_output,
            rows=self.rows.value(),
            cols=self.cols.value(),
            margin_top=self.margin_top.value(),
            margin_bottom=self.margin_bottom.value(),
            margin_left=self.margin_left.value(),
            margin_right=self.margin_right.value(),
            split=self.split_check.isChecked(),
            line_color=self.line_color,
            line_width=self.line_width.value(),
            endpoints_only=self.endpoints_check.isChecked(),
        )

    def process_images(self):
        if not self.source_files:
            QMessageBox.warning(self, "提示", "请先添加至少一张图片。")
            return

        base_output = self.output_directory()
        try:
            base_output.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            QMessageBox.critical(self, "输出目录错误", str(exc))
            return

        self.process_button.setEnabled(False)
        self.output_files = []
        errors = []
        try:
            for index, source in enumerate(self.source_files, 1):
                try:
                    generated = self._process_one(source, base_output)
                    self.output_files.extend(generated)
                    self.statusBar().showMessage(
                        f"处理中：{index}/{len(self.source_files)} - {source.name}"
                    )
                    QApplication.processEvents()
                except Exception as exc:
                    errors.append(f"{source.name}: {exc}")
        finally:
            self.process_button.setEnabled(True)

        self.update_output_preview()
        summary = f"处理完成！成功生成 {len(self.output_files)} 个文件。"
        if errors:
            summary += "\n\n以下文件处理失败：\n" + "\n".join(errors)
            QMessageBox.warning(self, "处理完成（部分失败）", summary)
        else:
            QMessageBox.information(self, "处理完成", summary)
        self.statusBar().showMessage(summary.splitlines()[0], 8000)

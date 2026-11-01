# -*- coding: utf-8 -*-
"""网格标线 / 分割的核心图像处理逻辑（与界面解耦）。"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageColor, ImageOps


def process_image(
    source: Path,
    base_output: Path,
    *,
    rows: int,
    cols: int,
    margin_top: int,
    margin_bottom: int,
    margin_left: int,
    margin_right: int,
    split: bool,
    line_color: str,
    line_width: int,
) -> list:
    """处理单张图片，返回生成的输出文件列表。

    split=True  时按网格分割输出 PNG 小块；
    split=False 时输出带网格标线的整张图片。
    """
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGBA")

    width, height = image.size
    top, bottom = margin_top, margin_bottom
    left, right = margin_left, margin_right

    if left + right >= width or top + bottom >= height:
        raise ValueError(
            f"Margin 超出图片范围：图片为 {width}×{height}，"
            f"左右合计 {left + right}，上下合计 {top + bottom}"
        )

    x0, y0 = left, top
    x1, y1 = width - right, height - bottom

    if split:
        return _split_tiles(image, source, base_output, rows, cols, x0, y0, x1, y1)
    return [
        _draw_marked(
            image, source, base_output, rows, cols, x0, y0, x1, y1,
            line_color, line_width,
        )
    ]


def _split_tiles(image, source, base_output, rows, cols, x0, y0, x1, y1):
    target_dir = base_output / source.stem
    target_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for row in range(rows):
        y_start = y0 + round((y1 - y0) * row / rows)
        y_end = y0 + round((y1 - y0) * (row + 1) / rows)
        for col in range(cols):
            x_start = x0 + round((x1 - x0) * col / cols)
            x_end = x0 + round((x1 - x0) * (col + 1) / cols)
            tile = image.crop((x_start, y_start, x_end, y_end))
            output_path = target_dir / f"{source.stem}_r{row + 1:02d}_c{col + 1:02d}.png"
            tile.save(output_path, "PNG")
            outputs.append(output_path)
    return outputs


def _draw_marked(image, source, base_output, rows, cols, x0, y0, x1, y1,
                 line_color, line_width):
    """标线模式：保留原图，在 Margin 内容区域边缘和内部绘制网格线。"""
    marked = image.copy()
    draw = ImageDraw.Draw(marked)
    color = ImageColor.getcolor(line_color, "RGBA")

    # 内容区域四边界线（Margin 不为 0 时也明确标出内容边界）
    draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=color, width=line_width)

    for col in range(1, cols):
        x = x0 + round((x1 - x0) * col / cols)
        draw.line((x, y0, x, y1 - 1), fill=color, width=line_width)

    for row in range(1, rows):
        y = y0 + round((y1 - y0) * row / rows)
        draw.line((x0, y, x1 - 1, y), fill=color, width=line_width)

    base_output.mkdir(parents=True, exist_ok=True)
    output_path = base_output / f"{source.stem}_grid.png"
    marked.save(output_path, "PNG")
    return output_path

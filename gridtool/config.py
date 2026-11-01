# -*- coding: utf-8 -*-
"""运行参数配置持久化：保存到项目目录下的 settings.json。"""

import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "settings.json"


def load_config() -> dict:
    """读取配置文件，不存在或损坏时返回空字典。"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_config(data: dict):
    """写入配置文件。"""
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

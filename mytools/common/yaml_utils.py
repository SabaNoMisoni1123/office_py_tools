from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"YAMLファイルが見つかりません: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("YAMLのルートは辞書形式である必要があります。")

    return data


def get_required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if value is None:
        raise ValueError(f"{key} は必須です。")
    if not isinstance(value, str):
        raise ValueError(f"{key} は文字列である必要があります。")
    return value


def get_optional_str(data: dict[str, Any], key: str, default: str = "") -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"{key} は文字列である必要があります。")
    return value


def get_str_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if value is None:
        return []

    if not isinstance(value, list):
        raise ValueError(f"{key} は配列である必要があります。")

    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(f"{key}[{i}] は文字列である必要があります。")

    return value
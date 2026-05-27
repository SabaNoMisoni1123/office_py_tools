from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORTED_MARKDOWN_FORMATS = ("gfm", "markdown", "commonmark")


@dataclass(frozen=True)
class DocxToMarkdownConfig:
    config_path: Path
    markdown_format: str
    extract_media: bool
    media_dir: Path | None


def default_docx_to_markdown_config_path(project_root: Path) -> Path:
    return project_root / "config" / "docx_to_markdown.json"


def load_docx_to_markdown_config(config_path: Path) -> DocxToMarkdownConfig:
    if not config_path.exists():
        return DocxToMarkdownConfig(
            config_path=config_path,
            markdown_format="gfm",
            extract_media=True,
            media_dir=None,
        )
    if not config_path.is_file():
        raise FileNotFoundError(f"docx 変換設定のパスはファイルではありません: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"docx 変換設定 JSON を読み込めません: {config_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("docx 変換設定のルートは JSON object にしてください。")

    markdown_format = read_markdown_format(data)
    extract_media = read_bool(data, "extract_media", default=True)
    media_dir = resolve_optional_path(read_optional_string(data, "media_dir"), config_path)

    return DocxToMarkdownConfig(
        config_path=config_path,
        markdown_format=markdown_format,
        extract_media=extract_media,
        media_dir=media_dir,
    )


def read_markdown_format(data: dict[str, Any]) -> str:
    value = data.get("markdown_format", "gfm")
    if value not in SUPPORTED_MARKDOWN_FORMATS:
        supported = ", ".join(SUPPORTED_MARKDOWN_FORMATS)
        raise ValueError(f"Markdown の出力形式は {supported} のいずれかにしてください。")
    return value


def read_bool(data: dict[str, Any], key: str, *, default: bool) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"docx 変換設定の {key} は true または false にしてください。")
    return value


def read_optional_string(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"docx 変換設定の {key} は null または空でない文字列にしてください。")
    return value


def resolve_optional_path(value: str | None, config_path: Path) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = config_path.parent / path
    return path.resolve(strict=False)

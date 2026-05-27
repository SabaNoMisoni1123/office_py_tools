from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mytools.common.markdown.css import is_http_url


@dataclass(frozen=True)
class MarkdownConverterConfig:
    config_path: Path
    html_css: tuple[str, ...]
    pdf_css: tuple[str, ...]
    docx_template: str | None
    html_standalone: bool


def default_config_path(project_root: Path) -> Path:
    return project_root / "config" / "markdown_converter.json"


def load_markdown_converter_config(config_path: Path) -> MarkdownConverterConfig:
    if not config_path.exists():
        return MarkdownConverterConfig(
            config_path=config_path,
            html_css=(),
            pdf_css=(),
            docx_template=None,
            html_standalone=True,
        )
    if not config_path.is_file():
        raise FileNotFoundError(f"Markdown 変換設定のパスはファイルではありません: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Markdown 変換設定 JSON を読み込めません: {config_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Markdown 変換設定のルートは JSON object にしてください。")

    html = read_section(data, "html")
    pdf = read_section(data, "pdf")
    docx = read_section(data, "docx")

    return MarkdownConverterConfig(
        config_path=config_path,
        html_css=resolve_config_css_list(read_string_list(html, "css"), config_path),
        pdf_css=resolve_config_css_list(read_string_list(pdf, "css"), config_path),
        docx_template=resolve_config_path_or_url(read_optional_string(docx, "template"), config_path),
        html_standalone=read_bool(html, "standalone", default=True),
    )


def read_section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Markdown 変換設定の {key} は object にしてください。")
    return value


def read_string_list(section: dict[str, Any], key: str) -> tuple[str, ...]:
    value = section.get(key, [])
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"Markdown 変換設定の {key} は文字列配列にしてください。")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Markdown 変換設定の {key} は空でない文字列配列にしてください。")
        result.append(item)
    return tuple(result)


def read_optional_string(section: dict[str, Any], key: str) -> str | None:
    value = section.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Markdown 変換設定の {key} は null または空でない文字列にしてください。")
    return value


def read_bool(section: dict[str, Any], key: str, *, default: bool) -> bool:
    value = section.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"Markdown 変換設定の {key} は true または false にしてください。")
    return value


def resolve_config_css_list(values: tuple[str, ...], config_path: Path) -> tuple[str, ...]:
    return tuple(resolve_config_path_or_url(value, config_path) for value in values)


def resolve_config_path_or_url(value: str | None, config_path: Path) -> str | None:
    if value is None:
        return None
    if is_http_url(value):
        return value
    path = Path(value)
    if not path.is_absolute():
        path = config_path.parent / path
    return str(path.resolve(strict=False))

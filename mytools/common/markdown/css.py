from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal
from urllib.parse import urlparse

from mytools.common import arg_path

CssKind = Literal["file", "url"]


@dataclass(frozen=True)
class ResolvedCss:
    original: str
    kind: CssKind
    value: str


def resolve_css_sources(
    sources: Iterable[str] | None, *, base_dir: Path
) -> tuple[ResolvedCss, ...]:
    if not sources:
        return ()

    resolved: list[ResolvedCss] = []
    for source in sources:
        if is_http_url(source):
            resolved.append(ResolvedCss(original=source, kind="url", value=source))
            continue

        css_path = arg_path.resolve_cli_path(source, base_dir=base_dir)
        if not css_path.exists():
            raise FileNotFoundError(f"CSS ファイルが見つかりません: {css_path}")
        if not css_path.is_file():
            raise FileNotFoundError(f"CSS として指定されたパスはファイルではありません: {css_path}")
        resolved.append(
            ResolvedCss(original=source, kind="file", value=str(css_path))
        )

    return tuple(resolved)


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

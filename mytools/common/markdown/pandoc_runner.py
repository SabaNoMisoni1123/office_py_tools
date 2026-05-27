from __future__ import annotations

import shutil
import subprocess
from os.path import relpath
from pathlib import Path

from mytools.common.markdown.css import ResolvedCss


class ExternalDependencyError(RuntimeError):
    pass


class PandocError(RuntimeError):
    pass


def ensure_pandoc_available() -> str:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise ExternalDependencyError(
            "Pandoc が見つかりません。pandoc コマンドをインストールし、PATH に追加してください。"
        )
    return pandoc


def convert_markdown_to_html(
    *,
    input_path: Path,
    output_path: Path,
    css: tuple[ResolvedCss, ...] = (),
    standalone: bool = True,
) -> None:
    args = [
        ensure_pandoc_available(),
        str(input_path),
        "--from",
        "markdown",
        "--to",
        "html",
        "--output",
        str(output_path),
    ]
    if standalone:
        args.append("--standalone")
    for css_source in css:
        args.extend(["--css", css_value_for_html(css_source, output_path=output_path)])

    run_pandoc(args)


def convert_markdown_to_docx(
    *,
    input_path: Path,
    output_path: Path,
    reference_doc: Path | None = None,
) -> None:
    args = [
        ensure_pandoc_available(),
        str(input_path),
        "--from",
        "markdown",
        "--to",
        "docx",
        "--output",
        str(output_path),
    ]
    if reference_doc is not None:
        args.extend(["--reference-doc", str(reference_doc)])

    run_pandoc(args)


def convert_docx_to_markdown(
    *,
    input_path: Path,
    output_path: Path,
    markdown_format: str,
    media_dir: Path | None = None,
) -> None:
    args = [
        ensure_pandoc_available(),
        str(input_path),
        "--from",
        "docx",
        "--to",
        markdown_format,
        "--output",
        str(output_path),
    ]
    if media_dir is not None:
        try:
            media_arg = relpath(media_dir, start=output_path.parent)
        except ValueError:
            media_arg = str(media_dir)
        args.extend(["--extract-media", media_arg])

    run_pandoc(args, cwd=output_path.parent)


def run_pandoc(args: list[str], *, cwd: Path | None = None) -> None:
    completed = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd is not None else None,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        if detail:
            raise PandocError(f"Pandoc の実行に失敗しました: {detail}")
        raise PandocError("Pandoc の実行に失敗しました。")


def css_value_for_html(css_source: ResolvedCss, *, output_path: Path) -> str:
    if css_source.kind == "url":
        return css_source.value

    css_path = Path(css_source.value)
    try:
        return relpath(css_path, start=output_path.parent)
    except ValueError:
        return str(css_path)

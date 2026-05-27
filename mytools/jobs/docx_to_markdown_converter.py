from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mytools.common import arg_path
from mytools.common.markdown import convert_docx_to_markdown, ensure_pandoc_available
from mytools.common.markdown.docx_config import SUPPORTED_MARKDOWN_FORMATS


@dataclass(frozen=True)
class DocxToMarkdownRequest:
    input_path: Path
    output_path: Path
    markdown_format: str
    media_dir: Path | None
    extract_media: bool
    dry_run: bool
    overwrite: bool


@dataclass(frozen=True)
class DocxToMarkdownPlan:
    input_path: Path
    output_path: Path
    markdown_format: str
    media_dir: Path | None
    extract_media: bool
    overwrite: bool


def build_plan(request: DocxToMarkdownRequest) -> DocxToMarkdownPlan:
    validate_input_path(request.input_path)
    validate_markdown_format(request.markdown_format)
    validate_output_path(request.output_path, overwrite=request.overwrite)

    media_dir = None
    if request.extract_media:
        media_dir = request.media_dir or default_media_dir(request.output_path)
        validate_media_dir(media_dir)

    return DocxToMarkdownPlan(
        input_path=request.input_path,
        output_path=request.output_path,
        markdown_format=request.markdown_format,
        media_dir=media_dir,
        extract_media=request.extract_media,
        overwrite=request.overwrite,
    )


def convert_docx_request_to_markdown(
    request: DocxToMarkdownRequest,
) -> DocxToMarkdownPlan:
    plan = build_plan(request)
    if request.dry_run:
        return plan

    ensure_pandoc_available()
    convert_docx_to_markdown(
        input_path=plan.input_path,
        output_path=plan.output_path,
        markdown_format=plan.markdown_format,
        media_dir=plan.media_dir if plan.extract_media else None,
    )
    return plan


def default_media_dir(output_path: Path) -> Path:
    return output_path.parent / f"{output_path.stem}_media"


def validate_input_path(input_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"入力 docx ファイルが見つかりません: {input_path}")
    if not input_path.is_file():
        raise FileNotFoundError(f"入力 docx パスはファイルではありません: {input_path}")
    if input_path.suffix.lower() != ".docx":
        raise ValueError(f"入力ファイルの拡張子は .docx にしてください: {input_path}")


def validate_markdown_format(markdown_format: str) -> None:
    if markdown_format not in SUPPORTED_MARKDOWN_FORMATS:
        supported = ", ".join(SUPPORTED_MARKDOWN_FORMATS)
        raise ValueError(f"Markdown の出力形式は {supported} のいずれかにしてください。")


def validate_output_path(output_path: Path, *, overwrite: bool) -> None:
    parent = arg_path.ensure_parent_dir(output_path, create=False)
    if not parent.exists():
        raise FileNotFoundError(f"出力先の親ディレクトリが見つかりません: {parent}")
    if not parent.is_dir():
        raise NotADirectoryError(f"出力先の親パスはディレクトリではありません: {parent}")
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"出力先ファイルは既に存在します。上書きする場合は --overwrite を指定してください: {output_path}"
        )
    if output_path.suffix.lower() not in {".md", ".markdown"}:
        raise ValueError(f"出力ファイルの拡張子は .md または .markdown にしてください: {output_path}")


def validate_media_dir(media_dir: Path) -> None:
    parent = media_dir.parent
    if not parent.exists():
        raise FileNotFoundError(f"メディア抽出先の親ディレクトリが見つかりません: {parent}")
    if not parent.is_dir():
        raise NotADirectoryError(f"メディア抽出先の親パスはディレクトリではありません: {parent}")
    if media_dir.exists() and not media_dir.is_dir():
        raise NotADirectoryError(f"メディア抽出先はディレクトリとして指定してください: {media_dir}")

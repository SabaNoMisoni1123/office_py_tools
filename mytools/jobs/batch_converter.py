from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mytools.common import arg_path
from mytools.common.markdown.docx_config import SUPPORTED_MARKDOWN_FORMATS
from mytools.common.pdf.image_converter import convert_pdf_to_png_images, plan_pdf_to_png_images
from mytools.jobs.docx_to_markdown_converter import (
    DocxToMarkdownRequest,
    convert_docx_request_to_markdown,
)
from mytools.jobs.markdown_converter import (
    MarkdownConvertRequest,
    convert_markdown,
)

KIND_MARKDOWN = "markdown"
KIND_DOCX = "docx"
KIND_PDF = "pdf"


@dataclass(frozen=True)
class BatchConvertRequest:
    cwd: Path
    input_dir: Path
    output_dir: Path
    kind: str
    output_format: str
    glob_pattern: str | None
    recursive: bool
    css_sources: tuple[str, ...]
    template_path: Path | None
    standalone: bool | None
    no_default_css: bool
    no_default_template: bool
    markdown_format: str | None
    media_dir: Path | None
    extract_media: bool
    quality: str
    summary_output_path: Path | None
    summary_format: str
    dry_run: bool
    overwrite: bool
    create_dirs: bool
    continue_on_error: bool
    allow_partial_success: bool


@dataclass(frozen=True)
class BatchConvertItemPlan:
    input_path: Path
    output_path: Path
    kind: str
    output_format: str


@dataclass(frozen=True)
class BatchConvertItemResult:
    plan: BatchConvertItemPlan
    status: str
    message: str


@dataclass(frozen=True)
class BatchConvertPlan:
    input_dir: Path
    output_dir: Path
    kind: str
    output_format: str
    item_plans: tuple[BatchConvertItemPlan, ...]
    results: tuple[BatchConvertItemResult, ...]


def run_batch_convert(request: BatchConvertRequest) -> BatchConvertPlan:
    item_plans = tuple(build_item_plans(request))
    results: list[BatchConvertItemResult] = []

    if request.dry_run:
        results = [
            BatchConvertItemResult(plan=plan, status="planned", message="")
            for plan in item_plans
        ]
    else:
        if request.create_dirs:
            request.output_dir.mkdir(parents=True, exist_ok=True)
        validate_output_dir(request.output_dir)
        for plan in item_plans:
            try:
                convert_one(request, plan)
                results.append(
                    BatchConvertItemResult(plan=plan, status="success", message="")
                )
            except Exception as exc:
                results.append(
                    BatchConvertItemResult(
                        plan=plan, status="failed", message=str(exc)
                    )
                )
                if not request.continue_on_error:
                    break

    if request.summary_output_path is not None and not request.dry_run:
        write_summary(results, request.summary_output_path, request.summary_format)

    if any(result.status == "failed" for result in results) and not request.allow_partial_success:
        raise RuntimeError("バッチ変換で失敗したファイルがあります。サマリを確認してください。")

    return BatchConvertPlan(
        input_dir=request.input_dir,
        output_dir=request.output_dir,
        kind=request.kind,
        output_format=request.output_format,
        item_plans=item_plans,
        results=tuple(results),
    )


def build_item_plans(request: BatchConvertRequest) -> list[BatchConvertItemPlan]:
    validate_input_dir(request.input_dir)
    validate_kind_and_format(request.kind, request.output_format)
    validate_summary_output(
        request.summary_output_path,
        overwrite=request.overwrite,
        create_dirs=request.create_dirs,
    )
    glob_pattern = request.glob_pattern or default_glob(request.kind, request.recursive)
    paths = sorted(path for path in request.input_dir.glob(glob_pattern) if path.is_file())
    return [
        BatchConvertItemPlan(
            input_path=path,
            output_path=build_output_path(request, path),
            kind=request.kind,
            output_format=request.output_format,
        )
        for path in paths
    ]


def validate_input_dir(input_dir: Path) -> None:
    if not input_dir.exists():
        raise FileNotFoundError(f"入力ディレクトリが見つかりません: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"入力はディレクトリで指定してください: {input_dir}")


def validate_output_dir(output_dir: Path) -> None:
    if not output_dir.exists():
        raise FileNotFoundError(f"出力ディレクトリが見つかりません: {output_dir}")
    if not output_dir.is_dir():
        raise NotADirectoryError(f"出力先はディレクトリで指定してください: {output_dir}")


def validate_summary_output(
    output_path: Path | None, *, overwrite: bool, create_dirs: bool
) -> None:
    if output_path is None:
        return
    parent = arg_path.ensure_parent_dir(output_path, create=create_dirs)
    if not parent.exists():
        raise FileNotFoundError(f"サマリ出力先の親ディレクトリが見つかりません: {parent}")
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"サマリ出力ファイルは既に存在します。上書きする場合は --overwrite を指定してください: {output_path}"
        )


def validate_kind_and_format(kind: str, output_format: str) -> None:
    allowed = {
        KIND_MARKDOWN: {"html", "pdf", "docx"},
        KIND_DOCX: {"markdown"},
        KIND_PDF: {"png"},
    }
    if kind not in allowed:
        raise ValueError("入力種別は markdown, docx, pdf のいずれかを指定してください。")
    if output_format not in allowed[kind]:
        supported = ", ".join(sorted(allowed[kind]))
        raise ValueError(f"{kind} の出力形式は {supported} のいずれかを指定してください。")


def default_glob(kind: str, recursive: bool) -> str:
    suffix = {KIND_MARKDOWN: "*.md", KIND_DOCX: "*.docx", KIND_PDF: "*.pdf"}[kind]
    return f"**/{suffix}" if recursive else suffix


def build_output_path(request: BatchConvertRequest, input_path: Path) -> Path:
    relative = input_path.relative_to(request.input_dir)
    if request.kind == KIND_PDF:
        return request.output_dir / relative.parent / input_path.stem
    suffix = {
        "html": ".html",
        "pdf": ".pdf",
        "docx": ".docx",
        "markdown": ".md",
    }[request.output_format]
    return request.output_dir / relative.with_suffix(suffix)


def convert_one(request: BatchConvertRequest, plan: BatchConvertItemPlan) -> None:
    parent = plan.output_path.parent
    if request.create_dirs:
        parent.mkdir(parents=True, exist_ok=True)
    if not parent.exists():
        raise FileNotFoundError(f"出力先の親ディレクトリが見つかりません: {parent}")

    if plan.kind == KIND_MARKDOWN:
        convert_markdown(
            MarkdownConvertRequest(
                cwd=request.cwd,
                input_path=plan.input_path,
                output_path=plan.output_path,
                output_format=plan.output_format,  # type: ignore[arg-type]
                css_sources=request.css_sources,
                template_path=request.template_path,
                standalone=request.standalone if request.standalone is not None else True,
                dry_run=False,
                overwrite=request.overwrite,
            )
        )
        return

    if plan.kind == KIND_DOCX:
        markdown_format = request.markdown_format or "gfm"
        if markdown_format not in SUPPORTED_MARKDOWN_FORMATS:
            raise ValueError("Markdown 形式は gfm, markdown, commonmark のいずれかを指定してください。")
        convert_docx_request_to_markdown(
            DocxToMarkdownRequest(
                input_path=plan.input_path,
                output_path=plan.output_path,
                markdown_format=markdown_format,
                media_dir=request.media_dir,
                extract_media=request.extract_media,
                dry_run=False,
                overwrite=request.overwrite,
            )
        )
        return

    if plan.kind == KIND_PDF:
        dpi = {"low": 150, "medium": 300, "high": 600}[request.quality]
        convert_pdf_to_png_images(
            plan.input_path,
            output_dir=plan.output_path,
            dpi=dpi,
            overwrite=request.overwrite,
        )
        return

    raise ValueError(f"未対応の入力種別です: {plan.kind}")


def write_summary(
    results: list[BatchConvertItemResult], output_path: Path, summary_format: str
) -> None:
    if summary_format == "csv":
        with output_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["status", "input_path", "output_path", "kind", "format", "message"],
            )
            writer.writeheader()
            for result in results:
                writer.writerow(result_to_dict(result))
        return
    if summary_format == "json":
        output_path.write_text(
            json.dumps([result_to_dict(result) for result in results], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return
    if summary_format == "markdown":
        lines = ["# バッチ変換サマリ", "", "| 状態 | 入力 | 出力 | メッセージ |", "|---|---|---|---|"]
        for result in results:
            lines.append(
                f"| {result.status} | `{result.plan.input_path}` | `{result.plan.output_path}` | {result.message} |"
            )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    raise ValueError("サマリ形式は csv, markdown, json のいずれかを指定してください。")


def result_to_dict(result: BatchConvertItemResult) -> dict[str, Any]:
    return {
        "status": result.status,
        "input_path": str(result.plan.input_path),
        "output_path": str(result.plan.output_path),
        "kind": result.plan.kind,
        "format": result.plan.output_format,
        "message": result.message,
    }

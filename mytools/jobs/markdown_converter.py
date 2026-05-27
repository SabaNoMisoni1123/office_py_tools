from __future__ import annotations

import tempfile
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
import shutil
import subprocess
import os
from typing import Literal

from mytools.common import arg_path
from mytools.common.markdown import (
    ExternalDependencyError,
    ResolvedCss,
    convert_markdown_to_docx,
    convert_markdown_to_html,
    ensure_pandoc_available,
    prepare_reference_doc,
    resolve_css_sources,
)

OutputFormat = Literal["html", "pdf", "docx"]


@dataclass(frozen=True)
class MarkdownConvertRequest:
    cwd: Path
    input_path: Path
    output_path: Path
    output_format: OutputFormat
    css_sources: tuple[str, ...]
    template_path: Path | None
    standalone: bool
    dry_run: bool
    overwrite: bool


@dataclass(frozen=True)
class MarkdownConvertPlan:
    input_path: Path
    output_path: Path
    output_format: OutputFormat
    css: tuple[ResolvedCss, ...]
    template_path: Path | None
    standalone: bool
    overwrite: bool


def build_plan(request: MarkdownConvertRequest) -> MarkdownConvertPlan:
    validate_input_path(request.input_path)
    validate_output_path(
        request.output_path,
        expected_format=request.output_format,
        overwrite=request.overwrite,
    )
    validate_option_combination(request)

    css = resolve_css_sources(request.css_sources, base_dir=request.cwd)
    template_path = request.template_path
    if template_path is not None:
        validate_template_path(template_path)

    return MarkdownConvertPlan(
        input_path=request.input_path,
        output_path=request.output_path,
        output_format=request.output_format,
        css=css,
        template_path=template_path,
        standalone=request.standalone,
        overwrite=request.overwrite,
    )


def convert_markdown(request: MarkdownConvertRequest) -> MarkdownConvertPlan:
    plan = build_plan(request)
    if request.dry_run:
        return plan

    ensure_pandoc_available()
    if plan.output_format == "html":
        convert_markdown_to_html(
            input_path=plan.input_path,
            output_path=plan.output_path,
            css=plan.css,
            standalone=plan.standalone,
        )
    elif plan.output_format == "pdf":
        convert_markdown_to_pdf(plan)
    elif plan.output_format == "docx":
        convert_markdown_to_docx_with_template(plan)
    else:
        raise ValueError(f"未対応の出力形式です: {plan.output_format}")

    return plan


def convert_markdown_to_pdf(plan: MarkdownConvertPlan) -> None:
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        html_path = temp_dir / "input.html"
        convert_markdown_to_html(
            input_path=plan.input_path,
            output_path=html_path,
            css=(),
            standalone=True,
        )
        try:
            convert_html_to_pdf_with_weasyprint_api(plan, html_path)
        except ExternalDependencyError as api_error:
            convert_html_to_pdf_with_weasyprint_cli(
                plan,
                html_path,
                fallback_reason=api_error,
            )


def convert_html_to_pdf_with_weasyprint_api(
    plan: MarkdownConvertPlan, html_path: Path
) -> None:
    try:
        # WeasyPrint prints diagnostics to stdout/stderr before raising when
        # native libraries are missing. Capture that and return a concise error.
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            from weasyprint import CSS, HTML  # type: ignore[import-not-found]
    except (ImportError, OSError) as exc:
        raise ExternalDependencyError(
            "WeasyPrint Python API を利用できません。"
            f"詳細: {exc}"
        ) from exc

    try:
        stylesheets = []
        for css_source in plan.css:
            if css_source.kind == "file":
                stylesheets.append(CSS(filename=css_source.value))
            else:
                stylesheets.append(CSS(url=css_source.value))
        HTML(filename=str(html_path), base_url=str(plan.input_path.parent)).write_pdf(
            str(plan.output_path),
            stylesheets=stylesheets,
        )
    except OSError as exc:
        raise ExternalDependencyError(
            "WeasyPrint Python API で PDF を生成できません。"
            f"詳細: {exc}"
        ) from exc


def convert_html_to_pdf_with_weasyprint_cli(
    plan: MarkdownConvertPlan, html_path: Path, *, fallback_reason: Exception
) -> None:
    executable = find_weasyprint_cli()
    if executable is None:
        raise ExternalDependencyError(
            "PDF 生成に必要な WeasyPrint を利用できません。"
            "weasyprint Python API または weasyprint コマンドを利用可能にしてください。"
            f"Python API の失敗理由: {fallback_reason}"
        ) from fallback_reason

    args = [
        executable,
        "--base-url",
        str(plan.input_path.parent),
        str(html_path),
        str(plan.output_path),
    ]
    for css_source in plan.css:
        args.extend(["--stylesheet", css_source.value])

    env = os.environ.copy()
    env["TEMP"] = str(html_path.parent)
    env["TMP"] = str(html_path.parent)
    completed = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        if detail:
            raise ExternalDependencyError(
                f"WeasyPrint コマンドで PDF を生成できませんでした: {detail}"
            )
        raise ExternalDependencyError("WeasyPrint コマンドで PDF を生成できませんでした。")


def find_weasyprint_cli() -> str | None:
    candidates: list[str] = []
    if os.name == "nt":
        completed = subprocess.run(
            ["where.exe", "weasyprint"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0:
            candidates.extend(
                line.strip()
                for line in completed.stdout.splitlines()
                if line.strip()
            )

    which_result = shutil.which("weasyprint")
    if which_result is not None:
        candidates.append(which_result)

    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None


def convert_markdown_to_docx_with_template(plan: MarkdownConvertPlan) -> None:
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        reference_doc = (
            prepare_reference_doc(plan.template_path, temp_dir)
            if plan.template_path is not None
            else None
        )
        convert_markdown_to_docx(
            input_path=plan.input_path,
            output_path=plan.output_path,
            reference_doc=reference_doc,
        )


def validate_input_path(input_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"入力 Markdown ファイルが見つかりません: {input_path}")
    if not input_path.is_file():
        raise FileNotFoundError(f"入力 Markdown パスはファイルではありません: {input_path}")


def validate_output_path(
    output_path: Path, *, expected_format: OutputFormat, overwrite: bool
) -> None:
    parent = arg_path.ensure_parent_dir(output_path, create=False)
    if not parent.exists():
        raise FileNotFoundError(f"出力先の親ディレクトリが見つかりません: {parent}")
    if not parent.is_dir():
        raise NotADirectoryError(f"出力先の親パスはディレクトリではありません: {parent}")
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"出力先ファイルは既に存在します。上書きする場合は --overwrite を指定してください: {output_path}"
        )

    suffix = output_path.suffix.lower().lstrip(".")
    if suffix and suffix != expected_format:
        raise ValueError(
            f"出力ファイルの拡張子が形式と一致しません: format={expected_format}, output={output_path}"
        )


def validate_option_combination(request: MarkdownConvertRequest) -> None:
    if request.output_format == "docx" and request.css_sources:
        raise ValueError("CSS は HTML または PDF 出力でのみ指定できます。")
    if request.output_format != "docx" and request.template_path is not None:
        raise ValueError("テンプレートは docx 出力でのみ指定できます。")


def validate_template_path(template_path: Path) -> None:
    if not template_path.exists():
        raise FileNotFoundError(f"Word テンプレートが見つかりません: {template_path}")
    if not template_path.is_file():
        raise FileNotFoundError(f"Word テンプレートのパスはファイルではありません: {template_path}")
    if template_path.suffix.lower() not in {".dotx", ".docx"}:
        raise ValueError("Word テンプレートには .dotx または .docx を指定してください。")

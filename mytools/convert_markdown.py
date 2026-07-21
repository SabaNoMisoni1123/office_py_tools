from __future__ import annotations

import argparse
from pathlib import Path
import sys

from mytools.common import arg_path
from mytools.common.markdown import (
    ExternalDependencyError,
    PandocError,
    default_config_path,
    load_markdown_converter_config,
)
from mytools.jobs.markdown_converter import (
    MarkdownConvertPlan,
    MarkdownConvertRequest,
    convert_markdown,
)


def main() -> int:
    parser = build_parser()
    parsed_arg = parser.parse_args()

    base_dir = arg_path.choose_base_dir(
        base_dir=parsed_arg.cwd, prefer="cwd", entry_file=__file__
    )
    project_root = Path(__file__).resolve(strict=False).parent.parent
    config_path = choose_config_path(
        parsed_arg.config_path,
        base_dir=Path(base_dir),
        project_root=project_root,
    )
    input_path = arg_path.resolve_cli_path(parsed_arg.input_path, base_dir=base_dir)
    output_dir = (
        arg_path.resolve_cli_path(parsed_arg.output_dir, base_dir=base_dir)
        if parsed_arg.output_dir is not None
        else input_path.parent
    )
    output_path = build_output_path(
        input_path=input_path,
        output_dir=output_dir,
        output_format=parsed_arg.output_format,
    )

    try:
        warn_if_unusual_markdown_extension(input_path)
        config = load_markdown_converter_config(config_path)
        css_sources = build_effective_css_sources(
            parsed_arg.output_format,
            cli_css_sources=tuple(parsed_arg.css_sources or ()),
            config=config,
            use_default_css=not parsed_arg.no_default_css,
        )
        template_path = build_effective_template_path(
            parsed_arg.template_path,
            output_format=parsed_arg.output_format,
            config=config,
            base_dir=Path(base_dir),
            use_default_template=not parsed_arg.no_default_template,
        )
        request = MarkdownConvertRequest(
            cwd=Path(base_dir),
            input_path=input_path,
            output_path=output_path,
            output_format=parsed_arg.output_format,
            css_sources=css_sources,
            template_path=template_path,
            standalone=effective_standalone(parsed_arg.standalone, config),
            dry_run=parsed_arg.dry_run,
            overwrite=parsed_arg.overwrite,
        )
        plan = convert_markdown(request)
        print_plan(plan, dry_run=parsed_arg.dry_run)
        return 0
    except (ValueError, FileNotFoundError, FileExistsError, NotADirectoryError) as e:
        print(f"エラー: {e}")
        return 1
    except (PandocError, OSError) as e:
        print(f"エラー: {e}")
        return 2
    except ExternalDependencyError as e:
        print(f"エラー: {e}")
        return 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Markdown ファイルを HTML、PDF、docx に変換します。"
    )
    parser.add_argument("--cwd", required=True, help="相対パス解釈の基準ディレクトリ")
    parser.add_argument("--input", dest="input_path", required=True, help="入力 Markdown ファイル")
    parser.add_argument(
        "-f",
        "--format",
        dest="output_format",
        required=True,
        choices=["html", "pdf", "docx"],
        help="出力形式",
    )
    parser.add_argument(
        "--out-dir",
        dest="output_dir",
        help=(
            "出力先ディレクトリ。省略時は入力 Markdown ファイルと同じディレクトリに出力します。"
        ),
    )
    parser.add_argument(
        "--css",
        dest="css_sources",
        action="append",
        help="HTML / PDF に適用する CSS。複数指定する場合は --css を繰り返します。",
    )
    parser.add_argument(
        "--template",
        dest="template_path",
        help="docx 出力で使用する Word テンプレートまたは参照文書（.dotx / .docx）",
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        help=(
            "Markdown 変換設定 JSON。省略時は実行ディレクトリ、"
            "~/.config、プロジェクト既定の順で探索します。"
        ),
    )
    parser.add_argument(
        "--standalone",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="HTML 出力時に完全な HTML 文書として出力します。既定は設定ファイルに従います。",
    )
    parser.add_argument(
        "--no-default-css",
        action="store_true",
        default=False,
        help="設定ファイルの既定 CSS を使いません。",
    )
    parser.add_argument(
        "--no-default-template",
        action="store_true",
        default=False,
        help="設定ファイルの既定 Word テンプレートを使いません。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="実際には変換せず、変換予定だけ表示します。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="出力先ファイルが既に存在する場合に上書きします。",
    )
    return parser


def choose_config_path(
    cli_config_path: str | None,
    *,
    base_dir: Path,
    project_root: Path,
) -> Path:
    """設定ファイルを優先順位に従って選ぶ。"""
    if cli_config_path is not None:
        return arg_path.resolve_cli_path(cli_config_path, base_dir=base_dir)

    invocation_config_path = base_dir / "config" / "markdown_converter.json"
    if invocation_config_path.exists():
        return invocation_config_path

    user_config_path = Path.home() / ".config" / "markdown_converter.json"
    if user_config_path.exists():
        return user_config_path

    return default_config_path(project_root)


def build_output_path(
    *, input_path: Path, output_dir: Path, output_format: str
) -> Path:
    """入力ファイル名を保ったまま、出力形式に対応する拡張子を付ける。"""
    return output_dir / f"{input_path.stem}.{output_format}"


def build_effective_css_sources(
    output_format: str,
    *,
    cli_css_sources: tuple[str, ...],
    config,
    use_default_css: bool,
) -> tuple[str, ...]:
    if not use_default_css:
        return cli_css_sources
    if output_format == "html":
        return config.html_css + cli_css_sources
    if output_format == "pdf":
        return config.pdf_css + cli_css_sources
    return cli_css_sources


def build_effective_template_path(
    cli_template_path: str | None,
    *,
    output_format: str,
    config,
    base_dir: Path,
    use_default_template: bool,
) -> Path | None:
    if cli_template_path is not None:
        return arg_path.resolve_cli_path(cli_template_path, base_dir=base_dir)
    if output_format != "docx":
        return None
    if use_default_template and config.docx_template is not None:
        return Path(config.docx_template)
    return None


def effective_standalone(cli_standalone: bool | None, config) -> bool:
    if cli_standalone is not None:
        return cli_standalone
    return config.html_standalone


def warn_if_unusual_markdown_extension(input_path: Path) -> None:
    """入力形式が Markdown と判断しにくい場合に利用者へ知らせる。"""
    if input_path.suffix.lower() not in {".md", ".markdown"}:
        print(
            "警告: 入力ファイルの拡張子は .md または .markdown を推奨します: "
            f"{input_path}",
            file=sys.stderr,
        )


def print_plan(plan: MarkdownConvertPlan, *, dry_run: bool) -> None:
    title = "変換予定" if dry_run else "変換結果"
    print(f"{title}:")
    print(f"- 入力: {plan.input_path}")
    print(f"- 出力: {plan.output_path}")
    print(f"- 形式: {plan.output_format}")
    print(f"- 上書き: {'する' if plan.overwrite else 'しない'}")
    if plan.output_format in {"html", "pdf"}:
        if plan.css:
            print("- CSS:")
            for css in plan.css:
                print(f"  - [{css.kind}] {css.value}")
        else:
            print("- CSS: なし")
    if plan.output_format == "docx":
        print(f"- テンプレート: {plan.template_path if plan.template_path else 'なし'}")


if __name__ == "__main__":
    raise SystemExit(main())

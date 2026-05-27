from __future__ import annotations

import argparse
from pathlib import Path

from mytools.common import arg_path
from mytools.jobs.batch_converter import (
    BatchConvertPlan,
    BatchConvertRequest,
    run_batch_convert,
)


def main() -> int:
    parser = build_parser()
    parsed_arg = parser.parse_args()

    base_dir = arg_path.choose_base_dir(
        base_dir=parsed_arg.cwd, prefer="cwd", entry_file=__file__
    )
    input_dir = arg_path.resolve_cli_path(parsed_arg.input_dir, base_dir=base_dir)
    output_dir = arg_path.resolve_cli_path(parsed_arg.output_dir, base_dir=base_dir)
    template_path = resolve_optional(parsed_arg.template_path, base_dir)
    media_dir = resolve_optional(parsed_arg.media_dir, base_dir)
    summary_output = resolve_optional(parsed_arg.summary_output, base_dir)

    try:
        request = BatchConvertRequest(
            cwd=Path(base_dir),
            input_dir=input_dir,
            output_dir=output_dir,
            kind=parsed_arg.kind,
            output_format=parsed_arg.output_format,
            glob_pattern=parsed_arg.glob_pattern,
            recursive=parsed_arg.recursive,
            css_sources=tuple(parsed_arg.css_sources or ()),
            template_path=template_path,
            standalone=parsed_arg.standalone,
            no_default_css=parsed_arg.no_default_css,
            no_default_template=parsed_arg.no_default_template,
            markdown_format=parsed_arg.markdown_format,
            media_dir=media_dir,
            extract_media=not parsed_arg.no_extract_media,
            quality=parsed_arg.quality,
            summary_output_path=summary_output,
            summary_format=parsed_arg.summary_format,
            dry_run=parsed_arg.dry_run,
            overwrite=parsed_arg.overwrite,
            create_dirs=parsed_arg.create_dirs,
            continue_on_error=parsed_arg.continue_on_error,
            allow_partial_success=parsed_arg.allow_partial_success,
        )
        plan = run_batch_convert(request)
        print_plan(plan, dry_run=parsed_arg.dry_run)
        return 0
    except (ValueError, FileNotFoundError, FileExistsError, NotADirectoryError) as e:
        print(f"エラー: {e}")
        return 1
    except RuntimeError as e:
        print(f"エラー: {e}")
        return 2
    except ImportError as e:
        print(f"エラー: {e}")
        return 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="複数ファイルをまとめて変換します。")
    parser.add_argument("--cwd", required=True, help="相対パス解決の基準ディレクトリ")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--kind", required=True, choices=["markdown", "docx", "pdf"])
    parser.add_argument("-f", "--format", dest="output_format", required=True)
    parser.add_argument("--glob", dest="glob_pattern")
    parser.add_argument("--config", dest="config_path", help="バッチ変換設定 JSON。初期実装では互換性のため受け付けます。")
    parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--css", dest="css_sources", action="append")
    parser.add_argument("--template", dest="template_path")
    parser.add_argument("--standalone", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--no-default-css", action="store_true", default=False)
    parser.add_argument("--no-default-template", action="store_true", default=False)
    parser.add_argument("--markdown-format", choices=["gfm", "markdown", "commonmark"])
    parser.add_argument("--media-dir")
    parser.add_argument("--no-extract-media", action="store_true", default=False)
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--summary-output")
    parser.add_argument("--summary-format", choices=["csv", "markdown", "json"], default="csv")
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--overwrite", action="store_true", default=False)
    parser.add_argument("--create-dirs", action="store_true", default=False)
    parser.add_argument("--continue-on-error", action="store_true", default=False)
    parser.add_argument("--allow-partial-success", action="store_true", default=False)
    return parser


def resolve_optional(value: str | None, base_dir: Path) -> Path | None:
    if value is None:
        return None
    return arg_path.resolve_cli_path(value, base_dir=base_dir)


def print_plan(plan: BatchConvertPlan, *, dry_run: bool) -> None:
    title = "バッチ変換予定" if dry_run else "バッチ変換結果"
    print(f"{title}:")
    print(f"- 入力ディレクトリ: {plan.input_dir}")
    print(f"- 出力ディレクトリ: {plan.output_dir}")
    print(f"- 入力種別: {plan.kind}")
    print(f"- 出力形式: {plan.output_format}")
    print(f"- 対象: {len(plan.item_plans)} 件")
    for result in plan.results:
        print(f"- [{result.status}] {result.plan.input_path} -> {result.plan.output_path}")
        if result.message:
            print(f"  {result.message}")


if __name__ == "__main__":
    raise SystemExit(main())

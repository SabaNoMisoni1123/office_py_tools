from __future__ import annotations

import argparse
from pathlib import Path

from mytools.common import arg_path
from mytools.common.markdown import (
    ExternalDependencyError,
    PandocError,
    default_docx_to_markdown_config_path,
    load_docx_to_markdown_config,
)
from mytools.common.markdown.docx_config import SUPPORTED_MARKDOWN_FORMATS
from mytools.jobs.docx_to_markdown_converter import (
    DocxToMarkdownPlan,
    DocxToMarkdownRequest,
    convert_docx_request_to_markdown,
)


def main() -> int:
    parser = build_parser()
    parsed_arg = parser.parse_args()

    base_dir = arg_path.choose_base_dir(
        base_dir=parsed_arg.cwd, prefer="cwd", entry_file=__file__
    )
    project_root = Path(__file__).resolve(strict=False).parent.parent
    config_path = (
        arg_path.resolve_cli_path(parsed_arg.config_path, base_dir=base_dir)
        if parsed_arg.config_path is not None
        else default_docx_to_markdown_config_path(project_root)
    )
    input_path = arg_path.resolve_cli_path(parsed_arg.input_path, base_dir=base_dir)
    output_path = arg_path.resolve_cli_path(parsed_arg.output_path, base_dir=base_dir)

    try:
        config = load_docx_to_markdown_config(config_path)
        markdown_format = parsed_arg.markdown_format or config.markdown_format
        extract_media = config.extract_media and not parsed_arg.no_extract_media
        media_dir = (
            arg_path.resolve_cli_path(parsed_arg.media_dir, base_dir=base_dir)
            if parsed_arg.media_dir is not None
            else config.media_dir
        )
        request = DocxToMarkdownRequest(
            input_path=input_path,
            output_path=output_path,
            markdown_format=markdown_format,
            media_dir=media_dir,
            extract_media=extract_media,
            dry_run=parsed_arg.dry_run,
            overwrite=parsed_arg.overwrite,
        )
        plan = convert_docx_request_to_markdown(request)
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
    parser = argparse.ArgumentParser(description="docx ファイルを Markdown に変換します。")
    parser.add_argument("--cwd", required=True, help="相対パス解釈の基準ディレクトリ")
    parser.add_argument("--input", dest="input_path", required=True, help="入力 docx ファイル")
    parser.add_argument("--output", dest="output_path", required=True, help="出力 Markdown ファイル")
    parser.add_argument(
        "--markdown-format",
        choices=SUPPORTED_MARKDOWN_FORMATS,
        help="出力 Markdown 方言。省略時は設定ファイルに従います。",
    )
    parser.add_argument(
        "--media-dir",
        help="docx 内画像などの抽出先ディレクトリ。省略時は <出力ファイル名>_media を使います。",
    )
    parser.add_argument(
        "--no-extract-media",
        action="store_true",
        default=False,
        help="docx 内画像などのメディアを抽出しません。",
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        help="docx 変換設定 JSON。省略時は config/docx_to_markdown.json を使います。",
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


def print_plan(plan: DocxToMarkdownPlan, *, dry_run: bool) -> None:
    title = "変換予定" if dry_run else "変換結果"
    print(f"{title}:")
    print(f"- 入力: {plan.input_path}")
    print(f"- 出力: {plan.output_path}")
    print(f"- Markdown形式: {plan.markdown_format}")
    print(f"- 上書き: {'する' if plan.overwrite else 'しない'}")
    if plan.extract_media:
        print(f"- メディア抽出先: {plan.media_dir}")
    else:
        print("- メディア抽出: しない")


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
from pathlib import Path

from mytools.common import arg_path
from mytools.jobs.report_generator import (
    ReportGeneratePlan,
    ReportGenerateRequest,
    generate_report,
)


def main() -> int:
    parser = build_parser()
    parsed_arg = parser.parse_args()

    base_dir = arg_path.choose_base_dir(
        base_dir=parsed_arg.cwd, prefer="cwd", entry_file=__file__
    )
    input_path = arg_path.resolve_cli_path(parsed_arg.input_path, base_dir=base_dir)
    config_path = arg_path.resolve_cli_path(parsed_arg.config_path, base_dir=base_dir)
    output_path = arg_path.resolve_cli_path(parsed_arg.output_path, base_dir=base_dir)
    summary_csv_output = resolve_optional(parsed_arg.summary_csv_output, base_dir)
    template_path = resolve_optional(parsed_arg.template_path, base_dir)

    try:
        request = ReportGenerateRequest(
            cwd=Path(base_dir),
            input_path=input_path,
            config_path=config_path,
            output_path=output_path,
            sheet_name=parsed_arg.sheet_name,
            encoding=parsed_arg.encoding,
            summary_csv_output_path=summary_csv_output,
            title=parsed_arg.title,
            template_path=template_path,
            dry_run=parsed_arg.dry_run,
            overwrite=parsed_arg.overwrite,
            create_dirs=parsed_arg.create_dirs,
        )
        plan = generate_report(request)
        print_plan(plan, dry_run=parsed_arg.dry_run)
        return 0
    except (ValueError, FileNotFoundError, FileExistsError, NotADirectoryError) as e:
        print(f"エラー: {e}")
        return 1
    except OSError as e:
        print(f"エラー: {e}")
        return 2
    except ImportError as e:
        print(f"エラー: {e}")
        return 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Excel / CSV から集計レポートを生成します。")
    parser.add_argument("--cwd", required=True, help="相対パス解決の基準ディレクトリ")
    parser.add_argument("--input", dest="input_path", required=True)
    parser.add_argument("--config", dest="config_path", required=True)
    parser.add_argument("--output", dest="output_path", required=True)
    parser.add_argument("--sheet", dest="sheet_name")
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--summary-csv-output")
    parser.add_argument("--title")
    parser.add_argument("--template", dest="template_path")
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--overwrite", action="store_true", default=False)
    parser.add_argument("--create-dirs", action="store_true", default=False)
    return parser


def resolve_optional(value: str | None, base_dir: Path) -> Path | None:
    if value is None:
        return None
    return arg_path.resolve_cli_path(value, base_dir=base_dir)


def print_plan(plan: ReportGeneratePlan, *, dry_run: bool) -> None:
    title = "レポート生成予定" if dry_run else "レポート生成結果"
    print(f"{title}:")
    print(f"- 入力: {plan.input_path}")
    print(f"- 出力: {plan.output_path}")
    print(f"- タイトル: {plan.title}")
    print(f"- 入力行数: {plan.row_count}")
    print(f"- フィルタ後行数: {plan.filtered_row_count}")
    print(f"- 集計キー: {', '.join(plan.group_by) if plan.group_by else 'なし'}")
    print(f"- 指標: {', '.join(plan.metric_names) if plan.metric_names else 'なし'}")
    print(f"- 集計 CSV 出力: {plan.summary_csv_output_path if plan.summary_csv_output_path else 'なし'}")
    print(f"- 上書き: {'する' if plan.overwrite else 'しない'}")


if __name__ == "__main__":
    raise SystemExit(main())


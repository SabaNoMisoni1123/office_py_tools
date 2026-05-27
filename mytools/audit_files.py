from __future__ import annotations

import argparse
from pathlib import Path

from mytools.common import arg_path
from mytools.jobs.file_auditor import FileAuditPlan, FileAuditRequest, run_file_audit


def main() -> int:
    parser = build_parser()
    parsed_arg = parser.parse_args()

    base_dir = arg_path.choose_base_dir(
        base_dir=parsed_arg.cwd, prefer="cwd", entry_file=__file__
    )
    root_dir = arg_path.resolve_cli_path(parsed_arg.root_dir, base_dir=base_dir)
    summary_output = resolve_optional(parsed_arg.summary_output, base_dir)
    list_output = resolve_optional(parsed_arg.list_output, base_dir)
    config_path = resolve_optional(parsed_arg.config_path, base_dir)

    try:
        request = FileAuditRequest(
            cwd=Path(base_dir),
            root_dir=root_dir,
            glob_pattern=parsed_arg.glob_pattern,
            exclude_globs=tuple(parsed_arg.exclude_globs or ()),
            summary_output_path=summary_output,
            list_output_path=list_output,
            summary_format=parsed_arg.summary_format,
            hash_algorithm=parsed_arg.hash_algorithm,
            max_size_mb=parsed_arg.max_size_mb,
            naming_regex=parsed_arg.naming_regex,
            config_path=config_path,
            dry_run=parsed_arg.dry_run,
            overwrite=parsed_arg.overwrite,
            create_dirs=parsed_arg.create_dirs,
        )
        plan = run_file_audit(request)
        print_plan(plan, dry_run=parsed_arg.dry_run)
        return 0
    except (ValueError, FileNotFoundError, FileExistsError, NotADirectoryError) as e:
        print(f"エラー: {e}")
        return 1
    except OSError as e:
        print(f"エラー: {e}")
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="指定フォルダ配下のファイルを棚卸しします。")
    parser.add_argument("--cwd", required=True, help="相対パス解決の基準ディレクトリ")
    parser.add_argument("--root", dest="root_dir", required=True)
    parser.add_argument("--glob", dest="glob_pattern")
    parser.add_argument("--exclude-glob", dest="exclude_globs", action="append")
    parser.add_argument("--summary-output")
    parser.add_argument("--list-output")
    parser.add_argument("--format", dest="summary_format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--hash", dest="hash_algorithm", choices=["none", "sha256"])
    parser.add_argument("--max-size-mb", type=int)
    parser.add_argument("--naming-regex")
    parser.add_argument("--config", dest="config_path")
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--overwrite", action="store_true", default=False)
    parser.add_argument("--create-dirs", action="store_true", default=False)
    return parser


def resolve_optional(value: str | None, base_dir: Path) -> Path | None:
    if value is None:
        return None
    return arg_path.resolve_cli_path(value, base_dir=base_dir)


def print_plan(plan: FileAuditPlan, *, dry_run: bool) -> None:
    title = "ファイル棚卸し予定" if dry_run else "ファイル棚卸し結果"
    print(f"{title}:")
    print(f"- 対象ディレクトリ: {plan.root_dir}")
    print(f"- 対象パターン: {plan.glob_pattern}")
    print(f"- 除外パターン: {', '.join(plan.exclude_globs) if plan.exclude_globs else 'なし'}")
    print(f"- 対象ファイル数: {plan.item_count}")
    print(f"- ハッシュ計算: {plan.hash_algorithm}")
    print(f"- サマリ出力: {plan.summary_output_path if plan.summary_output_path else 'なし'}")
    print(f"- 詳細一覧出力: {plan.list_output_path if plan.list_output_path else 'なし'}")


if __name__ == "__main__":
    raise SystemExit(main())


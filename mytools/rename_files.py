from __future__ import annotations

import argparse
from pathlib import Path

from mytools.common import arg_path
from mytools.common.file_renamer import (
    RenameResult,
    add_prefix_to_filenames,
    add_suffix_to_filenames,
    rename_with_basename,
)


def main() -> int:
    parser = build_parser()
    parsed_arg = parser.parse_args()

    base_dir = arg_path.choose_base_dir(
        base_dir=parsed_arg.cwd, prefer="cwd", entry_file=__file__
    )
    paths = arg_path.resolve_many_cli_paths(parsed_arg.paths, base_dir=base_dir)

    try:
        results = run_command(parsed_arg, paths)
        print_results(results, dry_run=parsed_arg.dry_run)
        return 0
    except Exception as e:
        print(f"エラー: {e}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="複数ファイルのファイル名を一括変更します。"
    )
    parser.add_argument("--cwd", required=True, help="相対パス解釈の基準ディレクトリ")
    parser.add_argument(
        "--operation",
        required=True,
        choices=["basename", "prefix", "suffix"],
        help="実行するリネーム操作を指定します。",
    )
    parser.add_argument("--base-name", help="basename 操作で使用するベースネーム")
    parser.add_argument("--prefix", help="prefix 操作で追加するプレフィックス")
    parser.add_argument("--suffix", help="suffix 操作で追加するサフィックス")
    parser.add_argument(
        "--path",
        dest="paths",
        action="append",
        required=True,
        help="リネーム対象ファイル。複数指定する場合は --path を繰り返します。",
    )
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--padding", type=int)
    parser.add_argument("--separator", default="_")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="実際には変更せず、変更予定だけ表示します。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="変更後ファイルが既に存在する場合に上書きします。",
    )

    return parser


def run_command(parsed_arg: argparse.Namespace, paths: list[Path]) -> list[RenameResult]:
    if parsed_arg.operation == "basename":
        if parsed_arg.base_name is None:
            raise ValueError("basename 操作では --base-name が必要です。")
        return rename_with_basename(
            parsed_arg.base_name,
            paths,
            start=parsed_arg.start,
            padding=parsed_arg.padding,
            separator=parsed_arg.separator,
            dry_run=parsed_arg.dry_run,
            overwrite=parsed_arg.overwrite,
        )

    if parsed_arg.operation == "prefix":
        if parsed_arg.prefix is None:
            raise ValueError("prefix 操作では --prefix が必要です。")
        return add_prefix_to_filenames(
            parsed_arg.prefix,
            paths,
            dry_run=parsed_arg.dry_run,
            overwrite=parsed_arg.overwrite,
        )

    if parsed_arg.operation == "suffix":
        if parsed_arg.suffix is None:
            raise ValueError("suffix 操作では --suffix が必要です。")
        return add_suffix_to_filenames(
            parsed_arg.suffix,
            paths,
            dry_run=parsed_arg.dry_run,
            overwrite=parsed_arg.overwrite,
        )

    raise ValueError(f"未対応の操作です: {parsed_arg.operation}")


def print_results(results: list[RenameResult], *, dry_run: bool) -> None:
    title = "変更予定" if dry_run else "変更結果"
    print(f"{title}:")
    for result in results:
        status = "skip" if not result.changed else "rename"
        print(f"- [{status}] {result.source} -> {result.target}")


if __name__ == "__main__":
    raise SystemExit(main())

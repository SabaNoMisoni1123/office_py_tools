"""フォルダツリーを更新時刻に応じてコピーする CLI。"""

from __future__ import annotations

import argparse
import os
import shutil
import stat
from pathlib import Path

from mytools.common import arg_path


class HelpOnErrorParser(argparse.ArgumentParser):
    """引数エラー時にも使い方全体を表示する ArgumentParser。"""

    def error(self, message: str) -> None:
        self.print_help()
        self.exit(2, f"\nエラー: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    # add_help=True は argparse の既定値だが、利用者向けに明示している。
    parser = HelpOnErrorParser(
        description="指定フォルダを再帰的にコピーします。",
        add_help=True,
    )
    parser.add_argument("--cwd", required=True, help="相対パスを解決する基準フォルダ")
    parser.add_argument("--source-dir", required=True, help="コピー元フォルダ")
    parser.add_argument("--destination-dir", required=True, help="コピー先フォルダ")
    parser.add_argument(
        "--skip-folder-containing",
        action="append",
        default=[],
        help="名前にこの文字列を含むフォルダと、その配下をコピーしない（繰り返し指定可）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="コピー先に同名ファイルがあっても、更新時刻にかかわらず上書きする",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="実際にはコピーせず、対象だけを表示する"
    )
    return parser


def is_skipped_folder(name: str, skip_strings: list[str]) -> bool:
    # 一つでも部分一致する除外文字列があれば、そのフォルダ以下を走査しない。
    return any(skip_string in name for skip_string in skip_strings)


def is_link_or_junction(path: Path) -> bool:
    """シンボリックリンクまたは Windows のジャンクションを検出する。"""
    if path.is_symlink():
        return True
    try:
        # Python 3.10 には Path.is_junction() がないため、再解析ポイントで判定する。
        return bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (AttributeError, FileNotFoundError, OSError):
        return False


def has_link_or_junction_component(path: Path) -> bool:
    """path 自身または親フォルダのいずれかがリンク／ジャンクションか調べる。"""
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if is_link_or_junction(current):
            return True
    return False


def is_hardlinked_file(path: Path) -> bool:
    """複数の名前で同じ実体を参照する通常ファイルを検出する。"""
    try:
        return path.is_file() and path.stat().st_nlink > 1
    except OSError:
        return False


def should_copy_file(source: Path, destination: Path, *, force: bool) -> bool:
    # ファイルとフォルダが同名の場合、意図しない場所へのコピーを防ぐ。
    if destination.exists() and destination.is_dir():
        raise IsADirectoryError(
            f"コピー先に同名のフォルダが存在するためコピーできません: {destination}"
        )
    if force or not destination.exists():
        return True
    # copy2() は更新時刻も維持するため、次回実行時に同一判定できる。
    return source.stat().st_mtime_ns != destination.stat().st_mtime_ns


def copy_tree(
    source: Path,
    destination: Path,
    *,
    skip_strings: list[str],
    force: bool,
    dry_run: bool,
) -> tuple[int, int]:
    """source 配下を走査し、destination に必要なファイルだけをコピーする。"""
    copied = 0
    skipped = 0

    # コピー先そのものまたは親にリンクがある場合、書き込み先の実体を保証できない。
    if has_link_or_junction_component(destination):
        print(f"[skip] コピー先にリンクまたはジャンクションが含まれます: {destination}")
        return copied, skipped + 1

    for current_dir, dirnames, filenames in os.walk(source):
        current = Path(current_dir)
        # dirnames をその場で絞ると、除外・リンクの各フォルダ配下には再帰しない。
        linked_dirs = [
            name for name in dirnames if is_link_or_junction(current / name)
        ]
        for name in linked_dirs:
            print(f"[skip] リンクまたはジャンクションのため除外: {current / name}")
            skipped += 1
        dirnames[:] = [
            name
            for name in dirnames
            if name not in linked_dirs and not is_skipped_folder(name, skip_strings)
        ]
        relative_dir = current.relative_to(source)
        target_dir = destination / relative_dir
        # コピー先ツリー内に後からリンクが見つかった場合も、その配下に書き込まない。
        if has_link_or_junction_component(target_dir):
            print(f"[skip] コピー先にリンクまたはジャンクションが含まれます: {target_dir}")
            skipped += len(filenames) + 1
            dirnames.clear()
            continue
        # ファイルが無いフォルダもコピー対象なので、先にフォルダを作成する。
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)

        for filename in filenames:
            source_file = current / filename
            target_file = target_dir / filename
            # リンクをたどるコピーや、ハードリンク実体の上書きは行わない。
            if is_link_or_junction(source_file) or is_hardlinked_file(source_file):
                print(f"[skip] コピー元がリンクまたはハードリンクです: {source_file}")
                skipped += 1
                continue
            if is_link_or_junction(target_file) or is_hardlinked_file(target_file):
                print(f"[skip] コピー先がリンクまたはハードリンクです: {target_file}")
                skipped += 1
                continue
            if should_copy_file(source_file, target_file, force=force):
                print(f"[copy] {source_file} -> {target_file}")
                if not dry_run:
                    # 内容に加え、更新時刻などのメタデータも保持する。
                    shutil.copy2(source_file, target_file)
                copied += 1
            else:
                print(f"[skip] {source_file} (更新時刻が同一)")
                skipped += 1

    return copied, skipped


def main() -> int:
    parsed = build_parser().parse_args()
    try:
        # 既存の共通処理で相対パス、~、環境変数を解決する。
        base_dir = arg_path.choose_base_dir(
            base_dir=parsed.cwd, prefer="cwd", entry_file=__file__
        )
        source = arg_path.resolve_cli_path(parsed.source_dir, base_dir=base_dir)
        destination = arg_path.resolve_cli_path(
            parsed.destination_dir, base_dir=base_dir
        )
        arg_path.validate_path(source, must_exist=True, kind="dir", readable=True)
        if is_link_or_junction(source):
            print(f"[skip] コピー元がリンクまたはジャンクションです: {source}")
            return 0
        # コピー先がコピー元の中にあると、自分自身を無限にコピーしてしまう。
        if destination == source or destination.is_relative_to(source):
            raise ValueError("コピー先にはコピー元フォルダまたはその配下を指定できません。")

        copied, skipped = copy_tree(
            source,
            destination,
            skip_strings=parsed.skip_folder_containing,
            force=parsed.force,
            dry_run=parsed.dry_run,
        )
        action = "コピー予定" if parsed.dry_run else "コピー完了"
        print(f"{action}: コピー {copied} 件、スキップ {skipped} 件")
        return 0
    except (OSError, ValueError) as error:
        print(f"エラー: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

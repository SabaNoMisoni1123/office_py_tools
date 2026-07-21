"""CLI エントリポイントで共有する、小さな補助関数群。

各コマンドは引数の解釈だけを担当し、パスの基準ディレクトリと
任意パスの解決はこのモジュールに集約する。これにより、ラッパー
スクリプトから渡される ``--cwd`` の意味をすべての CLI で統一する。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from mytools.common import arg_path


def add_cwd_argument(parser: argparse.ArgumentParser) -> None:
    """相対パスの基準となる必須の ``--cwd`` 引数を追加する。"""
    parser.add_argument("--cwd", required=True, help="相対パスを解決する基準ディレクトリ")


def resolve_base_dir(cwd: str, *, entry_file: str) -> Path:
    """CLI の ``--cwd`` を絶対パスとして正規化して返す。"""
    return arg_path.choose_base_dir(
        base_dir=Path(cwd), prefer="cwd", entry_file=entry_file
    )


def resolve_optional_path(value: str | None, *, base_dir: Path) -> Path | None:
    """省略可能な CLI パスを解決し、未指定時は ``None`` を返す。"""
    if value is None:
        return None
    return arg_path.resolve_cli_path(value, base_dir=base_dir)


def print_error(error: Exception) -> None:
    """利用者が読める形式で例外を表示する。"""
    print(f"エラー: {error}")

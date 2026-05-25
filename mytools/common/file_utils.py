from __future__ import annotations

from pathlib import Path

from mytools.common import arg_path


def ensure_file_exists(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"ファイルではありません: {path}")
    return path


def ensure_files_exist(paths: list[str], *, base_dir: Path | None = None) -> list[Path]:
    result: list[Path] = []

    for path_str in paths:
        path = arg_path.resolve_cli_path(path_str, base_dir=base_dir)
        ensure_file_exists(path)
        result.append(path)

    return result

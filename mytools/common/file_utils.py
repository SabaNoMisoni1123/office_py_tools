from __future__ import annotations

from pathlib import Path


def ensure_file_exists(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"ファイルではありません: {path}")
    return path


def ensure_files_exist(paths: list[str]) -> list[Path]:
    result: list[Path] = []

    for path_str in paths:
        path = Path(path_str)
        ensure_file_exists(path)
        result.append(path)

    return result
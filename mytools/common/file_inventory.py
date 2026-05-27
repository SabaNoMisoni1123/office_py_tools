from __future__ import annotations

import csv
import fnmatch
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from mytools.common import arg_path

DEFAULT_EXCLUDE_GLOBS = ("**/.git/**", "**/__pycache__/**", "**/.venv/**")


@dataclass(frozen=True)
class FileInventoryItem:
    path: Path
    relative_path: str
    name: str
    stem: str
    suffix: str
    size_bytes: int
    modified_at: str
    extension: str
    sha256: str | None
    naming_ok: bool | None


@dataclass(frozen=True)
class FileInventorySummary:
    root_dir: Path
    glob_pattern: str
    exclude_globs: tuple[str, ...]
    total_files: int
    total_size_bytes: int
    by_extension: dict[str, int]
    by_modified_month: dict[str, int]
    duplicate_names: dict[str, list[str]]
    duplicate_hashes: dict[str, list[str]]
    naming_violations: list[str]
    largest_files: list[FileInventoryItem]


def collect_inventory(
    *,
    root_dir: Path,
    glob_pattern: str,
    exclude_globs: tuple[str, ...],
    hash_algorithm: str,
    max_size_mb: int,
    naming_regex: str | None,
) -> tuple[list[FileInventoryItem], FileInventorySummary]:
    validate_root_dir(root_dir)
    validate_hash_algorithm(hash_algorithm)
    naming_pattern = re.compile(naming_regex) if naming_regex else None

    items: list[FileInventoryItem] = []
    for path in sorted(root_dir.glob(glob_pattern)):
        if not path.is_file():
            continue
        relative = path.relative_to(root_dir).as_posix()
        if is_excluded(relative, exclude_globs):
            continue
        stat = path.stat()
        sha256 = None
        if hash_algorithm == "sha256" and stat.st_size <= max_size_mb * 1024 * 1024:
            sha256 = calculate_sha256(path)
        naming_ok = None
        if naming_pattern is not None:
            naming_ok = naming_pattern.search(path.name) is not None
        items.append(
            FileInventoryItem(
                path=path,
                relative_path=relative,
                name=path.name,
                stem=path.stem,
                suffix=path.suffix,
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
                extension=path.suffix.lower() or "(none)",
                sha256=sha256,
                naming_ok=naming_ok,
            )
        )

    summary = build_summary(
        root_dir=root_dir,
        glob_pattern=glob_pattern,
        exclude_globs=exclude_globs,
        items=items,
    )
    return items, summary


def validate_root_dir(root_dir: Path) -> None:
    if not root_dir.exists():
        raise FileNotFoundError(f"棚卸し対象ディレクトリが見つかりません: {root_dir}")
    if not root_dir.is_dir():
        raise NotADirectoryError(f"棚卸し対象はディレクトリで指定してください: {root_dir}")


def validate_hash_algorithm(hash_algorithm: str) -> None:
    if hash_algorithm not in {"none", "sha256"}:
        raise ValueError("ハッシュ計算は none または sha256 を指定してください。")


def is_excluded(relative_path: str, exclude_globs: tuple[str, ...]) -> bool:
    candidates = (relative_path, f"/{relative_path}", f"**/{relative_path}")
    for pattern in exclude_globs:
        normalized = pattern.replace("\\", "/")
        for candidate in candidates:
            if fnmatch.fnmatch(candidate, normalized):
                return True
        parts = relative_path.split("/")
        if normalized.startswith("**/") and normalized.endswith("/**"):
            dirname = normalized[3:-3]
            if dirname in parts:
                return True
    return False


def calculate_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_summary(
    *,
    root_dir: Path,
    glob_pattern: str,
    exclude_globs: tuple[str, ...],
    items: list[FileInventoryItem],
) -> FileInventorySummary:
    by_extension: dict[str, int] = {}
    by_modified_month: dict[str, int] = {}
    names: dict[str, list[str]] = {}
    hashes: dict[str, list[str]] = {}
    naming_violations: list[str] = []

    for item in items:
        by_extension[item.extension] = by_extension.get(item.extension, 0) + 1
        month = item.modified_at[:7]
        by_modified_month[month] = by_modified_month.get(month, 0) + 1
        names.setdefault(item.name, []).append(item.relative_path)
        if item.sha256:
            hashes.setdefault(item.sha256, []).append(item.relative_path)
        if item.naming_ok is False:
            naming_violations.append(item.relative_path)

    duplicate_names = {
        name: paths for name, paths in sorted(names.items()) if len(paths) > 1
    }
    duplicate_hashes = {
        digest: paths for digest, paths in sorted(hashes.items()) if len(paths) > 1
    }
    largest_files = sorted(items, key=lambda item: item.size_bytes, reverse=True)[:20]
    return FileInventorySummary(
        root_dir=root_dir,
        glob_pattern=glob_pattern,
        exclude_globs=exclude_globs,
        total_files=len(items),
        total_size_bytes=sum(item.size_bytes for item in items),
        by_extension=dict(sorted(by_extension.items())),
        by_modified_month=dict(sorted(by_modified_month.items())),
        duplicate_names=duplicate_names,
        duplicate_hashes=duplicate_hashes,
        naming_violations=sorted(naming_violations),
        largest_files=largest_files,
    )


def write_inventory_csv(items: list[FileInventoryItem], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "path",
                "relative_path",
                "name",
                "stem",
                "suffix",
                "size_bytes",
                "modified_at",
                "extension",
                "sha256",
                "naming_ok",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "path": str(item.path),
                    "relative_path": item.relative_path,
                    "name": item.name,
                    "stem": item.stem,
                    "suffix": item.suffix,
                    "size_bytes": item.size_bytes,
                    "modified_at": item.modified_at,
                    "extension": item.extension,
                    "sha256": item.sha256 or "",
                    "naming_ok": "" if item.naming_ok is None else item.naming_ok,
                }
            )


def write_summary(summary: FileInventorySummary, output_path: Path, fmt: str) -> None:
    if fmt == "markdown":
        output_path.write_text(render_summary_markdown(summary), encoding="utf-8")
        return
    if fmt == "json":
        output_path.write_text(render_summary_json(summary), encoding="utf-8")
        return
    raise ValueError("サマリ形式は markdown または json を指定してください。")


def render_summary_json(summary: FileInventorySummary) -> str:
    data = asdict(summary)
    data["root_dir"] = str(summary.root_dir)
    data["largest_files"] = [
        {**asdict(item), "path": str(item.path)} for item in summary.largest_files
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


def render_summary_markdown(summary: FileInventorySummary) -> str:
    lines: list[str] = [
        "# ファイル棚卸しサマリ",
        "",
        "## 概要",
        "",
        f"- 対象ディレクトリ: `{summary.root_dir}`",
        f"- 対象パターン: `{summary.glob_pattern}`",
        f"- 除外パターン: {', '.join(f'`{p}`' for p in summary.exclude_globs) or 'なし'}",
        f"- ファイル数: {summary.total_files}",
        f"- 合計サイズ: {summary.total_size_bytes} bytes",
        "",
        "## 拡張子別サマリ",
        "",
        "| 拡張子 | 件数 |",
        "|---|---:|",
    ]
    for extension, count in summary.by_extension.items():
        lines.append(f"| {extension} | {count} |")

    lines.extend(["", "## 更新月別サマリ", "", "| 月 | 件数 |", "|---|---:|"])
    for month, count in summary.by_modified_month.items():
        lines.append(f"| {month} | {count} |")

    lines.extend(["", "## 大きいファイル上位", "", "| ファイル | サイズ |", "|---|---:|"])
    for item in summary.largest_files:
        lines.append(f"| `{item.relative_path}` | {item.size_bytes} |")

    lines.extend(["", "## 同名ファイル候補", ""])
    if summary.duplicate_names:
        for name, paths in summary.duplicate_names.items():
            lines.append(f"- `{name}`: {', '.join(f'`{p}`' for p in paths)}")
    else:
        lines.append("- なし")

    lines.extend(["", "## 同一ハッシュ候補", ""])
    if summary.duplicate_hashes:
        for digest, paths in summary.duplicate_hashes.items():
            lines.append(f"- `{digest}`: {', '.join(f'`{p}`' for p in paths)}")
    else:
        lines.append("- なし")

    lines.extend(["", "## 命名規則違反候補", ""])
    if summary.naming_violations:
        for path in summary.naming_violations:
            lines.append(f"- `{path}`")
    else:
        lines.append("- なし")
    lines.append("")
    return "\n".join(lines)


def ensure_output_allowed(path: Path | None, *, overwrite: bool, create_dirs: bool) -> None:
    if path is None:
        return
    parent = arg_path.ensure_parent_dir(path, create=create_dirs)
    if not parent.exists():
        raise FileNotFoundError(f"出力先の親ディレクトリが見つかりません: {parent}")
    if not parent.is_dir():
        raise NotADirectoryError(f"出力先の親パスはディレクトリではありません: {parent}")
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"出力ファイルは既に存在します。上書きする場合は --overwrite を指定してください: {path}"
        )


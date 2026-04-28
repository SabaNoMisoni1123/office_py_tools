from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from mytools.common.file_utils import ensure_file_exists


@dataclass(frozen=True)
class RenameItem:
    source: Path
    target: Path


@dataclass(frozen=True)
class RenameResult:
    source: Path
    target: Path
    changed: bool


def rename_with_basename(
    base_name: str,
    paths: Iterable[Path],
    *,
    start: int = 1,
    padding: int | None = None,
    separator: str = "_",
    dry_run: bool = False,
    overwrite: bool = False,
) -> list[RenameResult]:
    items = plan_basename_rename(
        base_name,
        paths,
        start=start,
        padding=padding,
        separator=separator,
        overwrite=overwrite,
    )
    return execute_rename_plan(items, dry_run=dry_run, overwrite=overwrite)


def add_prefix_to_filenames(
    prefix: str,
    paths: Iterable[Path],
    *,
    dry_run: bool = False,
    overwrite: bool = False,
) -> list[RenameResult]:
    items = plan_prefix_rename(prefix, paths, overwrite=overwrite)
    return execute_rename_plan(items, dry_run=dry_run, overwrite=overwrite)


def add_suffix_to_filenames(
    suffix: str,
    paths: Iterable[Path],
    *,
    dry_run: bool = False,
    overwrite: bool = False,
) -> list[RenameResult]:
    items = plan_suffix_rename(suffix, paths, overwrite=overwrite)
    return execute_rename_plan(items, dry_run=dry_run, overwrite=overwrite)


def plan_basename_rename(
    base_name: str,
    paths: Iterable[Path],
    *,
    start: int = 1,
    padding: int | None = None,
    separator: str = "_",
    overwrite: bool = False,
) -> list[RenameItem]:
    normalized_paths = _normalize_paths(paths)
    _validate_name_part(base_name, "base_name")
    _validate_name_part(separator, "separator", allow_empty=True)

    if start < 0:
        raise ValueError("start は 0 以上を指定してください。")

    if padding is not None and padding < 1:
        raise ValueError("padding は 1 以上を指定してください。")

    needs_number = len(normalized_paths) > 1
    if needs_number and padding is None:
        padding = max(2, len(str(start + len(normalized_paths) - 1)))

    items: list[RenameItem] = []
    for index, source in enumerate(normalized_paths):
        stem = base_name
        if needs_number:
            number = start + index
            number_text = str(number).zfill(padding or 0)
            stem = f"{base_name}{separator}{number_text}"

        target = source.with_name(f"{stem}{source.suffix}")
        items.append(RenameItem(source=source, target=target))

    validate_rename_plan(items, overwrite=overwrite)
    return items


def plan_prefix_rename(
    prefix: str,
    paths: Iterable[Path],
    *,
    overwrite: bool = False,
) -> list[RenameItem]:
    normalized_paths = _normalize_paths(paths)
    _validate_name_part(prefix, "prefix")

    items = [
        RenameItem(source=source, target=source.with_name(f"{prefix}{source.name}"))
        for source in normalized_paths
    ]
    validate_rename_plan(items, overwrite=overwrite)
    return items


def plan_suffix_rename(
    suffix: str,
    paths: Iterable[Path],
    *,
    overwrite: bool = False,
) -> list[RenameItem]:
    normalized_paths = _normalize_paths(paths)
    _validate_name_part(suffix, "suffix")

    items = [
        RenameItem(
            source=source,
            target=source.with_name(f"{source.stem}{suffix}{source.suffix}"),
        )
        for source in normalized_paths
    ]
    validate_rename_plan(items, overwrite=overwrite)
    return items


def validate_rename_plan(items: list[RenameItem], *, overwrite: bool = False) -> None:
    if not items:
        raise ValueError("リネーム対象ファイルを 1 件以上指定してください。")

    source_paths = [item.source for item in items]
    if len(set(source_paths)) != len(source_paths):
        raise ValueError("同じファイルが複数回指定されています。")

    target_paths = [item.target for item in items]
    if len(set(target_paths)) != len(target_paths):
        raise ValueError("複数のファイルが同じ変更後ファイル名になります。")

    for item in items:
        ensure_file_exists(item.source)
        if item.target == item.source:
            continue
        if item.target.exists() and not overwrite:
            raise FileExistsError(f"変更後ファイルが既に存在します: {item.target}")
        if item.target.exists() and item.target in source_paths:
            raise FileExistsError(
                f"変更後ファイルがリネーム対象にも含まれています: {item.target}"
            )


def execute_rename_plan(
    items: list[RenameItem],
    *,
    dry_run: bool = False,
    overwrite: bool = False,
) -> list[RenameResult]:
    validate_rename_plan(items, overwrite=overwrite)

    results: list[RenameResult] = []
    for item in items:
        if item.source == item.target:
            results.append(
                RenameResult(source=item.source, target=item.target, changed=False)
            )
            continue

        if not dry_run:
            if overwrite:
                item.source.replace(item.target)
            else:
                item.source.rename(item.target)

        results.append(
            RenameResult(source=item.source, target=item.target, changed=True)
        )

    return results


def _normalize_paths(paths: Iterable[Path]) -> list[Path]:
    if paths is None:
        raise ValueError("paths は None にできません。")
    return [Path(path) for path in paths]


def _validate_name_part(value: str, label: str, *, allow_empty: bool = False) -> None:
    if value is None:
        raise ValueError(f"{label} は None にできません。")

    if not allow_empty and value == "":
        raise ValueError(f"{label} は空文字にできません。")

    invalid_chars = {"/", "\\"}
    if any(char in value for char in invalid_chars):
        raise ValueError(f"{label} にパス区切り文字は使えません。")

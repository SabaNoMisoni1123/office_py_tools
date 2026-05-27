from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mytools.common.file_inventory import (
    DEFAULT_EXCLUDE_GLOBS,
    FileInventoryItem,
    FileInventorySummary,
    collect_inventory,
    ensure_output_allowed,
    write_inventory_csv,
    write_summary,
)


@dataclass(frozen=True)
class FileAuditRequest:
    cwd: Path
    root_dir: Path
    glob_pattern: str | None
    exclude_globs: tuple[str, ...]
    summary_output_path: Path | None
    list_output_path: Path | None
    summary_format: str
    hash_algorithm: str | None
    max_size_mb: int | None
    naming_regex: str | None
    config_path: Path | None
    dry_run: bool
    overwrite: bool
    create_dirs: bool


@dataclass(frozen=True)
class FileAuditPlan:
    root_dir: Path
    glob_pattern: str
    exclude_globs: tuple[str, ...]
    summary_output_path: Path | None
    list_output_path: Path | None
    summary_format: str
    hash_algorithm: str
    max_size_mb: int
    naming_regex: str | None
    item_count: int
    summary: FileInventorySummary


def run_file_audit(request: FileAuditRequest) -> FileAuditPlan:
    plan, items = build_plan(request)
    if request.dry_run:
        return plan
    if plan.summary_output_path is not None:
        write_summary(plan.summary, plan.summary_output_path, plan.summary_format)
    if plan.list_output_path is not None:
        write_inventory_csv(items, plan.list_output_path)
    return plan


def build_plan(
    request: FileAuditRequest,
) -> tuple[FileAuditPlan, list[FileInventoryItem]]:
    config = load_config(request.config_path)
    glob_pattern = request.glob_pattern or str(config.get("glob") or "**/*")
    config_excludes = tuple(str(item) for item in config.get("exclude_globs", ()))
    exclude_globs = request.exclude_globs or config_excludes or DEFAULT_EXCLUDE_GLOBS
    hash_algorithm = request.hash_algorithm or str(config.get("hash") or "none")
    max_size_mb = request.max_size_mb or int(config.get("max_size_mb") or 100)
    naming_regex = request.naming_regex
    if naming_regex is None and config.get("naming_regex") is not None:
        naming_regex = str(config.get("naming_regex"))

    if request.summary_format not in {"markdown", "json"}:
        raise ValueError("サマリ形式は markdown または json を指定してください。")
    if max_size_mb < 0:
        raise ValueError("--max-size-mb は 0 以上を指定してください。")

    ensure_output_allowed(
        request.summary_output_path,
        overwrite=request.overwrite,
        create_dirs=request.create_dirs,
    )
    ensure_output_allowed(
        request.list_output_path,
        overwrite=request.overwrite,
        create_dirs=request.create_dirs,
    )

    items, summary = collect_inventory(
        root_dir=request.root_dir,
        glob_pattern=glob_pattern,
        exclude_globs=exclude_globs,
        hash_algorithm=hash_algorithm,
        max_size_mb=max_size_mb,
        naming_regex=naming_regex,
    )
    return (
        FileAuditPlan(
            root_dir=request.root_dir,
            glob_pattern=glob_pattern,
            exclude_globs=exclude_globs,
            summary_output_path=request.summary_output_path,
            list_output_path=request.list_output_path,
            summary_format=request.summary_format,
            hash_algorithm=hash_algorithm,
            max_size_mb=max_size_mb,
            naming_regex=naming_regex,
            item_count=len(items),
            summary=summary,
        ),
        items,
    )


def load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"設定ファイルはファイルで指定してください: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("設定ファイルのルートは JSON オブジェクトにしてください。")
    return data


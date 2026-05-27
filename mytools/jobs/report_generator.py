from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from mytools.common import arg_path
from mytools.common.tabular.reader import read_table


@dataclass(frozen=True)
class ReportGenerateRequest:
    cwd: Path
    input_path: Path
    config_path: Path
    output_path: Path
    sheet_name: str | None
    encoding: str
    summary_csv_output_path: Path | None
    title: str | None
    template_path: Path | None
    dry_run: bool
    overwrite: bool
    create_dirs: bool


@dataclass(frozen=True)
class ReportGeneratePlan:
    input_path: Path
    output_path: Path
    title: str
    row_count: int
    filtered_row_count: int
    group_by: tuple[str, ...]
    metric_names: tuple[str, ...]
    summary_csv_output_path: Path | None
    overwrite: bool
    rows: list[dict[str, Any]]


def generate_report(request: ReportGenerateRequest) -> ReportGeneratePlan:
    plan = build_plan(request)
    if request.dry_run:
        return plan

    write_markdown_report(plan, template_path=request.template_path)
    if request.summary_csv_output_path is not None:
        write_summary_csv(plan.rows, request.summary_csv_output_path)
    return plan


def build_plan(request: ReportGenerateRequest) -> ReportGeneratePlan:
    validate_input_path(request.input_path)
    validate_output_path(
        request.output_path,
        overwrite=request.overwrite,
        create_dirs=request.create_dirs,
    )
    validate_output_path(
        request.summary_csv_output_path,
        overwrite=request.overwrite,
        create_dirs=request.create_dirs,
        allow_none=True,
    )
    config = load_config(request.config_path)
    header_row = int(config.get("input", {}).get("header_row", 1))
    records = read_table(
        request.input_path,
        sheet_name=request.sheet_name,
        encoding=request.encoding,
        header_row=header_row,
    )
    filtered = apply_filters(records, config.get("filters", []))
    group_by = tuple(str(item) for item in config.get("group_by", ()))
    metrics = config.get("metrics", [])
    validate_columns(records, group_by, metrics)
    summary_rows = aggregate(filtered, group_by=group_by, metrics=metrics)
    summary_rows = sort_rows(summary_rows, config.get("sort", []))
    if config.get("top_n") is not None:
        summary_rows = summary_rows[: int(config["top_n"])]

    title = request.title or str(config.get("title") or "集計レポート")
    return ReportGeneratePlan(
        input_path=request.input_path,
        output_path=request.output_path,
        title=title,
        row_count=len(records),
        filtered_row_count=len(filtered),
        group_by=group_by,
        metric_names=tuple(str(metric["name"]) for metric in metrics),
        summary_csv_output_path=request.summary_csv_output_path,
        overwrite=request.overwrite,
        rows=summary_rows,
    )


def validate_input_path(input_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {input_path}")
    if not input_path.is_file():
        raise FileNotFoundError(f"入力はファイルで指定してください: {input_path}")
    if input_path.suffix.lower() not in {".csv", ".xlsx"}:
        raise ValueError("入力ファイルは .csv または .xlsx を指定してください。")


def validate_output_path(
    output_path: Path | None,
    *,
    overwrite: bool,
    create_dirs: bool,
    allow_none: bool = False,
) -> None:
    if output_path is None:
        if allow_none:
            return
        raise ValueError("出力パスを指定してください。")
    parent = arg_path.ensure_parent_dir(output_path, create=create_dirs)
    if not parent.exists():
        raise FileNotFoundError(f"出力先の親ディレクトリが見つかりません: {parent}")
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"出力ファイルは既に存在します。上書きする場合は --overwrite を指定してください: {output_path}"
        )


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"設定ファイルはファイルで指定してください: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("設定ファイルのルートは JSON オブジェクトにしてください。")
    return data


def apply_filters(
    records: list[dict[str, Any]], filters: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not filters:
        return list(records)
    for item in filters:
        if not isinstance(item, dict):
            raise ValueError("filters はオブジェクト配列で指定してください。")
    return [record for record in records if all(match_filter(record, item) for item in filters)]


def match_filter(record: dict[str, Any], item: dict[str, Any]) -> bool:
    column = str(item.get("column"))
    operator = str(item.get("operator"))
    expected = item.get("value")
    if column not in record:
        raise ValueError(f"フィルタ対象列が入力に存在しません: {column}")
    value = record.get(column)
    text = "" if value is None else str(value)
    expected_text = "" if expected is None else str(expected)
    if operator == "equals":
        return text == expected_text
    if operator == "not_equals":
        return text != expected_text
    if operator == "contains":
        return expected_text in text
    if operator == "not_empty":
        return text != ""
    if operator == "empty":
        return text == ""
    raise ValueError(f"未対応のフィルタ演算子です: {operator}")


def validate_columns(
    records: list[dict[str, Any]], group_by: tuple[str, ...], metrics: list[dict[str, Any]]
) -> None:
    columns = set(records[0].keys()) if records else set()
    for column in group_by:
        if column not in columns:
            raise ValueError(f"集計キー列が入力に存在しません: {column}")
    for metric in metrics:
        if not isinstance(metric, dict):
            raise ValueError("metrics はオブジェクト配列で指定してください。")
        metric_type = str(metric.get("type"))
        if metric_type != "count":
            column = str(metric.get("column"))
            if column not in columns:
                raise ValueError(f"指標列が入力に存在しません: {column}")
        if "name" not in metric:
            raise ValueError("metrics[].name は必須です。")


def aggregate(
    records: list[dict[str, Any]], *, group_by: tuple[str, ...], metrics: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for record in records:
        key = tuple(record.get(column) for column in group_by)
        groups.setdefault(key, []).append(record)

    rows: list[dict[str, Any]] = []
    for key, group_records in groups.items():
        row: dict[str, Any] = {}
        for index, column in enumerate(group_by):
            row[column] = key[index]
        for metric in metrics:
            row[str(metric["name"])] = calculate_metric(group_records, metric)
        rows.append(row)
    if not group_by and not rows:
        rows.append({str(metric["name"]): calculate_metric([], metric) for metric in metrics})
    return rows


def calculate_metric(records: list[dict[str, Any]], metric: dict[str, Any]) -> Any:
    metric_type = str(metric.get("type"))
    if metric_type == "count":
        return len(records)
    column = str(metric.get("column"))
    values = [to_number(record.get(column), column) for record in records]
    if metric_type == "sum":
        return sum(values)
    if metric_type == "avg":
        return sum(values) / len(values) if values else 0
    if metric_type == "min":
        return min(values) if values else 0
    if metric_type == "max":
        return max(values) if values else 0
    raise ValueError(f"未対応の指標種別です: {metric_type}")


def to_number(value: Any, column: str) -> float:
    if value is None or value == "":
        raise ValueError(f"数値集計対象列に空値があります: {column}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"数値として解釈できない値があります: {column}={value}") from exc


def sort_rows(rows: list[dict[str, Any]], sort_config: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_rows = list(rows)
    for item in reversed(sort_config or []):
        column = str(item.get("column"))
        reverse = str(item.get("direction", "asc")).lower() == "desc"
        sorted_rows.sort(key=lambda row: row.get(column), reverse=reverse)
    return sorted_rows


def write_markdown_report(plan: ReportGeneratePlan, *, template_path: Path | None) -> None:
    content = render_markdown(plan)
    if template_path is not None:
        if not template_path.exists():
            raise FileNotFoundError(f"テンプレートが見つかりません: {template_path}")
        template = template_path.read_text(encoding="utf-8")
        content = template.replace("{{content}}", content)
    plan.output_path.write_text(content, encoding="utf-8")


def render_markdown(plan: ReportGeneratePlan) -> str:
    lines = [
        f"# {plan.title}",
        "",
        "## 概要",
        "",
        f"- 入力ファイル: `{plan.input_path}`",
        f"- 対象行数: {plan.row_count}",
        f"- フィルタ後行数: {plan.filtered_row_count}",
        f"- 作成日時: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## 集計結果",
        "",
    ]
    if not plan.rows:
        lines.append("集計結果はありません。")
        lines.append("")
        return "\n".join(lines)

    headers = list(plan.rows[0].keys())
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in plan.rows:
        lines.append("| " + " | ".join(format_cell(row.get(header)) for header in headers) + " |")
    lines.append("")
    return "\n".join(lines)


def format_cell(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return "" if value is None else str(value)


def write_summary_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    if not rows:
        output_path.write_text("", encoding="utf-8-sig")
        return
    headers = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

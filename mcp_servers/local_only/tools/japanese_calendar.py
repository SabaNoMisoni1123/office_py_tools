from __future__ import annotations

from datetime import date
from typing import Any

import jpholiday
from mcp.server.fastmcp import FastMCP

WEEKDAYS_JA = ("月", "火", "水", "木", "金", "土", "日")
WEEKDAYS_JA_LONG = (
    "月曜日",
    "火曜日",
    "水曜日",
    "木曜日",
    "金曜日",
    "土曜日",
    "日曜日",
)


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def get_japanese_date_info(date_text: str) -> dict[str, Any]:
        """YYYY-MM-DD の日付から曜日、日本の祝日、営業日可否を返します。"""
        return get_date_info(date_text)


def get_date_info(date_text: str) -> dict[str, Any]:
    target_date = _parse_iso_date(date_text)
    weekday_index = target_date.weekday()
    holiday_name = jpholiday.is_holiday_name(target_date)
    is_weekend = weekday_index >= 5
    is_japanese_holiday = holiday_name is not None

    return {
        "date": target_date.isoformat(),
        "year": target_date.year,
        "month": target_date.month,
        "day": target_date.day,
        "weekday_index": weekday_index,
        "weekday": WEEKDAYS_JA[weekday_index],
        "weekday_name": WEEKDAYS_JA_LONG[weekday_index],
        "is_saturday": weekday_index == 5,
        "is_sunday": weekday_index == 6,
        "is_weekend": is_weekend,
        "is_japanese_holiday": is_japanese_holiday,
        "holiday_name": holiday_name,
        "is_business_day": not is_weekend and not is_japanese_holiday,
        "source": "jpholiday package, based on Cabinet Office Japan holiday data",
        "accuracy_note": _accuracy_note(target_date),
    }


def _parse_iso_date(date_text: str) -> date:
    if date_text is None:
        raise ValueError(
            "date_text は None にできません。YYYY-MM-DD 形式で指定してください。"
        )

    normalized = str(date_text).strip()
    if not normalized:
        raise ValueError(
            "date_text は空文字列にできません。YYYY-MM-DD 形式で指定してください。"
        )

    try:
        return date.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            f"日付は YYYY-MM-DD 形式で指定してください: {date_text}"
        ) from exc


def _accuracy_note(target_date: date) -> str:
    if target_date.year <= 2026:
        return (
            "jpholiday が公式発表済みデータに基づく動作確認対象としている"
            "範囲です。"
        )
    if target_date.year == 2027:
        return (
            "内閣府は 2027 年の祝日一覧を公表済みです。jpholiday の収録状況は"
            "利用バージョンに依存します。"
        )
    return (
        "将来年の春分の日・秋分の日などは公式発表前に変わる可能性があります。"
        "最終確認には内閣府の最新公表を参照してください。"
    )

"""PDF を画像として扱う CLI で共通に使う品質設定。"""

from __future__ import annotations

from typing import Final


# DPI はレンダリング品質と処理時間・出力サイズのトレードオフを表す。
QUALITY_DPI_MAP: Final[dict[str, int]] = {
    "low": 150,
    "medium": 300,
    "high": 600,
}


def quality_to_dpi(quality: str) -> int:
    """品質名を DPI に変換し、未対応値には分かりやすく失敗する。"""
    try:
        return QUALITY_DPI_MAP[quality]
    except KeyError as exc:
        supported = ", ".join(sorted(QUALITY_DPI_MAP))
        raise ValueError(
            f"未対応の品質です: {quality}。指定できる値: {supported}"
        ) from exc

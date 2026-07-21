"""PDF の全ページを PNG へ変換する CLI。"""

from __future__ import annotations

import argparse
from typing import Sequence

from mytools.common import arg_path
from mytools.common.cli import add_cwd_argument, print_error, resolve_base_dir, resolve_optional_path
from mytools.common.pdf import (
    QUALITY_DPI_MAP,
    PdfPageImage,
    convert_pdf_to_png_images,
    plan_pdf_to_png_images,
    quality_to_dpi,
)


def main() -> int:
    """引数を解決して変換計画を表示、または変換を実行する。"""
    parsed = build_parser().parse_args()
    try:
        base_dir = resolve_base_dir(parsed.cwd, entry_file=__file__)
        pdf_path = arg_path.resolve_cli_path(parsed.pdf_path, base_dir=base_dir)
        output_dir = resolve_optional_path(parsed.output_dir, base_dir=base_dir)
        results = (
            plan_pdf_to_png_images(pdf_path, output_dir=output_dir)
            if parsed.dry_run
            else convert_pdf_to_png_images(
                pdf_path,
                output_dir=output_dir,
                dpi=quality_to_dpi(parsed.quality),
                overwrite=parsed.overwrite,
            )
        )
    except (ImportError, OSError, ValueError) as error:
        print_error(error)
        return 1

    print_results(results, dry_run=parsed.dry_run)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """この CLI の引数定義を構築する。"""
    parser = argparse.ArgumentParser(description="PDF の全ページを PNG 画像に変換します。")
    add_cwd_argument(parser)
    parser.add_argument("--pdf-path", required=True, help="入力 PDF ファイル")
    parser.add_argument("--output-dir", help="PNG の出力先ディレクトリ")
    parser.add_argument(
        "--quality", choices=sorted(QUALITY_DPI_MAP), default="medium",
        help="描画品質: low=150, medium=300, high=600 DPI（既定: medium）",
    )
    parser.add_argument("--dry-run", action="store_true", help="変更せず出力予定だけを表示")
    parser.add_argument("--overwrite", action="store_true", help="既存の PNG を上書き")
    return parser


def print_results(results: Sequence[PdfPageImage], *, dry_run: bool) -> None:
    """ページごとの出力先を表示する。"""
    print("変換予定:" if dry_run else "変換結果:")
    for result in results:
        status = "plan" if dry_run else "created"
        print(f"- [{status}] page {result.page_number}: {result.target}")


if __name__ == "__main__":
    raise SystemExit(main())

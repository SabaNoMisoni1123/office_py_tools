"""2 つの PDF をページ画像として比較する CLI。"""

from __future__ import annotations

import argparse

from mytools.common import arg_path
from mytools.common.cli import add_cwd_argument, print_error, resolve_base_dir, resolve_optional_path
from mytools.common.pdf import QUALITY_DPI_MAP, PdfDiffResult, compare_pdf_pages_as_images, quality_to_dpi


def main() -> int:
    """比較を実行する。差分ありは終了コード 1、実行エラーは 2 を返す。"""
    parsed = build_parser().parse_args()
    try:
        base_dir = resolve_base_dir(parsed.cwd, entry_file=__file__)
        result = compare_pdf_pages_as_images(
            arg_path.resolve_cli_path(parsed.left_pdf, base_dir=base_dir),
            arg_path.resolve_cli_path(parsed.right_pdf, base_dir=base_dir),
            output_dir=resolve_optional_path(parsed.output_dir, base_dir=base_dir),
            dpi=quality_to_dpi(parsed.quality),
            threshold=parsed.threshold,
            overwrite=parsed.overwrite,
        )
    except (ImportError, OSError, ValueError) as error:
        print_error(error)
        return 2

    print_result(result)
    return 1 if result.changed else 0


def build_parser() -> argparse.ArgumentParser:
    """この CLI の引数定義を構築する。"""
    parser = argparse.ArgumentParser(description="2 つの PDF をページ画像として比較します。")
    add_cwd_argument(parser)
    parser.add_argument("--left-pdf", required=True, help="比較元 PDF")
    parser.add_argument("--right-pdf", required=True, help="比較先 PDF")
    parser.add_argument("--output-dir", help="差分 PNG の出力先ディレクトリ")
    parser.add_argument("--quality", choices=sorted(QUALITY_DPI_MAP), default="medium")
    parser.add_argument("--threshold", type=int, default=0, help="無視する RGB チャンネル差（0〜255）")
    parser.add_argument("--overwrite", action="store_true", help="既存の差分 PNG を上書き")
    return parser


def print_result(result: PdfDiffResult) -> None:
    """比較結果を人が読みやすい形で表示する。"""
    print(f"出力先: {result.output_dir}")
    if not result.same_page_count:
        print(f"ページ数が異なります: left={result.left_page_count}, right={result.right_page_count}")
        return
    print("差分あり" if result.changed else "差分なし")
    for page in result.pages:
        if page.changed:
            ratio = page.diff_pixels / page.total_pixels * 100
            print(f"- page {page.page_number}: {ratio:.4f}% changed, diff={page.diff_image}")


if __name__ == "__main__":
    raise SystemExit(main())

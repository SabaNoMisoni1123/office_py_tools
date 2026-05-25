from __future__ import annotations

import argparse

from mytools.common import arg_path
from mytools.common.pdf import compare_pdf_pages_as_images
from mytools.pdf_to_png import QUALITY_DPI_MAP, quality_to_dpi


def main() -> int:
    parser = build_parser()
    parsed_arg = parser.parse_args()

    base_dir = arg_path.choose_base_dir(
        base_dir=parsed_arg.cwd, prefer="cwd", entry_file=__file__
    )
    left_pdf = arg_path.resolve_cli_path(parsed_arg.left_pdf, base_dir=base_dir)
    right_pdf = arg_path.resolve_cli_path(parsed_arg.right_pdf, base_dir=base_dir)
    output_dir = (
        arg_path.resolve_cli_path(parsed_arg.output_dir, base_dir=base_dir)
        if parsed_arg.output_dir is not None
        else None
    )

    try:
        result = compare_pdf_pages_as_images(
            left_pdf,
            right_pdf,
            output_dir=output_dir,
            dpi=quality_to_dpi(parsed_arg.quality),
            threshold=parsed_arg.threshold,
            overwrite=parsed_arg.overwrite,
        )
        print_result(result)
        return 1 if result.changed else 0
    except Exception as e:
        print(f"エラー: {e}")
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="2つの PDF をページごとに画像比較し、差分 PNG を出力します。"
    )
    parser.add_argument("--cwd", required=True, help="相対パス解決の基準ディレクトリ")
    parser.add_argument("--left-pdf", required=True, help="比較元の PDF ファイル")
    parser.add_argument("--right-pdf", required=True, help="比較先の PDF ファイル")
    parser.add_argument(
        "--output-dir",
        help="比較結果の出力先ディレクトリ。省略時は left PDF と同じ場所の diff_<left>__<right>",
    )
    parser.add_argument(
        "--quality",
        choices=sorted(QUALITY_DPI_MAP),
        default="medium",
        help="比較時の画像化品質。low=150DPI, medium=300DPI, high=600DPI。既定値は medium。",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=0,
        help="RGB 各チャンネルの差分許容値。0 は完全一致比較、1 以上で微小差分を無視します。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="出力先 PNG が既に存在する場合に上書きします。",
    )
    return parser


def print_result(result) -> None:
    print(f"出力先: {result.output_dir}")
    if not result.same_page_count:
        print("差分あり: ページ数が異なります。")
        print(f"- left: {result.left_page_count} ページ")
        print(f"- right: {result.right_page_count} ページ")
        return

    print("差分あり:" if result.changed else "差分なし:")
    for page in result.pages:
        if page.changed:
            ratio = page.diff_pixels / page.total_pixels * 100
            print(
                f"- page {page.page_number}: changed "
                f"({page.diff_pixels}/{page.total_pixels} pixels, {ratio:.4f}%) "
                f"diff={page.diff_image}"
            )
        else:
            print(f"- page {page.page_number}: same")


if __name__ == "__main__":
    raise SystemExit(main())

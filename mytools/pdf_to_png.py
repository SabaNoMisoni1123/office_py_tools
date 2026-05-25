from __future__ import annotations

import argparse

from mytools.common import arg_path
from mytools.common.pdf import convert_pdf_to_png_images, plan_pdf_to_png_images

QUALITY_DPI_MAP = {
    "low": 150,
    "medium": 300,
    "high": 600,
}


def main() -> int:
    parser = build_parser()
    parsed_arg = parser.parse_args()

    base_dir = arg_path.choose_base_dir(
        base_dir=parsed_arg.cwd, prefer="cwd", entry_file=__file__
    )
    pdf_path = arg_path.resolve_cli_path(parsed_arg.pdf_path, base_dir=base_dir)
    output_dir = (
        arg_path.resolve_cli_path(parsed_arg.output_dir, base_dir=base_dir)
        if parsed_arg.output_dir is not None
        else None
    )

    try:
        if parsed_arg.dry_run:
            results = plan_pdf_to_png_images(pdf_path, output_dir=output_dir)
        else:
            results = convert_pdf_to_png_images(
                pdf_path,
                output_dir=output_dir,
                dpi=quality_to_dpi(parsed_arg.quality),
                overwrite=parsed_arg.overwrite,
            )
        print_results(results, dry_run=parsed_arg.dry_run)
        return 0
    except Exception as e:
        print(f"エラー: {e}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PDF の全ページを PNG 画像に変換します。"
    )
    parser.add_argument("--cwd", required=True, help="相対パス解決の基準ディレクトリ")
    parser.add_argument("--pdf-path", required=True, help="変換対象の PDF ファイル")
    parser.add_argument(
        "--output-dir",
        help="PNG 画像の出力先ディレクトリ。省略時は PDF と同じ場所の img_<PDF名>",
    )
    parser.add_argument(
        "--quality",
        choices=sorted(QUALITY_DPI_MAP),
        default="medium",
        help="PNG 変換時の画質。low=150DPI, medium=300DPI, high=600DPI。既定値は medium。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="実際には作成せず、作成予定の PNG ファイルを表示します。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="出力先 PNG が既に存在する場合に上書きします。",
    )
    return parser


def quality_to_dpi(quality: str) -> int:
    try:
        return QUALITY_DPI_MAP[quality]
    except KeyError as exc:
        supported = ", ".join(sorted(QUALITY_DPI_MAP))
        raise ValueError(f"未対応の画質です: {quality}. 指定可能な値: {supported}") from exc


def print_results(results: list, *, dry_run: bool) -> None:
    title = "作成予定" if dry_run else "作成結果"
    print(f"{title}:")
    for result in results:
        status = "plan" if dry_run else "created"
        print(f"- [{status}] page {result.page_number}: {result.target}")


if __name__ == "__main__":
    raise SystemExit(main())

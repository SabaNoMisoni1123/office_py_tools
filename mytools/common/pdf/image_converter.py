from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mytools.common.file_utils import ensure_file_exists


@dataclass(frozen=True)
class PdfPageImage:
    page_number: int
    target: Path
    created: bool


def build_default_output_dir(pdf_path: Path) -> Path:
    pdf = Path(pdf_path)
    return pdf.with_name(f"img_{pdf.stem}")


def plan_pdf_to_png_images(
    pdf_path: Path,
    *,
    output_dir: Path | None = None,
) -> list[PdfPageImage]:
    pdf = _validate_pdf_path(pdf_path)
    output = _normalize_output_dir(pdf, output_dir)
    page_count = _get_pdf_page_count(pdf)
    padding = max(3, len(str(page_count)))

    return [
        PdfPageImage(
            page_number=page_number,
            target=output / f"page_{page_number:0{padding}d}.png",
            created=False,
        )
        for page_number in range(1, page_count + 1)
    ]


def convert_pdf_to_png_images(
    pdf_path: Path,
    *,
    output_dir: Path | None = None,
    dpi: int = 200,
    overwrite: bool = False,
) -> list[PdfPageImage]:
    if dpi <= 0:
        raise ValueError("dpi は 1 以上を指定してください。")

    pdf = _validate_pdf_path(pdf_path)
    output = _normalize_output_dir(pdf, output_dir)
    planned_images = plan_pdf_to_png_images(pdf, output_dir=output)

    if output.exists() and not output.is_dir():
        raise NotADirectoryError(f"出力先がディレクトリではありません: {output}")

    existing_targets = [item.target for item in planned_images if item.target.exists()]
    if existing_targets and not overwrite:
        raise FileExistsError(
            "出力先 PNG が既に存在します。上書きする場合は --overwrite を指定してください: "
            f"{existing_targets[0]}"
        )

    fitz = _import_pymupdf()
    output.mkdir(parents=True, exist_ok=True)

    results: list[PdfPageImage] = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(str(pdf)) as document:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            target = planned_images[page_index].target
            pixmap.save(str(target))
            results.append(
                PdfPageImage(
                    page_number=page_index + 1,
                    target=target,
                    created=True,
                )
            )

    return results


def get_pdf_page_count(pdf_path: Path) -> int:
    pdf = _validate_pdf_path(pdf_path)
    return _get_pdf_page_count(pdf)


def _validate_pdf_path(pdf_path: Path) -> Path:
    pdf = ensure_file_exists(Path(pdf_path))
    if pdf.suffix.lower() != ".pdf":
        raise ValueError(f"PDF ファイルを指定してください: {pdf}")
    return pdf


def _normalize_output_dir(pdf_path: Path, output_dir: Path | None) -> Path:
    if output_dir is None:
        return build_default_output_dir(pdf_path)
    return Path(output_dir)


def _get_pdf_page_count(pdf_path: Path) -> int:
    fitz = _import_pymupdf()
    with fitz.open(str(pdf_path)) as document:
        page_count = document.page_count

    if page_count < 1:
        raise ValueError(f"PDF にページがありません: {pdf_path}")
    return page_count


def _import_pymupdf():
    try:
        import fitz
    except ImportError as exc:
        raise ImportError(
            "PDF 画像変換には PyMuPDF が必要です。"
            " `python -m pip install -r requirements.txt` を実行してください。"
        ) from exc
    return fitz

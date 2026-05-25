from __future__ import annotations

import zlib
from dataclasses import dataclass
from pathlib import Path

from mytools.common.pdf.image_converter import _import_pymupdf, _validate_pdf_path


@dataclass(frozen=True)
class PdfDiffPageResult:
    page_number: int
    changed: bool
    diff_pixels: int
    total_pixels: int
    diff_image: Path | None


@dataclass(frozen=True)
class PdfDiffResult:
    left_pdf: Path
    right_pdf: Path
    output_dir: Path
    same_page_count: bool
    left_page_count: int
    right_page_count: int
    changed: bool
    pages: list[PdfDiffPageResult]


def build_default_diff_output_dir(left_pdf_path: Path, right_pdf_path: Path) -> Path:
    left = Path(left_pdf_path)
    right = Path(right_pdf_path)
    return left.parent / f"diff_{left.stem}__{right.stem}"


def compare_pdf_pages_as_images(
    left_pdf_path: Path,
    right_pdf_path: Path,
    *,
    output_dir: Path | None = None,
    dpi: int = 300,
    threshold: int = 0,
    overwrite: bool = False,
) -> PdfDiffResult:
    if dpi <= 0:
        raise ValueError("dpi は 1 以上を指定してください。")
    if threshold < 0 or threshold > 255:
        raise ValueError("threshold は 0 から 255 の範囲で指定してください。")

    left_pdf = _validate_pdf_path(left_pdf_path)
    right_pdf = _validate_pdf_path(right_pdf_path)
    output = (
        Path(output_dir)
        if output_dir is not None
        else build_default_diff_output_dir(left_pdf, right_pdf)
    )

    fitz = _import_pymupdf()
    with fitz.open(str(left_pdf)) as left_document, fitz.open(
        str(right_pdf)
    ) as right_document:
        left_page_count = left_document.page_count
        right_page_count = right_document.page_count

        if left_page_count != right_page_count:
            return PdfDiffResult(
                left_pdf=left_pdf,
                right_pdf=right_pdf,
                output_dir=output,
                same_page_count=False,
                left_page_count=left_page_count,
                right_page_count=right_page_count,
                changed=True,
                pages=[],
            )

        targets = _build_planned_targets(output, left_page_count)
        _validate_output_targets(targets, overwrite=overwrite)
        (output / "diff_pages").mkdir(parents=True, exist_ok=True)

        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        page_results: list[PdfDiffPageResult] = []

        for page_index in range(left_page_count):
            page_number = page_index + 1
            diff_image = targets[page_index]
            left_pixmap = left_document.load_page(page_index).get_pixmap(
                matrix=matrix, alpha=False
            )
            right_pixmap = right_document.load_page(page_index).get_pixmap(
                matrix=matrix, alpha=False
            )

            diff_pixels, total_pixels, diff_rgb, diff_width, diff_height = build_diff_rgb(
                left_pixmap.samples,
                left_pixmap.width,
                left_pixmap.height,
                right_pixmap.samples,
                right_pixmap.width,
                right_pixmap.height,
                threshold=threshold,
            )

            changed = diff_pixels > 0
            if changed:
                write_rgb_png(diff_image, diff_rgb, diff_width, diff_height)

            page_results.append(
                PdfDiffPageResult(
                    page_number=page_number,
                    changed=changed,
                    diff_pixels=diff_pixels,
                    total_pixels=total_pixels,
                    diff_image=diff_image if changed else None,
                )
            )

    return PdfDiffResult(
        left_pdf=left_pdf,
        right_pdf=right_pdf,
        output_dir=output,
        same_page_count=True,
        left_page_count=left_page_count,
        right_page_count=right_page_count,
        changed=any(page.changed for page in page_results),
        pages=page_results,
    )


def build_diff_rgb(
    left_samples: bytes,
    left_width: int,
    left_height: int,
    right_samples: bytes,
    right_width: int,
    right_height: int,
    *,
    threshold: int = 0,
) -> tuple[int, int, bytes, int, int]:
    output_width = max(left_width, right_width)
    output_height = max(left_height, right_height)
    total_pixels = output_width * output_height
    diff_pixels = 0
    output = bytearray(total_pixels * 3)

    for y in range(output_height):
        for x in range(output_width):
            output_offset = (y * output_width + x) * 3
            left_rgb = _get_rgb_at(left_samples, left_width, left_height, x, y)
            right_rgb = _get_rgb_at(right_samples, right_width, right_height, x, y)

            if left_rgb is None or right_rgb is None:
                changed = True
                base_rgb = (255, 255, 255)
            else:
                changed = _rgb_distance_over_threshold(left_rgb, right_rgb, threshold)
                base_rgb = _to_grayscale_rgb(left_rgb)

            if changed:
                diff_pixels += 1
                output[output_offset : output_offset + 3] = bytes((255, 0, 0))
            else:
                output[output_offset : output_offset + 3] = bytes(base_rgb)

    return diff_pixels, total_pixels, bytes(output), output_width, output_height


def write_rgb_png(path: Path, rgb_data: bytes, width: int, height: int) -> None:
    if width <= 0 or height <= 0:
        raise ValueError("PNG の幅と高さは 1 以上である必要があります。")

    expected_size = width * height * 3
    if len(rgb_data) != expected_size:
        raise ValueError(
            f"RGB データサイズが不正です: expected={expected_size}, actual={len(rgb_data)}"
        )

    raw_rows = bytearray()
    row_size = width * 3
    for y in range(height):
        raw_rows.append(0)
        start = y * row_size
        raw_rows.extend(rgb_data[start : start + row_size])

    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(
            b"IHDR",
            width.to_bytes(4, "big")
            + height.to_bytes(4, "big")
            + b"\x08\x02\x00\x00\x00",
        )
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw_rows)))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(png_bytes)


def _build_planned_targets(output_dir: Path, page_count: int) -> list[Path]:
    padding = max(3, len(str(page_count)))
    return [
        output_dir / "diff_pages" / f"page_{page_number:0{padding}d}_diff.png"
        for page_number in range(1, page_count + 1)
    ]


def _validate_output_targets(
    planned_targets: list[Path],
    *,
    overwrite: bool,
) -> None:
    existing_targets = [target for target in planned_targets if target.exists()]
    if existing_targets and not overwrite:
        raise FileExistsError(
            "出力先ファイルが既に存在します。上書きする場合は --overwrite を指定してください: "
            f"{existing_targets[0]}"
        )


def _get_rgb_at(
    samples: bytes,
    width: int,
    height: int,
    x: int,
    y: int,
) -> tuple[int, int, int] | None:
    if x >= width or y >= height:
        return None
    offset = (y * width + x) * 3
    return samples[offset], samples[offset + 1], samples[offset + 2]


def _rgb_distance_over_threshold(
    left_rgb: tuple[int, int, int],
    right_rgb: tuple[int, int, int],
    threshold: int,
) -> bool:
    return any(abs(left - right) > threshold for left, right in zip(left_rgb, right_rgb))


def _to_grayscale_rgb(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    gray = int(rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114)
    return gray, gray, gray


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(chunk_type)
    checksum = zlib.crc32(data, checksum)
    return (
        len(data).to_bytes(4, "big")
        + chunk_type
        + data
        + checksum.to_bytes(4, "big")
    )

from __future__ import annotations

import os
from pathlib import Path

from mytools.common.markdown.pandoc_runner import ExternalDependencyError


def prepare_reference_doc(template_path: Path, temp_dir: Path) -> Path:
    suffix = template_path.suffix.lower()
    if suffix == ".docx":
        return template_path
    if suffix != ".dotx":
        raise ValueError("Word テンプレートには .dotx または .docx を指定してください。")

    if os.name != "nt":
        raise ExternalDependencyError(
            "dotx テンプレートを使うには Windows と Microsoft Word が必要です。"
            "非 Windows 環境では docx 参照文書を指定してください。"
        )

    return convert_dotx_to_docx(template_path, temp_dir)


def convert_dotx_to_docx(template_path: Path, temp_dir: Path) -> Path:
    try:
        import win32com.client  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ExternalDependencyError(
            "dotx テンプレートを使うには pywin32 が必要です。"
            "pywin32 をインストールするか、docx 参照文書を指定してください。"
        ) from exc

    output_path = temp_dir / f"{template_path.stem}_reference.docx"
    word = None
    document = None
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        document = word.Documents.Add(
            Template=str(template_path),
            NewTemplate=False,
            DocumentType=0,
        )
        document.SaveAs2(str(output_path), FileFormat=16)
        return output_path
    except Exception as exc:
        raise ExternalDependencyError(
            f"dotx テンプレートから参照 docx を作成できませんでした: {exc}"
        ) from exc
    finally:
        if document is not None:
            document.Close(False)
        if word is not None:
            word.Quit()

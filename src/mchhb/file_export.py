"""Excel / PDF ファイルの一括生成。"""

from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

from .convert import process_response_to_extraction
from .excel_export import export_to_excel
from .models import ProcessResponse
from .pdf_export import export_to_pdf


def export_files(
    response: ProcessResponse,
    output_dir: Path,
    *,
    base_name: str = "vaccination_record",
) -> tuple[Path, Path]:
    """ProcessResponse から Excel と PDF を生成する。"""
    extraction = process_response_to_extraction(response)
    excel_path = output_dir / f"{base_name}.xlsx"
    pdf_path = output_dir / f"{base_name}.pdf"
    export_to_excel(extraction, excel_path, child_name=response.child_name)
    export_to_pdf(extraction, pdf_path, child_name=response.child_name)
    return excel_path, pdf_path


def export_zip(response: ProcessResponse, *, base_name: str = "vaccination_record") -> bytes:
    """Excel と PDF を ZIP にまとめて返す。"""
    buffer = io.BytesIO()
    with tempfile.TemporaryDirectory() as td, zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        excel_path, pdf_path = export_files(response, Path(td), base_name=base_name)
        zf.write(excel_path, arcname=excel_path.name)
        zf.write(pdf_path, arcname=pdf_path.name)
    return buffer.getvalue()

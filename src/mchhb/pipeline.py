"""OCR → JSON 整形パイプライン（Claude API のみ）。"""

from __future__ import annotations

from .clinic_utils import merge_split_clinic_names
from .claude_vision import extract_vaccinations_from_image
from .config import validate_for_processing
from .field_cleanup import sanitize_vaccination_records
from .formatter import format_ocr_text
from .models import ProcessImageResult, ProcessResponse, VaccinationRecord
from .ocr import ocr_image
from .ocr_prompts import is_ocr_refusal


def _merge_vaccinations(
    existing: list[VaccinationRecord],
    new_items: list[VaccinationRecord],
) -> list[VaccinationRecord]:
    """複数画像の結果をマージ（同一キーは後勝ち）。"""
    index: dict[tuple[str | None, str | None, str | None], VaccinationRecord] = {}
    for item in existing + new_items:
        key = (item.vaccine_name, item.dose_number, item.date)
        index[key] = item
    return list(index.values())


def process_images(images: list[tuple[str, bytes, str]]) -> ProcessResponse:
    """複数画像を処理する。"""
    validate_for_processing()

    ocr_results: list[ProcessImageResult] = []
    combined_ocr_parts: list[str] = []
    all_notes: list[str] = ["Claude Vision API で OCR しています。"]
    direct_extractions: list[VaccinationRecord] = []
    child_name: str | None = None

    for filename, image_bytes, mime_type in images:
        ocr_result, ocr_notes = ocr_image(image_bytes, mime_type)
        ocr_text = ocr_result.text
        all_notes.extend(ocr_notes)

        if not ocr_text.strip() or is_ocr_refusal(ocr_text):
            direct, pseudo_ocr, direct_notes = extract_vaccinations_from_image(image_bytes, mime_type)
            all_notes.extend(direct_notes)
            if direct.child_name and not child_name:
                child_name = direct.child_name
            direct_extractions = _merge_vaccinations(direct_extractions, direct.vaccinations)
            ocr_text = pseudo_ocr or ocr_text

        ocr_results.append(ProcessImageResult(filename=filename, ocr_text=ocr_text))
        if ocr_text.strip() and not is_ocr_refusal(ocr_text):
            combined_ocr_parts.append(f"## 画像: {filename}\n{ocr_text}")

    merged_vaccinations: list[VaccinationRecord] = list(direct_extractions)

    combined_ocr = "\n\n".join(combined_ocr_parts)
    if combined_ocr.strip():
        extraction, notes = format_ocr_text(combined_ocr)
        all_notes.extend(notes)
        if extraction.child_name and not child_name:
            child_name = extraction.child_name
        merged_vaccinations = _merge_vaccinations(merged_vaccinations, extraction.vaccinations)

    merged_vaccinations = merge_split_clinic_names(
        merged_vaccinations,
        combined_ocr or "\n\n".join(r.ocr_text for r in ocr_results),
    )
    merged_vaccinations = sanitize_vaccination_records(merged_vaccinations)

    return ProcessResponse(
        child_name=child_name,
        vaccinations=merged_vaccinations,
        ocr_results=ocr_results,
        notes=all_notes,
    )

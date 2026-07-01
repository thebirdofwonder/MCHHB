"""ProcessResponse を Excel/PDF 用スキーマに変換。"""

from __future__ import annotations

import re
from typing import Optional

from .models import ProcessResponse, VaccinationRecord
from .schema import ExtractionResult, VaccinationEntry


def _parse_dose_number(value: Optional[str]) -> int:
    if not value:
        return 1
    m = re.search(r"(\d+)", value)
    return int(m.group(1)) if m else 1


def _parse_dose_category(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    for label in ("I期 初回", "I期 追加", "II期"):
        if label.replace(" ", "") in value.replace(" ", ""):
            return label
    return None


def _split_manufacturer_lot(value: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not value:
        return None, None
    s = value.strip()
    lot_match = re.search(r"\b([A-Z]{1,4}\d[\w-]*)\b", s)
    if lot_match:
        lot = lot_match.group(1)
        manufacturer = s.replace(lot, "").strip(" /-")
        return manufacturer or None, lot
    return s, None


def record_to_entry(record: VaccinationRecord) -> VaccinationEntry:
    manufacturer, lot = _split_manufacturer_lot(record.manufacturer_lot)
    institution = record.clinic
    if record.remark and institution:
        institution = f"{institution}（{record.remark}）"
    elif record.remark:
        institution = record.remark

    return VaccinationEntry(
        vaccine_key=record.vaccine_name or "",
        dose_number=_parse_dose_number(record.dose_number),
        date=record.date,
        manufacturer=manufacturer,
        lot_number=lot,
        institution=institution,
        dose_category=_parse_dose_category(record.dose_number),
        confidence=record.confidence,
    )


def process_response_to_extraction(response: ProcessResponse) -> ExtractionResult:
    return ExtractionResult(
        child_name=response.child_name,
        entries=[record_to_entry(v) for v in response.vaccinations],
        raw_notes=response.notes,
    )

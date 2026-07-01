"""医療機関名の結合・正規化（印鑑の複数行対応）。"""

from __future__ import annotations

import re
from typing import Sequence

from .models import VaccinationRecord
from .ocr_types import OcrLine

CLINIC_SUFFIX_RE = re.compile(r"(クリニック|病院|医院|診療所|保健所|メディカルセンター|医療センター)")
DATE_RE = re.compile(r"\d{4}[-/.年]")
LOT_RE = re.compile(r"^[A-Z0-9\-]+$", re.IGNORECASE)
HYPHEN_TRAIL_RE = re.compile(r"[-－\s]+$")


def join_clinic_fragments(fragments: Sequence[str | OcrLine]) -> str:
    """
    医療機関欄内の複数 OCR 断片を1名称に結合する。

    - 上から下の順（OcrLine の場合は yMin → xMin）
    - 日本語は原則スペースなし
    - 行末の半角/全角ハイフンのみ除去（長音「ー」は保持）
    """
    if not fragments:
        return ""

    if isinstance(fragments[0], OcrLine):
        sorted_lines = sorted(fragments, key=lambda ln: (ln.bbox.y_min, ln.bbox.x_min))  # type: ignore[arg-type]
        parts = [ln.text.strip() for ln in sorted_lines if ln.text.strip()]  # type: ignore[union-attr]
    else:
        parts = [str(p).strip() for p in fragments if str(p).strip()]

    merged = ""
    for part in parts:
        part = HYPHEN_TRAIL_RE.sub("", part)
        merged += part
    return merged.strip()


def _is_clinic_suffix_line(line: str) -> bool:
    line = line.strip()
    return bool(line) and bool(CLINIC_SUFFIX_RE.search(line)) and len(line) <= 40


def _is_clinic_prefix_line(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 25:
        return False
    if DATE_RE.search(line) or LOT_RE.match(line):
        return False
    if CLINIC_SUFFIX_RE.search(line):
        return False
    return bool(re.search(r"[\u3040-\u9fff\u30a0-\u30ff]", line))


def extract_clinic_pairs_from_ocr(ocr_text: str) -> dict[str, str]:
    """OCR プレーンテキストから部分名→完全名マップを抽出（フォールバック用）。"""
    pairs: dict[str, str] = {}
    lines = [ln.strip() for ln in ocr_text.splitlines() if ln.strip()]

    for i in range(1, len(lines)):
        prev, curr = lines[i - 1], lines[i]
        if _is_clinic_suffix_line(curr) and _is_clinic_prefix_line(prev):
            full = join_clinic_fragments([prev, curr])
            pairs[curr] = full
            pairs[prev] = full

    for match in re.finditer(
        r"([\u3040-\u9fff\u30a0-\u30ff]{2,20})(こどもクリニック|[\u3040-\u9fff\u30a0-\u30ff]{1,15}(?:クリニック|病院|医院|診療所))",
        ocr_text,
    ):
        full = match.group(0)
        suffix = match.group(2)
        if suffix not in pairs or len(full) > len(pairs[suffix]):
            pairs[suffix] = full

    return pairs


def _best_full_name(clinic: str, pairs: dict[str, str]) -> str:
    if not clinic:
        return clinic
    clinic = clinic.strip()
    if clinic in pairs:
        return pairs[clinic]

    for partial, full in pairs.items():
        if clinic == partial or full.endswith(clinic):
            return full

    return clinic


def _propagate_clinic_by_date(records: list[VaccinationRecord]) -> None:
    by_date: dict[str, list[VaccinationRecord]] = {}
    for record in records:
        if record.date:
            by_date.setdefault(record.date, []).append(record)

    for group in by_date.values():
        clinics = [r.clinic.strip() for r in group if r.clinic and r.clinic.strip()]
        if len(clinics) < 2:
            continue
        longest = max(clinics, key=len)
        for record in group:
            if not record.clinic:
                continue
            current = record.clinic.strip()
            if len(current) < len(longest) and (current in longest or longest.endswith(current)):
                record.clinic = longest


def merge_split_clinic_names(
    records: list[VaccinationRecord],
    ocr_text: str,
) -> list[VaccinationRecord]:
    """テキストベースの医療機関名結合（Vision OCR フォールバック用）。"""
    pairs = extract_clinic_pairs_from_ocr(ocr_text)

    for record in records:
        if record.clinic:
            record.clinic = _best_full_name(record.clinic, pairs)

    _propagate_clinic_by_date(records)
    return records

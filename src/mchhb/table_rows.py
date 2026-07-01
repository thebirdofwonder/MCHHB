"""出力表の行構成（記録ありのみ + テンプレート外ワクチン）。"""

from __future__ import annotations

from dataclasses import dataclass

from .schema import (
    VACCINE_TEMPLATE,
    ExtractionResult,
    VaccinationEntry,
    VaccineRow,
    match_entry_to_template,
    template_key,
)


@dataclass
class OutputTableRow:
    template: VaccineRow
    entry: VaccinationEntry
    is_extra: bool = False


def _entry_has_data(entry: VaccinationEntry) -> bool:
    return bool(entry.date or entry.manufacturer or entry.lot_number or entry.institution)


def _extra_template_row(entry: VaccinationEntry) -> VaccineRow:
    return VaccineRow(
        disease_en=entry.vaccine_key,
        vaccine_ja=entry.vaccine_key,
        dose_category=entry.dose_category or "",
        dose_number=entry.dose_number,
        merge_disease_rows=1,
        merge_vaccine_rows=1,
    )


def build_output_rows(result: ExtractionResult) -> list[OutputTableRow]:
    """
    出力表の行を構築する。

    - テンプレート行: 接種記録があるものだけ含める
    - テンプレートにないワクチン: 末尾に行を追加
    """
    matched: dict[str, VaccinationEntry] = {}
    extras: list[VaccinationEntry] = []

    for entry in result.entries:
        if not _entry_has_data(entry):
            continue
        tkey = match_entry_to_template(entry)
        if tkey:
            matched[tkey] = entry
        else:
            extras.append(entry)

    rows: list[OutputTableRow] = []
    for template_row in VACCINE_TEMPLATE:
        tkey = template_key(template_row)
        entry = matched.get(tkey)
        if entry:
            rows.append(OutputTableRow(template=template_row, entry=entry, is_extra=False))

    for entry in extras:
        rows.append(
            OutputTableRow(
                template=_extra_template_row(entry),
                entry=entry,
                is_extra=True,
            )
        )

    return rows


def disease_merge_spans(rows: list[VaccineRow], *, start_index: int = 0) -> list[tuple[int, int]]:
    """縦結合する disease 列の (開始行, 終了行) インデックス（0-based, rows 内）。"""
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(rows)
    while i < n:
        j = i + 1
        while j < n and rows[j].disease_en == rows[i].disease_en:
            j += 1
        if j - i > 1:
            spans.append((start_index + i, start_index + j - 1))
        i = j
    return spans


def vaccine_merge_spans(rows: list[VaccineRow], *, start_index: int = 0) -> list[tuple[int, int]]:
    """縦結合する vaccine 列の (開始行, 終了行) インデックス。"""
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(rows)
    while i < n:
        j = i + 1
        while j < n and rows[j].vaccine_ja == rows[i].vaccine_ja and rows[j].disease_en == rows[i].disease_en:
            j += 1
        if j - i > 1:
            spans.append((start_index + i, start_index + j - 1))
        i = j
    return spans

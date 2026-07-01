"""Document AI の座標情報から接種記録行を再構成する。"""

from __future__ import annotations

import re
from typing import Optional

from .clinic_utils import join_clinic_fragments
from .field_cleanup import is_schedule_or_page_noise
from .ocr_types import BBox, LayoutVaccinationRow, OcrLine

HEADER_SKIP_RE = re.compile(
    r"(ワクチン|接種年月日|メーカー|ロット|接種者|備考|Vaccine|Y/M/D|Physician|Remarks|予防接種)",
    re.IGNORECASE,
)
DATE_IN_TEXT_RE = re.compile(
    r"(20\d{2}|令和|平成|昭和)[^\d]{0,3}(\d{1,2})[^\d]{0,3}(\d{1,2})|"
    r"(20\d{2})[./\-年](\d{1,2})[./\-月](\d{1,2})"
)
PAGE_NO_RE = re.compile(r"^\d{1,3}$")

DEFAULT_COLUMNS = {
    "vaccine": (0.0, 0.22),
    "date": (0.16, 0.34),
    "manufacturer_lot": (0.30, 0.52),
    "clinic": (0.50, 0.72),
    "remark": (0.70, 0.84),
}
TABLE_X_MAX_DEFAULT = 0.86


def _normalize_date(text: str) -> Optional[str]:
    text = text.strip()
    m = re.search(r"(20\d{2})[./\-年](\d{1,2})[./\-月](\d{1,2})", text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"
    return None


def _is_noise_line(line: OcrLine) -> bool:
    text = line.text.strip()
    if not text or len(text) <= 1:
        return True
    if PAGE_NO_RE.match(text):
        return True
    if HEADER_SKIP_RE.search(text) and len(text) < 20:
        return True
    if is_schedule_or_page_noise(text):
        return True
    return False


def _table_x_max(lines: list[OcrLine]) -> float:
    """接種記録表の右端（隣ページの文字を除外する境界）。"""
    xs: list[float] = []
    for ln in lines:
        text = ln.text.strip()
        if is_schedule_or_page_noise(text):
            continue
        if (
            DATE_IN_TEXT_RE.search(text)
            or _manufacturer_lot_like(text)
            or _clinic_like(text)
            or _remark_like(text)
        ):
            xs.append(ln.bbox.x_max)
    if xs:
        return min(0.92, max(xs) + 0.04)
    return TABLE_X_MAX_DEFAULT


def _in_table_bounds(line: OcrLine, x_max: float) -> bool:
    return line.bbox.center_x <= x_max and line.bbox.x_min < x_max


def _manufacturer_lot_like(text: str) -> bool:
    text = text.strip()
    return bool(
        re.search(r"[A-Z]{1,4}\d", text)
        or re.search(r"\d+[A-Z]{1,3}\d*", text)
        or "ファイザー" in text
        or "バクス" in text
        or "MSD" in text
        or "タケダ" in text
        or "シノジ" in text
    )


def _remark_like(text: str) -> bool:
    text = text.strip()
    return bool(
        re.match(r"^[\d.]+\s*ml$", text, re.I)
        or text in ("左", "右")
        or re.match(r"^[左右上下]$", text)
        or re.match(r"^\d+\.?\d*\s*ml", text, re.I)
    )


def _clinic_like(text: str) -> bool:
    return bool(
        re.search(r"(クリニック|病院|医院|診療所|こども|子ども|リバーシティ|愛育|センター|保健所)", text)
    )


def _cluster_rows(lines: list[OcrLine], y_threshold: float = 0.025) -> list[list[OcrLine]]:
    table_x_max = _table_x_max(lines)
    usable = [
        ln for ln in lines if not _is_noise_line(ln) and _in_table_bounds(ln, table_x_max)
    ]
    if not usable:
        return []

    date_anchors = [ln for ln in usable if DATE_IN_TEXT_RE.search(ln.text)]
    if date_anchors:
        date_anchors.sort(key=lambda ln: ln.bbox.center_y)
        used: set[int] = set()
        clusters: list[list[OcrLine]] = []

        for anchor in date_anchors:
            cluster = [anchor]
            used.add(id(anchor))
            band_min = anchor.bbox.y_min - y_threshold
            band_max = anchor.bbox.y_max + y_threshold

            for ln in usable:
                if id(ln) in used:
                    continue
                cy = ln.bbox.center_y
                if band_min <= cy <= band_max or ln.bbox.vertical_overlap_ratio(anchor.bbox) >= 0.25:
                    cluster.append(ln)
                    used.add(id(ln))
            clusters.append(cluster)

        leftovers = [ln for ln in usable if id(ln) not in used]
        for ln in leftovers:
            placed = False
            for cluster in clusters:
                anchor = next((x for x in cluster if DATE_IN_TEXT_RE.search(x.text)), cluster[0])
                if abs(ln.bbox.center_y - anchor.bbox.center_y) <= y_threshold * 1.5:
                    cluster.append(ln)
                    placed = True
                    break
            if not placed:
                clusters.append([ln])

        clusters.sort(key=lambda c: min(ln.bbox.center_y for ln in c))
        return clusters

    usable.sort(key=lambda ln: (ln.bbox.center_y, ln.bbox.x_min))
    clusters: list[list[OcrLine]] = []
    for line in usable:
        placed = False
        for cluster in clusters:
            ref = cluster[0]
            if abs(line.bbox.center_y - ref.bbox.center_y) <= y_threshold:
                cluster.append(line)
                placed = True
                break
        if not placed:
            clusters.append([line])
    return clusters


def _infer_column_ranges(lines: list[OcrLine]) -> dict[str, tuple[float, float]]:
    date_x: list[float] = []
    lot_x: list[float] = []
    clinic_x: list[float] = []
    remark_x: list[float] = []
    vaccine_x: list[float] = []

    for ln in lines:
        text = ln.text.strip()
        if DATE_IN_TEXT_RE.search(text):
            date_x.append(ln.bbox.center_x)
        elif _remark_like(text):
            remark_x.append(ln.bbox.center_x)
        elif _manufacturer_lot_like(text):
            lot_x.append(ln.bbox.center_x)
        elif _clinic_like(text):
            clinic_x.append(ln.bbox.center_x)
        elif len(text) >= 3 and ln.bbox.center_x < 0.28:
            vaccine_x.append(ln.bbox.center_x)

    def span(values: list[float], default: tuple[float, float], pad: float = 0.06) -> tuple[float, float]:
        if not values:
            return default
        lo, hi = min(values), max(values)
        return (max(0.0, lo - pad), min(1.0, hi + pad))

    return {
        "vaccine": span(vaccine_x, DEFAULT_COLUMNS["vaccine"]),
        "date": span(date_x, DEFAULT_COLUMNS["date"]),
        "manufacturer_lot": span(lot_x, DEFAULT_COLUMNS["manufacturer_lot"]),
        "clinic": span(clinic_x, DEFAULT_COLUMNS["clinic"]),
        "remark": span(remark_x, DEFAULT_COLUMNS["remark"]),
    }


def _in_column(line: OcrLine, x_range: tuple[float, float]) -> bool:
    return x_range[0] <= line.bbox.center_x <= x_range[1]


def _classify_line(
    ln: OcrLine,
    columns: dict[str, tuple[float, float]],
    table_x_max: float,
) -> str:
    """1 OCR 行を列カテゴリに分類（排他的）。"""
    text = ln.text.strip()
    cx = ln.bbox.center_x

    if not _in_table_bounds(ln, table_x_max) or is_schedule_or_page_noise(text):
        return "unknown"

    if DATE_IN_TEXT_RE.search(text):
        return "date"
    if _remark_like(text) or (_in_column(ln, columns["remark"]) and cx >= columns["clinic"][0]):
        return "remark"
    if _manufacturer_lot_like(text) and cx < columns["clinic"][0]:
        return "manufacturer_lot"
    if _clinic_like(text) and cx >= columns["clinic"][0] and cx < columns["remark"][1]:
        return "clinic"
    if _in_column(ln, columns["manufacturer_lot"]) and cx < columns["clinic"][0]:
        return "manufacturer_lot"
    if _in_column(ln, columns["clinic"]) and cx >= columns["clinic"][0]:
        return "clinic"
    if _in_column(ln, columns["remark"]):
        return "remark"
    if _in_column(ln, columns["vaccine"]) or cx < columns["date"][0]:
        return "vaccine"
    if cx < 0.28:
        return "vaccine"
    return "unknown"


def _assign_cluster(
    cluster: list[OcrLine],
    columns: dict[str, tuple[float, float]],
    table_x_max: float,
) -> LayoutVaccinationRow:
    vaccine_parts: list[OcrLine] = []
    date_parts: list[OcrLine] = []
    lot_parts: list[OcrLine] = []
    clinic_parts: list[OcrLine] = []
    remark_parts: list[OcrLine] = []

    for ln in sorted(cluster, key=lambda x: (x.bbox.center_y, x.bbox.center_x)):
        category = _classify_line(ln, columns, table_x_max)
        if category == "date":
            date_parts.append(ln)
        elif category == "remark":
            remark_parts.append(ln)
        elif category == "manufacturer_lot":
            lot_parts.append(ln)
        elif category == "clinic":
            clinic_parts.append(ln)
        elif category == "vaccine":
            vaccine_parts.append(ln)

    from .field_cleanup import clean_manufacturer_lot, clean_remark, extract_clinic_name

    vaccine_name = join_clinic_fragments([ln.text for ln in sorted(vaccine_parts, key=lambda x: x.bbox.x_min)])
    manufacturer_lot = clean_manufacturer_lot(
        join_clinic_fragments(
            [ln.text for ln in sorted(lot_parts, key=lambda x: (x.bbox.y_min, x.bbox.x_min))]
        )
    )
    clinic = extract_clinic_name(join_clinic_fragments(clinic_parts))
    remark = clean_remark(
        join_clinic_fragments([ln.text for ln in sorted(remark_parts, key=lambda x: x.bbox.x_min)])
    )

    date = _normalize_date(" ".join(ln.text for ln in date_parts))

    ys = [ln.bbox.y_min for ln in cluster]
    xs = [ln.bbox.x_min for ln in cluster]
    x2 = [ln.bbox.x_max for ln in cluster]
    y2 = [ln.bbox.y_max for ln in cluster]
    row_bbox = BBox(min(xs), min(ys), max(x2), max(y2)) if cluster else BBox(0, 0, 0, 0)
    avg_conf = sum(ln.confidence for ln in cluster) / len(cluster) if cluster else 0.0

    return LayoutVaccinationRow(
        vaccine_name=vaccine_name or None,
        date=date,
        manufacturer_lot=manufacturer_lot or None,
        clinic=clinic or None,
        remark=remark or None,
        bbox=row_bbox,
        confidence=avg_conf,
    )


def extract_layout_rows(lines: list[OcrLine]) -> list[LayoutVaccinationRow]:
    if not lines:
        return []
    columns = _infer_column_ranges(lines)
    table_x_max = _table_x_max(lines)
    rows: list[LayoutVaccinationRow] = []
    for cluster in _cluster_rows(lines):
        row = _assign_cluster(cluster, columns, table_x_max)
        if row.vaccine_name or row.date or row.manufacturer_lot or row.clinic or row.remark:
            rows.append(row)
    return rows


def layout_rows_to_hint_text(rows: list[LayoutVaccinationRow]) -> str:
    if not rows:
        return ""
    parts = ["[Document AI レイアウト解析ヒント — 列ごとに分離済み]"]
    for i, row in enumerate(rows, 1):
        parts.append(
            f"行{i}: ワクチン={row.vaccine_name or '?'} | 接種日={row.date or '?'} | "
            f"メーカー又は製剤名／ロット={row.manufacturer_lot or '?'} | "
            f"医療機関={row.clinic or '?'} | 備考={row.remark or '?'}"
        )
    return "\n".join(parts)


def _match_layout_row(record, row: LayoutVaccinationRow) -> bool:
    date_match = record.date and row.date and record.date == row.date
    if not date_match:
        return False
    if record.vaccine_name and row.vaccine_name:
        a = record.vaccine_name.replace(" ", "")
        b = row.vaccine_name.replace(" ", "")
        return a in b or b in a
    return True


def apply_layout_field_overrides(
    records: list,
    layout_rows: list[LayoutVaccinationRow],
) -> None:
    """レイアウト解析結果で各列を上書き（日付・ワクチン名でマッチ）。"""
    from .models import VaccinationRecord

    for record in records:
        if not isinstance(record, VaccinationRecord):
            continue
        best: Optional[LayoutVaccinationRow] = None
        for row in layout_rows:
            if _match_layout_row(record, row):
                best = row
                break
            if record.date and row.date and record.date == row.date and not best:
                best = row

        if not best:
            continue

        if best.manufacturer_lot:
            record.manufacturer_lot = best.manufacturer_lot
        if best.clinic:
            if not record.clinic or len(best.clinic) >= len(record.clinic):
                record.clinic = best.clinic
        if best.remark:
            record.remark = best.remark


# 後方互換
apply_layout_clinic_overrides = apply_layout_field_overrides

"""レイアウト解析・医療機関名結合のテスト。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mchhb.clinic_utils import join_clinic_fragments
from mchhb.layout import extract_layout_rows
from mchhb.ocr_types import BBox, OcrLine


def _line(text: str, x0: float, y0: float, x1: float, y1: float) -> OcrLine:
    return OcrLine(text=text, bbox=BBox(x0, y0, x1, y1))


def test_join_clinic_fragments():
    assert join_clinic_fragments(["リバーシティ", "こどもクリニック"]) == "リバーシティこどもクリニック"
    assert join_clinic_fragments(["リバーシティ-", "こどもクリニック"]) == "リバーシティこどもクリニック"


def test_layout_merges_stamp_and_separates_columns():
    lines = [
        _line("小児用肺炎球菌", 0.05, 0.30, 0.18, 0.34),
        _line("2026.6.23", 0.22, 0.30, 0.32, 0.34),
        _line("MJ4998ファイザー", 0.40, 0.30, 0.55, 0.34),
        _line("リバーシティ", 0.65, 0.29, 0.78, 0.32),
        _line("こどもクリニック", 0.65, 0.32, 0.82, 0.35),
        _line("0.5ml", 0.88, 0.30, 0.95, 0.34),
    ]
    rows = extract_layout_rows(lines)
    row = next(r for r in rows if r.date == "2026-06-23")
    assert row.manufacturer_lot == "MJ4998ファイザー"
    assert row.clinic == "リバーシティこどもクリニック"
    assert row.remark == "0.5ml"
    assert "ファイザー" not in (row.clinic or "")
    assert "0.5ml" not in (row.clinic or "")


if __name__ == "__main__":
    test_join_clinic_fragments()
    test_layout_merges_stamp_and_separates_columns()
    print("All tests passed")

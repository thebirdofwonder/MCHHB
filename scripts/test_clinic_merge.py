"""医療機関名結合のテスト。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mchhb.clinic_utils import extract_clinic_pairs_from_ocr, merge_split_clinic_names
from mchhb.models import VaccinationRecord


def test_river_city_clinic_pair():
    ocr = """
小児用肺炎球菌
2026.6.23
リバーシティ
こどもクリニック
"""
    pairs = extract_clinic_pairs_from_ocr(ocr)
    assert pairs["こどもクリニック"] == "リバーシティこどもクリニック"


def test_merge_clinic_on_records():
    ocr = "リバーシティ\nこどもクリニック\n"
    records = [
        VaccinationRecord(
            vaccine_name="小児用肺炎球菌",
            dose_number="1回目",
            date="2026-06-23",
            clinic="こどもクリニック",
        ),
        VaccinationRecord(
            vaccine_name="B型肝炎",
            dose_number="1回目",
            date="2026-06-23",
            clinic="こどもクリニック",
        ),
    ]
    merge_split_clinic_names(records, ocr)
    assert all(r.clinic == "リバーシティこどもクリニック" for r in records)


if __name__ == "__main__":
    test_river_city_clinic_pair()
    test_merge_clinic_on_records()
    print("All tests passed")

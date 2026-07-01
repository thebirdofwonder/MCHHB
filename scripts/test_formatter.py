"""formatter のユニットテスト（API 呼び出しなし）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mchhb.formatter import _normalize_record
from mchhb.models import VaccinationRecord


def test_normalize_sets_needs_review_on_null_fields():
    record = _normalize_record(
        {
            "vaccine_name": "小児用肺炎球菌",
            "dose_number": "1回目",
            "date": "2024-06-10",
            "lot_number": None,
            "clinic": None,
            "confidence": "medium",
            "needs_review": False,
        }
    )
    assert record.needs_review is True
    assert record.vaccine_name == "小児用肺炎球菌"


def test_normalize_high_confidence_complete_record():
    record = _normalize_record(
        {
            "vaccine_name": "BCG",
            "dose_number": "1回目",
            "date": "2024-01-15",
            "lot_number": "ABC123",
            "clinic": "中央保健所",
            "confidence": "high",
            "needs_review": False,
        }
    )
    assert record.needs_review is False
    assert record.confidence == "high"


if __name__ == "__main__":
    test_normalize_sets_needs_review_on_null_fields()
    test_normalize_high_confidence_complete_record()
    print("All tests passed")

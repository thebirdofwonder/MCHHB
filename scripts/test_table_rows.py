"""出力表行構成のテスト。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mchhb.schema import ExtractionResult, VaccinationEntry, VACCINE_TEMPLATE, template_key
from mchhb.table_rows import build_output_rows


def test_only_rows_with_records():
    result = ExtractionResult(
        entries=[
            VaccinationEntry(
                vaccine_key="Pneumococcal",
                dose_number=1,
                date="2026-06-23",
                manufacturer="プレベナー",
                institution="こどもクリニック",
            )
        ]
    )
    rows = build_output_rows(result)
    assert len(rows) == 1
    assert rows[0].template.vaccine_ja == "小児肺炎球菌"
    assert len(rows) < len(VACCINE_TEMPLATE)


def test_extra_vaccine_added():
    result = ExtractionResult(
        entries=[
            VaccinationEntry(
                vaccine_key="RSV",
                dose_number=1,
                date="2026-03-16",
                manufacturer="ファイザー",
                lot_number="MJ4998",
                institution="愛育病院",
            )
        ]
    )
    rows = build_output_rows(result)
    assert len(rows) == 1
    assert rows[0].is_extra
    assert rows[0].template.vaccine_ja == "RSV"


def test_mixed_template_and_extra():
    result = ExtractionResult(
        entries=[
            VaccinationEntry(
                vaccine_key="Pneumococcal",
                dose_number=1,
                date="2026-06-23",
                institution="クリニックA",
            ),
            VaccinationEntry(
                vaccine_key="ロタウイルス",
                dose_number=1,
                date="2027-04-19",
                institution="クリニックB",
            ),
        ]
    )
    rows = build_output_rows(result)
    assert len(rows) == 2
    assert not rows[0].is_extra
    assert rows[1].is_extra


if __name__ == "__main__":
    test_only_rows_with_records()
    test_extra_vaccine_added()
    test_mixed_template_and_extra()
    print("All tests passed")

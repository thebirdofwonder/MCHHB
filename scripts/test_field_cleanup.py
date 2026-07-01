"""フィールドクリーンアップのテスト。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mchhb.field_cleanup import (
    clean_manufacturer_lot,
    clean_remark,
    extract_clinic_name,
    is_schedule_or_page_noise,
)


def test_schedule_noise():
    s = "丸囲み数字(①、②など)は、ワクチンの種類毎に接種の回数乳児期愛育病院5か月"
    assert is_schedule_or_page_noise(s)


def test_extract_aiiku():
    s = "丸囲み数字(①、②など)は、ワクチンの種類毎に接種の回数乳児期愛育病院5か月6か月"
    assert extract_clinic_name(s) == "愛育病院"


def test_clean_manufacturer_lot_removes_clinic():
    s = "ロタテック Z013753 リバーシティ経Measles風しん第2期Rubella"
    cleaned = clean_manufacturer_lot(s)
    assert cleaned is not None
    assert "リバーシティ" not in cleaned
    assert "Measles" not in cleaned
    assert "ロタテック" in cleaned


def test_clean_remark_rsv_schedule():
    s = "乳児期4か月5か月6か月7か月8か月"
    assert is_schedule_or_page_noise(s)
    assert clean_remark(s) is None


if __name__ == "__main__":
    test_schedule_noise()
    test_extract_aiiku()
    test_clean_manufacturer_lot_removes_clinic()
    test_clean_remark_rsv_schedule()
    print("All tests passed")

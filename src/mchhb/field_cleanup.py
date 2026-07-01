"""抽出フィールドのノイズ除去・正規化。"""

from __future__ import annotations

import re
from typing import Optional

from .models import VaccinationRecord

# 隣ページの接種スケジュール表など
SCHEDULE_NOISE_RE = re.compile(
    r"丸囲み数字|乳児期|幼児期|学童期|"
    r"\d+か月|\d+歳|歳歳|"
    r"Measles|Rubella|MR|MMR|"
    r"Brand\s*name|Lot\.?\s*No|Manufacturer|"
    r"第[０-９0-9]+期|初回|追加|"
    r"ワクチンの種類毎|接種の回数",
    re.IGNORECASE,
)

CLINIC_NAME_PATTERNS = [
    re.compile(r"リバーシティこどもクリニック"),
    re.compile(r"リバーシティ\s*こどもクリニック"),
    re.compile(r"愛育病院"),
    re.compile(r"[\u3040-\u9fff\u30a0-\u30ff]{2,12}こどもクリニック"),
    re.compile(r"[\u3040-\u9fff\u30a0-\u30ff]{2,12}クリニック"),
    re.compile(r"[\u3040-\u9fff\u30a0-\u30ff]{2,10}病院"),
    re.compile(r"[\u3040-\u9fff\u30a0-\u30ff]{2,10}医院"),
]

CLINIC_FRAGMENT_RE = re.compile(
    r"リバーシティ|こどもクリニック|愛育病院|"
    r"右大腿|左大腿|第[０-９0-9]+期\s*初回|"
    r"\d+\.?\d*\s*ml|ml|"
    r"Manufacturer|Brand\s*name|Lot\.?\s*No\.?",
    re.IGNORECASE,
)

ML_RE = re.compile(r"\d+\.?\d*\s*ml", re.I)
PERIOD_LABEL_RE = re.compile(r"乳児期|幼児期|学童期")
MONTH_AGE_RE = re.compile(r"\d+か月")
CIRCLED_NUM_HINT_RE = re.compile(r"丸囲み数字|①|②|③|④|⑤|⑥|⑦|⑧|⑨|⑩")


def is_schedule_or_page_noise(text: str) -> bool:
    """隣ページの接種スケジュール表などのノイズかどうか。"""
    if not text:
        return False
    s = text.strip()
    if not s:
        return False

    # 強いシグナル（文字数に関係なく除外）
    if PERIOD_LABEL_RE.search(s):
        return True
    if CIRCLED_NUM_HINT_RE.search(s):
        return True
    if len(MONTH_AGE_RE.findall(s)) >= 2:
        return True
    if re.search(r"ワクチンの種類毎|接種の回数", s):
        return True

    if len(s) > 35 and SCHEDULE_NOISE_RE.search(s):
        return True
    if SCHEDULE_NOISE_RE.search(s) and len(s) > 20:
        return True
    return False


def extract_clinic_name(text: Optional[str]) -> Optional[str]:
    """汚染された clinic 文字列から医療機関名だけを抽出。"""
    if not text:
        return None
    cleaned = text.strip()
    if not cleaned:
        return None

    normalized = re.sub(r"\s+", "", cleaned)
    for pat in CLINIC_NAME_PATTERNS:
        m = pat.search(cleaned) or pat.search(normalized)
        if m:
            name = m.group(0).replace(" ", "")
            if "リバーシティ" in name and "こどもクリニック" in name:
                return "リバーシティこどもクリニック"
            return name.strip()

    if is_schedule_or_page_noise(cleaned):
        return None

    # 短い名称のみ許容
    if len(cleaned) <= 24 and not ML_RE.search(cleaned) and not SCHEDULE_NOISE_RE.search(cleaned):
        return cleaned

    return None


def clean_manufacturer_lot(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    s = text.strip()
    if not s:
        return None

    s = re.sub(r"Brand\s*name\s*/?\s*Lot\.?\s*No\.?", "", s, flags=re.I)
    s = re.sub(r"Manufacturer\s*or\s*", "", s, flags=re.I)
    s = CLINIC_FRAGMENT_RE.sub("", s)
    s = re.sub(r"Measles.*?Rubella", "", s, flags=re.I)
    s = re.sub(r"経\s*$", "", s)
    s = re.sub(r"\s+", " ", s).strip()

    if not s or is_schedule_or_page_noise(s):
        return None
    if len(s) > 80:
        return None
    return s or None


def clean_remark(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    s = text.strip()
    if not s:
        return None

    if is_schedule_or_page_noise(s):
        return None

    # 備考らしい短い記載以外は捨てる（隣ページのか月表など）
    if PERIOD_LABEL_RE.search(s) or len(MONTH_AGE_RE.findall(s)) >= 1 and not ML_RE.search(s):
        return None

    # clinic 名が混入した備考から ml・部位だけ残す試み
    if "クリニック" in s and ML_RE.search(s):
        parts = []
        for m in ML_RE.finditer(s):
            parts.append(m.group(0))
        for kw in ("右大腿", "左大腿", "第1期", "初回"):
            if kw in s:
                parts.append(kw)
        if parts:
            return "、".join(dict.fromkeys(parts))
        return None

    if len(s) > 60 and SCHEDULE_NOISE_RE.search(s):
        return None
    return s


def sanitize_vaccination_record(record: VaccinationRecord) -> VaccinationRecord:
    """1件の接種記録をクリーンアップ。"""
    record.manufacturer_lot = clean_manufacturer_lot(record.manufacturer_lot)
    record.clinic = extract_clinic_name(record.clinic)
    record.remark = clean_remark(record.remark)

    if any(
        v is None or v == ""
        for v in (
            record.vaccine_name,
            record.dose_number,
            record.date,
            record.manufacturer_lot,
            record.clinic,
            record.remark,
        )
    ):
        record.needs_review = True

    return record


def sanitize_vaccination_records(records: list[VaccinationRecord]) -> list[VaccinationRecord]:
    return [sanitize_vaccination_record(r) for r in records]

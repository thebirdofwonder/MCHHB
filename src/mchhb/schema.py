"""ワクチン接種記録表のテンプレート定義。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VaccineRow:
    """接種記録表の1行分のテンプレート行。"""

    disease_en: str
    vaccine_ja: str
    dose_category: str = ""
    dose_number: int = 1
    merge_disease_rows: int = 1
    merge_vaccine_rows: int = 1


@dataclass
class VaccinationEntry:
    """画像から抽出した1回分の接種記録。"""

    vaccine_key: str
    dose_number: int
    date: Optional[str] = None
    manufacturer: Optional[str] = None
    lot_number: Optional[str] = None
    institution: Optional[str] = None
    dose_category: Optional[str] = None
    confidence: Optional[str] = None
    source_image: Optional[str] = None


@dataclass
class ExtractionResult:
    """複数画像からの抽出結果。"""

    child_name: Optional[str] = None
    entries: list[VaccinationEntry] = field(default_factory=list)
    raw_notes: list[str] = field(default_factory=list)


# アウトプット表の行構成（添付スプレッドシートに準拠）
VACCINE_TEMPLATE: list[VaccineRow] = [
    VaccineRow("BCG / Tuberculin", "BCG", dose_number=1, merge_disease_rows=2, merge_vaccine_rows=1),
    VaccineRow("BCG / Tuberculin", "ツベルクリン", dose_number=1, merge_disease_rows=0, merge_vaccine_rows=1),
    VaccineRow(
        "Diphtheria Tetanus Pertussis",
        "DPT 三種混合",
        "I期 初回",
        1,
        merge_disease_rows=6,
        merge_vaccine_rows=3,
    ),
    VaccineRow("Diphtheria Tetanus Pertussis", "DPT 三種混合", "I期 初回", 2),
    VaccineRow("Diphtheria Tetanus Pertussis", "DPT 三種混合", "I期 初回", 3),
    VaccineRow("Diphtheria Tetanus Pertussis", "DPT 三種混合", "I期 追加", 4, merge_vaccine_rows=1),
    VaccineRow(
        "Diphtheria Tetanus Pertussis",
        "DT 二種混合",
        "I期 初回",
        5,
        merge_vaccine_rows=2,
    ),
    VaccineRow("Diphtheria Tetanus Pertussis", "DT 二種混合", "I期 追加", 6),
    VaccineRow("Polio", "小児麻痺(ポリオ)", dose_number=1, merge_disease_rows=4, merge_vaccine_rows=4),
    VaccineRow("Polio", "小児麻痺(ポリオ)", dose_number=2),
    VaccineRow("Polio", "小児麻痺(ポリオ)", dose_number=3),
    VaccineRow("Polio", "小児麻痺(ポリオ)", dose_number=4),
    VaccineRow("Measles", "麻しん", dose_number=1, merge_disease_rows=1, merge_vaccine_rows=1),
    VaccineRow("Rubella", "風しん", dose_number=1, merge_disease_rows=1, merge_vaccine_rows=1),
    VaccineRow("Measles Rubella (MR)", "MR", dose_number=1, merge_disease_rows=2, merge_vaccine_rows=2),
    VaccineRow("Measles Rubella (MR)", "MR", dose_number=2),
    VaccineRow("Mumps", "おたふくかぜ", dose_number=1, merge_disease_rows=1, merge_vaccine_rows=1),
    VaccineRow("Varicella", "水痘", dose_number=1, merge_disease_rows=2, merge_vaccine_rows=2),
    VaccineRow("Varicella", "水痘", dose_number=2),
    VaccineRow(
        "Measles mumps rubella (MMR)",
        "MMR",
        dose_number=1,
        merge_disease_rows=1,
        merge_vaccine_rows=1,
    ),
    VaccineRow(
        "Japanese encephalitis",
        "日本脳炎",
        "I期 初回",
        1,
        merge_disease_rows=4,
        merge_vaccine_rows=2,
    ),
    VaccineRow("Japanese encephalitis", "日本脳炎", "I期 初回", 2),
    VaccineRow("Japanese encephalitis", "日本脳炎", "I期 追加", 3, merge_vaccine_rows=1),
    VaccineRow("Japanese encephalitis", "日本脳炎", "II期", 4, merge_vaccine_rows=1),
    VaccineRow("Hepatitis A", "A型肝炎", dose_number=1, merge_disease_rows=3, merge_vaccine_rows=3),
    VaccineRow("Hepatitis A", "A型肝炎", dose_number=2),
    VaccineRow("Hepatitis A", "A型肝炎", dose_number=3),
    VaccineRow("Hepatitis B", "B型肝炎", dose_number=1, merge_disease_rows=3, merge_vaccine_rows=3),
    VaccineRow("Hepatitis B", "B型肝炎", dose_number=2),
    VaccineRow("Hepatitis B", "B型肝炎", dose_number=3),
    VaccineRow("Meningitis", "流行性髄膜炎", dose_number=1, merge_disease_rows=3, merge_vaccine_rows=3),
    VaccineRow("Meningitis", "流行性髄膜炎", dose_number=2),
    VaccineRow("Meningitis", "流行性髄膜炎", dose_number=3),
    VaccineRow(
        "Haemophilus influenzae b",
        "インフルエンザ桿菌（ヒブ）",
        dose_number=1,
        merge_disease_rows=4,
        merge_vaccine_rows=4,
    ),
    VaccineRow("Haemophilus influenzae b", "インフルエンザ桿菌（ヒブ）", dose_number=2),
    VaccineRow("Haemophilus influenzae b", "インフルエンザ桿菌（ヒブ）", dose_number=3),
    VaccineRow("Haemophilus influenzae b", "インフルエンザ桿菌（ヒブ）", dose_number=4),
    VaccineRow("Pneumococcal", "小児肺炎球菌", dose_number=1, merge_disease_rows=4, merge_vaccine_rows=4),
    VaccineRow("Pneumococcal", "小児肺炎球菌", dose_number=2),
    VaccineRow("Pneumococcal", "小児肺炎球菌", dose_number=3),
    VaccineRow("Pneumococcal", "小児肺炎球菌", dose_number=4),
]

# テンプレート行を検索するためのキー（英語病名 + 日本語ワクチン名 + 回数）
VACCINE_KEY_ALIASES: dict[str, list[str]] = {
    "BCG": ["BCG", "bcg", "結核"],
    "ツベルクリン": ["ツベルクリン", "tuberculin"],
    "DPT": ["DPT", "三種混合", "四種混合", "DPT-IPV", "ジフテリア・破傷風・百日咳"],
    "DT": ["DT", "二種混合", "ジフテリア・破傷風"],
    "Polio": ["ポリオ", "polio", "小児麻痺", "IPV", "OPV"],
    "Measles": ["麻しん", "measles"],
    "Rubella": ["風しん", "rubella"],
    "MR": ["MR", "麻しん風しん", "麻疹風疹"],
    "Mumps": ["おたふくかぜ", "mumps"],
    "Varicella": ["水痘", "varicella", "水ぼうそう"],
    "MMR": ["MMR", "麻しんおたふくかぜ風しん"],
    "Japanese encephalitis": ["日本脳炎", "je", "脳炎"],
    "Hepatitis A": ["A型肝炎", "hepatitis a", "A型"],
    "Hepatitis B": ["B型肝炎", "hepatitis b", "B型", "HBV", "HB"],
    "Meningitis": ["流行性髄膜炎", "髄膜炎", "meningitis"],
    "Hib": ["ヒブ", "hib", "インフルエンザ桿菌", "b型"],
    "Pneumococcal": ["肺炎球菌", "pneumococcal", "小児肺炎球菌", "PCV"],
}


def template_key(row: VaccineRow) -> str:
    return f"{row.disease_en}|{row.vaccine_ja}|{row.dose_number}"


def match_entry_to_template(entry: VaccinationEntry) -> Optional[str]:
    """抽出エントリをテンプレート行キーにマッピングする。"""
    key = entry.vaccine_key.upper()

    for row in VACCINE_TEMPLATE:
        aliases = []
        for alias_group, terms in VACCINE_KEY_ALIASES.items():
            if alias_group in row.disease_en or alias_group in row.vaccine_ja:
                aliases.extend(terms)
            if alias_group.upper() == key or alias_group == entry.vaccine_key:
                aliases.extend(terms)

        haystack = f"{row.disease_en} {row.vaccine_ja}".lower()
        entry_haystack = f"{entry.vaccine_key} {entry.dose_category or ''}".lower()

        if key in row.vaccine_ja.upper() or key in row.disease_en.upper():
            if entry.dose_number == row.dose_number:
                if not entry.dose_category or entry.dose_category == row.dose_category:
                    return template_key(row)
                if entry.dose_category.replace(" ", "") in row.dose_category.replace(" ", ""):
                    return template_key(row)

        for term in VACCINE_KEY_ALIASES.get(entry.vaccine_key, []):
            if term.lower() in haystack and entry.dose_number == row.dose_number:
                if row.dose_category and entry.dose_category:
                    if entry.dose_category.replace(" ", "") not in row.dose_category.replace(" ", ""):
                        continue
                return template_key(row)

        for term in aliases:
            if term.lower() in entry_haystack and term.lower() in haystack:
                if entry.dose_number == row.dose_number:
                    return template_key(row)

    return None

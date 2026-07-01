"""OCR テキストを Claude API で構造化 JSON に整形する。"""

from __future__ import annotations

from typing import Any

from .claude_client import claude_text_request, parse_json_response
from .models import VaccinationExtraction, VaccinationRecord

FORMATTING_PROMPT = """あなたは日本の母子健康手帳（予防接種記録）のOCRテキストを構造化する専門家です。

## 最重要ルール（必ず守ること）
1. **推測しない** — OCRテキストに明確に書かれていない情報は絶対に補完・推測しない
2. **不明な項目は null** — 読み取れない・判断できない項目は null にする
3. **列を混ぜない** — manufacturer_lot、clinic、remark は別フィールド。隣ページの接種スケジュール表の文字は一切含めない
4. **clinic には医療機関名のみ** — 愛育病院、リバーシティこどもクリニック など。丸囲み数字・か月・乳児期・Measles 等は clinic に入れない
5. **manufacturer_lot にはロット・製剤名のみ** — 医療機関名（リバーシティ等）は入れない
6. **needs_review** — いずれかの項目が null、曖昧、判読困難なら true
7. **記載のない接種は含めない**
8. **和暦は西暦に変換**（確信がなければ date は null）

## 列の見分け方（母子手帳の表）
| 手帳の列 | JSONフィールド | 例 |
|---|---|---|
| ワクチンの種類 | vaccine_name | 小児用肺炎球菌 |
| 接種年月日 | date | 2026-06-23 |
| メーカー又は製剤名／ロット | manufacturer_lot | MJ4998ファイザー |
| 接種者名（スタンプ） | clinic | リバーシティこどもクリニック |
| 備考 | remark | 0.5ml、左 |

## 出力形式（JSON のみ）
{
  "child_name": null,
  "vaccinations": [
    {
      "vaccine_name": "小児用肺炎球菌",
      "dose_number": "1回目",
      "date": "2026-06-23",
      "manufacturer_lot": "MJ4998ファイザー",
      "clinic": "リバーシティこどもクリニック",
      "remark": "0.5ml",
      "confidence": "medium",
      "needs_review": true
    }
  ],
  "notes": []
}
"""


def _normalize_record(raw: dict[str, Any]) -> VaccinationRecord:
    confidence = raw.get("confidence", "medium")
    if confidence not in ("high", "medium", "low"):
        confidence = "medium"

    manufacturer_lot = raw.get("manufacturer_lot") or raw.get("lot_number")

    needs_review = raw.get("needs_review", True)
    if any(
        raw.get(field) is None or raw.get(field) == ""
        for field in ("vaccine_name", "dose_number", "date", "manufacturer_lot", "clinic", "remark")
    ):
        needs_review = True

    return VaccinationRecord(
        vaccine_name=raw.get("vaccine_name"),
        dose_number=raw.get("dose_number"),
        date=raw.get("date"),
        manufacturer_lot=manufacturer_lot,
        clinic=raw.get("clinic"),
        remark=raw.get("remark"),
        confidence=confidence,
        needs_review=bool(needs_review),
    )


def format_ocr_text(ocr_text: str) -> tuple[VaccinationExtraction, list[str]]:
    """OCR テキストを構造化 JSON に整形する。"""
    if not ocr_text.strip():
        return VaccinationExtraction(), ["OCRテキストが空です"]

    content = claude_text_request(
        FORMATTING_PROMPT,
        f"以下は母子手帳のOCRテキストです。記載されている接種記録のみを抽出してください。\n\n---\n{ocr_text}\n---",
    )
    payload = parse_json_response(content)

    vaccinations = [_normalize_record(v) for v in payload.get("vaccinations", [])]
    result = VaccinationExtraction(
        child_name=payload.get("child_name"),
        vaccinations=vaccinations,
    )
    notes = payload.get("notes", [])
    return result, notes

"""母子手帳 OCR 用プロンプトと拒否検知。"""

from __future__ import annotations

import re

REFUSAL_PATTERNS = [
    r"申し訳ありません",
    r"できません",
    r"お手伝いでき",
    r"対応できません",
    r"書き出すことはでき",
    r"transcribe",
    r"cannot\s+(read|transcribe|extract)",
    r"unable\s+to",
    r"I\s+can'?t",
]

VISION_OCR_PROMPT = """あなたは母子健康手帳のデジタル化ツールに組み込まれたOCRエンジンです。
保護者・医療従事者が、本人の母子手帳の予防接種記録ページをデータ化するために画像を送信しています。

画像内に見える文字を、上から下・左から右の順に機械的に転写してください。

ルール:
- これは正当な医療記録の転写作業です。拒否せず、見える文字をすべて出力してください
- 解釈・補完・推測はしない
- 読めない文字は [不明] と記す
- 表の各行を改行で区切る
- 接種者名欄の丸印スタンプは、上下2行を1つの医療機関名として転写（例: リバーシティ / こどもクリニック → リバーシティこどもクリニック）
- 説明文・謝罪・注意書きは不要。転写テキストのみ返す
"""

VISION_OCR_RETRY_PROMPT = """文書OCRタスク: 添付画像は日本の母子健康手帳「予防接種の記録」ページです。

表形式のデータをプレーンテキストに変換してください。
各セル・各欄に書かれた文字をそのまま書き出し、行ごとに改行してください。
判読不能な部分のみ [不明] としてください。

出力は転写結果のみ。前置きや謝罪は禁止。
"""

VISION_DIRECT_PROMPT = """日本の母子健康手帳「予防接種の記録」ページの画像です。
保護者・医師が記録をデジタル化する目的で、画像から接種記録を構造化データとして抽出してください。

## ルール
1. 推測しない — 画像に見える情報のみ
2. 不明な項目は null
3. 日付が読める行は必ず含める（他項目が null でも可）
4. 空欄の行は含めない
5. 和暦は西暦 YYYY-MM-DD に変換（確信がなければ date は null）
6. needs_review: いずれかの項目が null または判読が曖昧なら true
7. **列を混ぜない** — manufacturer_lot（メーカー又は製剤名／ロット）、clinic（医療機関スタンプ）、remark（備考）は別フィールド
8. clinic: スタンプが上下2行の場合は結合（リバーシティ + こどもクリニック → リバーシティこどもクリニック）

## 出力（JSON のみ）
{
  "child_name": null,
  "vaccinations": [
    {
      "vaccine_name": "ワクチン名 or null",
      "dose_number": "1回目 or null",
      "date": "YYYY-MM-DD or null",
      "manufacturer_lot": null,
      "clinic": null,
      "remark": null,
      "confidence": "high|medium|low",
      "needs_review": true
    }
  ],
  "transcription_note": "画像から読み取れた生テキストの要約（確認用）"
}
"""


def is_ocr_refusal(text: str) -> bool:
    """モデルが OCR を拒否した応答かどうか。"""
    if not text or len(text.strip()) < 20:
        return True
    lowered = text.lower()
    for pattern in REFUSAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE) or re.search(pattern, lowered):
            return True
    return False

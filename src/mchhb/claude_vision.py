"""Claude Vision API による OCR 拒否検知・リトライ・画像直接抽出。"""

from __future__ import annotations

from .claude_client import claude_vision_request, parse_json_response
from .formatter import _normalize_record
from .models import VaccinationExtraction
from .ocr_prompts import (
    VISION_DIRECT_PROMPT,
    VISION_OCR_PROMPT,
    VISION_OCR_RETRY_PROMPT,
    is_ocr_refusal,
)


def ocr_with_claude_vision(image_bytes: bytes, mime_type: str) -> tuple[str, list[str]]:
    """
    Claude Vision で OCR。拒否時はリトライし、それでもダメなら空文字を返す。
    Returns: (ocr_text, notes)
    """
    notes: list[str] = []

    text = claude_vision_request(VISION_OCR_PROMPT, image_bytes, mime_type)
    if not is_ocr_refusal(text):
        return text, notes

    notes.append("OCR 1回目が拒否または不完全だったため、別プロンプトで再試行しました。")
    text = claude_vision_request(VISION_OCR_RETRY_PROMPT, image_bytes, mime_type)
    if not is_ocr_refusal(text):
        return text, notes

    notes.append("OCR が拒否されました。画像からの直接抽出にフォールバックします。")
    return "", notes


def extract_vaccinations_from_image(
    image_bytes: bytes,
    mime_type: str,
) -> tuple[VaccinationExtraction, str, list[str]]:
    """
    OCR 拒否時のフォールバック: 画像から直接 JSON 抽出。
    Returns: (extraction, pseudo_ocr_text_for_display, notes)
    """
    notes: list[str] = ["Claude Vision API による画像直接抽出を使用しました。"]
    content = claude_vision_request(VISION_DIRECT_PROMPT, image_bytes, mime_type)
    payload = parse_json_response(content)

    vaccinations = [_normalize_record(v) for v in payload.get("vaccinations", [])]
    extraction = VaccinationExtraction(
        child_name=payload.get("child_name"),
        vaccinations=vaccinations,
    )

    transcription = payload.get("transcription_note", "")
    lines = [f"[画像から直接抽出 — {len(vaccinations)} 件]"]
    if transcription:
        lines.append(transcription)
    for i, v in enumerate(vaccinations, 1):
        lines.append(
            f"{i}. {v.vaccine_name or '[不明]'} | {v.dose_number or '-'} | {v.date or '-'} | "
            f"{v.manufacturer_lot or '-'} | {v.clinic or '-'} | {v.remark or '-'}"
        )
    pseudo_ocr = "\n".join(lines)
    return extraction, pseudo_ocr, notes

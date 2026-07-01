"""OCR（Claude Vision API）。"""

from __future__ import annotations

import mimetypes

from .claude_vision import ocr_with_claude_vision
from .ocr_types import DocumentOcrResult


def ocr_image(image_bytes: bytes, mime_type: str) -> tuple[DocumentOcrResult, list[str]]:
    """画像バイト列を Claude Vision で OCR する。"""
    text, notes = ocr_with_claude_vision(image_bytes, mime_type)
    return DocumentOcrResult(text=text, lines=[], layout_rows=[]), notes


def guess_mime_type(filename: str, fallback: str = "image/jpeg") -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime if mime and mime.startswith("image/") else fallback

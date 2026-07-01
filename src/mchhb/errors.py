"""API エラーをわかりやすい日本語に変換。"""

from __future__ import annotations


def friendly_api_error(exc: Exception) -> str:
    msg = str(exc)

    if "not_found_error" in msg and "model" in msg:
        return (
            "指定した Claude モデルが見つかりません。\n"
            ".env の ANTHROPIC_MODEL を確認してください（例: claude-sonnet-4-6）。"
        )

    if "authentication" in msg.lower() or "invalid x-api-key" in msg.lower():
        return "ANTHROPIC_API_KEY が無効です。.env の API キーを確認してください。"

    if len(msg) > 300:
        return msg[:300] + "…"
    return msg

"""環境変数の検証（Claude API のみ）。"""

from __future__ import annotations

import os


PLACEHOLDER_VALUES = {
    "sk-ant-...",
    "sk-ant-your-key-here",
}


def _is_placeholder(value: str | None) -> bool:
    if not value:
        return True
    stripped = value.strip()
    return stripped in PLACEHOLDER_VALUES or stripped.startswith("your-")


def is_claude_configured() -> bool:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return bool(key) and not _is_placeholder(key)


def validate_for_processing() -> None:
    """処理前に Claude API キーを検証する。"""
    if not is_claude_configured():
        raise ConfigurationError(
            "ANTHROPIC_API_KEY が未設定です。.env に Claude API キーを設定してください。"
        )


class ConfigurationError(Exception):
    """環境設定エラー。"""

    def __init__(self, message: str | None = None):
        super().__init__(message or "環境変数の設定が不完全です。.env を確認してください。")

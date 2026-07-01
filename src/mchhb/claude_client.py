"""Claude API 共通クライアント。"""

from __future__ import annotations

import base64
import json
import os
import re
from typing import Any

import anthropic


def claude_model() -> str:
    return os.environ.get(
        "ANTHROPIC_MODEL",
        os.environ.get("ANTHROPIC_VISION_MODEL", "claude-sonnet-4-6"),
    )


def parse_json_response(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def claude_text_request(system: str, user: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=claude_model(),
        max_tokens=4096,
        temperature=0,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    parts: list[str] = []
    for block in response.content:
        if block.type == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()


def claude_vision_request(prompt: str, image_bytes: bytes, mime_type: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    response = client.messages.create(
        model=claude_model(),
        max_tokens=4096,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    parts: list[str] = []
    for block in response.content:
        if block.type == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()

"""FastAPI Web アプリ（Claude API → Excel / PDF 出力）。"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from mchhb.config import ConfigurationError, is_claude_configured  # noqa: E402
from mchhb.errors import friendly_api_error  # noqa: E402
from mchhb.file_export import export_zip  # noqa: E402
from mchhb.pipeline import process_images  # noqa: E402

load_dotenv()

app = FastAPI(title="MCHHB Vaccination Extractor", version="0.3.0")

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/tiff", "image/bmp"}

NO_CACHE = {"Cache-Control": "no-cache, no-store, must-revalidate"}

FOOTER_BG = {
    "ok": "#2e7d32",
    "warn": "#e65100",
    "error": "#c62828",
    "info": "#2c3e50",
}


def _backend_status_info() -> tuple[str, str, bool]:
    """(message, level, can_process)"""
    if not is_claude_configured():
        return (
            "ANTHROPIC_API_KEY が未設定です。.env を編集してサーバーを再起動してください。",
            "error",
            False,
        )
    return ("Claude API", "ok", True)


def _render_index() -> HTMLResponse:
    message, level, can_process = _backend_status_info()
    bg = FOOTER_BG.get(level, FOOTER_BG["info"])
    html = (TEMPLATE_DIR / "index.html").read_text(encoding="utf-8")
    html = html.replace("{{BACKEND_MESSAGE}}", message)
    html = html.replace("{{BACKEND_BG}}", bg)
    html = html.replace("{{PROCESS_DISABLED}}", "" if can_process else "disabled")
    return HTMLResponse(html, headers=NO_CACHE)


@app.get("/")
async def index():
    return _render_index()


@app.get("/api/status")
async def status():
    message, level, can_process = _backend_status_info()
    return {
        "claude_configured": is_claude_configured(),
        "message": message,
        "level": level,
        "can_process": can_process,
    }


@app.post("/api/process")
async def process(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="画像ファイルを1枚以上アップロードしてください")

    images: list[tuple[str, bytes, str]] = []
    for f in files:
        content_type = f.content_type or "image/jpeg"
        if content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail=f"非対応のファイル形式: {f.filename}")
        data = await f.read()
        if not data:
            raise HTTPException(status_code=400, detail=f"空のファイル: {f.filename}")
        images.append((f.filename or "image", data, content_type))

    try:
        result = process_images(images)
        zip_bytes = export_zip(result)
        count = len(result.vaccinations)
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": 'attachment; filename="vaccination_record.zip"',
                "X-Vaccination-Count": str(count),
            },
        )
    except ConfigurationError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except KeyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"環境変数が未設定です: {e}. .env を確認してください。",
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=friendly_api_error(e)) from e


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

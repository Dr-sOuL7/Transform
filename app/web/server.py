"""Local web UI for the transformation engine (design section 10).

A small FastAPI app that wraps the same offline pipeline the CLI uses. It runs
entirely on localhost -- no data leaves the machine. Uploaded and produced
files live in a per-run temp directory and are served back for download by
token.

Launch with::

    python -m app.web            # http://127.0.0.1:8000
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.pipeline import transform_document
from app.configs.presets import EDITABLE_RULES
from app.configs.loader import load_presets, resolve_enabled
from app.rules.registry import rule_catalog

_HERE = Path(__file__).parent
_STATIC = _HERE / "static"
_WORKDIR = Path(tempfile.gettempdir()) / "text_transform_web"
_WORKDIR.mkdir(exist_ok=True)

# token -> (output_path, download_filename)
_OUTPUTS: dict[str, tuple[str, str]] = {}

app = FastAPI(title="Offline Text Transformation")
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((_STATIC / "index.html").read_text(encoding="utf-8"))


@app.get("/api/config")
def config() -> dict:
    """Presets, toggleable rule ids, and full rule metadata for the UI."""
    return {
        "presets": load_presets(),
        "editable_rules": EDITABLE_RULES,
        "catalog": rule_catalog(),
    }


@app.post("/api/transform")
async def transform(
    file: UploadFile = File(...),
    preset: str = Form("balanced"),
    overrides: str = Form("{}"),
) -> dict:
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Please upload a .docx file.")
    if preset not in load_presets():
        raise HTTPException(status_code=400, detail=f"Unknown preset: {preset}")

    try:
        override_map = json.loads(overrides) if overrides else {}
        if not isinstance(override_map, dict):
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid overrides payload.")

    token = uuid.uuid4().hex
    in_path = _WORKDIR / f"{token}_in.docx"
    out_path = _WORKDIR / f"{token}_out.docx"
    in_path.write_bytes(await file.read())

    enabled = resolve_enabled(preset, [], [])
    # Apply per-rule overrides from the UI toggles.
    for rule_id, value in override_map.items():
        enabled[rule_id] = bool(value)

    try:
        report = transform_document(str(in_path), str(out_path), enabled=enabled)
    except Exception as exc:  # noqa: BLE001 - surface any parse/engine error to the UI
        raise HTTPException(status_code=422, detail=f"Could not process document: {exc}")
    finally:
        in_path.unlink(missing_ok=True)

    base = Path(file.filename).stem
    download_name = f"{base}.refined.docx"
    _OUTPUTS[token] = (str(out_path), download_name)

    payload = report.to_dict()
    payload["token"] = token
    payload["download_name"] = download_name
    return payload


@app.get("/api/download/{token}")
def download(token: str) -> FileResponse:
    entry = _OUTPUTS.get(token)
    if not entry or not os.path.isfile(entry[0]):
        raise HTTPException(status_code=404, detail="Result not found or expired.")
    path, name = entry
    return FileResponse(path, media_type=_DOCX_MIME, filename=name)


def main() -> None:
    import uvicorn

    host = os.environ.get("TT_HOST", "127.0.0.1")
    port = int(os.environ.get("TT_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()

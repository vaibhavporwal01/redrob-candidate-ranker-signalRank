from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from redrob.loader import load_candidates
from redrob.pipeline import rank_candidates
from redrob.config import load_scoring_config

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "app" / "ui"
SAMPLE = ROOT / "data" / "sample_candidates.json"

app = FastAPI(title="Signalrank — Redrob Candidate Intelligence", version="1.0.0")
app.mount("/static", StaticFiles(directory=UI), name="static")

_candidate_store: dict[str, dict[str, Any]] = {}


def _remember(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for item in results:
        _candidate_store[item["candidate_id"]] = item
    return [_public(item) for item in results]


def _public(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key != "candidate"}


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(UI / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(content=b"", media_type="image/x-icon")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ready", "engine": "redrob-core/1.0"}


@app.get("/api/demo")
def demo() -> dict[str, Any]:
    with SAMPLE.open("r", encoding="utf-8") as handle:
        candidates = json.load(handle)
    results = rank_candidates(candidates, top_n=len(candidates))
    return {"source": "curated demo set", "total": len(candidates), "results": _remember(results)}


@app.post("/rank", include_in_schema=True)
@app.post("/api/rank", include_in_schema=False)
async def rank_upload(file: UploadFile = File(...)) -> dict[str, Any]:
    if not (file.filename or "").lower().endswith((".jsonl", ".json")):
        raise HTTPException(400, "Upload a .jsonl or .json candidate file")
    try:
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as handle:
            size = 0
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                size += len(chunk)
                if size > 500 * 1024 * 1024:
                    raise HTTPException(413, "Uploads are limited to 500 MB")
                handle.write(chunk)
            temporary = Path(handle.name)

        try:
            if (file.filename or "").lower().endswith(".json"):
                with temporary.open("r", encoding="utf-8") as f:
                    candidates = json.load(f)
                if not isinstance(candidates, list):
                    raise ValueError("JSON upload must contain an array")
            else:
                candidates = load_candidates(temporary)
        finally:
            temporary.unlink(missing_ok=True)
        if not candidates:
            raise ValueError("No candidates found")
        demo_pool_limit = int(load_scoring_config()["retrieval"]["candidate_pool_size"])
        results = rank_candidates(candidates, top_n=min(demo_pool_limit, len(candidates)))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"source": file.filename, "total": len(candidates), "results": _remember(results)}


@app.get("/candidate/{candidate_id}", include_in_schema=True)
@app.get("/api/candidate/{candidate_id}", include_in_schema=False)
def candidate_detail(candidate_id: str) -> dict[str, Any]:
    if candidate_id not in _candidate_store:
        raise HTTPException(404, "Candidate not found in this ranking session")
    return _candidate_store[candidate_id]

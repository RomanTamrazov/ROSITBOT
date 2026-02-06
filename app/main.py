from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .pipeline import ClarificationNeeded, build_pipeline
from .types import ParseRequest, ParseResponse

app = FastAPI(title="ROSIT", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

pipeline = build_pipeline()


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")




@app.post("/parse_command", response_model=ParseResponse, response_model_exclude_none=True)
def parse_command(req: ParseRequest) -> ParseResponse:
    try:
        plan = pipeline.parse(req.text, strict_override=req.strict)
        return ParseResponse(status="ok", plan=plan)
    except ClarificationNeeded as e:
        return ParseResponse(status="error", message=str(e), needs_clarification=True)
    except Exception as e:
        return ParseResponse(status="error", message=str(e), needs_clarification=False)

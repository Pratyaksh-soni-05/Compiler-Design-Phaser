from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from compiler import (
    lexical_analysis, syntax_analysis, semantic_analysis,
    intermediate_code, optimization, target_code, compile_all,
)

app = FastAPI(title="Compiler Phases API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,        # ✅ added
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompileRequest(BaseModel):
    code: str

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Compiler Phases API running"}

# ── Full compile ──────────────────────────────────────────────────────────────
@app.post("/api/compile")
def compile_code(req: CompileRequest):
    return compile_all(req.code)

# ── Individual phases ─────────────────────────────────────────────────────────
@app.post("/api/phase/{phase_id}")   # ✅ single dynamic route instead of 6 separate ones
def run_phase(phase_id: int, req: CompileRequest):
    handlers = {
        0: lexical_analysis,
        1: syntax_analysis,
        2: semantic_analysis,
        3: intermediate_code,
        4: optimization,
        5: target_code,
    }
    if phase_id not in handlers:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Phase {phase_id} not found")
    return handlers[phase_id](req.code)

# ── Static files LAST ─────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Only mount static if the directory actually has an index.html
if os.path.exists(os.path.join(BASE_DIR, "index.html")):
    app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
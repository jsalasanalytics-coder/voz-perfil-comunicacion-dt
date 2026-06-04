"""API FastAPI — software interno tipo CRM de entrenadores.

Gestiona entrenadores (con foto) y sus conferencias. Agregar una conferencia dispara
un job en segundo plano (descarga + transcripción con progreso/ETA + análisis), y el
perfil se calcula sobre las respuestas del DT (topic modeling + métricas + conclusiones).
"""
from __future__ import annotations

import json
import threading
import traceback
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import profile, store, transcription

app = FastAPI(title="Scout Comunicacional de DTs — NLP")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

JOBS: dict[str, dict] = {}
_lock = threading.Lock()


def _set(job_id: str, **kw):
    with _lock:
        JOBS[job_id].update(kw)


# ── Schemas ─────────────────────────────────────────────────────────
class CoachIn(BaseModel):
    name: str
    team: str | None = None


class ConfIn(BaseModel):
    url: str


class ExplainIn(BaseModel):
    text: str


# ── Helpers ─────────────────────────────────────────────────────────
def _coach_card(coach: dict) -> dict:
    """Resumen para la lista: agrega foto y % de confianza si ya hay análisis."""
    cid = coach["id"]
    card = {
        "id": cid, "name": coach["name"], "team": coach.get("team", ""),
        "n_conferences": coach.get("n_conferences", 0),
        "photo_url": f"/api/coaches/{cid}/photo" if coach.get("photo_ext") else None,
        "confianza": None, "headline": None,
    }
    cache = store.COACHES_DIR / cid / "_analysis.json"
    if cache.exists():
        try:
            data = json.loads(cache.read_text(encoding="utf-8"))
            if data.get("ready"):
                card["confianza"] = data["metrics"]["confianza"]
                card["headline"] = data["metrics"]["headline"]
        except Exception:
            pass
    return card


# ── Job: agregar conferencia ────────────────────────────────────────
def _run_add_conference(job_id: str, coach_id: str, url: str):
    try:
        def on_progress(stage, frac, eta):
            _set(job_id, stage=stage, fraction=round(frac, 3), eta=eta)

        _set(job_id, status="running", stage="info", fraction=0.0, eta=None)
        record = transcription.process_url(url, on_progress=on_progress)
        _set(job_id, title=record["title"])
        store.add_conference(coach_id, record)
        profile.invalidate_cache(coach_id)

        _set(job_id, status="running", stage="analyzing", fraction=1.0, eta=None)
        profile.analyze_coach(coach_id)  # deja el perfil listo en caché

        _set(job_id, status="done", stage="done", fraction=1.0)
    except Exception as e:  # pragma: no cover
        _set(job_id, status="error", error=str(e))
        traceback.print_exc()


# ── Endpoints: salud ────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── Endpoints: entrenadores ─────────────────────────────────────────
@app.get("/api/coaches")
def list_coaches():
    return [_coach_card(c) for c in store.list_coaches()]


@app.post("/api/coaches")
def create_coach(body: CoachIn):
    if not body.name.strip():
        raise HTTPException(400, "El nombre es obligatorio.")
    return store.create_coach(body.name, body.team)


@app.delete("/api/coaches/{coach_id}")
def delete_coach(coach_id: str):
    if not store.delete_coach(coach_id):
        raise HTTPException(404, "Entrenador no encontrado.")
    return {"deleted": coach_id}


@app.post("/api/coaches/{coach_id}/photo")
async def upload_photo(coach_id: str, file: UploadFile = File(...)):
    ext = (file.filename or "jpg").rsplit(".", 1)[-1]
    content = await file.read()
    coach = store.set_photo(coach_id, content, ext)
    if not coach:
        raise HTTPException(404, "Entrenador no encontrado.")
    return {"ok": True, "photo_url": f"/api/coaches/{coach_id}/photo"}


@app.get("/api/coaches/{coach_id}/photo")
def get_photo(coach_id: str):
    p = store.photo_path(coach_id)
    if not p:
        raise HTTPException(404, "Sin foto.")
    return FileResponse(p)


@app.get("/api/coaches/{coach_id}/profile")
def coach_profile(coach_id: str, n_topics: int | None = None):
    try:
        return profile.analyze_coach(coach_id, n_topics=n_topics)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ── Endpoints: conferencias ─────────────────────────────────────────
@app.post("/api/coaches/{coach_id}/conferences")
def add_conference(coach_id: str, body: ConfIn):
    if not store.get_coach(coach_id):
        raise HTTPException(404, "Entrenador no encontrado.")
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {"status": "pending", "stage": "info", "fraction": 0.0,
                    "eta": None, "title": None, "error": None, "coach_id": coach_id}
    threading.Thread(target=_run_add_conference, args=(job_id, coach_id, body.url),
                     daemon=True).start()
    return {"job_id": job_id}


@app.delete("/api/coaches/{coach_id}/conferences/{conf_id}")
def delete_conference(coach_id: str, conf_id: str):
    if not store.delete_conference(coach_id, conf_id):
        raise HTTPException(404, "Conferencia no encontrada.")
    profile.invalidate_cache(coach_id)
    return {"deleted": conf_id}


@app.post("/api/pipeline/explain")
def pipeline_explain(body: ExplainIn):
    return profile.explain_pipeline(body.text)


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job no encontrado.")
    return job

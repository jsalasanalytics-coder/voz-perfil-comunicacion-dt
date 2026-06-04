"""Persistencia tipo CRM: entrenadores y sus conferencias en disco.

Estructura:
  data/coaches/<coach_id>/coach.json
  data/coaches/<coach_id>/photo.<ext>          (opcional)
  data/coaches/<coach_id>/conferences/<conf_id>.json
"""
from __future__ import annotations

import json
import re
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import config

COACHES_DIR = config.DATA_DIR / "coaches"
COACHES_DIR.mkdir(parents=True, exist_ok=True)


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)[:40] or "dt"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coach_dir(coach_id: str) -> Path:
    return COACHES_DIR / coach_id


# ── Entrenadores ────────────────────────────────────────────────────
def create_coach(name: str, team: str | None = None) -> dict:
    cid = f"{_slug(name)}-{uuid.uuid4().hex[:6]}"
    d = _coach_dir(cid)
    (d / "conferences").mkdir(parents=True, exist_ok=True)
    coach = {"id": cid, "name": name.strip(), "team": (team or "").strip(),
             "photo_ext": None, "created_at": _now()}
    (d / "coach.json").write_text(json.dumps(coach, ensure_ascii=False, indent=2), encoding="utf-8")
    return coach


def get_coach(coach_id: str) -> dict | None:
    fp = _coach_dir(coach_id) / "coach.json"
    if not fp.exists():
        return None
    return json.loads(fp.read_text(encoding="utf-8"))


def _save_coach(coach: dict) -> None:
    fp = _coach_dir(coach["id"]) / "coach.json"
    fp.write_text(json.dumps(coach, ensure_ascii=False, indent=2), encoding="utf-8")


def list_coaches() -> list[dict]:
    out = []
    for d in sorted(COACHES_DIR.iterdir()):
        fp = d / "coach.json"
        if fp.exists():
            c = json.loads(fp.read_text(encoding="utf-8"))
            c["n_conferences"] = len(list((d / "conferences").glob("*.json")))
            out.append(c)
    return out


def delete_coach(coach_id: str) -> bool:
    import shutil
    d = _coach_dir(coach_id)
    if d.exists():
        shutil.rmtree(d)
        return True
    return False


def set_photo(coach_id: str, content: bytes, ext: str) -> dict | None:
    coach = get_coach(coach_id)
    if not coach:
        return None
    ext = ext.lower().lstrip(".")
    if ext == "jpeg":
        ext = "jpg"
    # borrar fotos previas
    for old in _coach_dir(coach_id).glob("photo.*"):
        old.unlink()
    (_coach_dir(coach_id) / f"photo.{ext}").write_bytes(content)
    coach["photo_ext"] = ext
    _save_coach(coach)
    return coach


def photo_path(coach_id: str) -> Path | None:
    coach = get_coach(coach_id)
    if not coach or not coach.get("photo_ext"):
        return None
    p = _coach_dir(coach_id) / f"photo.{coach['photo_ext']}"
    return p if p.exists() else None


# ── Conferencias ────────────────────────────────────────────────────
def add_conference(coach_id: str, record: dict) -> dict:
    conf_id = uuid.uuid4().hex[:10]
    record = {**record, "id": conf_id, "coach_id": coach_id, "created_at": _now()}
    fp = _coach_dir(coach_id) / "conferences" / f"{conf_id}.json"
    fp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def list_conferences(coach_id: str) -> list[dict]:
    cdir = _coach_dir(coach_id) / "conferences"
    if not cdir.exists():
        return []
    confs = [json.loads(fp.read_text(encoding="utf-8")) for fp in cdir.glob("*.json")]
    # ordenar por fecha del video si existe, si no por created_at
    confs.sort(key=lambda c: (c.get("upload_date") or "", c.get("created_at") or ""))
    return confs


def delete_conference(coach_id: str, conf_id: str) -> bool:
    fp = _coach_dir(coach_id) / "conferences" / f"{conf_id}.json"
    if fp.exists():
        fp.unlink()
        return True
    return False

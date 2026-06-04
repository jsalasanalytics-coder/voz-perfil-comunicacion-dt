"""Migra los transcripts viejos (data/transcripts/*.json) al store CRM como
entrenadores con sus conferencias, etiquetando pregunta/respuesta."""
import json
from app import config, speakers, store

TEAM = {"Bielsa": "Selección de Uruguay", "Gallardo": "River Plate",
        "Ramón Díaz": "varios", "Nicolás Diez": "Argentinos Juniors"}

by_coach = {}
for fp in (config.DATA_DIR / "transcripts").glob("*.json"):
    rec = json.loads(fp.read_text(encoding="utf-8"))
    by_coach.setdefault(rec.get("coach") or "Desconocido", []).append(rec)

# evitar duplicar si ya existen
existing = {c["name"] for c in store.list_coaches()}

for coach_name, recs in by_coach.items():
    if coach_name in existing:
        print(f"– {coach_name} ya existe, salteo")
        continue
    coach = store.create_coach(coach_name, TEAM.get(coach_name, ""))
    for rec in recs:
        segs = speakers.tag_segments(rec.get("segments", []))
        store.add_conference(coach["id"], {
            "url": rec.get("url"), "title": rec.get("title"),
            "duration": None, "upload_date": None,
            "text": rec.get("text", ""), "segments": segs,
            "speaker_summary": speakers.summary(segs),
        })
    print(f"✓ {coach_name}: {len(recs)} conferencia(s) -> {coach['id']}")

print("\nEntrenadores en el store:")
for c in store.list_coaches():
    print(f"  {c['name']} ({c['team']}) — {c['n_conferences']} conf — id={c['id']}")

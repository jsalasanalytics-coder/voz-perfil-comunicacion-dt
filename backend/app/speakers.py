"""Separación pregunta (periodista) vs respuesta (entrenador).

En una conferencia de prensa hay dos roles: el periodista que pregunta y el DT que
responde. No usamos diarización por voz (lenta y con dependencias pesadas) sino una
heurística lingüística sobre los segmentos transcriptos: las preguntas tienen marcas
interrogativas y suelen ser cortas; el resto es el DT.

El perfil de comunicación se construye SOLO sobre lo que dice el entrenador.
"""
from __future__ import annotations

import re

QUESTION_WORDS = {
    "qué", "que", "cómo", "como", "cuál", "cual", "cuáles", "cuando", "cuándo",
    "dónde", "donde", "quién", "quien", "cuánto", "cuanto", "cuántos", "porqué",
}
# Frases típicas de periodistas dirigiéndose al DT.
JOURNALIST_CUES = (
    "una pregunta", "una consulta", "te quería preguntar", "le quería preguntar",
    "quería consultarte", "quería preguntarte", "consultarle", "pregunta para",
    "te consulto", "le consulto", "primera pregunta", "última pregunta",
)
_INTERROGATIVE_START = re.compile(r"^\s*[¿]?\s*(" + "|".join(QUESTION_WORDS) + r")\b", re.IGNORECASE)


def classify(text: str) -> str:
    """Devuelve 'PREGUNTA' o 'DT' para un segmento de texto."""
    t = text.strip().lower()
    if not t:
        return "DT"
    n_words = len(t.split())
    # Señal fuerte: marca interrogativa explícita y enunciado no demasiado largo.
    if ("?" in t or "¿" in t) and n_words <= 40:
        return "PREGUNTA"
    if any(cue in t for cue in JOURNALIST_CUES):
        return "PREGUNTA"
    # Arranque interrogativo en un enunciado corto (preguntas suelen ser breves).
    if _INTERROGATIVE_START.match(t) and n_words <= 25:
        return "PREGUNTA"
    return "DT"


def tag_segments(segments: list[dict]) -> list[dict]:
    """Agrega 'speaker' a cada segmento."""
    return [{**s, "speaker": classify(s.get("text", ""))} for s in segments]


def coach_text(segments: list[dict]) -> str:
    """Texto de todo lo que dijo el entrenador (segmentos DT)."""
    return " ".join(s["text"].strip() for s in segments if s.get("speaker") == "DT").strip()


def question_text(segments: list[dict]) -> str:
    """Texto de todas las preguntas de los periodistas."""
    return " ".join(s["text"].strip() for s in segments if s.get("speaker") == "PREGUNTA").strip()


def summary(segments: list[dict]) -> dict:
    n_q = sum(1 for s in segments if s.get("speaker") == "PREGUNTA")
    n_dt = sum(1 for s in segments if s.get("speaker") == "DT")
    return {"n_preguntas": n_q, "n_respuestas": n_dt, "n_segmentos": len(segments)}

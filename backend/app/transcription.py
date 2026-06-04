"""Ingesta y transcripción de conferencias de prensa.

Paso de *ingesta de datos* (no es el aporte de NLP):
  1. Descarga el audio de un link de YouTube con yt-dlp.
  2. Lo transcribe en español con faster-whisper (ASR), reportando progreso/ETA.
  3. Etiqueta cada segmento como pregunta del periodista o respuesta del DT.
"""
from __future__ import annotations

import re
import time
import unicodedata
from pathlib import Path
from typing import Callable

from . import config, speakers

_whisper_model = None  # carga perezosa (singleton)


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)[:60] or "conf"


def fetch_info(url: str) -> dict:
    """Metadatos del video (sin descargar): título, duración, fecha."""
    import yt_dlp

    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "no_warnings": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "title": info.get("title", "conferencia"),
        "duration": info.get("duration"),       # segundos
        "upload_date": info.get("upload_date"),  # YYYYMMDD
    }


def download_audio(url: str, title: str) -> Path:
    """Descarga el audio del video como WAV. Devuelve la ruta."""
    import yt_dlp

    slug = _slug(title)
    out_base = config.AUDIO_DIR / slug
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(out_base) + ".%(ext)s",
        "quiet": True, "no_warnings": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "wav", "preferredquality": "192"}
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    audio_path = out_base.with_suffix(".wav")
    if not audio_path.exists():
        cands = list(config.AUDIO_DIR.glob(f"{slug}.*"))
        if not cands:
            raise FileNotFoundError(f"No se pudo descargar el audio de {url}")
        audio_path = cands[0]
    return audio_path


def _get_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        _whisper_model = WhisperModel(
            config.WHISPER_MODEL, device="cpu", compute_type=config.WHISPER_COMPUTE_TYPE
        )
    return _whisper_model


def transcribe_audio(
    audio_path: Path,
    duration: float | None = None,
    on_progress: Callable[[float, float | None], None] | None = None,
) -> dict:
    """Transcribe audio reportando progreso (fracción 0-1) y ETA en segundos."""
    model = _get_model()
    segments, info = model.transcribe(
        str(audio_path), language=config.WHISPER_LANGUAGE, vad_filter=True
    )
    total = duration or getattr(info, "duration", None)
    start_t = time.time()
    segs, parts = [], []
    for s in segments:
        txt = s.text.strip()
        segs.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": txt})
        parts.append(txt)
        if on_progress and total:
            frac = min(0.99, s.end / total)
            elapsed = time.time() - start_t
            eta = (elapsed / frac - elapsed) if frac > 0.02 else None
            on_progress(frac, eta)
    if on_progress:
        on_progress(1.0, 0)
    return {"text": " ".join(parts).strip(), "segments": segs}


def process_url(
    url: str, on_progress: Callable[[str, float, float | None], None] | None = None
) -> dict:
    """Pipeline de ingesta: metadatos -> descarga -> transcripción -> etiquetado.

    on_progress(stage, fraction, eta_seconds) se llama durante el proceso.
    Devuelve el registro de la conferencia (sin guardar; lo guarda el caller).
    """
    def report(stage, frac, eta=None):
        if on_progress:
            on_progress(stage, frac, eta)

    report("info", 0.0)
    info = fetch_info(url)
    report("downloading", 0.0)
    audio_path = download_audio(url, info["title"])
    result = transcribe_audio(
        audio_path, duration=info.get("duration"),
        on_progress=lambda f, eta: report("transcribing", f, eta),
    )
    segments = speakers.tag_segments(result["segments"])
    return {
        "url": url,
        "title": info["title"],
        "duration": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "text": result["text"],
        "segments": segments,
        "speaker_summary": speakers.summary(segments),
    }

"""Configuración central del backend."""
from pathlib import Path

# ── Rutas ───────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
DATA_DIR = BASE_DIR.parent / "data"                        # PROYECTO/data
AUDIO_DIR = DATA_DIR / "audio"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
MODELS_DIR = DATA_DIR / "models"

for _d in (AUDIO_DIR, TRANSCRIPTS_DIR, MODELS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── Transcripción (Whisper) ─────────────────────────────────────────
# "small" = buen balance calidad/velocidad en CPU arm64 para español.
# "medium" mejora la calidad pero es ~3x más lento.
WHISPER_MODEL = "small"
WHISPER_LANGUAGE = "es"
WHISPER_COMPUTE_TYPE = "int8"   # cuantización para CPU

# ── Embeddings / Topic Modeling ─────────────────────────────────────
# Modelo de embeddings multilingüe (sirve para español) usado por BERTopic.
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# ── Sentimiento (capa de aplicación) ────────────────────────────────
# pysentimiento usa RoBERTuito (entrenado en español rioplatense).
SENTIMENT_LANG = "es"

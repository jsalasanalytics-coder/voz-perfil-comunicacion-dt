"""Perfil de Comunicación del DT (capa de aplicación sobre el topic modeling).

- topic modeling sobre las RESPUESTAS del entrenador (no las preguntas),
- distribución de tópicos, sentimiento y evolución conferencia a conferencia,
- métricas/radar, % de confianza y conclusiones (metrics.py).
"""
from __future__ import annotations

import json
import threading
from collections import Counter, defaultdict

from . import metrics, preprocess, speakers, store, topic_model

# BERTopic/UMAP usan Numba, que NO es thread-safe. FastAPI atiende en un pool de
# hilos, así que dos análisis simultáneos crasheaban el proceso. Serializamos todo
# el cómputo pesado con este lock (los resultados se cachean, así que no penaliza).
_compute_lock = threading.Lock()

_sentiment = None


def _get_sentiment():
    global _sentiment
    if _sentiment is None:
        from pysentimiento import create_analyzer

        _sentiment = create_analyzer(task="sentiment", lang="es")
    return _sentiment


def _sentiment_batch(sentences: list[str]) -> list[str]:
    if not sentences:
        return []
    analyzer = _get_sentiment()
    try:
        preds = analyzer.predict(sentences)          # batch (rápido)
        return [p.output for p in preds]
    except Exception:
        return [analyzer.predict(s).output for s in sentences]


def _coach_text(record: dict) -> str:
    """Texto del DT: usa segmentos etiquetados si existen; si no, el texto completo."""
    segs = record.get("segments")
    if segs and any("speaker" in s for s in segs):
        return speakers.coach_text(segs)
    return record.get("text", "")


def _topic_label(words: list[str], k: int = 3) -> str:
    return " · ".join(words[:k]) if words else "—"


def _norm(c: Counter) -> dict:
    total = sum(c.values())
    return {str(k): round(v / total, 4) for k, v in c.items()} if total else {}


def _auto_n_topics(n_sentences: int) -> int:
    if n_sentences < 25:
        return 3
    if n_sentences < 60:
        return 4
    if n_sentences < 120:
        return 5
    return 6


# ── Análisis de un entrenador (app) ─────────────────────────────────
def analyze_coach(coach_id: str, n_topics: int | None = None, use_cache: bool = True) -> dict:
    coach = store.get_coach(coach_id)
    if not coach:
        raise ValueError("Entrenador no encontrado.")
    confs = store.list_conferences(coach_id)
    if not confs:
        return {"coach": coach, "ready": False, "reason": "Sin conferencias cargadas."}

    sig = "|".join(sorted(c["id"] for c in confs)) + f"#nt={n_topics}"
    cache_fp = store.COACHES_DIR / coach_id / "_analysis.json"

    def _read_cache():
        if cache_fp.exists():
            try:
                d = json.loads(cache_fp.read_text(encoding="utf-8"))
                if d.get("_sig") == sig:
                    return d
            except Exception:
                pass
        return None

    if use_cache:
        hit = _read_cache()
        if hit:
            return hit

    # Serializamos el cómputo pesado (BERTopic/Numba/spaCy/Torch no son thread-safe).
    with _compute_lock:
        # Otro hilo pudo haber calculado lo mismo mientras esperábamos el lock.
        if use_cache:
            hit = _read_cache()
            if hit:
                return hit

        # 1) Frases del DT, con su conferencia de origen.
        sentences, conf_of = [], []
        for c in confs:
            for s in preprocess.split_sentences(_coach_text(c)):
                sentences.append(s)
                conf_of.append(c)

        if len(sentences) < 5:
            return {"coach": coach, "ready": False,
                    "reason": "Muy poco material del DT para analizar (subí más conferencias)."}

        nt = n_topics or _auto_n_topics(len(sentences))

        # 2) Topic modeling sobre las respuestas del DT.
        tmodel, topics = topic_model.fit_bertopic(sentences, n_topics=nt)
        topic_words = topic_model.bertopic_topic_words(tmodel, topn=10)

        # 3) Sentimiento por frase.
        sentiments = _sentiment_batch(sentences)

        # 4) Métricas / radar / confianza / conclusiones.
        m = metrics.compute(sentences, sentiments)

        # 5) Agregaciones de tópicos.
        tcount = Counter()
        tsent = defaultdict(Counter)
        conf_topics = defaultdict(Counter)
        conf_sent = defaultdict(Counter)
        for t, sent, c in zip(topics, sentiments, conf_of):
            if t == -1:
                continue
            tcount[t] += 1
            tsent[t][sent] += 1
            conf_topics[c["id"]][t] += 1
            conf_sent[c["id"]][sent] += 1
        total = sum(tcount.values()) or 1
        topics_out = [
            {"id": int(tid), "label": _topic_label(w), "words": w,
             "size": int(tcount[tid]), "share": round(tcount[tid] / total, 4),
             "sentiment": _norm(tsent[tid])}
            for tid, w in sorted(topic_words.items(), key=lambda kv: -tcount[kv[0]])
        ]

        # 6) Evolución por conferencia.
        labels = {t["id"]: t["label"] for t in topics_out}
        evolution = [
            {"conf_id": c["id"], "title": c.get("title"), "date": c.get("upload_date"),
             "topic_distribution": _norm(conf_topics[c["id"]]),
             "sentiment": _norm(conf_sent[c["id"]])}
            for c in confs
        ]

        # 7) Preguntas de los periodistas (agregado).
        q_total = sum(c.get("speaker_summary", {}).get("n_preguntas", 0) for c in confs)

        coherence_cv = round(
            topic_model.coherence_cv(list(topic_words.values()),
                                     preprocess.tokenize_corpus(sentences)), 4)

        result = {
            "_sig": sig,
            "ready": True,
            "coach": coach,
            "n_conferences": len(confs),
            "n_sentences": len(sentences),
            "n_topics": len(topics_out),
            "topics": topics_out,
            "topic_labels": labels,
            "metrics": m,
            "evolution": evolution,
            "questions": {"total": q_total},
            "conferences": [
                {"id": c["id"], "title": c.get("title"), "url": c.get("url"),
                 "date": c.get("upload_date"), "duration": c.get("duration"),
                 **c.get("speaker_summary", {})}
                for c in confs
            ],
            "coherence": {"bertopic_cv": coherence_cv},
        }
        cache_fp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result


def invalidate_cache(coach_id: str) -> None:
    fp = store.COACHES_DIR / coach_id / "_analysis.json"
    if fp.exists():
        fp.unlink()


# ── Demo interactiva del pipeline (para explicar el flujo) ──────────
def explain_pipeline(text: str) -> dict:
    """Transforma un texto por cada etapa del pipeline NLP, para mostrarlo paso a paso."""
    text = (text or "").strip()
    if not text:
        return {"raw": "", "stages": []}
    with _compute_lock:
        sentences = preprocess.split_sentences(text, min_words=1) or [text]
        sentiments = _sentiment_batch(sentences)
        stages = [
            {
                "sentence": s,
                "speaker": speakers.classify(s),         # PREGUNTA (periodista) o DT
                "lemmas": preprocess.content_tokens(s),  # tokens de contenido lematizados
                "sentiment": sent,                       # POS / NEU / NEG
            }
            for s, sent in zip(sentences, sentiments)
        ]
    dt = [st for st in stages if st["speaker"] == "DT"]
    dt_sents = [st["sentence"] for st in dt]
    dt_sentiment = [st["sentiment"] for st in dt]
    mini_metrics = metrics.compute(dt_sents, dt_sentiment) if dt_sents else None
    return {
        "raw": text,
        "n_sentences": len(sentences),
        "n_questions": sum(1 for st in stages if st["speaker"] == "PREGUNTA"),
        "stages": stages,
        "bag_of_words": sorted({l for st in dt for l in st["lemmas"]}),
        "metrics": mini_metrics,
    }


# ── Análisis multi-DT (para el notebook académico) ──────────────────
def build_profile(records: list[dict], n_topics: int | None = None, run_lda: bool = True) -> dict:
    """Topic modeling pooled sobre varias conferencias/DTs (usado en el notebook)."""
    sentences, meta = [], []
    for r in records:
        coach = r.get("coach") or "Desconocido"
        for s in preprocess.split_sentences(_coach_text(r)):
            sentences.append(s)
            meta.append(coach)
    if len(sentences) < 5:
        raise ValueError(f"Corpus demasiado chico ({len(sentences)} oraciones).")

    nt = n_topics or _auto_n_topics(len(sentences))
    tmodel, topics = topic_model.fit_bertopic(sentences, n_topics=nt)
    topic_words = topic_model.bertopic_topic_words(tmodel, topn=10)
    sentiments = _sentiment_batch(sentences)

    tcount, tsent = Counter(), defaultdict(Counter)
    coach_topic, coach_sent = defaultdict(Counter), defaultdict(Counter)
    coach_sents = defaultdict(list)
    for t, sent, coach, s in zip(topics, sentiments, meta, sentences):
        coach_sents[coach].append((s, sent))
        if t == -1:
            continue
        tcount[t] += 1
        tsent[t][sent] += 1
        coach_topic[coach][t] += 1
        coach_sent[coach][sent] += 1
    total = sum(tcount.values()) or 1
    topics_out = [
        {"id": int(tid), "label": _topic_label(w), "words": w,
         "size": int(tcount[tid]), "share": round(tcount[tid] / total, 4),
         "sentiment": _norm(tsent[tid])}
        for tid, w in sorted(topic_words.items(), key=lambda kv: -tcount[kv[0]])
    ]
    coaches_out = {}
    for coach, cnt in coach_topic.items():
        sents = [s for s, _ in coach_sents[coach]]
        senti = [se for _, se in coach_sents[coach]]
        coaches_out[coach] = {
            "n_sentences": int(sum(cnt.values())),
            "topic_distribution": _norm(cnt),
            "sentiment": _norm(coach_sent[coach]),
            "metrics": metrics.compute(sents, senti),
        }
    tokenized = preprocess.tokenize_corpus(sentences)
    coherence = {"bertopic_cv": round(
        topic_model.coherence_cv(list(topic_words.values()), tokenized), 4)}
    if run_lda:
        coherence["lda_search"] = topic_model.search_lda_k(tokenized)
    return {"n_sentences": len(sentences), "topics": topics_out,
            "coaches": coaches_out, "coherence": coherence}

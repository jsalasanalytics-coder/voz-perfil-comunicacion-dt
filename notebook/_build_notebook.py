"""Genera el notebook académico (analisis_topic_modeling.ipynb).

Construye un .ipynb válido reutilizando los módulos del backend (app/*).
Ejecutar: python _build_notebook.py
"""
import json
from pathlib import Path

cells = []


def md(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)})


def code(src):
    cells.append({
        "cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
        "source": src.strip("\n").splitlines(keepends=True),
    })


md(r"""
# Perfil de Comunicación de Entrenadores de Fútbol mediante Topic Modeling

**Trabajo Práctico Integrador — Procesamiento de Lenguaje Natural**
Ingeniería en Inteligencia Artificial · Universidad de Palermo

---

## 1. Introducción

Las conferencias de prensa de los entrenadores de fútbol son una fuente rica de
información sobre **cómo comunica** un DT: de qué temas habla, en qué proporción y
cómo cambia su discurso. Hoy ese análisis se hace de forma manual y subjetiva.

**Tarea de NLP elegida (una sola): Topic Modeling.**

Reformulamos el objetivo —"perfil de comunicación del DT"— como un problema de
topic modeling:

> El perfil de comunicación de un entrenador = la **distribución de tópicos** latentes
> en su discurso + su **evolución** + un **descriptor de sentimiento** por tópico.

El topic modeling es el núcleo metodológico; el perfil es la capa de aplicación.

**Metodología (toda del APUNTE 7 de la cursada):**
- **BERTopic** (Sentence-BERT + UMAP + HDBSCAN/K-means + c-TF-IDF) — modelo principal.
- **LDA** (gensim) — baseline.
- **Coherencia c_v** — métrica para comparar y elegir el nº de tópicos.
- `pysentimiento` — descriptor de sentimiento (secundario).
""")

md("## 2. Configuración\n\nEl notebook reutiliza los módulos del backend (`app/`).")

code(r"""
import sys
from pathlib import Path

# Hacer visible el paquete del backend
BACKEND = Path.cwd().parent / "backend"
sys.path.insert(0, str(BACKEND))

import pandas as pd
import matplotlib.pyplot as plt

from app import transcription, preprocess, topic_model, profile

pd.set_option("display.max_colwidth", 80)
print("Módulos cargados.")
""")

md(r"""
## 3. Dataset

Corpus propio de transcripciones de conferencias de prensa de DTs del fútbol
argentino, generado con el pipeline de ingesta (yt-dlp + Whisper). Los transcripts
están en `data/transcripts/`.

> Para agregar conferencias nuevas: `transcription.process_url("<link de YouTube>", coach="<DT>")`
""")

code(r"""
records = transcription.load_transcripts()
df = pd.DataFrame([
    {"DT": r.get("coach"), "conferencia": r.get("title"),
     "caracteres": len(r.get("text", "")), "segmentos": len(r.get("segments", []))}
    for r in records
])
print(f"Conferencias en el corpus: {len(records)}")
df
""")

code(r"""
# Ejemplo de transcripción (primeros 500 caracteres)
print(records[0]["coach"], "—", records[0]["title"], "\n")
print(records[0]["text"][:500], "…")
""")

md(r"""
## 4. Preprocesamiento

- **Segmentación en oraciones**: cada oración es la unidad de documento del topic modeling.
- **Tokens de contenido** (sustantivos, verbos, adjetivos, propios), lematizados y sin
  stopwords ni muletillas — usados para LDA y para la coherencia c_v.
""")

code(r"""
sentences, meta = [], []
for r in records:
    for s in preprocess.split_sentences(r["text"]):
        sentences.append(s)
        meta.append({"coach": r.get("coach") or "Desconocido",
                     "conf": r.get("title") or r.get("url")})

print(f"Oraciones totales: {len(sentences)}\n")
print("Ejemplo de oración:\n ", sentences[0])
print("\nTokens de contenido de esa oración:\n ", preprocess.content_tokens(sentences[0]))
""")

md(r"""
## 5. Topic Modeling con BERTopic (modelo principal)

BERTopic genera embeddings de las oraciones con Sentence-BERT, reduce dimensionalidad
con UMAP, las agrupa (HDBSCAN automático o K-means con nº fijo) y describe cada tópico
con c-TF-IDF.
""")

code(r"""
# n_topics=None -> HDBSCAN descubre el nº de tópicos automáticamente.
# Para corpus chicos de texto corto, fijar n_topics (K-means) suele dar tópicos
# más interpretables. Probamos ambos.
tmodel, topics = topic_model.fit_bertopic(sentences, n_topics=5)
topic_words = topic_model.bertopic_topic_words(tmodel, topn=10)

for tid, words in topic_words.items():
    print(f"Tópico {tid}: {', '.join(words)}")
""")

code(r"""
# Tamaño de cada tópico
info = tmodel.get_topic_info()[["Topic", "Count", "Name"]]
info
""")

md("### Coherencia c_v del modelo BERTopic")

code(r"""
tokenized = preprocess.tokenize_corpus(sentences)
cv_bertopic = topic_model.coherence_cv(list(topic_words.values()), tokenized)
print(f"Coherencia c_v (BERTopic): {cv_bertopic:.4f}")
""")

md(r"""
## 6. Baseline: LDA y selección del número de tópicos

Ajustamos LDA (gensim) variando el número de tópicos *k* y elegimos el *k* que
maximiza la coherencia c_v.
""")

code(r"""
lda_search = topic_model.search_lda_k(tokenized, ks=range(3, 11))
sdf = pd.DataFrame(lda_search)
best = sdf.loc[sdf["coherence_cv"].idxmax()]
print(f"Mejor k = {int(best['k'])}  (c_v = {best['coherence_cv']:.4f})")

plt.figure(figsize=(7, 4))
plt.plot(sdf["k"], sdf["coherence_cv"], "o-", color="#0071e3")
plt.axvline(best["k"], ls="--", color="gray", alpha=.6)
plt.xlabel("Número de tópicos (k)"); plt.ylabel("Coherencia c_v")
plt.title("LDA — selección del número de tópicos"); plt.grid(alpha=.3); plt.show()
""")

md("## 7. Comparación BERTopic vs LDA")

code(r"""
lda, _, _ = topic_model.fit_lda(tokenized, int(best["k"]))
cv_lda = topic_model.coherence_cv(topic_model.lda_topic_words(lda), tokenized)

comp = pd.DataFrame({"modelo": ["BERTopic", f"LDA (k={int(best['k'])})"],
                     "coherencia_cv": [cv_bertopic, cv_lda]})
plt.figure(figsize=(5, 3.5))
plt.bar(comp["modelo"], comp["coherencia_cv"], color=["#0071e3", "#34c759"])
plt.ylabel("Coherencia c_v"); plt.title("BERTopic vs LDA"); plt.show()
comp
""")

md(r"""
## 8. Perfil de Comunicación del DT (capa de aplicación)

Sobre el topic modeling construimos el perfil: distribución de tópicos por entrenador,
sentimiento por tópico y evolución conferencia a conferencia.
""")

code(r"""
prof = profile.build_profile(records, n_topics=5, run_lda=False)
print(f"Oraciones: {prof['n_sentences']} | Tópicos: {len(prof['topics'])} | "
      f"c_v BERTopic: {prof['coherence']['bertopic_cv']}")

topics_df = pd.DataFrame([
    {"tópico": t["id"], "etiqueta": t["label"], "peso_%": round(t["share"]*100, 1),
     "POS": t["sentiment"].get("POS", 0), "NEU": t["sentiment"].get("NEU", 0),
     "NEG": t["sentiment"].get("NEG", 0)}
    for t in prof["topics"]
])
topics_df
""")

code(r"""
# Distribución de tópicos por DT (heatmap simple)
labels = {t["id"]: t["label"] for t in prof["topics"]}
rows = []
for coach, p in prof["coaches"].items():
    row = {"DT": coach}
    for tid, share in p["topic_distribution"].items():
        row[labels.get(int(tid), tid)] = round(share*100, 1)
    rows.append(row)
dist = pd.DataFrame(rows).set_index("DT").fillna(0)
dist
""")

code(r"""
# Perfil de cada DT como barras apiladas
ax = dist.plot(kind="barh", stacked=True, figsize=(9, 1.2*len(dist)+1),
               colormap="tab20")
ax.set_xlabel("% del discurso"); ax.set_title("Perfil de comunicación por entrenador")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
plt.tight_layout(); plt.show()
""")

code(r"""
# Sentimiento general por DT
sent_rows = [{"DT": c, **{k: round(v*100,1) for k,v in p["sentiment"].items()}}
             for c, p in prof["coaches"].items()]
pd.DataFrame(sent_rows).set_index("DT").fillna(0)[["POS","NEU","NEG"]]
""")

md(r"""
## 9. Discusión, limitaciones y conclusiones

**Conclusiones**
- El topic modeling permite construir un perfil objetivo y reproducible de cómo
  comunica cada entrenador, a partir de texto transcripto automáticamente.
- BERTopic produce tópicos más interpretables que LDA en texto conversacional corto;
  la coherencia c_v sirvió para comparar y para elegir el nº de tópicos.

**Limitaciones**
- Ruido de ASR (Whisper transcribe mal algunos nombres propios, p. ej. "River").
- Corpus chico: a más conferencias, tópicos más estables y mejor coherencia.
- El sentimiento es un descriptor agregado, no un análisis fino por frase.

**Trabajo futuro**
- Ampliar el corpus; normalizar nombres propios; etiquetar manualmente una muestra
  para validar la interpretación de los tópicos.
""")

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3 (venv)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
    },
    "nbformat": 4, "nbformat_minor": 5,
}

out = Path(__file__).parent / "analisis_topic_modeling.ipynb"
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Notebook generado: {out}  ({len(cells)} celdas)")

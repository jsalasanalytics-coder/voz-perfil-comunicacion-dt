"""Núcleo metodológico: Topic Modeling.

Modelo principal : BERTopic (Sentence-BERT + UMAP + HDBSCAN + c-TF-IDF)
Baseline         : LDA (gensim)
Métrica de selección: coherencia c_v (gensim)

Todas las técnicas provienen del APUNTE 7 de la cursada.
"""
from __future__ import annotations

from . import config, preprocess

_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        _embedder = SentenceTransformer(config.EMBEDDING_MODEL)
    return _embedder


# ── Coherencia c_v (común a cualquier modelo) ───────────────────────
def coherence_cv(topics_words: list[list[str]], tokenized_docs: list[list[str]]) -> float:
    """Coherencia c_v de un conjunto de tópicos (listas de palabras)."""
    from gensim.corpora import Dictionary
    from gensim.models.coherencemodel import CoherenceModel

    tokenized_docs = [d for d in tokenized_docs if d]
    if not tokenized_docs:
        return 0.0
    dictionary = Dictionary(tokenized_docs)
    # Sólo palabras presentes en el diccionario, tópicos con >=2 términos.
    topics = [[w for w in t if w in dictionary.token2id] for t in topics_words]
    topics = [t for t in topics if len(t) >= 2]
    if not topics:
        return 0.0
    cm = CoherenceModel(
        topics=topics, texts=tokenized_docs, dictionary=dictionary, coherence="c_v"
    )
    return float(cm.get_coherence())


# ── BERTopic (modelo principal) ─────────────────────────────────────
def fit_bertopic(docs: list[str], min_topic_size: int = 5, n_topics: int | None = None):
    """Ajusta BERTopic sobre una lista de documentos (oraciones).

    n_topics:
      - None  -> clustering automático con HDBSCAN (descubre el nº de tópicos).
      - int   -> fuerza ese nº de tópicos con K-means (más estable en corpus
                 chicos de texto corto, como las conferencias).
    Ambas técnicas provienen del APUNTE 7 (K-means y BERTopic/HDBSCAN).
    """
    from bertopic import BERTopic
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP

    n = len(docs)
    # Hiperparámetros adaptados al tamaño del corpus (conferencias -> corpus chico).
    n_neighbors = max(2, min(15, n - 1))
    umap_model = UMAP(
        n_neighbors=n_neighbors, n_components=5, min_dist=0.0,
        metric="cosine", random_state=42,
    )
    if n_topics:
        from sklearn.cluster import KMeans

        cluster_model = KMeans(n_clusters=min(n_topics, max(2, n // 2)), random_state=42, n_init=10)
    else:
        from hdbscan import HDBSCAN

        cluster_model = HDBSCAN(
            min_cluster_size=max(2, min_topic_size), min_samples=1,
            metric="euclidean", cluster_selection_method="eom", prediction_data=True,
        )
    # min_df adaptativo: en corpus chicos exigir df>=2 vacía el vocabulario
    # y rompe el c-TF-IDF. Subimos el umbral sólo cuando hay suficientes docs.
    min_df = 2 if n >= 30 else 1
    vectorizer_model = CountVectorizer(
        stop_words=preprocess.stopwords(), ngram_range=(1, 2), min_df=min_df,
    )

    topic_model = BERTopic(
        embedding_model=_get_embedder(),
        umap_model=umap_model,
        hdbscan_model=cluster_model,
        vectorizer_model=vectorizer_model,
        language="multilingual",
        calculate_probabilities=False,
        verbose=False,
    )
    topics, _ = topic_model.fit_transform(docs)
    return topic_model, topics


def bertopic_topic_words(topic_model, topn: int = 10) -> dict[int, list[str]]:
    """Palabras representativas por tópico (excluye el tópico de outliers -1)."""
    out = {}
    for tid in topic_model.get_topics():
        if tid == -1:
            continue
        out[tid] = [w for w, _ in topic_model.get_topic(tid)][:topn]
    return out


# ── LDA (baseline) ──────────────────────────────────────────────────
def fit_lda(tokenized_docs: list[list[str]], num_topics: int):
    """Ajusta LDA con gensim. Devuelve (modelo, diccionario, corpus_bow)."""
    from gensim.corpora import Dictionary
    from gensim.models import LdaModel

    tokenized_docs = [d for d in tokenized_docs if d]
    dictionary = Dictionary(tokenized_docs)
    dictionary.filter_extremes(no_below=2, no_above=0.6)
    corpus = [dictionary.doc2bow(d) for d in tokenized_docs]
    lda = LdaModel(
        corpus=corpus, id2word=dictionary, num_topics=num_topics,
        random_state=42, passes=10, alpha="auto", per_word_topics=False,
    )
    return lda, dictionary, corpus


def lda_topic_words(lda, topn: int = 10) -> list[list[str]]:
    return [[w for w, _ in lda.show_topic(t, topn=topn)] for t in range(lda.num_topics)]


def search_lda_k(tokenized_docs: list[list[str]], ks=range(3, 11)) -> list[dict]:
    """Barre nº de tópicos en LDA y reporta coherencia c_v de cada k."""
    results = []
    for k in ks:
        try:
            lda, _, _ = fit_lda(tokenized_docs, k)
            c = coherence_cv(lda_topic_words(lda), tokenized_docs)
            results.append({"k": int(k), "coherence_cv": round(c, 4)})
        except Exception as e:  # pragma: no cover
            results.append({"k": int(k), "coherence_cv": None, "error": str(e)})
    return results

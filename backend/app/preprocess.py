"""Preprocesamiento de texto en español con spaCy.

Provee:
  - segmentación en oraciones (unidad de documento para el topic modeling)
  - tokens lematizados de contenido (para LDA y para la coherencia c_v)
  - lista de stopwords ampliada (muletillas de conferencias)
"""
from __future__ import annotations

import spacy

# Muletillas y ruido típico de conferencias de prensa orales.
EXTRA_STOPWORDS = {
    "bueno", "eh", "este", "digamos", "nada", "obvio", "obviamente", "tipo",
    "claro", "mira", "viste", "entonces", "osea", "o_sea", "ehh", "mmm",
    "decir", "creo", "ser", "haber", "tener", "hacer", "ir", "estar",
    "cosa", "tema", "momento", "manera", "forma", "vez", "parte",
    "hoy", "ahora", "siempre", "ahi", "ahí", "aca", "acá", "alla", "allá",
    "asi", "así", "tambien", "también", "igual", "che", "mira", "miren",
    "muy", "mas", "más", "menos", "poco", "mucho", "verdad", "pregunta",
}

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        # No necesitamos NER para esto -> lo desactivamos por velocidad.
        _nlp = spacy.load("es_core_news_md", disable=["ner"])
        for w in EXTRA_STOPWORDS:
            _nlp.vocab[w].is_stop = True
    return _nlp


def stopwords() -> list[str]:
    """Stopwords en español (spaCy + muletillas) para el CountVectorizer."""
    nlp = _get_nlp()
    return sorted(set(nlp.Defaults.stop_words) | EXTRA_STOPWORDS)


def split_sentences(text: str, min_words: int = 4) -> list[str]:
    """Divide un texto en oraciones; descarta las muy cortas (ruido)."""
    nlp = _get_nlp()
    sents = []
    for doc in nlp.pipe([text]):
        for sent in doc.sents:
            s = sent.text.strip()
            if len(s.split()) >= min_words:
                sents.append(s)
    return sents


def content_tokens(text: str) -> list[str]:
    """Tokens lematizados de contenido (sustantivos, verbos, adjetivos, propios).

    Usado para LDA y para calcular la coherencia c_v de cualquier modelo.
    """
    nlp = _get_nlp()
    keep_pos = {"NOUN", "PROPN", "ADJ", "VERB"}
    toks = []
    for doc in nlp.pipe([text]):
        for t in doc:
            if (
                t.pos_ in keep_pos
                and not t.is_stop
                and not t.is_punct
                and t.is_alpha
                and len(t.lemma_) > 2
            ):
                toks.append(t.lemma_.lower())
    return toks


def tokenize_corpus(docs: list[str]) -> list[list[str]]:
    """Aplica content_tokens a una lista de documentos (oraciones)."""
    return [content_tokens(d) for d in docs]

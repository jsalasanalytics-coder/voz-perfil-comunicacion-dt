"""Métricas del perfil comunicacional (capa de aplicación para el dirigente).

A partir de las frases del DT y su sentimiento, calcula 6 dimensiones interpretables
(0-100) para un gráfico de radar, un % de confianza destacado y conclusiones en
lenguaje claro. Se apoya en léxicos en español + el análisis de sentimiento.

Es un descriptor derivado; la tarea central de NLP del proyecto sigue siendo el
topic modeling.
"""
from __future__ import annotations

import re

# ── Léxicos en español ──────────────────────────────────────────────
LEX = {
    "certeza": [
        "seguro", "segura", "seguros", "convencido", "convencida", "convencidos",
        "confío", "confiamos", "confianza", "sin dudas", "sin duda", "claramente",
        "por supuesto", "garantizo", "estoy seguro", "tengo la certeza", "indudable",
        "firme", "contundente", "absolutamente", "plenamente", "totalmente", "sé que",
        "vamos a", "tenemos que ganar", "decididos", "decisión tomada",
    ],
    "incertidumbre": [
        "ojalá", "veremos", "no sé", "no se", "capaz", "quizás", "quizá", "tal vez",
        "puede ser", "puede que", "intentaremos", "trataremos", "esperemos", "esperamos",
        "si dios quiere", "habrá que ver", "no estoy seguro", "supongo", "creo que",
        "me parece", "vamos viendo", "veremos qué", "no sabemos",
    ],
    "autocritica": [
        "nos faltó", "faltó", "error", "errores", "nos equivocamos", "me equivoqué",
        "tenemos que mejorar", "hay que mejorar", "mejorar", "no estuvimos", "fallamos",
        "fallé", "responsabilidad", "asumo", "me hago cargo", "corregir", "nos costó",
        "no fuimos", "no jugamos bien", "no me gustó", "debemos", "no merecíamos",
        "autocrítica", "lo hicimos mal",
    ],
    "tactico": [
        "presión", "presionar", "presionamos", "marca", "marcar", "posesión", "pelota",
        "línea", "bloque", "mediocampo", "esquema", "sistema", "juego", "jugada", "jugadas",
        "espacios", "defensa", "defensivo", "defensiva", "ataque", "ofensivo", "salida",
        "circulación", "banda", "posición", "táctica", "táctico", "recuperar", "transición",
        "achicar", "retroceder", "pressing", "doble cinco", "volante", "lateral", "central",
    ],
    "rival": [
        "rival", "rivales", "adversario", "el otro equipo", "contrincante", "enfrente",
        "ellos", "su equipo", "merecieron", "nos superaron", "fueron superiores",
    ],
    "grupo": [
        "grupo", "plantel", "equipo", "compañeros", "vestuario", "unidos", "unión",
        "juntos", "familia", "club", "hinchada", "gente", "nosotros", "colectivo",
        "jugadores", "muchachos", "chicos", "los pibes", "entrega", "esfuerzo",
    ],
}


def _matcher(terms: list[str]):
    words = [t for t in terms if " " not in t]
    phrases = [t for t in terms if " " in t]
    word_re = re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b") if words else None

    def hit(text_lower: str) -> bool:
        if word_re and word_re.search(text_lower):
            return True
        return any(p in text_lower for p in phrases)

    return hit


_MATCHERS = {k: _matcher(v) for k, v in LEX.items()}


def _clamp(x: float, lo: float = 0, hi: float = 100) -> int:
    return int(round(max(lo, min(hi, x))))


def compute(sentences: list[str], sentiments: list[str]) -> dict:
    """sentences: frases del DT. sentiments: 'POS'/'NEU'/'NEG' alineados a cada frase."""
    n = len(sentences) or 1
    lowered = [s.lower() for s in sentences]

    # Proporción de frases que tocan cada dimensión.
    prop = {k: sum(1 for t in lowered if m(t)) / n for k, m in _MATCHERS.items()}

    pos = sentiments.count("POS") / len(sentiments) if sentiments else 0
    neg = sentiments.count("NEG") / len(sentiments) if sentiments else 0
    neu = sentiments.count("NEU") / len(sentiments) if sentiments else 0

    # Índices. (Escalado calibrado para no saturar y mantener poder comparativo.)
    certeza_idx = prop["certeza"] - prop["incertidumbre"]      # ~[-0.3, 0.3]
    sentiment_idx = pos - neg                                   # [-1, 1]

    # Confianza y positividad tienen un punto neutro (~55); el resto parte de 0
    # (= "no habla de eso"), que es interpretable de por sí.
    confianza = _clamp(55 + 110 * certeza_idx + 22 * sentiment_idx, 8, 96)
    positividad = _clamp(55 + 50 * sentiment_idx, 2, 98)
    autocritica = _clamp(prop["autocritica"] * 170)
    tactico = _clamp(prop["tactico"] * 120)
    foco_rival = _clamp(prop["rival"] * 200)
    cohesion = _clamp(prop["grupo"] * 110)

    radar = [
        {"axis": "Confianza", "value": confianza},
        {"axis": "Positividad", "value": positividad},
        {"axis": "Autocrítica", "value": autocritica},
        {"axis": "Enfoque táctico", "value": tactico},
        {"axis": "Foco en el rival", "value": foco_rival},
        {"axis": "Cohesión / grupo", "value": cohesion},
    ]

    return {
        "radar": radar,
        "confianza": confianza,
        "sentiment": {"POS": round(pos, 3), "NEU": round(neu, 3), "NEG": round(neg, 3)},
        "conclusions": _conclusions(
            confianza, positividad, autocritica, tactico, foco_rival, cohesion
        ),
        "headline": _headline(confianza, positividad, tactico, foco_rival, cohesion, autocritica),
    }


# ── Conclusiones en lenguaje claro (para un dirigente) ──────────────
def _conclusions(conf, posit, autoc, tact, rival, grupo) -> list[str]:
    c = []
    if conf >= 70:
        c.append(f"Proyecta **alta confianza** ({conf}%): transmite seguridad y convicción.")
    elif conf >= 50:
        c.append(f"Transmite una **confianza moderada** ({conf}%).")
    else:
        c.append(f"Su discurso muestra **cautela e incertidumbre** (confianza {conf}%).")

    if posit >= 65:
        c.append("Tono **claramente positivo**: destaca lo bueno y motiva.")
    elif posit <= 40:
        c.append("Tono **predominantemente crítico/negativo**.")
    else:
        c.append("Tono **equilibrado** entre lo positivo y lo crítico.")

    if autoc >= 50:
        c.append("Tiene **alta autocrítica**: asume responsabilidades y reconoce qué mejorar.")
    elif autoc <= 20:
        c.append("**Rara vez expone autocrítica** en público.")

    foci = {"táctico": tact, "el rival": rival, "el grupo y el plantel": grupo}
    dom = max(foci, key=foci.get)
    if foci[dom] >= 40:
        c.append(f"Su discurso se centra sobre todo en **{dom}**.")
    return c


def _headline(conf, posit, tact, rival, grupo, autoc) -> str:
    conf_w = "confianza alta" if conf >= 70 else ("confianza media" if conf >= 50 else "perfil cauto")
    foci = {"perfil táctico": tact, "foco en el rival": rival, "foco en el grupo": grupo}
    dom = max(foci, key=foci.get)
    extra = "con fuerte autocrítica" if autoc >= 50 else (
        "de tono positivo" if posit >= 65 else "de tono medido")
    return f"Comunicador de {conf_w}, {dom} y {extra}."

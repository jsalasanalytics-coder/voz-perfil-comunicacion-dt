"""Prueba de humo del núcleo NLP con un corpus sintético (sin YouTube).

Valida: preprocesamiento -> BERTopic -> coherencia c_v -> LDA baseline ->
sentimiento -> perfil de comunicación, end-to-end.
"""
import json

from app import profile

# Frases tipo conferencia de prensa de DTs argentinos, varios temas.
PRESION = [
    "Necesitamos presionar mucho más arriba y no dejar jugar al rival.",
    "Nos faltó intensidad y presión en la mitad de la cancha.",
    "El equipo presionó bien los primeros minutos pero después aflojó.",
    "La idea es recuperar rápido la pelota con presión alta.",
    "Cuando presionamos en bloque alto generamos muchas situaciones.",
    "Nos costó sostener la intensidad de la presión todo el partido.",
]
RIVAL = [
    "El rival fue muy superior en el mediocampo durante todo el partido.",
    "Enfrentamos a un gran equipo que nos complicó con su circulación.",
    "Sabíamos que el rival iba a tener la pelota y nos replegamos.",
    "El adversario nos superó en intensidad y en juego aéreo.",
    "Respetamos al rival pero salimos a proponer nuestro juego.",
    "El otro equipo manejó los tiempos del partido mejor que nosotros.",
]
ARBITRO = [
    "El árbitro se equivocó en una jugada clave que cambió el partido.",
    "No quiero hablar del árbitro pero el penal no existió nunca.",
    "Las decisiones arbitrales nos perjudicaron en momentos importantes.",
    "El referí cobró cosas raras y nos sacó del partido.",
    "Hubo fallos del árbitro que condicionaron el resultado final.",
    "Prefiero no opinar del arbitraje para no tener problemas.",
]
JUGADORES = [
    "Estoy muy orgulloso del esfuerzo y la entrega de los jugadores.",
    "Los chicos jóvenes están respondiendo de una manera bárbara.",
    "El plantel trabaja muy bien y eso se ve reflejado en la cancha.",
    "Confío plenamente en cada uno de los jugadores del equipo.",
    "El grupo está sano y comprometido con la idea que proponemos.",
    "Tenemos jugadores de jerarquía que marcan la diferencia.",
]
MENTALIDAD = [
    "Tenemos que mejorar muchísimo en la cabeza y en la actitud.",
    "El equipo necesita madurar y manejar mejor los momentos.",
    "Hay que tener tranquilidad y confianza para revertir esto.",
    "La mentalidad ganadora se construye partido a partido.",
    "Nos falta carácter para sostener los resultados afuera de casa.",
    "Estamos convencidos del camino aunque los resultados no acompañen.",
]


def make_records():
    bielsa = PRESION + JUGADORES + MENTALIDAD[:3] + RIVAL[:2]
    gallardo = ARBITRO + RIVAL + MENTALIDAD[3:] + PRESION[:2]
    return [
        {"coach": "Bielsa", "title": "Conferencia fecha 1", "text": " ".join(bielsa)},
        {"coach": "Gallardo", "title": "Conferencia fecha 1", "text": " ".join(gallardo)},
        {"coach": "Bielsa", "title": "Conferencia fecha 2",
         "text": " ".join(JUGADORES + PRESION[:3] + ARBITRO[:1])},
    ]


if __name__ == "__main__":
    recs = make_records()
    print(f"Conferencias: {len(recs)}")
    prof = profile.build_profile(recs, min_topic_size=3, run_lda=True)
    print(f"\nOraciones: {prof['n_sentences']} | outliers: {prof['n_outliers']}")
    print(f"Coherencia BERTopic c_v: {prof['coherence']['bertopic_cv']}")
    print("\n── Tópicos detectados ──")
    for t in prof["topics"]:
        print(f"  [{t['id']}] {t['label']:35s} size={t['size']:2d} share={t['share']} sent={t['sentiment']}")
    print("\n── Perfil por DT ──")
    for coach, d in prof["coaches"].items():
        print(f"  {coach}: {d['n_sentences']} frases | temas={d['topic_distribution']}")
        print(f"           sentimiento={d['sentiment']}")
    print("\n── Búsqueda de k en LDA (coherencia c_v) ──")
    for r in prof["coherence"]["lda_search"]:
        print(f"  k={r['k']}: c_v={r.get('coherence_cv')}")
    print("\nOK — núcleo NLP validado.")

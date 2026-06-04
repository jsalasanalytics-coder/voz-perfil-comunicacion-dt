# Voz — Perfil de Comunicación de Entrenadores mediante Topic Modeling

Trabajo Práctico Integrador — Procesamiento de Lenguaje Natural
Ingeniería en Inteligencia Artificial — Universidad de Palermo

**Voz** es un software interno tipo CRM: gestionás entrenadores (con foto), les cargás
conferencias de prensa por link de YouTube, y la app construye el perfil comunicacional
de cada DT — distinguiendo las preguntas del periodista de las respuestas del entrenador,
y mostrando un radar de 6 dimensiones, un % de confianza y conclusiones claras para la
toma de decisiones.

---

## 1. Planteamiento del problema

En el fútbol profesional, las conferencias de prensa de los entrenadores son una
fuente rica de información sobre **cómo comunica** un DT: de qué temas habla, en qué
proporción y cómo cambia su discurso según el contexto (victorias, derrotas, rival).
Hoy ese análisis se hace de forma manual y subjetiva.

**Tarea de NLP elegida (una sola, según indicación del docente): Topic Modeling.**

Reformulamos el objetivo original del proyecto —"perfil de comunicación del DT"— como
un problema de topic modeling:

> El perfil de comunicación de un entrenador = la **distribución de tópicos** latentes
> en su discurso, su **evolución** a lo largo de las conferencias y un **descriptor de
> sentimiento** por tópico.

El topic modeling es el núcleo metodológico evaluable; el "perfil de comunicación" es
la capa de aplicación que se construye encima.

## 2. Respuesta a la devolución del docente

1. **¿Están transcriptas?** No. Las transcribimos nosotros con **Whisper (ASR)** a
   partir de links de YouTube. La transcripción es un paso de *ingesta de datos*, no el
   aporte de NLP.
2. **Una sola tarea de NLP** → Topic Modeling (la que sugirió el docente).
3. **No es clasificación de sentimiento.** El sentimiento aparece sólo como descriptor
   secundario por tópico dentro del perfil, no como tarea central.

## 3. Metodología

| Etapa | Herramienta |
|-------|-------------|
| Ingesta | `yt-dlp` (descarga de audio de YouTube) |
| Transcripción (ASR) | `faster-whisper` (español) |
| Preprocesamiento | `spaCy` (`es_core_news_md`) |
| **Topic Modeling (principal)** | **BERTopic** (Sentence-BERT + UMAP + HDBSCAN) |
| **Topic Modeling (baseline)** | **LDA** (`gensim`) |
| Selección de nº de tópicos | **Coherencia `c_v`** (`gensim`) |
| Descriptor de sentimiento | `pysentimiento` (RoBERTuito, español) |

Todas las técnicas provienen del material de la cursada (APUNTE 7 — Clustering y
Topic Modeling).

## 4. Dataset

Corpus propio de transcripciones de conferencias de prensa de DTs del **fútbol
argentino**, generado con el pipeline de ingesta a partir de links de YouTube
(videos de ~20 min). Los transcripts quedan versionados en `data/transcripts/`.

## 5. Resultados esperados

- Comparación BERTopic vs LDA por coherencia `c_v`.
- Tópicos interpretables (presión, rival, individualidades, mentalidad, árbitro, etc.).
- **Perfil de comunicación** por DT: distribución de tópicos + sentimiento + evolución.
- Visualizaciones (BERTopic, nubes de palabras, evolución temporal).

## 6. Entregables

1. **Informe** (PDF) — metodología, experimentos y resultados.
2. **Repositorio** (este) — notebook reproducible + app.
3. **Video** (10 min) — demo de la app web.

## 7. Estructura del repositorio

```
PROYECTO/
├── backend/        API FastAPI + pipeline NLP (transcripción, topic modeling, perfil)
├── frontend/       App web Next.js (estética Apple) para la demo
├── notebook/       Notebook académico reproducible (núcleo del informe)
└── data/           audio (no versionado) · transcripts · modelos (no versionado)
```

## 8. Cómo correr

**Todo junto (recomendado):**
```bash
./run.sh
```
Levanta el backend en http://localhost:8000 y el frontend en http://localhost:3000.
La primera vez crea el entorno e instala dependencias automáticamente.

**Manual:**
```bash
# Backend
cd backend
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download es_core_news_md
uvicorn app.main:app --reload          # http://localhost:8000

# Frontend (otra terminal)
cd frontend
npm install && npm run dev             # http://localhost:3000
```

**Notebook académico** (requiere el venv del backend + jupyter):
```bash
cd notebook
../backend/venv/bin/pip install jupyter
../backend/venv/bin/jupyter notebook analisis_topic_modeling.ipynb
```

### Uso
1. En la barra lateral, escribí el nombre de un entrenador y Enter → entra a su ficha.
2. Pegá el link de YouTube de una conferencia → "Agregar conferencia". Se descarga,
   se transcribe con Whisper (con barra de progreso/ETA) y se analiza.
3. La ficha muestra el % de confianza, el radar comunicacional, el sentimiento, los
   tópicos y las conclusiones. Podés sumar más conferencias y subir una foto del DT.

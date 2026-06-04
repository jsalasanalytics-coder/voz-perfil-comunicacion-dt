# Perfil de Comunicación de Entrenadores de Fútbol mediante Topic Modeling

**Trabajo Práctico Integrador — Procesamiento de Lenguaje Natural**
Ingeniería en Inteligencia Artificial · Universidad de Palermo

*(Borrador del informe. Completar autores, fechas y refinar con el grupo.)*

---

## Resumen

Presentamos un sistema que analiza conferencias de prensa de entrenadores de fútbol
y construye, de forma automática y reproducible, un **perfil de comunicación** de cada
DT. La tarea central de NLP es **topic modeling**: descubrir los temas latentes del
discurso y su distribución. Sobre ese núcleo se construye el perfil (distribución de
tópicos, evolución y un descriptor de sentimiento). El pipeline transcribe los videos
con Whisper, preprocesa con spaCy y modela los tópicos con BERTopic, usando LDA como
baseline y la coherencia *c_v* como métrica.

## 1. Introducción (problema y motivación)

En el fútbol profesional, lo que dice un entrenador en conferencia de prensa es materia
prima para el análisis deportivo y comunicacional, pero hoy se procesa de forma manual
y subjetiva. Nos propusimos responder, con NLP, una pregunta concreta y de valor para
un club: **¿de qué habla un DT y cómo es su perfil comunicacional?**

Reformulamos esa pregunta como un problema de **topic modeling**:

> El perfil de comunicación de un entrenador = la distribución de **tópicos** latentes
> en su discurso, su **evolución** a lo largo de las conferencias y un **descriptor de
> sentimiento** por tópico.

El topic modeling es el núcleo metodológico evaluable; el "perfil" es la capa de
aplicación que se construye encima y que da utilidad práctica al trabajo.

## 2. Trabajos relacionados / estado de la cuestión

- **Topic modeling clásico**: LDA (Blei et al., 2003) modela cada documento como mezcla
  de tópicos y cada tópico como distribución de palabras.
- **Topic modeling neuronal**: BERTopic (Grootendorst, 2022) combina embeddings de
  oraciones (Sentence-BERT), reducción de dimensionalidad (UMAP), clustering
  (HDBSCAN o K-means) y una representación por **c-TF-IDF**. Suele producir tópicos más
  coherentes en texto corto y conversacional.
- **Evaluación de tópicos**: la coherencia **c_v** (Röder et al., 2015) correlaciona bien
  con el juicio humano sobre la interpretabilidad de los tópicos.
- **Análisis de sentimiento en español**: `pysentimiento` / RoBERTuito (Pérez et al.),
  entrenado en español rioplatense.

Todas estas técnicas se trabajaron en la cursada (APUNTE 7 — Clustering y Topic Modeling).

## 3. Metodología

El sistema es un pipeline de cuatro etapas:

1. **Ingesta y transcripción (ASR).** A partir de links de YouTube, `yt-dlp` descarga el
   audio y `faster-whisper` lo transcribe en español. *Es un paso de obtención de datos,
   no el aporte de NLP.*
2. **Preprocesamiento.** Con `spaCy` (`es_core_news_md`) segmentamos el texto en oraciones
   (la unidad de documento) y extraemos tokens de contenido lematizados (sustantivos,
   verbos, adjetivos y propios), descartando stopwords y muletillas de oralidad.
3. **Topic Modeling (núcleo).**
   - *Modelo principal:* **BERTopic**. Embeddings con
     `paraphrase-multilingual-MiniLM-L12-v2`, UMAP, clustering y c-TF-IDF. El clustering
     es **HDBSCAN** (descubre el nº de tópicos) o **K-means** (nº fijo), más estable en
     corpus chicos de texto corto.
   - *Baseline:* **LDA** (`gensim`), barriendo el número de tópicos *k*.
   - *Métrica:* **coherencia c_v** (`gensim`), usada para comparar modelos y elegir *k*.
4. **Perfil de comunicación (aplicación).** Cada oración se asigna a un tópico; se calcula
   la distribución de tópicos por DT, el sentimiento por tópico (`pysentimiento`) y la
   evolución conferencia a conferencia.

**Entorno:** Python 3.12. Backend `FastAPI`; frontend `Next.js` (interfaz tipo Apple) que
consume la API y muestra el perfil. El backend procesa los videos como *jobs* en segundo
plano por la duración de la transcripción.

## 4. Experimentos y resultados

**Dataset.** Corpus propio de conferencias de DTs del fútbol argentino, transcriptas con
el pipeline (≈ N conferencias / M oraciones — completar con los valores finales).

**Comparación de modelos.** Reportamos la coherencia *c_v* de BERTopic frente al mejor
LDA (k elegido por coherencia). *(Insertar tabla/figura del notebook.)*

**Tópicos detectados.** El modelo separa temas interpretables del discurso futbolero
(p. ej. *juego/jugadas*, *partido/equipo*, *rival*, *hinchada/club*). *(Insertar tabla
de tópicos con sus palabras clave.)*

**Perfil por DT.** La distribución de tópicos difiere claramente entre entrenadores
—p. ej. un DT muy centrado en el análisis de jugadas vs. otro en la coyuntura del
partido— lo que valida el enfoque como "huella comunicacional". *(Insertar gráfico de
barras apiladas por DT y el cuadro de sentimiento.)*

> Las figuras y tablas se generan en `notebook/analisis_topic_modeling.ipynb`.

## 5. Discusión, análisis de errores y limitaciones

- **Ruido de ASR.** Whisper transcribe mal algunos nombres propios (p. ej. "River" →
  "Ríbe"), lo que introduce términos espurios en los tópicos. Mitigable con normalización
  de entidades.
- **Tamaño del corpus.** Con pocas conferencias, HDBSCAN tiende a sub-segmentar; fijar el
  número de tópicos con K-means da resultados más interpretables. A mayor corpus, tópicos
  más estables y mejor coherencia.
- **Coherencia moderada.** Es esperable en texto oral corto; sirve sobre todo como medida
  *comparativa* entre configuraciones, no como valor absoluto.
- **Sentimiento agregado.** Es un descriptor del perfil, no un análisis fino frase a frase.

## 6. Conclusiones

El topic modeling permite construir un perfil objetivo, automático y reproducible de cómo
comunica cada entrenador a partir de conferencias transcriptas. BERTopic resultó más
interpretable que LDA en este tipo de texto, y la coherencia *c_v* fue una guía útil para
elegir la configuración. La interfaz web hace el análisis accesible para un público no
técnico (cuerpo técnico, prensa, dirigencia), cumpliendo el objetivo de aplicación real.

**Trabajo futuro:** ampliar el corpus, normalizar nombres propios, validar la
interpretación de los tópicos con etiquetado manual y agregar comparación entre DTs.

## Referencias

- Blei, Ng, Jordan (2003). *Latent Dirichlet Allocation*. JMLR.
- Grootendorst (2022). *BERTopic: Neural topic modeling with class-based TF-IDF*.
- Röder, Both, Hinneburg (2015). *Exploring the Space of Topic Coherence Measures*. WSDM.
- Pérez et al. *pysentimiento: A Python toolkit for Sentiment Analysis and Social NLP*.

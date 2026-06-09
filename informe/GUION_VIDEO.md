# Guion del video — Voz · Perfil de comunicación de entrenadores

**Duración objetivo:** 10 minutos · **Audiencia:** dirigencia / comité evaluador (sin
conocimientos previos de NLP) · **Todos los integrantes participan.**

Estructura: **primeros ~6 min** = presentación con slides (problema → enfoque →
herramientas → resultados); **últimos ~4 min** = demo en vivo de la app ("la prueba").
Hablar claro y sintético, con énfasis en *para qué sirve* cada cosa.

> Convención: **[Integrante 1/2/3]** = repartir entre los miembros del grupo.
> **(SLIDE …)** = qué mostrar en pantalla. **(DEMO …)** = qué hacer en la app.

---

## Bloque 1 — Apertura y problema · ~1:15 · [Integrante 1]

**(SLIDE 1 — Portada: "Voz" + nombres + materia)**

> "Hola, somos [nombres]. Presentamos **Voz**, un proyecto de Procesamiento de
> Lenguaje Natural de la Ingeniería en IA de la Universidad de Palermo.
>
> Arrancamos con una pregunta simple: en un club de fútbol, **¿de qué habla
> realmente un director técnico cuando da una conferencia de prensa, y cómo lo
> comunica?** Hoy eso lo hace una persona a mano: escucha, toma notas y opina.
> No es medible, no es comparable y no escala a varios entrenadores o varios
> rivales a la vez.
>
> Nuestro objetivo fue convertir esas conferencias en un **perfil de comunicación
> objetivo y comparable** de cada técnico — algo útil para la dirigencia, el
> cuerpo técnico y la prensa."

**(SLIDE 2 — "El problema": foto de conferencia + 3 viñetas: subjetivo · no
comparable · no escala)**

---

## Bloque 2 — Enfoque: qué hicimos y por qué · ~1:30 · [Integrante 2]

**(SLIDE 3 — La idea en una frase)**

> "La tarea central de NLP que elegimos es **topic modeling**: una técnica que,
> sin que nadie le diga las categorías de antemano, **descubre sola los temas de
> los que habla un texto**. Si la aplicamos a lo que dice un entrenador, obtenemos
> los temas de su discurso y en qué proporción habla de cada uno.
>
> Definimos el **perfil de comunicación** como tres cosas: **de qué temas habla**
> (los tópicos), **con qué tono** (un descriptor de sentimiento) y **cómo cambia**
> conferencia a conferencia. El topic modeling es el corazón del trabajo; el
> perfil es la aplicación práctica que construimos encima."

**(SLIDE 4 — Diagrama del pipeline en 4 pasos, con íconos)**

> "Para llegar ahí seguimos cuatro pasos, que vemos en pantalla."

---

## Bloque 3 — Herramientas, explicadas simple · ~2:00 · [Integrante 3]

**(SLIDE 5 — Pipeline de 4 etapas; ir resaltando cada una)**

> "Paso 1, **conseguir los datos.** Partimos de un link de YouTube de una
> conferencia. Un programa baja el audio y otro, **Whisper**, lo pasa a texto
> automáticamente. Esto es solo *preparar el material*, todavía no es el análisis.
>
> Paso 2, **limpiar el texto.** Separamos lo que pregunta el periodista de lo que
> responde el técnico —porque solo nos interesa el DT— y nos quedamos con las
> palabras que aportan significado.
>
> Paso 3, **el análisis principal: encontrar los temas.** Usamos **BERTopic**, que
> agrupa frases parecidas y descubre los temas del discurso. Lo comparamos contra
> un método clásico, **LDA**, y medimos cuál arma temas más claros con una métrica
> estándar llamada **coherencia**. Es decir: la decisión de qué modelo usar no fue
> a ojo, la respaldamos con un número.
>
> Paso 4, **construir el perfil.** Con los temas y el tono armamos un **radar de
> seis dimensiones** —confianza, positividad, autocrítica, foco táctico, foco en
> el rival y cohesión de grupo— y conclusiones escritas en lenguaje claro."

**(SLIDE 6 — Logos/íconos: YouTube · Whisper · spaCy · BERTopic · LDA, en una fila)**

---

## Bloque 4 — Resultados · ~1:30 · [Integrante 1]

**(SLIDE 7 — Tabla: BERTopic vs LDA por coherencia + corpus: 6 DTs)**

> "Trabajamos con un **corpus propio** de conferencias de seis técnicos del fútbol
> argentino, que transcribimos nosotros. Dos resultados para destacar:
>
> Primero, el método **encuentra temas que tienen sentido** sin ayuda humana:
> aparecen el rival, el plantel, el juego, los resultados.
>
> Segundo, y lo más importante para el negocio: **los perfiles distinguen
> claramente a un entrenador de otro.** Un técnico que viene de ganar muestra un
> perfil positivo y centrado en el grupo; uno bajo presión muestra cautela e
> incertidumbre. El mismo método los separa solo, sin que nadie lo ajuste a mano —
> eso es lo que llamamos una **huella comunicacional**."

**(SLIDE 8 — Dos radares lado a lado: un DT positivo vs uno cauto)**

---

## Bloque 5 — Demo en vivo · "la prueba" · ~3:00 · [Integrante 2 + 3]

**(DEMO — pantalla compartida con la app en `localhost:3000`)**

> "Ahora lo mostramos funcionando."

1. **(DEMO)** "Esta es la app. En el panel lateral tenemos a los entrenadores
   cargados." → abrir la ficha de un DT con conferencia ya analizada.
2. **(DEMO)** Señalar **el % de confianza** y **el radar de 6 dimensiones**:
   "esto resume en un vistazo cómo comunica."
3. **(DEMO)** Mostrar **los tópicos** con sus palabras y proporciones, y el
   **sentimiento**: "de esto habla, en esta proporción, con este tono."
4. **(DEMO)** Leer **las conclusiones automáticas** en lenguaje claro.
5. **(DEMO — opcional, si el tiempo lo permite)** Pegar un **link de YouTube** de
   una conferencia y mostrar cómo se descarga y transcribe con la barra de
   progreso. *(Si la transcripción es larga, mostrar una ya procesada en su lugar.)*
6. **(DEMO)** Entrar a la sección **Comparar** / **Metodología** para cerrar.

> "En segundos pasamos de un video de veinte minutos a un perfil que la dirigencia
> puede leer y comparar."

---

## Bloque 6 — Cierre y conclusiones · ~0:45 · [Integrante 3]

**(SLIDE 9 — Conclusiones + trabajo futuro)**

> "Para cerrar: con NLP convertimos conferencias en un **perfil de comunicación
> objetivo, automático y comparable** de cada técnico. Es **reproducible** —está
> todo en un notebook y en el repositorio— y **accesible** para alguien sin
> conocimientos técnicos, gracias a la app.
>
> Como trabajo futuro: ampliar el corpus, corregir nombres propios mal
> transcriptos y sumar un comparador directo entre entrenadores.
>
> Gracias."

**(SLIDE 10 — "Gracias" + link al repositorio)**

---

### Checklist de grabación
- [ ] App corriendo (`./run.sh`) y al menos un DT ya analizado **antes** de grabar.
- [ ] Slides exportadas (se puede usar `PRESENTACION_DIRIGENCIA.html`).
- [ ] Probar el audio y la pantalla compartida.
- [ ] Cronometrar: si la demo se estira, recortar el paso del link de YouTube.
- [ ] Que se vea/escuche a los tres integrantes.

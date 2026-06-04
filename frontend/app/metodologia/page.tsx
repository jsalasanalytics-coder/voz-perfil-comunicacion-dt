"use client";

import { useEffect, useRef, useState } from "react";
import { explainPipeline, PipelineExplain } from "@/lib/api";
import { SENT_COLORS, SENT_LABEL } from "@/lib/theme";

const EXAMPLE =
  "¿Cómo viviste la eliminación? Estoy muy orgulloso del esfuerzo del equipo, " +
  "pero nos faltó intensidad en la presión y tenemos que mejorar en defensa.";

const STEPS = [
  { key: "ingesta", title: "Ingesta", tool: "yt-dlp",
    what: "Del link de YouTube se descarga solo el audio." },
  { key: "asr", title: "Transcripción (ASR)", tool: "Whisper",
    what: "El audio se convierte en texto en español." },
  { key: "qa", title: "Pregunta vs respuesta", tool: "Heurística lingüística",
    what: "Se separa lo que pregunta el periodista de lo que responde el DT." },
  { key: "prep", title: "Preprocesamiento", tool: "spaCy",
    what: "Cada oración se reduce a sus lemas de contenido (sin muletillas)." },
  { key: "topic", title: "Topic Modeling", tool: "BERTopic + LDA · c_v", core: true,
    what: "El vocabulario se agrupa en temas latentes. Es el núcleo del proyecto." },
  { key: "sent", title: "Sentimiento", tool: "pysentimiento",
    what: "Cada frase del DT se clasifica en positivo, neutro o negativo." },
  { key: "perfil", title: "Perfil y radar", tool: "Léxicos + agregación",
    what: "Todo se combina en métricas, % de confianza y conclusiones." },
];

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function Spinner() {
  return <span className="inline-block w-4 h-4 rounded-full border-2 border-line border-t-accent animate-spin" />;
}

function Mono({ children }: { children: React.ReactNode }) {
  return <div className="text-[13px] leading-relaxed bg-black/[0.03] rounded-xl p-3 text-ink/90">{children}</div>;
}

function SpeakerTag({ s }: { s: "PREGUNTA" | "DT" }) {
  const dt = s === "DT";
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded-full whitespace-nowrap ${
      dt ? "bg-accent/10 text-accent" : "bg-black/[0.06] text-subtle"
    }`}>{dt ? "DT" : "Periodista"}</span>
  );
}

function StepOutput({ k, res }: { k: string; res: PipelineExplain }) {
  const dt = res.stages.filter((s) => s.speaker === "DT");
  switch (k) {
    case "ingesta":
      return <Mono>🎧 Audio obtenido del video. (En el demo partimos del texto.)</Mono>;
    case "asr":
      return <Mono>“{res.raw}”</Mono>;
    case "qa":
      return (
        <div className="space-y-1.5">
          {res.stages.map((s, i) => (
            <div key={i} className="flex items-center gap-2">
              <SpeakerTag s={s.speaker} />
              <span className="text-[13px]">{s.sentence}</span>
            </div>
          ))}
          <p className="text-[11px] text-subtle pt-1">→ Se descartan las preguntas; sigue solo el DT.</p>
        </div>
      );
    case "prep":
      return (
        <div className="space-y-2">
          {dt.map((s, i) => (
            <div key={i} className="flex flex-wrap items-center gap-1.5">
              {s.lemmas.length ? s.lemmas.map((l) => (
                <span key={l} className="text-xs px-2 py-0.5 rounded-full bg-black/[0.05] text-subtle">{l}</span>
              )) : <span className="text-xs text-subtle">—</span>}
            </div>
          ))}
        </div>
      );
    case "topic":
      return (
        <div>
          <div className="flex flex-wrap gap-1.5">
            {res.bag_of_words.map((w) => (
              <span key={w} className="text-xs px-2 py-0.5 rounded-full bg-accent/10 text-accent">{w}</span>
            ))}
          </div>
          <p className="text-[11px] text-subtle mt-2">
            Con todo el corpus del DT, BERTopic agrupa este vocabulario en temas (ej. presión, rival, grupo).
          </p>
        </div>
      );
    case "sent":
      return (
        <div className="space-y-1.5">
          {dt.map((s, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="text-[10px] px-2 py-0.5 rounded-full text-white" style={{ background: SENT_COLORS[s.sentiment] }}>
                {SENT_LABEL[s.sentiment]}
              </span>
              <span className="text-[13px] truncate">{s.sentence}</span>
            </div>
          ))}
        </div>
      );
    case "perfil":
      if (!res.metrics) return <Mono>Sin frases del DT para perfilar.</Mono>;
      return (
        <div className="flex items-center gap-5">
          <div className="text-center shrink-0">
            <div className="text-3xl font-semibold tabular-nums">{res.metrics.confianza}%</div>
            <div className="text-[10px] text-subtle">confianza</div>
          </div>
          <div className="flex-1 grid grid-cols-2 gap-x-4 gap-y-1 text-[12px]">
            {res.metrics.radar.filter((r) => r.axis !== "Confianza").map((r) => (
              <div key={r.axis} className="flex justify-between border-b border-line py-0.5">
                <span className="text-subtle">{r.axis}</span>
                <span className="font-medium tabular-nums">{r.value}</span>
              </div>
            ))}
          </div>
        </div>
      );
    default:
      return null;
  }
}

export default function Metodologia() {
  const [text, setText] = useState(EXAMPLE);
  const [res, setRes] = useState<PipelineExplain | null>(null);
  const [step, setStep] = useState(-1);
  const [running, setRunning] = useState(false);
  const auto = useRef(false);

  useEffect(() => {
    if (typeof window !== "undefined" && new URLSearchParams(window.location.search).has("demo") && !auto.current) {
      auto.current = true;
      run();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const run = async () => {
    setRunning(true);
    setRes(null);
    setStep(-1);
    const data = await explainPipeline(text);   // procesa una vez
    setRes(data);
    for (let i = 0; i < STEPS.length; i++) {     // se "ejecuta" etapa por etapa
      setStep(i);
      await sleep(850);
    }
    setRunning(false);
  };

  return (
    <div className="max-w-3xl mx-auto px-8 py-12">
      <header className="mb-7">
        <h1 className="text-[32px] font-semibold tracking-tight leading-none">Cómo funciona</h1>
        <p className="text-subtle mt-2">
          Mirá el pipeline ejecutarse paso a paso. La tarea central de NLP es <b>topic modeling</b>;
          el resto son etapas de apoyo.
        </p>
      </header>

      <div className="rounded-3xl border border-line bg-white p-5 mb-8">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          disabled={running}
          className="w-full px-4 py-3 rounded-2xl border border-line bg-white outline-none focus:border-accent transition text-sm resize-none disabled:opacity-60"
        />
        <div className="flex justify-end mt-3">
          <button
            onClick={run}
            disabled={running || !text.trim()}
            className="px-6 py-2.5 rounded-2xl bg-ink text-white font-medium hover:bg-black transition active:scale-95 disabled:opacity-40"
          >
            {running ? "Ejecutando…" : "▶ Ejecutar el pipeline"}
          </button>
        </div>
      </div>

      {/* Timeline de ejecución */}
      <ol className="relative border-l border-line ml-4 space-y-3">
        {STEPS.map((s, i) => {
          const revealed = step >= i;
          const active = running && step === i;
          const done = step > i || (!running && step >= i);
          return (
            <li key={s.key} className="ml-6">
              {/* nodo */}
              <span className={`absolute -left-[9px] mt-4 w-4 h-4 rounded-full grid place-items-center transition ${
                done ? "bg-accent text-white" : active ? "bg-white border-2 border-accent" : "bg-white border-2 border-line"
              }`}>
                {done && <span className="text-[9px]">✓</span>}
              </span>

              <div className={`rounded-2xl border bg-white p-4 transition ${
                active ? "border-accent/50 ring-1 ring-accent/20"
                : revealed ? (s.core ? "border-accent/40" : "border-line")
                : "border-line opacity-50"
              }`}>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[11px] text-subtle tabular-nums">{i + 1}</span>
                  <span className="font-medium text-sm">{s.title}</span>
                  {s.core && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-accent/10 text-accent uppercase tracking-wide">núcleo</span>}
                  <span className="text-[11px] text-subtle">· {s.tool}</span>
                  {active && <span className="ml-auto"><Spinner /></span>}
                </div>
                <p className="text-[12px] text-subtle mt-1">{s.what}</p>
                {revealed && res && <div className="mt-3">{<StepOutput k={s.key} res={res} />}</div>}
              </div>
            </li>
          );
        })}
      </ol>

      {!res && (
        <p className="text-center text-sm text-subtle mt-6">
          Escribí una frase (o usá el ejemplo) y tocá <b>Ejecutar</b> para ver el desglose en vivo.
        </p>
      )}
    </div>
  );
}

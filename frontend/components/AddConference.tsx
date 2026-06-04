"use client";

import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { addConference, getJob, Job } from "@/lib/api";

const STAGE_LABEL: Record<string, string> = {
  info: "Leyendo el video…",
  downloading: "Descargando audio…",
  transcribing: "Transcribiendo con Whisper…",
  analyzing: "Analizando el discurso…",
  done: "Listo",
};

function fmtEta(s: number | null) {
  if (s == null || s <= 0) return "";
  const m = Math.floor(s / 60);
  const sec = Math.round(s % 60);
  return m > 0 ? `~${m} min ${sec}s restantes` : `~${sec}s restantes`;
}

export default function AddConference({
  coachId,
  onDone,
}: {
  coachId: string;
  onDone: () => void;
}) {
  const [url, setUrl] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const [err, setErr] = useState("");
  const poll = useRef<ReturnType<typeof setInterval> | null>(null);

  const start = async () => {
    if (!url.trim()) return;
    setErr("");
    setJob({ status: "pending", stage: "info", fraction: 0, eta: null, title: null, error: null });
    try {
      const { job_id } = await addConference(coachId, url.trim());
      poll.current = setInterval(async () => {
        try {
          const jb = await getJob(job_id);
          setJob(jb);
          if (jb.status === "done") {
            clearInterval(poll.current!);
            setJob(null);
            setUrl("");
            onDone();
          } else if (jb.status === "error") {
            clearInterval(poll.current!);
            setErr(jb.error || "Error en el análisis");
            setJob(null);
          }
        } catch {}
      }, 1200);
    } catch (e: any) {
      setErr(e.message + " — ¿está corriendo el backend?");
      setJob(null);
    }
  };

  const running = job !== null;
  const pct = Math.round((job?.fraction ?? 0) * 100);

  return (
    <div className="glass rounded-xl3 shadow-card p-5">
      {!running ? (
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && start()}
            placeholder="Pegá el link de YouTube de una conferencia…"
            className="flex-1 px-4 py-3 rounded-2xl border border-line bg-white/70 outline-none focus:border-accent transition"
          />
          <button
            onClick={start}
            disabled={!url.trim()}
            className="px-6 py-3 rounded-2xl bg-accent text-white font-semibold hover:brightness-110 transition active:scale-95 disabled:opacity-40"
          >
            Agregar conferencia
          </button>
        </div>
      ) : (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">{STAGE_LABEL[job!.stage] ?? job!.stage}</span>
            <span className="text-xs text-subtle">{fmtEta(job!.eta)}</span>
          </div>
          <div className="h-2.5 rounded-full bg-line overflow-hidden">
            <motion.div
              className="h-full bg-accent"
              animate={{ width: `${["transcribing", "analyzing", "done"].includes(job!.stage) ? pct : 8}%` }}
              transition={{ ease: "easeOut" }}
            />
          </div>
          {job!.title && <p className="text-xs text-subtle mt-2 truncate">{job!.title}</p>}
        </div>
      )}
      {err && <p className="text-sm text-[#ff3b30] mt-3">{err}</p>}
    </div>
  );
}

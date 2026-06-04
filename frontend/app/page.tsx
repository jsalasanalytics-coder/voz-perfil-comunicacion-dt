"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CoachCard, createCoach, listCoaches, photoUrl } from "@/lib/api";
import { coachesChanged } from "@/components/Shell";

function Avatar({ c }: { c: CoachCard }) {
  const url = photoUrl(c.photo_url);
  return url ? (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={url} alt="" className="w-12 h-12 rounded-2xl object-cover" />
  ) : (
    <span className="w-12 h-12 rounded-2xl bg-black/[0.05] text-subtle grid place-items-center text-lg font-medium">
      {c.name.slice(0, 1).toUpperCase()}
    </span>
  );
}

export default function Home() {
  const [coaches, setCoaches] = useState<CoachCard[] | null>(null);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  const load = () => listCoaches().then(setCoaches).catch(() => setCoaches([]));
  useEffect(() => {
    load();
    const h = () => load();
    window.addEventListener("coaches-changed", h);
    return () => window.removeEventListener("coaches-changed", h);
  }, []);

  const create = async () => {
    if (!name.trim() || busy) return;
    setBusy(true);
    try {
      const { id } = await createCoach(name.trim(), "");
      coachesChanged();
      router.push(`/coach/${id}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-10 py-16">
      <header className="mb-8">
        <h1 className="text-[34px] font-semibold tracking-tight leading-none">Entrenadores</h1>
        <p className="text-subtle mt-2">Cómo comunica cada DT, a partir de sus conferencias.</p>
      </header>

      {/* Alta de entrenador (siempre visible y obvia) */}
      <div className="flex gap-2 mb-8">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && create()}
          placeholder="Nombre del entrenador…"
          className="flex-1 px-4 py-3 rounded-2xl border border-line bg-white outline-none focus:border-accent transition"
        />
        <button
          onClick={create}
          disabled={!name.trim() || busy}
          className="px-6 py-3 rounded-2xl bg-ink text-white font-medium hover:bg-black transition active:scale-95 disabled:opacity-40 whitespace-nowrap"
        >
          {busy ? "Creando…" : "Nuevo entrenador"}
        </button>
      </div>

      {coaches === null ? (
        <p className="text-subtle">Cargando…</p>
      ) : coaches.length === 0 ? (
        <p className="text-subtle">
          Creá tu primer entrenador con el campo de arriba. Después le cargás las conferencias.
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {coaches.map((c) => (
            <Link
              key={c.id}
              href={`/coach/${c.id}`}
              className="block rounded-3xl border border-line bg-white p-5 transition hover:border-black/20 hover:shadow-card"
            >
              <div className="flex items-center gap-4">
                <Avatar c={c} />
                <div className="min-w-0 flex-1">
                  <p className="font-medium truncate">{c.name}</p>
                  <p className="text-[13px] text-subtle truncate">
                    {c.team || `${c.n_conferences} conferencia${c.n_conferences !== 1 ? "s" : ""}`}
                  </p>
                </div>
                {c.confianza != null && (
                  <div className="text-right">
                    <div className="text-xl font-semibold tabular-nums leading-none">{c.confianza}%</div>
                    <div className="text-[11px] text-subtle mt-1">confianza</div>
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

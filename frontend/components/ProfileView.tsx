"use client";

import { useRef } from "react";
import { useRouter } from "next/navigation";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
} from "recharts";
import {
  Profile, deleteCoach, deleteConference, photoUrl, uploadPhoto,
} from "@/lib/api";
import { coachesChanged } from "./Shell";
import RadarProfile from "./Radar";
import AddConference from "./AddConference";
import { topicColor, SENT_COLORS, SENT_LABEL } from "@/lib/theme";

function ConfidenceRing({ value }: { value: number }) {
  const color = value >= 65 ? "#34c759" : value >= 45 ? "#ff9500" : "#ff3b30";
  const r = 44, c = 2 * Math.PI * r;
  return (
    <div className="relative grid place-items-center shrink-0" style={{ width: 108, height: 108 }}>
      <svg width={108} height={108} className="-rotate-90">
        <circle cx={54} cy={54} r={r} stroke="#e5e5ea" strokeWidth={9} fill="none" />
        <circle cx={54} cy={54} r={r} stroke={color} strokeWidth={9} fill="none"
          strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - value / 100)}
          style={{ transition: "stroke-dashoffset 1s ease" }} />
      </svg>
      <div className="absolute text-center">
        <div className="text-2xl font-semibold tabular-nums leading-none">{value}%</div>
        <div className="text-[10px] text-subtle mt-0.5">confianza</div>
      </div>
    </div>
  );
}

function SentimentBar({ s }: { s: Record<string, number> }) {
  return (
    <div>
      <div className="flex h-2 rounded-full overflow-hidden bg-line">
        {["POS", "NEU", "NEG"].map((k) =>
          s[k] ? <div key={k} style={{ width: `${s[k] * 100}%`, background: SENT_COLORS[k] }} /> : null
        )}
      </div>
      <div className="flex gap-3 mt-1.5">
        {["POS", "NEU", "NEG"].map((k) =>
          s[k] ? (
            <span key={k} className="text-[11px] text-subtle flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: SENT_COLORS[k] }} />
              {SENT_LABEL[k]} {Math.round(s[k]! * 100)}%
            </span>
          ) : null
        )}
      </div>
    </div>
  );
}

const card = "rounded-3xl border border-line bg-white";

export default function ProfileView({ profile, reload }: { profile: Profile; reload: () => void }) {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const coach = profile.coach;
  const m = profile.metrics;

  const onPhoto = async (f: File | null) => {
    if (!f) return;
    await uploadPhoto(coach.id, f);
    coachesChanged();
    reload();
  };
  const removeCoach = async () => {
    if (!confirm(`¿Eliminar a ${coach.name}?`)) return;
    await deleteCoach(coach.id);
    coachesChanged();
    router.push("/");
  };
  const removeConf = async (confId: string) => {
    if (!confirm("¿Eliminar esta conferencia?")) return;
    await deleteConference(coach.id, confId);
    coachesChanged();
    reload();
  };

  const avatar = photoUrl(coach.photo_ext ? `/api/coaches/${coach.id}/photo` : null);

  return (
    <div className="max-w-4xl mx-auto px-8 py-10 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => fileRef.current?.click()} className="relative group shrink-0" title="Cambiar foto">
          {avatar ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={avatar} alt="" className="w-16 h-16 rounded-2xl object-cover" />
          ) : (
            <span className="w-16 h-16 rounded-2xl bg-black/[0.05] text-subtle grid place-items-center text-xl font-medium">
              {coach.name.slice(0, 1).toUpperCase()}
            </span>
          )}
          <span className="absolute inset-0 rounded-2xl bg-black/40 text-white text-[10px] grid place-items-center opacity-0 group-hover:opacity-100 transition">
            Cambiar
          </span>
        </button>
        <input ref={fileRef} type="file" accept="image/*" hidden onChange={(e) => onPhoto(e.target.files?.[0] ?? null)} />
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-semibold tracking-tight leading-tight">{coach.name}</h1>
          <p className="text-sm text-subtle">{coach.team || "—"}</p>
        </div>
        <button onClick={removeCoach} className="text-[13px] text-subtle hover:text-[#ff3b30] transition">Eliminar</button>
      </div>

      {!profile.ready ? (
        <>
          <div className={`${card} p-5`}>
            <p className="font-medium">Cargá la primera conferencia</p>
            <p className="text-subtle text-sm mt-1">{profile.reason}</p>
          </div>
          <AddConference coachId={coach.id} onDone={reload} />
        </>
      ) : (
        <>
          {/* Franja superior: confianza + stats + sentimiento + headline */}
          <div className={`${card} p-5`}>
            <div className="flex flex-col sm:flex-row items-center gap-5">
              <ConfidenceRing value={m!.confianza} />
              <div className="flex-1 w-full">
                <p className="text-[15px] font-medium">{m!.headline}</p>
                <div className="flex gap-6 mt-3 mb-4 text-sm">
                  <div><span className="font-semibold">{profile.n_conferences}</span> <span className="text-subtle">conf.</span></div>
                  <div><span className="font-semibold">{profile.n_sentences}</span> <span className="text-subtle">frases DT</span></div>
                  <div><span className="font-semibold">{profile.questions?.total}</span> <span className="text-subtle">preguntas</span></div>
                </div>
                <SentimentBar s={m!.sentiment} />
              </div>
            </div>
          </div>

          {/* Radar + Conclusiones */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`${card} p-5`}>
              <p className="font-semibold text-sm mb-1">Perfil comunicacional</p>
              <RadarProfile data={m!.radar} />
            </div>
            <div className={`${card} p-5`}>
              <p className="font-semibold text-sm mb-2">Conclusiones</p>
              <ul className="divide-y divide-line">
                {m!.conclusions.map((c, i) => (
                  <li key={i} className="text-sm leading-relaxed text-ink/90 py-2 first:pt-0"
                      dangerouslySetInnerHTML={{ __html: c.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>") }} />
                ))}
              </ul>
            </div>
          </div>

          {/* Tópicos (compacto) */}
          <div className={`${card} p-5`}>
            <div className="flex items-baseline justify-between mb-3">
              <p className="font-semibold text-sm">¿De qué habla?</p>
              <p className="text-[11px] text-subtle">topic modeling · BERTopic</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
              {profile.topics!.map((t, i) => (
                <div key={t.id} className="border-b border-line pb-3 last:border-0">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="w-2 h-2 rounded-full shrink-0" style={{ background: topicColor(i) }} />
                      <span className="text-sm font-medium truncate">{t.label}</span>
                    </div>
                    <span className="text-xs text-subtle tabular-nums">{(t.share * 100).toFixed(0)}%</span>
                  </div>
                  <p className="text-[12px] text-subtle mt-1 truncate">{t.words.slice(0, 6).join(", ")}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Evolución */}
          {profile.evolution && profile.evolution.length > 1 && (
            <div className={`${card} p-5`}>
              <p className="font-semibold text-sm mb-3">Evolución del discurso</p>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={profile.evolution.map((e, idx) => {
                  const row: any = { name: `C${idx + 1}` };
                  for (const [id, v] of Object.entries(e.topic_distribution))
                    row[profile.topic_labels?.[id] ?? id] = Math.round(v * 1000) / 10;
                  return row;
                })}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#6e6e73" }} />
                  <YAxis tick={{ fontSize: 11, fill: "#6e6e73" }} unit="%" />
                  <Tooltip />
                  {profile.topics!.map((t, i) => (
                    <Bar key={t.id} dataKey={t.label} stackId="a" fill={topicColor(i)} isAnimationActive={false} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Conferencias + alta */}
          <div className={`${card} p-5`}>
            <p className="font-semibold text-sm mb-3">Conferencias ({profile.conferences?.length})</p>
            <div className="space-y-2 mb-4">
              {profile.conferences!.map((c) => (
                <div key={c.id} className="group flex items-center gap-3 border border-line rounded-2xl px-4 py-2.5">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{c.title}</p>
                    <p className="text-[11px] text-subtle">{c.n_preguntas ?? 0} preguntas · {c.n_respuestas ?? 0} del DT</p>
                  </div>
                  <button onClick={() => removeConf(c.id)}
                          className="text-[11px] text-subtle hover:text-[#ff3b30] transition opacity-0 group-hover:opacity-100">
                    Quitar
                  </button>
                </div>
              ))}
            </div>
            <AddConference coachId={coach.id} onDone={reload} />
          </div>

          {profile.coherence && (
            <p className="text-center text-[11px] text-subtle">
              Validado con coherencia c_v = {profile.coherence.bertopic_cv} (BERTopic).
            </p>
          )}
        </>
      )}
    </div>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend,
} from "recharts";
import { CoachCard, Profile, getProfile, listCoaches } from "@/lib/api";

const A_COLOR = "#0071e3";
const B_COLOR = "#ff9500";

function Picker({
  coaches, value, onChange, exclude,
}: {
  coaches: CoachCard[];
  value: string;
  onChange: (id: string) => void;
  exclude?: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="px-4 py-2.5 rounded-2xl border border-line bg-white outline-none focus:border-accent transition text-sm"
    >
      {coaches.filter((c) => c.id !== exclude).map((c) => (
        <option key={c.id} value={c.id}>{c.name}</option>
      ))}
    </select>
  );
}

export default function Compare() {
  const [coaches, setCoaches] = useState<CoachCard[]>([]);
  const [aId, setAId] = useState("");
  const [bId, setBId] = useState("");
  const [a, setA] = useState<Profile | null>(null);
  const [b, setB] = useState<Profile | null>(null);

  useEffect(() => {
    listCoaches().then((cs) => {
      const ready = cs.filter((c) => c.n_conferences > 0);
      setCoaches(ready);
      if (ready[0]) setAId(ready[0].id);
      if (ready[1]) setBId(ready[1].id);
    });
  }, []);

  useEffect(() => { if (aId) getProfile(aId).then(setA); }, [aId]);
  useEffect(() => { if (bId) getProfile(bId).then(setB); }, [bId]);

  const radarData = useMemo(() => {
    if (!a?.metrics || !b?.metrics) return [];
    return a.metrics.radar.map((ax, i) => ({
      axis: ax.axis,
      A: ax.value,
      B: b.metrics!.radar[i]?.value ?? 0,
    }));
  }, [a, b]);

  if (coaches.length < 2)
    return (
      <div className="max-w-4xl mx-auto px-10 py-16">
        <h1 className="text-[34px] font-semibold tracking-tight">Comparar</h1>
        <p className="text-subtle mt-3">Necesitás al menos dos entrenadores con conferencias cargadas.</p>
      </div>
    );

  return (
    <div className="max-w-4xl mx-auto px-10 py-16">
      <header className="mb-8">
        <h1 className="text-[34px] font-semibold tracking-tight leading-none">Comparar</h1>
        <p className="text-subtle mt-2">Dos perfiles comunicacionales, lado a lado.</p>
      </header>

      <div className="flex items-center gap-3 mb-8">
        <span className="w-3 h-3 rounded-full" style={{ background: A_COLOR }} />
        <Picker coaches={coaches} value={aId} onChange={setAId} exclude={bId} />
        <span className="text-subtle text-sm">vs</span>
        <span className="w-3 h-3 rounded-full" style={{ background: B_COLOR }} />
        <Picker coaches={coaches} value={bId} onChange={setBId} exclude={aId} />
      </div>

      {a?.metrics && b?.metrics && (
        <>
          <div className="rounded-3xl border border-line bg-white p-6 mb-6">
            <ResponsiveContainer width="100%" height={360}>
              <RadarChart data={radarData} outerRadius="70%">
                <PolarGrid stroke="#e5e5ea" />
                <PolarAngleAxis dataKey="axis" tick={{ fontSize: 12, fill: "#1d1d1f" }} />
                <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                <Radar name={a.coach.name} dataKey="A" stroke={A_COLOR} fill={A_COLOR} fillOpacity={0.2} strokeWidth={2} isAnimationActive={false} />
                <Radar name={b.coach.name} dataKey="B" stroke={B_COLOR} fill={B_COLOR} fillOpacity={0.2} strokeWidth={2} isAnimationActive={false} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <div className="rounded-3xl border border-line bg-white overflow-hidden">
            <div className="grid grid-cols-[1fr_auto_auto] gap-x-6 px-6 py-3 text-xs text-subtle border-b border-line">
              <span>Dimensión</span>
              <span className="text-right w-16" style={{ color: A_COLOR }}>{a.coach.name.split(" ")[0]}</span>
              <span className="text-right w-16" style={{ color: B_COLOR }}>{b.coach.name.split(" ")[0]}</span>
            </div>
            {[{ axis: "Confianza", A: a.metrics.confianza, B: b.metrics.confianza },
              ...a.metrics.radar.filter((x) => x.axis !== "Confianza").map((ax, i) => ({
                axis: ax.axis, A: ax.value,
                B: b.metrics!.radar.find((y) => y.axis === ax.axis)?.value ?? 0,
              }))].map((row) => (
              <div key={row.axis} className="grid grid-cols-[1fr_auto_auto] gap-x-6 px-6 py-3 text-sm border-b border-line last:border-0">
                <span>{row.axis}</span>
                <span className="text-right w-16 tabular-nums font-medium">{row.A}</span>
                <span className="text-right w-16 tabular-nums font-medium">{row.B}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { CoachCard, createCoach, listCoaches, photoUrl } from "@/lib/api";
import { coachesChanged } from "./Shell";

function Avatar({ c, size = 26 }: { c: CoachCard; size?: number }) {
  const url = photoUrl(c.photo_url);
  return url ? (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={url} alt="" className="rounded-full object-cover"
         style={{ width: size, height: size }} />
  ) : (
    <span className="rounded-full bg-black/[0.06] text-subtle grid place-items-center font-medium"
          style={{ width: size, height: size, fontSize: size * 0.42 }}>
      {c.name.slice(0, 1).toUpperCase()}
    </span>
  );
}

export default function Sidebar() {
  const [coaches, setCoaches] = useState<CoachCard[]>([]);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const path = usePathname();
  const router = useRouter();

  const load = () => listCoaches().then(setCoaches).catch(() => {});
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
      setName("");
      coachesChanged();
      router.push(`/coach/${id}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 border-r border-line bg-[#fbfbfd] flex flex-col">
      <Link href="/" className="px-6 pt-7 pb-5 text-[22px] font-semibold tracking-tight">
        Voz
      </Link>

      <div className="px-2 space-y-0.5">
        {[
          { href: "/", label: "Entrenadores" },
          { href: "/comparar", label: "Comparar" },
          { href: "/metodologia", label: "Cómo funciona" },
        ].map((it) => (
          <Link
            key={it.href}
            href={it.href}
            className={`block px-3 py-2 rounded-xl text-[13px] font-medium transition ${
              path === it.href ? "bg-black/[0.06] text-ink" : "text-subtle hover:bg-black/[0.03]"
            }`}
          >
            {it.label}
          </Link>
        ))}
      </div>

      <div className="px-5 mt-5 mb-1 text-[11px] uppercase tracking-wide text-subtle/70">
        Plantel
      </div>
      <nav className="px-2 flex-1 overflow-y-auto space-y-0.5">
        {coaches.map((c) => {
          const active = path === `/coach/${c.id}`;
          return (
            <Link
              key={c.id}
              href={`/coach/${c.id}`}
              className={`flex items-center gap-3 px-3 py-2 rounded-xl transition ${
                active ? "bg-black/[0.05]" : "hover:bg-black/[0.03]"
              }`}
            >
              <Avatar c={c} />
              <span className="text-[13px] truncate">{c.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-line">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && create()}
          placeholder="Nuevo entrenador"
          className="w-full px-3 py-2 rounded-xl bg-black/[0.04] text-[13px] outline-none focus:bg-white focus:ring-1 focus:ring-line transition placeholder:text-subtle"
        />
      </div>
    </aside>
  );
}

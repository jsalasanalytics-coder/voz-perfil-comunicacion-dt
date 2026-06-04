"use client";

import Sidebar from "./Sidebar";

export default function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 min-w-0 overflow-x-hidden">{children}</main>
    </div>
  );
}

// Bus de eventos mínimo para refrescar listas tras crear/borrar.
export const coachesChanged = () =>
  typeof window !== "undefined" && window.dispatchEvent(new Event("coaches-changed"));

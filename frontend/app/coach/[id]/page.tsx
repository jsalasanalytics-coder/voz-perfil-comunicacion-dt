"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getProfile, Profile } from "@/lib/api";
import ProfileView from "@/components/ProfileView";

export default function CoachPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [profile, setProfile] = useState<Profile | null>(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setErr("");
    try {
      const p = await getProfile(id);
      setProfile(p);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    setLoading(true);
    setProfile(null);
    load();
  }, [id, load]);

  if (loading)
    return <div className="max-w-5xl mx-auto px-8 py-12 text-subtle">Analizando el perfil…</div>;
  if (err)
    return <div className="max-w-5xl mx-auto px-8 py-12 text-[#ff3b30]">Error: {err}</div>;
  if (!profile) return null;

  return <ProfileView profile={profile} reload={load} />;
}

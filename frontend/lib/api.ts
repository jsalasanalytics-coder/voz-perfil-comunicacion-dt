export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export const photoUrl = (path: string | null) => (path ? `${API_BASE}${path}` : null);

export type CoachCard = {
  id: string;
  name: string;
  team: string;
  n_conferences: number;
  photo_url: string | null;
  confianza: number | null;
  headline: string | null;
};

export type Sentiment = { POS?: number; NEU?: number; NEG?: number };
export type RadarAxis = { axis: string; value: number };

export type Topic = {
  id: number;
  label: string;
  words: string[];
  size: number;
  share: number;
  sentiment: Sentiment;
};

export type Metrics = {
  radar: RadarAxis[];
  confianza: number;
  sentiment: Sentiment;
  conclusions: string[];
  headline: string;
};

export type EvolutionPoint = {
  conf_id: string;
  title: string;
  date: string | null;
  topic_distribution: Record<string, number>;
  sentiment: Sentiment;
};

export type ConferenceRow = {
  id: string;
  title: string;
  url: string;
  date: string | null;
  duration: number | null;
  n_preguntas?: number;
  n_respuestas?: number;
  n_segmentos?: number;
};

export type Profile = {
  ready: boolean;
  reason?: string;
  coach: { id: string; name: string; team: string; photo_ext: string | null };
  n_conferences?: number;
  n_sentences?: number;
  n_topics?: number;
  topics?: Topic[];
  topic_labels?: Record<string, string>;
  metrics?: Metrics;
  evolution?: EvolutionPoint[];
  questions?: { total: number };
  conferences?: ConferenceRow[];
  coherence?: { bertopic_cv: number };
};

export type Job = {
  status: "pending" | "running" | "done" | "error";
  stage: string;
  fraction: number;
  eta: number | null;
  title: string | null;
  error: string | null;
};

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = res.statusText;
    try {
      msg = (await res.json()).detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export const listCoaches = () =>
  fetch(`${API_BASE}/api/coaches`).then((r) => j<CoachCard[]>(r));

export const createCoach = (name: string, team: string) =>
  fetch(`${API_BASE}/api/coaches`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, team }),
  }).then((r) => j<{ id: string }>(r));

export const deleteCoach = (id: string) =>
  fetch(`${API_BASE}/api/coaches/${id}`, { method: "DELETE" }).then((r) => j(r));

export const uploadPhoto = (id: string, file: File) => {
  const fd = new FormData();
  fd.append("file", file);
  return fetch(`${API_BASE}/api/coaches/${id}/photo`, { method: "POST", body: fd }).then(
    (r) => j<{ photo_url: string }>(r)
  );
};

export const getProfile = (id: string, nTopics?: number | null) =>
  fetch(
    `${API_BASE}/api/coaches/${id}/profile` +
      (nTopics ? `?n_topics=${nTopics}` : "")
  ).then((r) => j<Profile>(r));

export const addConference = (id: string, url: string) =>
  fetch(`${API_BASE}/api/coaches/${id}/conferences`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  }).then((r) => j<{ job_id: string }>(r));

export const deleteConference = (id: string, confId: string) =>
  fetch(`${API_BASE}/api/coaches/${id}/conferences/${confId}`, {
    method: "DELETE",
  }).then((r) => j(r));

export const getJob = (jobId: string) =>
  fetch(`${API_BASE}/api/jobs/${jobId}`).then((r) => j<Job>(r));

export type PipelineStage = {
  sentence: string;
  speaker: "PREGUNTA" | "DT";
  lemmas: string[];
  sentiment: "POS" | "NEU" | "NEG";
};

export type PipelineExplain = {
  raw: string;
  n_sentences: number;
  n_questions: number;
  stages: PipelineStage[];
  bag_of_words: string[];
  metrics: Metrics | null;
};

export const explainPipeline = (text: string) =>
  fetch(`${API_BASE}/api/pipeline/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  }).then((r) => j<PipelineExplain>(r));

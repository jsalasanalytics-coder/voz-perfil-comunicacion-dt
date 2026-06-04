// Paleta de colores para tópicos y sentimiento (estética Apple, tonos suaves).
export const TOPIC_COLORS = [
  "#0071e3", "#34c759", "#ff9500", "#ff375f", "#5e5ce6",
  "#00c7be", "#ffcc00", "#af52de", "#ff6482", "#64d2ff",
  "#30b0c7", "#bf5af2",
];

export const SENT_COLORS: Record<string, string> = {
  POS: "#34c759",
  NEU: "#8e8e93",
  NEG: "#ff3b30",
};

export const SENT_LABEL: Record<string, string> = {
  POS: "Positivo",
  NEU: "Neutro",
  NEG: "Negativo",
};

export const topicColor = (i: number) => TOPIC_COLORS[i % TOPIC_COLORS.length];

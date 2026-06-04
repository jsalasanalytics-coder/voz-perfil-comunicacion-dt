"use client";

import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
} from "recharts";
import { RadarAxis } from "@/lib/api";

export default function RadarProfile({ data }: { data: RadarAxis[] }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data} outerRadius="72%">
        <PolarGrid stroke="#e5e5ea" />
        <PolarAngleAxis dataKey="axis" tick={{ fontSize: 12, fill: "#1d1d1f" }} />
        <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
        <Radar
          dataKey="value"
          stroke="#0071e3"
          fill="#0071e3"
          fillOpacity={0.25}
          strokeWidth={2}
          isAnimationActive={false}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}

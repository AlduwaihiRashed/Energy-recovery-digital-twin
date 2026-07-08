"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { HistoryReading } from "@/lib/types";

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function PowerFlowChart({ readings }: { readings: HistoryReading[] }) {
  const data = readings.map((r) => ({ ts: r.ts, power_kw: r.power_kw }));

  return (
    <div className="rounded-lg border border-surface-border bg-surface p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-foreground/60">Power output (kW)</h3>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="powerFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#14b8a6" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#14b8a6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#223350" vertical={false} />
          <XAxis
            dataKey="ts"
            tickFormatter={formatTime}
            stroke="#223350"
            tick={{ fill: "#8896ab", fontSize: 10 }}
            minTickGap={40}
          />
          <YAxis stroke="#223350" tick={{ fill: "#8896ab", fontSize: 10 }} width={48} />
          <Tooltip
            contentStyle={{ background: "#111f36", border: "1px solid #223350", borderRadius: 8, fontSize: 12 }}
            labelFormatter={(v) => formatTime(v as string)}
            formatter={(value) => [`${Number(value).toFixed(0)} kW`, "Power"]}
          />
          <Area type="monotone" dataKey="power_kw" stroke="#14b8a6" strokeWidth={2} fill="url(#powerFill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

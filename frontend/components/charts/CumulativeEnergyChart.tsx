"use client";

import { useMemo } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ROW_INTERVAL_HOURS } from "@/lib/constants";
import type { HistoryReading } from "@/lib/types";

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function CumulativeEnergyChart({ readings }: { readings: HistoryReading[] }) {
  const data = useMemo(() => {
    let cumulativeKwh = 0;
    return readings.map((r) => {
      cumulativeKwh += r.power_kw * ROW_INTERVAL_HOURS;
      return { ts: r.ts, cumulative_kwh: cumulativeKwh };
    });
  }, [readings]);

  return (
    <div className="rounded-lg border border-surface-border bg-surface p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-foreground/60">
        Cumulative energy recovered (kWh)
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="cumulativeFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
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
          <YAxis stroke="#223350" tick={{ fill: "#8896ab", fontSize: 10 }} width={56} />
          <Tooltip
            contentStyle={{ background: "#111f36", border: "1px solid #223350", borderRadius: 8, fontSize: 12 }}
            labelFormatter={(v) => formatTime(v as string)}
            formatter={(value) => [`${Number(value).toFixed(1)} kWh`, "Cumulative energy"]}
          />
          <Area type="monotone" dataKey="cumulative_kwh" stroke="#10b981" strokeWidth={2} fill="url(#cumulativeFill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

"use client";

import { useMemo, useState } from "react";
import { AlarmList } from "@/components/alarms/AlarmList";
import { CumulativeEnergyChart } from "@/components/charts/CumulativeEnergyChart";
import { PowerFlowChart } from "@/components/charts/PowerFlowChart";
import { TimeRangeControl } from "@/components/charts/TimeRangeControl";
import { CopilotPanel } from "@/components/chat/CopilotPanel";
import { KpiTile } from "@/components/kpi/KpiTile";
import { PidDiagram } from "@/components/pid/PidDiagram";
import { ROW_INTERVAL_HOURS } from "@/lib/constants";
import { useAlarms } from "@/hooks/useAlarms";
import { useHistoryQuery, useKpis } from "@/hooks/useHistoryQuery";
import { useStationSocket } from "@/hooks/useStationSocket";

const STATION_ID = "station-1";
const STATION_NAME = "Downtown Letdown Station";

export default function Home() {
  const { snapshot, status } = useStationSocket(STATION_ID);
  const [rangeHours, setRangeHours] = useState(24);
  const historyLimit = Math.max(10, Math.ceil(rangeHours / ROW_INTERVAL_HOURS));
  const readings = useHistoryQuery(STATION_ID, historyLimit, 5000);
  const kpis = useKpis(STATION_ID, 5000);
  const alarms = useAlarms(STATION_ID, 4000);

  const alarmTags = useMemo(
    () => new Set(alarms.filter((a) => a.active && a.tag).map((a) => a.tag)),
    [alarms]
  );

  const statusColor =
    status === "open" ? "text-accent-green" : status === "connecting" ? "text-accent-amber" : "text-accent-red";

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 p-6 md:p-8">
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Energy Recovery Digital Twin</h1>
          <p className="text-sm text-foreground/60">{STATION_NAME}</p>
        </div>
        <p className="text-xs text-foreground/50">
          live feed: <span className={statusColor}>{status}</span>
        </p>
      </header>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KpiTile label="Power output" value={snapshot ? `${snapshot.power_kw.toFixed(0)} kW` : "--"} accent="teal" />
        <KpiTile
          label="Efficiency"
          value={snapshot ? `${snapshot.efficiency_pct.toFixed(1)}%` : "--"}
          accent="purple"
        />
        <KpiTile
          label="CO2 avoided"
          value={kpis ? `${(kpis.cumulative_co2_avoided_kg / 1000).toFixed(2)} t` : "--"}
          sublabel="cumulative"
          accent="green"
        />
        <KpiTile
          label="Revenue"
          value={kpis ? `$${kpis.cumulative_revenue_usd.toFixed(0)}` : "--"}
          sublabel="cumulative"
          accent="amber"
        />
      </section>

      <PidDiagram snapshot={snapshot} alarmTags={alarmTags} />

      <div className="flex justify-end">
        <TimeRangeControl rangeHours={rangeHours} onChange={setRangeHours} />
      </div>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <PowerFlowChart readings={readings} />
        <CumulativeEnergyChart readings={readings} />
      </section>

      <AlarmList alarms={alarms} />

      <CopilotPanel />
    </div>
  );
}

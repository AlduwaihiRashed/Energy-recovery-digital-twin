"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchHistory, fetchKpis } from "@/lib/api";
import type { HistoryReading, KpiRollup } from "@/lib/types";

export function useHistoryQuery(stationId: string, limit = 200, intervalMs = 5000) {
  const [readings, setReadings] = useState<HistoryReading[]>([]);

  const refresh = useCallback(async () => {
    try {
      const res = await fetchHistory(stationId, limit);
      setReadings(res.readings);
    } catch {
      // keep last known readings on a transient fetch failure
    }
  }, [stationId, limit]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => clearInterval(id);
  }, [refresh, intervalMs]);

  return readings;
}

export function useKpis(stationId: string, intervalMs = 5000) {
  const [kpis, setKpis] = useState<KpiRollup | null>(null);

  const refresh = useCallback(async () => {
    try {
      setKpis(await fetchKpis(stationId));
    } catch {
      // keep last known kpis on a transient fetch failure
    }
  }, [stationId]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => clearInterval(id);
  }, [refresh, intervalMs]);

  return kpis;
}

"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchAlarms } from "@/lib/api";
import type { Alarm } from "@/lib/types";

export function useAlarms(stationId: string, intervalMs = 4000) {
  const [alarms, setAlarms] = useState<Alarm[]>([]);

  const refresh = useCallback(async () => {
    try {
      const res = await fetchAlarms(stationId, false);
      setAlarms(res.alarms);
    } catch {
      // keep last known alarms on a transient fetch failure
    }
  }, [stationId]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => clearInterval(id);
  }, [refresh, intervalMs]);

  return alarms;
}

"use client";

import { useEffect, useRef, useState } from "react";
import { stationWsUrl } from "@/lib/api";
import type { StationSnapshot } from "@/lib/types";

export type ConnectionStatus = "connecting" | "open" | "closed";

export function useStationSocket(stationId: string) {
  const [snapshot, setSnapshot] = useState<StationSnapshot | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedByCleanup = useRef(false);

  useEffect(() => {
    closedByCleanup.current = false;

    function connect() {
      const ws = new WebSocket(stationWsUrl(stationId));
      socketRef.current = ws;
      setStatus("connecting");

      ws.onopen = () => {
        reconnectAttempt.current = 0;
        setStatus("open");
      };

      ws.onmessage = (event) => {
        try {
          setSnapshot(JSON.parse(event.data) as StationSnapshot);
        } catch {
          // ignore malformed frame
        }
      };

      ws.onclose = () => {
        setStatus("closed");
        if (closedByCleanup.current) return;
        const delayMs = Math.min(1000 * 2 ** reconnectAttempt.current, 10_000);
        reconnectAttempt.current += 1;
        reconnectTimer.current = setTimeout(connect, delayMs);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      closedByCleanup.current = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      socketRef.current?.close();
    };
  }, [stationId]);

  return { snapshot, status };
}

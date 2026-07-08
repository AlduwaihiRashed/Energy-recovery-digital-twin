import type { Alarm, CopilotChatResponse, HistoryReading, KpiRollup } from "@/lib/types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8001";
export const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE ?? "ws://localhost:8001";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`POST ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function stationWsUrl(stationId: string): string {
  return `${WS_BASE}/ws/stations/${stationId}`;
}

export function fetchHistory(stationId: string, limit = 200) {
  return getJson<{ station_id: string; readings: HistoryReading[] }>(
    `/api/stations/${stationId}/history?limit=${limit}`
  );
}

export function fetchAlarms(stationId: string, activeOnly = false) {
  return getJson<{ station_id: string; alarms: Alarm[] }>(
    `/api/stations/${stationId}/alarms?active_only=${activeOnly}`
  );
}

export function fetchKpis(stationId: string) {
  return getJson<KpiRollup>(`/api/stations/${stationId}/kpis`);
}

export function sendCopilotChat(message: string, history: { role: string; content: string }[]) {
  return postJson<CopilotChatResponse>("/api/copilot/chat", { message, history });
}

export interface StationSnapshot {
  station_id: string;
  sim_timestamp: string;
  mode: "turboexpander" | "bypass";
  pi_001_inlet_psi: number;
  fi_001_flow_sm3h: number;
  ti_002_preheat_temp_c: number;
  pt_003_outlet_psi: number;
  power_kw: number;
  efficiency_pct: number;
  active_fault_names: string[];
}

export interface HistoryReading {
  id: number;
  station_id: string;
  ts: string;
  pi_001_inlet_psi: number;
  fi_001_flow_sm3h: number;
  ti_002_preheat_temp_c: number;
  pt_003_outlet_psi: number;
  power_kw: number;
  efficiency_pct: number;
  mode: "turboexpander" | "bypass";
}

export interface Alarm {
  id: number;
  station_id: string;
  ts: string;
  severity: "info" | "warning" | "critical";
  tag: string;
  message: string;
  active: number;
  cleared_ts: string | null;
}

export interface KpiRollup {
  station_id: string;
  reading_count: number;
  avg_power_kw: number;
  avg_efficiency_pct: number;
  cumulative_energy_kwh: number;
  cumulative_co2_avoided_kg: number;
  cumulative_revenue_usd: number;
}

export interface ToolTraceEntry {
  name: string;
  args: Record<string, unknown>;
  result: unknown;
}

export interface CopilotChatMessage {
  role: "user" | "assistant";
  content: string;
  toolTrace?: ToolTraceEntry[];
}

export interface CopilotChatResponse {
  reply: string;
  tool_trace: ToolTraceEntry[];
}

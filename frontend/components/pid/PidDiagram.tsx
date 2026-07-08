import { InstrumentBadge } from "@/components/pid/InstrumentBadge";
import type { StationSnapshot } from "@/lib/types";

interface PidDiagramProps {
  snapshot: StationSnapshot | null;
  alarmTags?: Set<string>;
}

function Pipe({ active, color = "teal" }: { active: boolean; color?: "teal" | "amber" | "green" }) {
  const colorClass = active
    ? color === "amber"
      ? "bg-accent-amber"
      : color === "green"
        ? "bg-accent-green"
        : "bg-accent-teal"
    : "bg-surface-border";
  return <div className={`h-0.5 w-6 shrink-0 md:w-10 ${colorClass}`} />;
}

function EquipmentBox({
  label,
  sublabel,
  active,
  children,
}: {
  label: string;
  sublabel?: string;
  active: boolean;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-2">
      {children}
      <div
        className={`flex min-w-[76px] flex-col items-center justify-center gap-0.5 rounded-md border-2 px-3 py-2 text-center ${
          active ? "border-accent-teal bg-accent-teal/5" : "border-surface-border"
        }`}
      >
        <span className="text-[10px] font-semibold uppercase tracking-wide text-foreground/70">{label}</span>
        {sublabel && <span className="text-xs font-mono text-foreground">{sublabel}</span>}
      </div>
    </div>
  );
}

export function PidDiagram({ snapshot, alarmTags = new Set() }: PidDiagramProps) {
  const isTurbo = snapshot?.mode === "turboexpander";
  const isBypass = snapshot?.mode === "bypass";

  const pi001 = snapshot ? snapshot.pi_001_inlet_psi.toFixed(0) : "--";
  const fi001 = snapshot ? snapshot.fi_001_flow_sm3h.toFixed(0) : "--";
  const ti002 = snapshot ? snapshot.ti_002_preheat_temp_c.toFixed(1) : "--";
  const pt003 = snapshot ? snapshot.pt_003_outlet_psi.toFixed(0) : "--";
  const powerKw = snapshot ? snapshot.power_kw.toFixed(0) : "--";

  return (
    <div className="rounded-xl border border-surface-border bg-surface/40 p-4 md:p-6">
      <div className="mb-4 flex items-center justify-between text-[10px] uppercase tracking-wide text-foreground/40">
        <span>High pressure gas inlet</span>
        <span className={`rounded-full px-2 py-0.5 font-semibold ${isBypass ? "bg-accent-red/10 text-accent-red" : "bg-accent-teal/10 text-accent-teal"}`}>
          {snapshot ? snapshot.mode : "warming up..."}
        </span>
        <span>Low pressure outlet</span>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-1 overflow-x-auto md:flex-nowrap md:justify-between">
        <div className="flex flex-col items-center gap-2">
          <InstrumentBadge tag="PI-001" value={pi001} unit="psi" alarm={alarmTags.has("PI-001")} />
          <InstrumentBadge tag="FI-001" value={fi001} unit="Sm3/h" alarm={alarmTags.has("FI-001")} />
        </div>

        <Pipe active={Boolean(snapshot)} />

        <EquipmentBox label="HX" sublabel="Preheater" active={Boolean(snapshot)}>
          <InstrumentBadge tag="TI-002" value={ti002} unit="C" alarm={alarmTags.has("TI-002")} />
        </EquipmentBox>

        <Pipe active={isTurbo} color="amber" />

        <div
          className={`flex h-20 w-20 shrink-0 flex-col items-center justify-center rounded-full border-2 text-center ${
            isTurbo ? "border-accent-teal bg-accent-teal/10" : "border-surface-border"
          }`}
        >
          <span className="text-[9px] font-semibold leading-tight text-foreground/70">
            TURBO
            <br />
            EXPANDER
          </span>
        </div>

        <Pipe active={isTurbo} color="green" />

        <EquipmentBox label="Gen" sublabel={`${powerKw} kW`} active={isTurbo} />

        <Pipe active={Boolean(snapshot)} />

        <InstrumentBadge tag="PT-003" value={pt003} unit="psi" alarm={alarmTags.has("PT-003")} />
      </div>

      <div className="mt-6 flex items-center justify-center">
        <div
          className={`rounded-lg border-2 px-4 py-2 text-xs font-semibold ${
            isBypass ? "border-accent-red text-accent-red" : "border-surface-border text-foreground/30"
          }`}
        >
          Bypass PRV{isBypass ? " -- active" : ""}
        </div>
      </div>
    </div>
  );
}

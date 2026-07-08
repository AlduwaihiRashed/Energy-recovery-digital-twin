import type { Alarm } from "@/lib/types";

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

const SEVERITY_BORDER: Record<string, string> = {
  critical: "border-accent-red",
  warning: "border-accent-amber",
  info: "border-accent-teal",
};

const SEVERITY_TEXT: Record<string, string> = {
  critical: "text-accent-red",
  warning: "text-accent-amber",
  info: "text-accent-teal",
};

export function AlarmList({ alarms }: { alarms: Alarm[] }) {
  return (
    <div className="rounded-lg border border-surface-border bg-surface p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-foreground/60">Alarms</h3>
      {alarms.length === 0 ? (
        <p className="text-sm text-foreground/40">No alarms recorded yet.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {alarms.slice(0, 10).map((alarm) => (
            <li
              key={alarm.id}
              className={`flex items-start justify-between gap-3 rounded-md border-l-4 bg-background/40 px-3 py-2 text-sm ${
                alarm.active ? SEVERITY_BORDER[alarm.severity] ?? SEVERITY_BORDER.info : "border-surface-border"
              }`}
            >
              <div className="flex flex-col">
                <span className={alarm.active ? "font-medium text-foreground" : "font-medium text-foreground/40"}>
                  {alarm.tag && <span className="mr-1 font-mono text-xs">{alarm.tag}</span>}
                  {alarm.message}
                </span>
                <span className="text-xs text-foreground/40">
                  {formatTime(alarm.ts)}
                  {!alarm.active && alarm.cleared_ts ? ` -- cleared ${formatTime(alarm.cleared_ts)}` : ""}
                </span>
              </div>
              <span
                className={`shrink-0 text-[10px] font-semibold uppercase ${
                  alarm.active ? SEVERITY_TEXT[alarm.severity] ?? SEVERITY_TEXT.info : "text-foreground/30"
                }`}
              >
                {alarm.active ? alarm.severity : "resolved"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

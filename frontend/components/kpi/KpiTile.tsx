type Accent = "teal" | "purple" | "amber" | "green";

const ACCENT_TEXT: Record<Accent, string> = {
  teal: "text-accent-teal",
  purple: "text-accent-purple",
  amber: "text-accent-amber",
  green: "text-accent-green",
};

interface KpiTileProps {
  label: string;
  value: string;
  sublabel?: string;
  accent?: Accent;
}

export function KpiTile({ label, value, sublabel, accent = "teal" }: KpiTileProps) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-surface-border bg-surface p-4">
      <span className="text-xs font-medium uppercase tracking-normal text-foreground/60">{label}</span>
      <span className={`text-2xl font-semibold ${ACCENT_TEXT[accent]}`}>{value}</span>
      {sublabel && <span className="text-xs text-foreground/50">{sublabel}</span>}
    </div>
  );
}

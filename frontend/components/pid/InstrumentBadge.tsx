interface InstrumentBadgeProps {
  tag: string;
  value: string;
  unit: string;
  alarm?: boolean;
}

export function InstrumentBadge({ tag, value, unit, alarm = false }: InstrumentBadgeProps) {
  return (
    <div
      className={`flex flex-col items-center gap-0.5 rounded-full border-2 bg-surface px-3 py-1.5 shadow-lg ${
        alarm ? "border-accent-red" : "border-accent-teal"
      }`}
    >
      <span className={`text-[10px] font-semibold leading-none ${alarm ? "text-accent-red" : "text-accent-teal"}`}>
        {tag}
      </span>
      <span className="whitespace-nowrap font-mono text-xs leading-none text-foreground">
        {value}
        <span className="ml-0.5 text-foreground/50">{unit}</span>
      </span>
    </div>
  );
}

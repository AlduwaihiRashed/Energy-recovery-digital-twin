interface RangeOption {
  label: string;
  hours: number;
}

const RANGE_OPTIONS: RangeOption[] = [
  { label: "6h", hours: 6 },
  { label: "24h", hours: 24 },
  { label: "3d", hours: 72 },
];

export function TimeRangeControl({
  rangeHours,
  onChange,
}: {
  rangeHours: number;
  onChange: (hours: number) => void;
}) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-foreground/40">Range (sim time):</span>
      <div className="flex gap-1">
        {RANGE_OPTIONS.map((opt) => (
          <button
            key={opt.hours}
            type="button"
            onClick={() => onChange(opt.hours)}
            className={`rounded-md px-2 py-1 font-medium transition-colors ${
              rangeHours === opt.hours
                ? "bg-accent-teal/15 text-accent-teal"
                : "text-foreground/50 hover:text-foreground/80"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

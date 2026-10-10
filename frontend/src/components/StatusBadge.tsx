import { riskClass } from "../lib/format";

export function StatusBadge({ value }: { value: string }) {
  return (
    <span className={`inline-flex rounded border px-2 py-0.5 text-[11px] font-medium tracking-wide ${riskClass(value)}`}>
      {value}
    </span>
  );
}

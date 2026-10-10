import type { RiskCategory } from "../types/api";

export function riskClass(category: RiskCategory | string): string {
  switch (category) {
    case "CRITICAL":
      return "text-high bg-high/10 border-high/30";
    case "HIGH":
      return "text-rose-300 bg-rose-500/10 border-rose-500/30";
    case "MEDIUM":
      return "text-amber-300 bg-amber-500/10 border-amber-500/30";
    default:
      return "text-low bg-emerald-500/10 border-emerald-500/30";
  }
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

export function maskValue(type: string, value: string): string {
  if (type !== "account_like" || value.length < 8) return value;
  return `${value.slice(0, 2)}••••${value.slice(-4)}`;
}

export function relationshipLabel(type: string): string {
  return type.replaceAll("_", " ");
}

import { RiskLevel } from "../lib/api";

export function RiskBadge({ level }: { level: RiskLevel }) {
  return <span className={`risk risk-${level.toLowerCase()}`}>{level}</span>;
}


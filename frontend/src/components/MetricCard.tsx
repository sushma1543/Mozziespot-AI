import { LucideIcon } from "lucide-react";

type Props = {
  label: string;
  value: string | number;
  icon: LucideIcon;
  tone?: "neutral" | "warning" | "danger";
};

export function MetricCard({ label, value, icon: Icon, tone = "neutral" }: Props) {
  return (
    <section className={`metric metric-${tone}`}>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
      </div>
      <Icon size={22} aria-hidden />
    </section>
  );
}


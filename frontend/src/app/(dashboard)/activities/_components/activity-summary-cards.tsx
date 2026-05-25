import { cn } from "@/lib/utils";

export type ActivitySummaryStats = {
  bugs: number;
  incrementos: number;
  concluidas: number;
  pendentesVisao: number;
};

type MetricCardProps = {
  value: number;
  label: string;
  valueClassName: string;
};

function MetricCard({ value, label, valueClassName }: MetricCardProps) {
  return (
    <div className="flex min-w-[140px] flex-1 flex-col items-center justify-center rounded-xl border bg-card px-4 py-5 text-center shadow-sm">
      <div className={cn("text-[1.75rem] font-bold leading-none", valueClassName)}>
        {value}
      </div>
      <div className="mt-1 text-sm text-muted-foreground">{label}</div>
    </div>
  );
}

type ActivitySummaryCardsProps = {
  stats: ActivitySummaryStats;
};

export function ActivitySummaryCards({ stats }: ActivitySummaryCardsProps) {
  return (
    <div className="flex flex-wrap justify-center gap-4">
      <MetricCard value={stats.bugs} label="Bugs" valueClassName="text-red-600" />
      <MetricCard
        value={stats.incrementos}
        label="Incrementos"
        valueClassName="text-blue-600"
      />
      <MetricCard
        value={stats.concluidas}
        label="Concluídas"
        valueClassName="text-green-600"
      />
      <MetricCard
        value={stats.pendentesVisao}
        label="Pendentes (visão)"
        valueClassName="text-slate-500"
      />
    </div>
  );
}

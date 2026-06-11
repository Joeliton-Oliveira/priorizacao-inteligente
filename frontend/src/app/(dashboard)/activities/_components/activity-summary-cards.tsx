import type { LucideIcon } from "lucide-react";
import { Bug, CheckCircle2, Clock, Layers } from "lucide-react";
import { cn } from "@/lib/utils";
import { DashboardPanel } from "./dashboard-panel";

export type ActivitySummaryStats = {
  bugs: number;
  incrementos: number;
  concluidas: number;
  pendentesVisao: number;
};

type SummaryCardConfig = {
  value: number;
  title: string;
  description: string;
  icon: LucideIcon;
  iconWrapClass: string;
  iconClass: string;
  valueClass: string;
  borderGlow: string;
};

type ActivitySummaryCardsProps = {
  stats: ActivitySummaryStats;
};

function SummaryCard({
  value,
  title,
  description,
  icon: Icon,
  iconWrapClass,
  iconClass,
  valueClass,
  borderGlow,
}: SummaryCardConfig) {
  return (
    <DashboardPanel className={cn("border-l-2", borderGlow)}>
      <div className="flex items-center gap-4 px-5 py-5">
        <div
          className={cn(
            "flex size-12 shrink-0 items-center justify-center rounded-xl ring-1 ring-inset",
            iconWrapClass,
          )}
        >
          <Icon className={cn("size-6", iconClass)} />
        </div>
        <div className="min-w-0">
          <p className={cn("text-3xl font-bold leading-none tabular-nums", valueClass)}>{value}</p>
          <p className="mt-1.5 text-sm font-semibold text-foreground">{title}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
        </div>
      </div>
    </DashboardPanel>
  );
}

export function ActivitySummaryCards({ stats }: ActivitySummaryCardsProps) {
  const cards: SummaryCardConfig[] = [
    {
      value: stats.bugs,
      title: "Bugs",
      description: "Mapeados no período",
      icon: Bug,
      iconWrapClass: "bg-red-500/15 ring-red-500/25",
      iconClass: "text-red-400",
      valueClass: "text-red-400",
      borderGlow: "border-l-red-500/50",
    },
    {
      value: stats.incrementos,
      title: "Incrementos",
      description: "Avaliados no período",
      icon: Layers,
      iconWrapClass: "bg-blue-500/15 ring-blue-500/25",
      iconClass: "text-blue-400",
      valueClass: "text-blue-400",
      borderGlow: "border-l-blue-500/50",
    },
    {
      value: stats.concluidas,
      title: "Concluídas",
      description: "Finalizadas no período",
      icon: CheckCircle2,
      iconWrapClass: "bg-emerald-500/15 ring-emerald-500/25",
      iconClass: "text-emerald-400",
      valueClass: "text-emerald-400",
      borderGlow: "border-l-emerald-500/50",
    },
    {
      value: stats.pendentesVisao,
      title: "Pendentes",
      description: "No backlog atual",
      icon: Clock,
      iconWrapClass: "bg-violet-500/15 ring-violet-500/25",
      iconClass: "text-violet-400",
      valueClass: "text-violet-400",
      borderGlow: "border-l-violet-500/50",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <SummaryCard key={card.title} {...card} />
      ))}
    </div>
  );
}

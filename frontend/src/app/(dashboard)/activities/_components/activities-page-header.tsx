import { LineChart } from "lucide-react";

export function ActivitiesPageHeader() {
  return (
    <header className="flex items-start gap-4">
      <div className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-blue-600/20 ring-1 ring-blue-500/30">
        <LineChart className="size-6 text-blue-400" />
      </div>
      <div className="min-w-0 space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          Atividades priorizadas
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Visão analítica de bugs e incrementos classificados pela matriz de priorização.
        </p>
      </div>
    </header>
  );
}

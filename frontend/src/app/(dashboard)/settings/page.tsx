import { QueueSettingsForm } from "./_components/queue-settings-form";
import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="mx-auto w-full max-w-[1440px] space-y-5 pb-8">
      <div className="flex items-start gap-4">
        <div className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600/30 to-indigo-600/20 ring-1 ring-violet-500/30">
          <Settings className="size-6 text-violet-300" />
        </div>
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">Calibragem</h1>
          <p className="max-w-3xl text-sm text-muted-foreground">
            Ajuste a vazão bugs x incrementos e os limites WIP usados pela fila e pela
            esteira Kanban.
          </p>
        </div>
      </div>

      <QueueSettingsForm />
    </div>
  );
}

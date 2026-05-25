"use client";

import { useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { QueueSettingsForm } from "./_components/queue-settings-form";

type SettingsTab = "queue" | "kanban";

const TAB_LABELS: Record<SettingsTab, string> = {
  queue: "Fila",
  kanban: "Kanban",
};

function isSettingsTab(value: string | null): value is SettingsTab {
  return value === "queue" || value === "kanban";
}

export default function SettingsPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const activeTab: SettingsTab = useMemo(() => {
    const tab = searchParams.get("tab");
    return isSettingsTab(tab) ? tab : "queue";
  }, [searchParams]);

  const switchTab = (tab: SettingsTab) => {
    const next = new URLSearchParams(searchParams.toString());
    next.set("tab", tab);
    router.replace(`${pathname}?${next.toString()}`);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Configurações</h1>

      <div className="flex gap-2">
        {(Object.keys(TAB_LABELS) as SettingsTab[]).map((tab) => (
          <Button
            key={tab}
            type="button"
            variant={activeTab === tab ? "default" : "outline"}
            onClick={() => switchTab(tab)}
          >
            {TAB_LABELS[tab]}
          </Button>
        ))}
      </div>

      {activeTab === "queue" && <QueueSettingsForm />}

      {activeTab === "kanban" && (
        <div className="mx-auto max-w-lg rounded-xl border bg-card p-5 text-muted-foreground shadow-sm">
          Configurações específicas do Kanban serão disponibilizadas em breve. Os limites
          WIP por coluna estão na aba Fila.
        </div>
      )}
    </div>
  );
}

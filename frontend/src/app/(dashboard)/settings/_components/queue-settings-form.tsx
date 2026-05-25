"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { NumberStepper } from "./number-stepper";

export type QueueSettings = {
  percentualBugs: number;
  wip: {
    toDo: number;
    develop: number;
    test: number;
    deploy: number;
  };
};

const STORAGE_KEY = "intelli-reqs-queue-settings";

export const DEFAULT_QUEUE_SETTINGS: QueueSettings = {
  percentualBugs: 50,
  wip: {
    toDo: 5,
    develop: 2,
    test: 2,
    deploy: 1,
  },
};

const WIP_FIELDS: {
  key: keyof QueueSettings["wip"];
  label: string;
  hint: string;
}[] = [
  { key: "toDo", label: "WIP — TO DO", hint: "Sugestão: 5 a 8." },
  { key: "develop", label: "WIP — DEVELOP", hint: "Sugestão: 2–3." },
  { key: "test", label: "WIP — TEST", hint: "Sugestão: 2." },
  { key: "deploy", label: "WIP — DEPLOY", hint: "Sugestão: 1." },
];

export function loadQueueSettings(): QueueSettings {
  if (typeof window === "undefined") return DEFAULT_QUEUE_SETTINGS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_QUEUE_SETTINGS;
    const parsed = JSON.parse(raw) as QueueSettings;
    return {
      percentualBugs: parsed.percentualBugs ?? DEFAULT_QUEUE_SETTINGS.percentualBugs,
      wip: { ...DEFAULT_QUEUE_SETTINGS.wip, ...parsed.wip },
    };
  } catch {
    return DEFAULT_QUEUE_SETTINGS;
  }
}

export function saveQueueSettings(settings: QueueSettings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

export function QueueSettingsForm() {
  const [settings, setSettings] = useState<QueueSettings>(DEFAULT_QUEUE_SETTINGS);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    setSettings(loadQueueSettings());
  }, []);

  const percentualMelhorias = 100 - settings.percentualBugs;

  const updateWip = (key: keyof QueueSettings["wip"], value: number) => {
    setSettings((prev) => ({
      ...prev,
      wip: { ...prev.wip, [key]: value },
    }));
  };

  const handleSave = () => {
    saveQueueSettings(settings);
    setSavedMessage("Regras da fila guardadas com sucesso.");
    window.setTimeout(() => setSavedMessage(null), 4000);
  };

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-6">
      <section className="space-y-4 rounded-xl border bg-card p-5 shadow-sm">
        <div className="space-y-1">
          <h2 className="text-base font-semibold">
            Distribuição da fila entre bugs e melhorias
          </h2>
          <p className="text-sm text-muted-foreground">
            Defina o percentual para bugs; melhorias completam 100%.
          </p>
        </div>

        <div className="space-y-2">
          <Label className="text-sm font-semibold">Percentual da fila para bugs</Label>
          <NumberStepper
            value={settings.percentualBugs}
            min={0}
            max={100}
            onChange={(percentualBugs) =>
              setSettings((prev) => ({ ...prev, percentualBugs }))
            }
          />
        </div>

        <div className="space-y-2">
          <Label className="text-sm font-semibold text-muted-foreground">
            Percentual para melhorias
          </Label>
          <p className="text-sm text-muted-foreground">Calculado automaticamente.</p>
          <NumberStepper value={percentualMelhorias} readOnly min={0} max={100} />
        </div>
      </section>

      <section className="space-y-4 rounded-xl border bg-card p-5 shadow-sm">
        <h2 className="text-base font-semibold">Limites WIP por coluna</h2>

        {WIP_FIELDS.map(({ key, label, hint }) => (
          <div key={key} className="space-y-2">
            <Label className="text-sm font-semibold">{label}</Label>
            <p className="text-sm text-muted-foreground">{hint}</p>
            <NumberStepper
              value={settings.wip[key]}
              min={0}
              max={99}
              onChange={(value) => updateWip(key, value)}
            />
          </div>
        ))}
      </section>

      <div className="space-y-2">
        <Button type="button" onClick={handleSave}>
          Salvar regras da fila
        </Button>
        {savedMessage ? (
          <p className="text-sm text-green-600 dark:text-green-500">{savedMessage}</p>
        ) : null}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import {
  Bug,
  FlaskConical,
  ListChecks,
  Rocket,
  Save,
  SlidersHorizontal,
  Workflow,
} from "lucide-react";
import { DashboardPanel } from "@/app/(dashboard)/activities/_components/dashboard-panel";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { NumberStepper } from "./number-stepper";
import type { ConfigFila } from "@/lib/priorizacao/types";

export const DEFAULT_QUEUE_SETTINGS: ConfigFila = {
  vazao: {
    bugs: 60,
    incrementos: 40,
  },
  envelhecimento: {
    intervalo_dias: 10,
    incremento_base: 1,
    limite_maximo: null,
  },
  quadrantes_incremento: {},
  quadrantes_bug: {},
  fases: {},
  incremento_por_faixa_bug: {},
  incremento_por_faixa_incremento: {},
  wip: {
    TO_DO: 5,
    DEVELOP: 2,
    TEST: 2,
    DEPLOY: 1,
  },
};

const WIP_FIELDS: {
  key: keyof ConfigFila["wip"];
  label: string;
  hint: string;
}[] = [
  { key: "TO_DO", label: "WIP — TO DO", hint: "Sugestão: 5 a 8." },
  { key: "DEVELOP", label: "WIP — DEVELOP", hint: "Sugestão: 2–3." },
  { key: "TEST", label: "WIP — TEST", hint: "Sugestão: 2." },
  { key: "DEPLOY", label: "WIP — DEPLOY", hint: "Sugestão: 1." },
];

function clampPercentual(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(100, Math.max(0, Math.round(value)));
}

function mergeConfig(config: Partial<ConfigFila> | null | undefined): ConfigFila {
  const bugs = clampPercentual(config?.vazao?.bugs ?? DEFAULT_QUEUE_SETTINGS.vazao.bugs);
  return {
    ...DEFAULT_QUEUE_SETTINGS,
    ...config,
    vazao: {
      ...DEFAULT_QUEUE_SETTINGS.vazao,
      ...(config?.vazao ?? {}),
      bugs,
      incrementos: 100 - bugs,
    },
    envelhecimento: {
      ...DEFAULT_QUEUE_SETTINGS.envelhecimento,
      ...(config?.envelhecimento ?? {}),
    },
    wip: {
      ...DEFAULT_QUEUE_SETTINGS.wip,
      ...(config?.wip ?? {}),
    },
  };
}

export function QueueSettingsForm() {
  const [settings, setSettings] = useState<ConfigFila>(DEFAULT_QUEUE_SETTINGS);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadConfig() {
      try {
        setIsLoading(true);
        setErrorMessage(null);
        const response = await fetch("/api/priorizacao/config-fila", { cache: "no-store" });
        const data = await response.json().catch(() => null);
        if (!response.ok) {
          throw new Error(
            (data && typeof data === "object" && "detail" in data && typeof data.detail === "string"
              ? data.detail
              : "Não foi possível carregar a calibragem."),
          );
        }
        if (!cancelled) {
          setSettings(mergeConfig(data as Partial<ConfigFila>));
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            error instanceof Error ? error.message : "Não foi possível carregar a calibragem.",
          );
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadConfig();

    return () => {
      cancelled = true;
    };
  }, []);

  const percentualBugs = clampPercentual(settings.vazao.bugs);
  const percentualMelhorias = 100 - percentualBugs;

  const updateWip = (key: keyof ConfigFila["wip"], value: number) => {
    setSettings((prev) => ({
      ...prev,
      wip: { ...prev.wip, [key]: Math.max(0, value) },
    }));
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setSavedMessage(null);
      setErrorMessage(null);
      const bugs = clampPercentual(settings.vazao.bugs);
      const payload: ConfigFila = {
        ...settings,
        vazao: { bugs, incrementos: 100 - bugs },
      };
      const response = await fetch("/api/priorizacao/config-fila", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(
          (data && typeof data === "object" && "detail" in data && typeof data.detail === "string"
            ? data.detail
            : "Não foi possível salvar a calibragem."),
        );
      }
      setSavedMessage("Configuração salva (inclui WIP do Kanban).");
      window.setTimeout(() => setSavedMessage(null), 4000);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Não foi possível salvar a calibragem.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex w-full flex-col gap-5">
      {errorMessage ? (
        <p className="rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-red-400">
          {errorMessage}
        </p>
      ) : null}

      <DashboardPanel className="overflow-hidden border-rose-500/15 shadow-rose-950/10">
        <div className="border-b border-rose-500/10 bg-gradient-to-r from-rose-500/[0.06] to-transparent px-5 py-4">
          <div className="flex items-start gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-rose-500/15 text-rose-300 ring-1 ring-rose-500/25">
              <Bug className="size-5" />
            </div>
            <div>
              <h2 className="text-2xl font-bold tracking-tight">
                Distribuição da fila entre bugs e melhorias
              </h2>
              <p className="mt-0.5 text-sm text-muted-foreground">
                Defina o percentual para bugs; melhorias completam 100%.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 p-4 md:grid-cols-2 md:p-5">
          <div className="space-y-2 rounded-xl border border-white/10 bg-black/15 p-4">
            <Label className="text-sm font-semibold">Percentual da fila para bugs</Label>
            <p className="text-sm text-muted-foreground">Valor entre 0 e 100.</p>
            <div className="relative">
              <NumberStepper
                value={percentualBugs}
                min={0}
                max={100}
                disabled={isLoading || isSaving}
                className="h-11 w-full rounded-xl border-rose-500/30 bg-black/20 pr-12 text-base font-semibold text-foreground"
                onChange={(raw) => {
                  const bugs = clampPercentual(raw);
                  setSettings((prev) => ({
                    ...prev,
                    vazao: {
                      bugs,
                      incrementos: 100 - bugs,
                    },
                  }));
                }}
              />
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded-md border border-white/10 bg-white/[0.04] px-2 py-0.5 text-xs font-semibold text-muted-foreground">
                %
              </span>
            </div>
          </div>

          <div className="space-y-2 rounded-xl border border-white/10 bg-black/15 p-4">
            <Label className="text-sm font-semibold">Percentual para melhorias</Label>
            <p className="text-sm text-muted-foreground">
              Calculado automaticamente (completa 100%).
            </p>
            <div className="relative">
              <NumberStepper
                value={percentualMelhorias}
                readOnly
                min={0}
                max={100}
                className="h-11 w-full rounded-xl border-blue-500/20 bg-white/[0.02] pr-12 text-base font-semibold text-slate-200"
              />
              <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded-md border border-white/10 bg-white/[0.04] px-2 py-0.5 text-xs font-semibold text-muted-foreground">
                %
              </span>
            </div>
          </div>
        </div>
      </DashboardPanel>

      <DashboardPanel className="overflow-hidden border-blue-500/15 shadow-blue-950/10">
        <div className="border-b border-blue-500/10 bg-gradient-to-r from-blue-500/[0.06] to-transparent px-5 py-4">
          <div className="flex items-start gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-blue-500/15 text-blue-300 ring-1 ring-blue-500/25">
              <SlidersHorizontal className="size-5" />
            </div>
            <div>
              <h2 className="text-2xl font-bold tracking-tight">Limites WIP por coluna</h2>
              <p className="mt-0.5 text-sm text-muted-foreground">
                Configure os limites máximos sugeridos para cada coluna da esteira Kanban.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-0 lg:p-5">
          {WIP_FIELDS.map(({ key, label, hint }, index) => (
            <div
              key={key}
              className={cn(
                "space-y-2 rounded-xl border border-white/10 bg-black/15 p-4 lg:rounded-none lg:border-0 lg:bg-transparent",
                index > 0 && "lg:border-l lg:border-white/10 lg:pl-5",
                index === 0 && "lg:pr-5",
              )}
            >
              <div className="flex items-center gap-2">
                <div className="flex size-8 items-center justify-center rounded-lg border border-white/10 bg-white/[0.04]">
                  {key === "TO_DO" ? (
                    <ListChecks className="size-4 text-blue-300" />
                  ) : key === "DEVELOP" ? (
                    <Workflow className="size-4 text-violet-300" />
                  ) : key === "TEST" ? (
                    <FlaskConical className="size-4 text-amber-300" />
                  ) : (
                    <Rocket className="size-4 text-emerald-300" />
                  )}
                </div>
                <Label className="text-sm font-semibold">{label}</Label>
              </div>
              <p className="text-sm text-muted-foreground">{hint}</p>
              <NumberStepper
                value={settings.wip[key]}
                min={0}
                max={99}
                disabled={isLoading || isSaving}
                className="h-11 w-full rounded-xl border-white/15 bg-black/20 text-base font-semibold"
                onChange={(value) => updateWip(key, value)}
              />
            </div>
          ))}
        </div>
      </DashboardPanel>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Button
          type="button"
          onClick={handleSave}
          disabled={isLoading || isSaving}
          className="h-11 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-5 text-white shadow-lg shadow-violet-950/30 hover:from-violet-500 hover:to-indigo-500"
        >
          <Save className="size-4" />
          Salvar regras da fila
        </Button>
        <p className="text-sm text-muted-foreground">
          As alterações serão aplicadas imediatamente.
        </p>
        {savedMessage ? (
          <p className="text-sm text-emerald-400">{savedMessage}</p>
        ) : null}
      </div>
    </div>
  );
}

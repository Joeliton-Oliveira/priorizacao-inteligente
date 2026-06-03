"use client";

import type { ReactNode } from "react";

export function ActivityNewPageShell({ children }: { children: ReactNode }) {
  return (
    <div className="relative mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-0 py-1 sm:max-w-5xl">
      <div
        className="pointer-events-none absolute -inset-x-4 -top-4 bottom-0 -z-10 rounded-3xl opacity-80 sm:-inset-x-8"
        aria-hidden
      >
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(139,92,246,0.15),transparent)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_100%_0%,rgba(59,130,246,0.08),transparent)]" />
      </div>

      <header className="shrink-0 space-y-1.5">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Cadastrar
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Fluxo em 2 etapas para entrada inicial da demanda e estruturação inteligente com IA.
        </p>
      </header>

      {children}
    </div>
  );
}

"use client";

import { ActivityForm } from "../_components/activity-form/activity-form";

export default function NewActivityPage() {
  return (
    <div className="mx-auto flex min-h-0 flex-1 max-w-3xl flex-col gap-3">
      <div className="shrink-0">
        <h1 className="text-xl font-semibold tracking-tight">Cadastrar</h1>
        <p className="text-base text-muted-foreground">
          Formulário para relatar bug, feature ou outra atividade do sistema.
        </p>
      </div>

      <ActivityForm />
    </div>
  );
}

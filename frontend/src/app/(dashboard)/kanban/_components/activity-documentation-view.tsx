"use client";

import type { ReactNode } from "react";
import { ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  isBacklogDocumentacaoEmpty,
  isDevelopDocumentacaoEmpty,
  isDeployDocumentacaoEmpty,
  isTestDocumentacaoEmpty,
  isToDoDocumentacaoEmpty,
  type ActivityDocumentation,
  type BacklogDocumentacao,
  type DeployDocumentacao,
  type DevelopDocumentacao,
  type TestDocumentacao,
  type ToDoDocumentacao,
} from "./activity-documentation-data";
import { CASO_TESTE_STATUS_OPTIONS } from "./test-case-types";
import { TODO_CHECKLIST_OPTIONS } from "./todo-checklist";

function formatDateBr(iso: string) {
  if (!iso) return "—";
  const [year, month, day] = iso.split("-");
  if (!year || !month || !day) return iso;
  return `${day}/${month}/${year}`;
}

function checklistLabels(values: string[]) {
  const map = Object.fromEntries(
    TODO_CHECKLIST_OPTIONS.map((option) => [option.value, option.label]),
  );
  return values.map((value) => map[value] ?? value).join(", ") || "—";
}

function DocField({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="text-sm whitespace-pre-wrap">{value || "—"}</p>
    </div>
  );
}

function DocList({ label, items }: { label: string; items: string[] }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">—</p>
      ) : (
        <ul className="list-inside list-disc space-y-0.5 text-sm">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function PhaseEmptyState({
  title,
  onPreencher,
}: {
  title: string;
  onPreencher?: () => void;
}) {
  return (
    <section className="space-y-3 border-t pt-4">
      <h3 className="text-sm font-bold text-primary">{title}</h3>
      <Button type="button" variant="secondary" size="sm" onClick={onPreencher}>
        Preencher
      </Button>
    </section>
  );
}

function PhaseFilledSection({
  title,
  onEditar,
  contentClassName,
  children,
}: {
  title: string;
  onEditar?: () => void;
  contentClassName?: string;
  children: ReactNode;
}) {
  return (
    <section className="space-y-3 border-t pt-4">
      <Collapsible defaultOpen={false} className="group/phase space-y-3">
        <CollapsibleTrigger className="flex w-full items-center gap-2 text-left">
          <ChevronRight className="size-4 shrink-0 text-muted-foreground transition-transform group-data-[state=open]/phase:rotate-90" />
          <h3 className="text-sm font-bold text-primary">{title}</h3>
        </CollapsibleTrigger>
        <Button type="button" variant="secondary" size="sm" onClick={onEditar}>
          Editar
        </Button>
        <CollapsibleContent>
          <div className={`space-y-4 ${contentClassName ?? ""}`}>{children}</div>
        </CollapsibleContent>
      </Collapsible>
    </section>
  );
}

function BacklogPhaseSection({
  backlog,
  onPreencher,
}: {
  backlog: BacklogDocumentacao;
  onPreencher?: () => void;
}) {
  const title = "BACKLOG — documento de requisito";

  if (isBacklogDocumentacaoEmpty(backlog)) {
    return <PhaseEmptyState title={title} onPreencher={onPreencher} />;
  }

  return (
    <PhaseFilledSection
      title={title}
      onEditar={onPreencher}
      contentClassName="rounded-lg border bg-muted/20 p-4"
    >
      <DocField label="Nome da funcionalidade" value={backlog.nomeFuncionalidade} />
      <DocField label="Descrição detalhada" value={backlog.descricaoDetalhada} />
      <DocField label="Restrições" value={backlog.restricoes} />
      <DocList label="Requisitos funcionais (RF)" items={backlog.requisitosFuncionais} />
      <DocList
        label="Requisitos não funcionais (RNF)"
        items={backlog.requisitosNaoFuncionais}
      />
      <DocList label="Regras de negócio" items={backlog.regrasNegocio} />
      <DocList label="Critérios de aceitação" items={backlog.criteriosAceitacao} />
    </PhaseFilledSection>
  );
}

function ToDoPhaseSection({
  toDo,
  onPreencher,
}: {
  toDo?: ToDoDocumentacao;
  onPreencher?: () => void;
}) {
  const title = "TO DO — prontidão para desenvolvimento";

  if (isToDoDocumentacaoEmpty(toDo)) {
    return <PhaseEmptyState title={title} onPreencher={onPreencher} />;
  }

  return (
    <PhaseFilledSection title={title} onEditar={onPreencher}>
      <DocField
        label="Responsável pelo desenvolvimento"
        value={toDo!.responsavelDesenvolvimento}
      />
      <DocField label="Registado por" value={toDo!.registradoPor} />
      <DocField label="Data da prontidão" value={formatDateBr(toDo!.dataProntidao)} />
      <DocField label="Observações técnicas" value={toDo!.observacoesTecnicas} />
      <DocField label="Checklist" value={checklistLabels(toDo!.checklist)} />
    </PhaseFilledSection>
  );
}

function DevelopPhaseSection({
  develop,
  onPreencher,
}: {
  develop?: DevelopDocumentacao;
  onPreencher?: () => void;
}) {
  const title = "DEVELOP — entrega de desenvolvimento";

  if (isDevelopDocumentacaoEmpty(develop)) {
    return <PhaseEmptyState title={title} onPreencher={onPreencher} />;
  }

  return (
    <PhaseFilledSection title={title} onEditar={onPreencher}>
      <DocField label="Nome / correção" value={develop!.nomeEntrega} />
      <DocField label="O que foi desenvolvido" value={develop!.descricaoDesenvolvido} />
      <DocField label="O que foi alterado" value={develop!.alteracoes} />
      <DocField label="O que validar (QA)" value={develop!.validacaoQa} />
      <DocField label="Branch" value={develop!.branchReferencia} />
      <DocField label="Commit" value={develop!.commitReferencia} />
      <DocField label="Desenvolvedor" value={develop!.desenvolvedor} />
      <DocField
        label="Data de entrega para teste"
        value={formatDateBr(develop!.dataEntregaTeste)}
      />
    </PhaseFilledSection>
  );
}

function statusLabel(status: string) {
  return (
    CASO_TESTE_STATUS_OPTIONS.find((option) => option.value === status)?.label ?? status
  );
}

function TestPhaseSection({
  test,
  onPreencher,
}: {
  test?: TestDocumentacao;
  onPreencher?: () => void;
}) {
  const title = "TEST — casos de teste";

  if (isTestDocumentacaoEmpty(test)) {
    return <PhaseEmptyState title={title} onPreencher={onPreencher} />;
  }

  return (
    <PhaseFilledSection title={title} onEditar={onPreencher}>
      {test!.casos.map((caso, index) => (
        <div key={index} className="space-y-2 rounded-lg border bg-muted/20 p-3">
          <p className="text-sm font-semibold">Caso de teste {index + 1}</p>
          <DocField label="Resumo" value={caso.resumo} />
          <DocField label="Status" value={statusLabel(caso.status)} />
          <DocField label="Executor" value={caso.executor} />
        </div>
      ))}
    </PhaseFilledSection>
  );
}

function DeployPhaseSection({
  deploy,
  onPreencher,
}: {
  deploy?: DeployDocumentacao;
  onPreencher?: () => void;
}) {
  const title = "DEPLOY — deploy";

  if (isDeployDocumentacaoEmpty(deploy)) {
    return <PhaseEmptyState title={title} onPreencher={onPreencher} />;
  }

  return (
    <PhaseFilledSection title={title} onEditar={onPreencher}>
      <DocField label="Versão entregue" value={deploy!.versaoEntregue} />
      <DocField label="Ambiente" value={deploy!.ambiente} />
      <DocField label="Data do deploy" value={formatDateBr(deploy!.dataDeploy)} />
      <DocField label="Responsável" value={deploy!.responsavelDeploy} />
      <DocField label="Observações" value={deploy!.observacoes} />
    </PhaseFilledSection>
  );
}

export type DocumentationPhaseId = "backlog" | "to-do" | "develop" | "test" | "deploy";

type ActivityDocumentationViewProps = {
  data: ActivityDocumentation;
  onPreencherFase?: (phase: DocumentationPhaseId) => void;
};

export function ActivityDocumentationView({
  data,
  onPreencherFase,
}: ActivityDocumentationViewProps) {
  return (
    <div className="space-y-4 pr-1">
      <div className="border-b border-primary/30 pb-4">
        <h2 className="text-sm font-bold">Resumo da documentação (BACKLOG → DEPLOY)</h2>
      </div>

      <BacklogPhaseSection
        backlog={data.backlog}
        onPreencher={() => onPreencherFase?.("backlog")}
      />
      <ToDoPhaseSection toDo={data.toDo} onPreencher={() => onPreencherFase?.("to-do")} />
      <DevelopPhaseSection
        develop={data.develop}
        onPreencher={() => onPreencherFase?.("develop")}
      />
      <TestPhaseSection test={data.test} onPreencher={() => onPreencherFase?.("test")} />
      <DeployPhaseSection
        deploy={data.deploy}
        onPreencher={() => onPreencherFase?.("deploy")}
      />
    </div>
  );
}

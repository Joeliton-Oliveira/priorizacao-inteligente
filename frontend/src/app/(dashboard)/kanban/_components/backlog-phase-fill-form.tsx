"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  normalizeBacklogRestricoes,
  type BacklogDocumentacao,
} from "./activity-documentation-data";
import { NumberedListField } from "./numbered-list-field";

function listFromBacklog(items: string[]) {
  return items.length > 0 ? [...items] : [""];
}

type BacklogPhaseFillFormProps = {
  initial: BacklogDocumentacao;
  onSave: (backlog: BacklogDocumentacao) => void;
  onCancel: () => void;
  requirementType?: string | null;
};

export function BacklogPhaseFillForm({
  initial,
  onSave,
  onCancel,
  requirementType,
}: BacklogPhaseFillFormProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [nomeFuncionalidade, setNomeFuncionalidade] = useState(initial.nomeFuncionalidade);
  const [descricaoDetalhada, setDescricaoDetalhada] = useState(initial.descricaoDetalhada);
  const [restricoes, setRestricoes] = useState(initial.restricoes);
  const [requisitosFuncionais, setRequisitosFuncionais] = useState(() =>
    listFromBacklog(initial.requisitosFuncionais),
  );
  const [requisitosNaoFuncionais, setRequisitosNaoFuncionais] = useState(() =>
    listFromBacklog(initial.requisitosNaoFuncionais),
  );
  const [regrasNegocio, setRegrasNegocio] = useState(() =>
    listFromBacklog(initial.regrasNegocio),
  );
  const [criteriosAceitacao, setCriteriosAceitacao] = useState(() =>
    listFromBacklog(initial.criteriosAceitacao),
  );

  const trimList = (items: string[]) => items.map((item) => item.trim()).filter(Boolean);
  const isBug = (requirementType || "").trim().toUpperCase() === "BUG";
  const totalSteps = isBug ? 2 : 3;
  const isLastStep = currentStep === totalSteps;

  const handleSave = () => {
    onSave({
      nomeFuncionalidade: nomeFuncionalidade.trim(),
      descricaoDetalhada: descricaoDetalhada.trim(),
      restricoes: normalizeBacklogRestricoes(restricoes),
      requisitosFuncionais: trimList(requisitosFuncionais),
      requisitosNaoFuncionais: trimList(requisitosNaoFuncionais),
      regrasNegocio: trimList(regrasNegocio),
      criteriosAceitacao: trimList(criteriosAceitacao),
    });
  };

  return (
    <div className="space-y-5 pr-1">
      <div className="space-y-2">
        <p className="text-sm font-semibold">Documento de requisito</p>
        <p className="text-xs text-muted-foreground">Passo {currentStep} de {totalSteps}</p>
      </div>

      {currentStep === 1 ? (
        <div className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="doc-nome-funcionalidade">Nome da funcionalidade</Label>
            <Input
              id="doc-nome-funcionalidade"
              value={nomeFuncionalidade}
              onChange={(event) => setNomeFuncionalidade(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="doc-descricao-detalhada">Descrição detalhada</Label>
            <Textarea
              id="doc-descricao-detalhada"
              value={descricaoDetalhada}
              onChange={(event) => setDescricaoDetalhada(event.target.value)}
              className="min-h-[100px]"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="doc-restricoes">Restrições (opcional)</Label>
            <Textarea
              id="doc-restricoes"
              value={restricoes}
              onChange={(event) => setRestricoes(event.target.value)}
              placeholder="Deixe em branco para registrar «Nenhuma»"
              className="min-h-[100px]"
            />
          </div>
        </div>
      ) : null}

      {currentStep === 2 ? (
        <div className="space-y-5">
          <NumberedListField
            label="Requisitos funcionais (RF)"
            items={requisitosFuncionais}
            onChange={setRequisitosFuncionais}
            addButtonLabel="Adicionar mais um RF"
            tagMode
          />

          <NumberedListField
            label="Requisitos não funcionais (RNF)"
            items={requisitosNaoFuncionais}
            onChange={setRequisitosNaoFuncionais}
            addButtonLabel="Adicionar mais um RNF"
            tagMode
          />
        </div>
      ) : null}

      {currentStep === 3 && !isBug ? (
        <div className="space-y-5">
          <NumberedListField
            label="Regras de negócio"
            items={regrasNegocio}
            onChange={setRegrasNegocio}
            addButtonLabel="Adicionar mais uma regra"
            tagMode
          />

          <NumberedListField
            label="Critérios de aceitação"
            items={criteriosAceitacao}
            onChange={setCriteriosAceitacao}
            addButtonLabel="Adicionar mais um critério"
            tagMode
          />
        </div>
      ) : null}

      <div className="flex w-full flex-col gap-2 border-t pt-4 sm:flex-row">
        {currentStep > 1 ? (
          <Button
            type="button"
            variant="outline"
            className="w-full sm:flex-1"
            onClick={() => setCurrentStep((prev) => Math.max(prev - 1, 1))}
          >
            <ChevronLeft className="mr-1 size-4" />
            Voltar
          </Button>
        ) : null}
        {currentStep === 1 ? (
          <Button type="button" variant="outline" className="w-full sm:flex-1" onClick={onCancel}>
            Cancelar
          </Button>
        ) : null}
        {isLastStep ? (
          <Button type="button" className="w-full sm:flex-1" onClick={handleSave}>
            Guardar esta fase
          </Button>
        ) : (
          <Button
            type="button"
            className="w-full sm:flex-1"
            onClick={() => setCurrentStep((prev) => Math.min(prev + 1, totalSteps))}
          >
            Próximo
            <ChevronRight className="ml-1 size-4" />
          </Button>
        )}
      </div>
    </div>
  );
}

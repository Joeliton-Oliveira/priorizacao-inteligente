"use client";

import { ChevronLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { AnaliseRequisitoResponse } from "@/lib/priorizacao/types";

type AiAnalysisStepProps = {
  direction: "next" | "prev";
  analise: AnaliseRequisitoResponse;
  evaluatorName: string;
  onEvaluatorNameChange: (value: string) => void;
  answers: Record<number, number>;
  onAnswerChange: (idPergunta: number, valor: number) => void;
  validationError: string | null;
  isSaving: boolean;
  onBack: () => void;
  onSave: () => void;
};

function tipoBadgeClass(tipo: string) {
  return tipo.toUpperCase() === "BUG"
    ? "bg-red-600/15 text-red-500"
    : "bg-blue-600/15 text-blue-500";
}

export function AiAnalysisStep({
  direction,
  analise,
  evaluatorName,
  onEvaluatorNameChange,
  answers,
  onAnswerChange,
  validationError,
  isSaving,
  onBack,
  onSave,
}: AiAnalysisStepProps) {
  const tipo = analise.tipo_requisito.toUpperCase();

  return (
    <div
      className={`flex flex-col gap-4 ${
        direction === "next"
          ? "animate-in fade-in-0 slide-in-from-right-4 duration-300"
          : ""
      }`}
    >
      <Card className="rounded-xl shadow-sm">
        <CardHeader className="pb-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="flex size-7 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
              2
            </span>
            <h2 className="text-base font-semibold">Demanda estruturada pela IA</h2>
          </div>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            <span className="font-medium">Classificação: </span>
            <span
              className={`inline-flex rounded-md px-2 py-0.5 text-xs font-semibold ${tipoBadgeClass(tipo)}`}
            >
              {tipo === "BUG" ? "Bug" : "Incremento"}
            </span>
          </p>
          <div>
            <p className="font-semibold">Título</p>
            <p className="text-muted-foreground">{analise.titulo_requisito}</p>
          </div>
          <div>
            <p className="font-semibold">Descrição</p>
            <p className="whitespace-pre-wrap text-muted-foreground">
              {analise.descricao_requisito}
            </p>
          </div>
          <div>
            <p className="font-semibold">Objetivo</p>
            <p className="text-muted-foreground">{analise.objetivo}</p>
          </div>
          <div>
            <p className="font-semibold">Finalidade</p>
            <p className="text-muted-foreground">{analise.finalidade}</p>
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-xl shadow-sm">
        <CardHeader className="pb-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="flex size-7 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
              3
            </span>
            <h2 className="text-base font-semibold">Avaliação da prioridade</h2>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="evaluator">Responsável pela avaliação</Label>
            <Input
              id="evaluator"
              placeholder="Nome"
              value={evaluatorName}
              onChange={(e) => onEvaluatorNameChange(e.target.value)}
              className="h-9 max-w-md"
            />
          </div>

          {analise.perguntas_avaliacao.map((pergunta, index) => (
            <Card key={pergunta.id_pergunta} className="border-muted bg-muted/20">
              <CardContent className="space-y-3 pt-4">
                <div>
                  <p className="text-sm font-medium leading-snug">
                    <span className="font-bold">P{index + 1}</span> {pergunta.texto}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    [{pergunta.dimensao}]
                  </p>
                </div>
                <fieldset className="space-y-2">
                  {pergunta.opcoes_resposta.map((opcao) => (
                    <label
                      key={opcao.valor}
                      className="flex cursor-pointer items-start gap-2 text-sm"
                    >
                      <input
                        type="radio"
                        name={`pergunta-${pergunta.id_pergunta}`}
                        value={opcao.valor}
                        checked={answers[pergunta.id_pergunta] === opcao.valor}
                        onChange={() =>
                          onAnswerChange(pergunta.id_pergunta, opcao.valor)
                        }
                        className="mt-1"
                      />
                      <span>
                        {opcao.rotulo} ({opcao.valor})
                      </span>
                    </label>
                  ))}
                </fieldset>
              </CardContent>
            </Card>
          ))}

          {validationError ? (
            <p className="text-sm text-destructive">{validationError}</p>
          ) : null}

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button
              type="button"
              variant="outline"
              className="h-11 flex-1"
              onClick={onBack}
              disabled={isSaving}
            >
              <ChevronLeft className="mr-2 size-4" />
              Voltar
            </Button>
            <Button
              type="button"
              className="h-11 flex-1"
              onClick={onSave}
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <Loader2 className="mr-2 size-4 animate-spin" />
                  Salvando…
                </>
              ) : (
                "Salvar avaliação e posicionar na matriz"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

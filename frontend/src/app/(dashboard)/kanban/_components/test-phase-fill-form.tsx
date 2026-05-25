"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { TestDocumentacao } from "./activity-documentation-data";
import {
  CASO_TESTE_STATUS_OPTIONS,
  casoTesteVazio,
  normalizeCasoTesteStatus,
  type CasoTeste,
} from "./test-case-types";

type TestPhaseFillFormProps = {
  cardId: string;
  initial?: TestDocumentacao;
  onSave: (test: TestDocumentacao) => void;
  onCancel: () => void;
};

export function TestPhaseFillForm({
  cardId,
  initial,
  onSave,
  onCancel,
}: TestPhaseFillFormProps) {
  const [casos, setCasos] = useState<CasoTeste[]>(
    initial?.casos?.length ? initial.casos.map((caso) => ({ ...caso })) : [casoTesteVazio()],
  );

  const updateCaso = (index: number, patch: Partial<CasoTeste>) => {
    setCasos((prev) =>
      prev.map((caso, i) => (i === index ? { ...caso, ...patch } : caso)),
    );
  };

  const handleSave = () => {
    onSave({
      casos: casos.map((caso) => ({
        resumo: caso.resumo.trim(),
        passos: caso.passos.trim(),
        resultadoEsperado: caso.resultadoEsperado.trim(),
        resultadoObtido: caso.resultadoObtido.trim(),
        status: normalizeCasoTesteStatus(caso.status),
        executor: caso.executor.trim(),
        dataExecucao: caso.dataExecucao.trim(),
        evidencia: caso.evidencia.trim(),
      })),
    });
  };

  return (
    <div className="space-y-5 pr-1">
      <p className="text-sm text-muted-foreground">Requisito #{cardId} — casos de teste</p>

      {casos.map((caso, index) => (
        <div
          key={index}
          className="space-y-4 rounded-lg border bg-muted/20 p-4"
        >
          <p className="text-sm font-semibold">Caso de teste {index + 1}</p>

          <div className="space-y-2">
            <Label htmlFor={`caso-resumo-${index}`}>Resumo</Label>
            <Input
              id={`caso-resumo-${index}`}
              value={caso.resumo}
              onChange={(event) => updateCaso(index, { resumo: event.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor={`caso-passos-${index}`}>Passos de execução</Label>
            <Textarea
              id={`caso-passos-${index}`}
              value={caso.passos}
              onChange={(event) => updateCaso(index, { passos: event.target.value })}
              className="min-h-[72px]"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor={`caso-esperado-${index}`}>Resultado esperado</Label>
            <Textarea
              id={`caso-esperado-${index}`}
              value={caso.resultadoEsperado}
              onChange={(event) =>
                updateCaso(index, { resultadoEsperado: event.target.value })
              }
              className="min-h-[72px]"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor={`caso-obtido-${index}`}>Resultado obtido</Label>
            <Textarea
              id={`caso-obtido-${index}`}
              value={caso.resultadoObtido}
              onChange={(event) =>
                updateCaso(index, { resultadoObtido: event.target.value })
              }
              className="min-h-[72px]"
            />
          </div>

          <div className="space-y-2">
            <Label>Status</Label>
            <Select
              value={caso.status}
              onValueChange={(value) =>
                updateCaso(index, { status: normalizeCasoTesteStatus(value) })
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CASO_TESTE_STATUS_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor={`caso-executor-${index}`}>Executor (quem testou)</Label>
            <Input
              id={`caso-executor-${index}`}
              value={caso.executor}
              onChange={(event) => updateCaso(index, { executor: event.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor={`caso-data-${index}`}>Data de execução</Label>
            <Input
              id={`caso-data-${index}`}
              type="date"
              value={caso.dataExecucao}
              onChange={(event) => updateCaso(index, { dataExecucao: event.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor={`caso-evidencia-${index}`}>
              Evidência / observação (links, anexos, notas)
            </Label>
            <Textarea
              id={`caso-evidencia-${index}`}
              value={caso.evidencia}
              onChange={(event) => updateCaso(index, { evidencia: event.target.value })}
              className="min-h-[72px]"
            />
          </div>
        </div>
      ))}

      <Button
        type="button"
        variant="outline"
        size="sm"
        className="text-primary"
        onClick={() => setCasos((prev) => [...prev, casoTesteVazio()])}
      >
        Adicionar caso de teste
      </Button>

      <div className="flex flex-wrap gap-2 border-t pt-4">
        <Button type="button" onClick={handleSave}>
          Guardar esta fase
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Voltar
        </Button>
      </div>
    </div>
  );
}

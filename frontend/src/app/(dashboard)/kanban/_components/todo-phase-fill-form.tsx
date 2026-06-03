"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { ToDoDocumentacao } from "./activity-documentation-data";
import { TODO_CHECKLIST_OPTIONS } from "./todo-checklist";

type ToDoPhaseFillFormProps = {
  initial?: ToDoDocumentacao;
  onSave: (toDo: ToDoDocumentacao) => void;
  onCancel: () => void;
};

export function ToDoPhaseFillForm({
  initial,
  onSave,
  onCancel,
}: ToDoPhaseFillFormProps) {
  const [responsavelDesenvolvimento, setResponsavelDesenvolvimento] = useState(
    initial?.responsavelDesenvolvimento ?? "",
  );
  const [registradoPor, setRegistradoPor] = useState(initial?.registradoPor ?? "");
  const [dataProntidao, setDataProntidao] = useState(initial?.dataProntidao ?? "");
  const [observacoesTecnicas, setObservacoesTecnicas] = useState(
    initial?.observacoesTecnicas ?? "",
  );
  const [checklist, setChecklist] = useState<string[]>(initial?.checklist ?? []);

  const toggleChecklistItem = (value: string, checked: boolean) => {
    setChecklist((prev) =>
      checked ? [...prev, value] : prev.filter((item) => item !== value),
    );
  };

  const handleSave = () => {
    onSave({
      responsavelDesenvolvimento: responsavelDesenvolvimento.trim(),
      registradoPor: registradoPor.trim(),
      dataProntidao: dataProntidao.trim(),
      observacoesTecnicas: observacoesTecnicas.trim(),
      checklist,
    });
  };

  return (
    <div className="space-y-5 pr-1">
      <div className="space-y-2">
        <Label htmlFor="todo-responsavel">
          Responsável pelo desenvolvimento (nome ou identificador)
        </Label>
        <Input
          id="todo-responsavel"
          value={responsavelDesenvolvimento}
          onChange={(event) => setResponsavelDesenvolvimento(event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="todo-registrado">Registado por (quem formaliza a prontidão)</Label>
        <Input
          id="todo-registrado"
          value={registradoPor}
          onChange={(event) => setRegistradoPor(event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="todo-data">Data da prontidão</Label>
        <Input
          id="todo-data"
          type="date"
          value={dataProntidao}
          onChange={(event) => setDataProntidao(event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="todo-observacoes">
          Observações técnicas (links, dependências, notas)
        </Label>
        <Textarea
          id="todo-observacoes"
          value={observacoesTecnicas}
          onChange={(event) => setObservacoesTecnicas(event.target.value)}
          className="min-h-[120px]"
        />
      </div>

      <div className="space-y-2">
        <Label>
          Checklist de prontidão (obrigatório marcar todos para liberar o gate)
        </Label>
        <p className="text-xs text-muted-foreground">
          O item «Responsável… definido» conta como satisfeito se preencheu o campo
          «Responsável…» acima. «Critérios de aceitação…» conta como satisfeito se na aba
          BACKLOG existir pelo menos um critério de aceitação guardado.
        </p>
        <div className="flex flex-col gap-3 pt-1">
          {TODO_CHECKLIST_OPTIONS.map((option) => (
            <label
              key={option.value}
              className="flex cursor-pointer items-start gap-2 text-sm leading-snug"
            >
              <input
                type="checkbox"
                className="mt-0.5 size-4 shrink-0 rounded border-input"
                checked={checklist.includes(option.value)}
                onChange={(event) =>
                  toggleChecklistItem(option.value, event.target.checked)
                }
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
      </div>

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

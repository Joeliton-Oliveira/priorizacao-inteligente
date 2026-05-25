"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { BacklogDocumentacao } from "./activity-documentation-data";
import { NumberedListField } from "./numbered-list-field";

function listFromBacklog(items: string[]) {
  return items.length > 0 ? [...items] : [""];
}

type BacklogPhaseFillFormProps = {
  initial: BacklogDocumentacao;
  onSave: (backlog: BacklogDocumentacao) => void;
  onCancel: () => void;
};

export function BacklogPhaseFillForm({
  initial,
  onSave,
  onCancel,
}: BacklogPhaseFillFormProps) {
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

  const handleSave = () => {
    onSave({
      nomeFuncionalidade: nomeFuncionalidade.trim(),
      descricaoDetalhada: descricaoDetalhada.trim(),
      restricoes: restricoes.trim(),
      requisitosFuncionais: trimList(requisitosFuncionais),
      requisitosNaoFuncionais: trimList(requisitosNaoFuncionais),
      regrasNegocio: trimList(regrasNegocio),
      criteriosAceitacao: trimList(criteriosAceitacao),
    });
  };

  return (
    <div className="space-y-5 pr-1">
      <p className="text-sm font-semibold">Cabeçalho do documento de requisito</p>

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
        <Label htmlFor="doc-restricoes">Restrições (use «Nenhuma» se não houver)</Label>
        <Textarea
          id="doc-restricoes"
          value={restricoes}
          onChange={(event) => setRestricoes(event.target.value)}
          className="min-h-[100px]"
        />
      </div>

      <NumberedListField
        label="Requisitos funcionais (RF)"
        items={requisitosFuncionais}
        onChange={setRequisitosFuncionais}
        addButtonLabel="Adicionar mais um RF"
      />

      <NumberedListField
        label="Requisitos não funcionais (RNF)"
        items={requisitosNaoFuncionais}
        onChange={setRequisitosNaoFuncionais}
        addButtonLabel="Adicionar mais um RNF"
      />

      <NumberedListField
        label="Regras de negócio"
        items={regrasNegocio}
        onChange={setRegrasNegocio}
        addButtonLabel="Adicionar mais uma regra"
      />

      <NumberedListField
        label="Critérios de aceitação"
        items={criteriosAceitacao}
        onChange={setCriteriosAceitacao}
        addButtonLabel="Adicionar mais um critério"
      />

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

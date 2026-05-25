"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { DevelopDocumentacao } from "./activity-documentation-data";

type DevelopPhaseFillFormProps = {
  cardId: string;
  initial?: DevelopDocumentacao;
  onSave: (develop: DevelopDocumentacao) => void;
  onCancel: () => void;
};

export function DevelopPhaseFillForm({
  cardId,
  initial,
  onSave,
  onCancel,
}: DevelopPhaseFillFormProps) {
  const [nomeEntrega, setNomeEntrega] = useState(initial?.nomeEntrega ?? "");
  const [descricaoDesenvolvido, setDescricaoDesenvolvido] = useState(
    initial?.descricaoDesenvolvido ?? "",
  );
  const [alteracoes, setAlteracoes] = useState(initial?.alteracoes ?? "");
  const [validacaoQa, setValidacaoQa] = useState(initial?.validacaoQa ?? "");
  const [branchReferencia, setBranchReferencia] = useState(initial?.branchReferencia ?? "");
  const [commitReferencia, setCommitReferencia] = useState(initial?.commitReferencia ?? "");
  const [desenvolvedor, setDesenvolvedor] = useState(initial?.desenvolvedor ?? "");
  const [dataEntregaTeste, setDataEntregaTeste] = useState(initial?.dataEntregaTeste ?? "");

  const handleSave = () => {
    onSave({
      nomeEntrega: nomeEntrega.trim(),
      descricaoDesenvolvido: descricaoDesenvolvido.trim(),
      alteracoes: alteracoes.trim(),
      validacaoQa: validacaoQa.trim(),
      branchReferencia: branchReferencia.trim(),
      commitReferencia: commitReferencia.trim(),
      desenvolvedor: desenvolvedor.trim(),
      dataEntregaTeste: dataEntregaTeste.trim(),
    });
  };

  return (
    <div className="space-y-5 pr-1">
      <p className="text-sm text-muted-foreground">
        Requisito #{cardId} — entrega de desenvolvimento
      </p>

      <div className="space-y-2">
        <Label htmlFor="develop-nome">Nome da funcionalidade / correção</Label>
        <Input
          id="develop-nome"
          value={nomeEntrega}
          onChange={(event) => setNomeEntrega(event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="develop-desenvolvido">O que foi desenvolvido</Label>
        <Textarea
          id="develop-desenvolvido"
          value={descricaoDesenvolvido}
          onChange={(event) => setDescricaoDesenvolvido(event.target.value)}
          className="min-h-[88px]"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="develop-alteracoes">
          O que foi alterado (módulos, serviços, ecrãs…)
        </Label>
        <Textarea
          id="develop-alteracoes"
          value={alteracoes}
          onChange={(event) => setAlteracoes(event.target.value)}
          className="min-h-[88px]"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="develop-validacao">O que deve ser validado (orientação ao QA)</Label>
        <Textarea
          id="develop-validacao"
          value={validacaoQa}
          onChange={(event) => setValidacaoQa(event.target.value)}
          className="min-h-[88px]"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="develop-branch">Branch de referência</Label>
        <Input
          id="develop-branch"
          value={branchReferencia}
          onChange={(event) => setBranchReferencia(event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="develop-commit">Commit de referência (hash ou link)</Label>
        <Input
          id="develop-commit"
          value={commitReferencia}
          onChange={(event) => setCommitReferencia(event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="develop-desenvolvedor">Desenvolvedor (nome ou identificador)</Label>
        <Input
          id="develop-desenvolvedor"
          value={desenvolvedor}
          onChange={(event) => setDesenvolvedor(event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="develop-data">Data de entrega para teste</Label>
        <Input
          id="develop-data"
          type="date"
          value={dataEntregaTeste}
          onChange={(event) => setDataEntregaTeste(event.target.value)}
        />
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

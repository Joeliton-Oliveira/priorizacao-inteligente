"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { DeployDocumentacao } from "./activity-documentation-data";

type DeployPhaseFillFormProps = {
  cardId: string;
  initial?: DeployDocumentacao;
  onSave: (deploy: DeployDocumentacao) => void;
  onCancel: () => void;
};

export function DeployPhaseFillForm({
  cardId,
  initial,
  onSave,
  onCancel,
}: DeployPhaseFillFormProps) {
  const [versaoEntregue, setVersaoEntregue] = useState(initial?.versaoEntregue ?? "");
  const [ambiente, setAmbiente] = useState(initial?.ambiente ?? "");
  const [dataDeploy, setDataDeploy] = useState(initial?.dataDeploy ?? "");
  const [responsavelDeploy, setResponsavelDeploy] = useState(initial?.responsavelDeploy ?? "");
  const [observacoes, setObservacoes] = useState(initial?.observacoes ?? "");

  const handleSave = () => {
    onSave({
      versaoEntregue: versaoEntregue.trim(),
      ambiente: ambiente.trim(),
      dataDeploy: dataDeploy.trim(),
      responsavelDeploy: responsavelDeploy.trim(),
      observacoes: observacoes.trim(),
    });
  };

  return (
    <div className="space-y-5 pr-1">
      <p className="text-sm text-muted-foreground">Requisito #{cardId} — registo de deploy</p>

      <div className="space-y-2">
        <Label htmlFor="deploy-versao">Versão entregue (release / tag)</Label>
        <Input
          id="deploy-versao"
          value={versaoEntregue}
          onChange={(event) => setVersaoEntregue(event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="deploy-ambiente">Ambiente (ex.: produção, homologação, staging)</Label>
        <Input
          id="deploy-ambiente"
          value={ambiente}
          onChange={(event) => setAmbiente(event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="deploy-data">Data do deploy</Label>
        <Input
          id="deploy-data"
          type="date"
          value={dataDeploy}
          onChange={(event) => setDataDeploy(event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="deploy-responsavel">
          Responsável pelo deploy (nome ou identificador)
        </Label>
        <Input
          id="deploy-responsavel"
          value={responsavelDeploy}
          onChange={(event) => setResponsavelDeploy(event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="deploy-observacoes">
          Observações (opcional: pipeline, URL, rollback…)
        </Label>
        <Textarea
          id="deploy-observacoes"
          value={observacoes}
          onChange={(event) => setObservacoes(event.target.value)}
          className="min-h-[100px]"
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

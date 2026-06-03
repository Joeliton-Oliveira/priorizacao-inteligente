"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Clock3,
  FolderKanban,
  FolderSync,
  Plus,
  Settings2,
} from "lucide-react";
import { DashboardPanel } from "@/app/(dashboard)/activities/_components/dashboard-panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { CustomModal } from "@/components/ui/CustomModal";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import type {
  ProjetoDetalhado,
  ProjetoHistoricoVersao,
  ProjetoStatus,
  ProjetoTipoOrigem,
} from "@/lib/priorizacao/types";

type ModalMode = "create" | "status" | "version" | "history" | null;

type CreateProjectState = {
  nome_projeto: string;
  descricao: string;
  responsavel: string;
  tipo_origem: ProjetoTipoOrigem;
  versao_atual: string;
  status_projeto: ProjetoStatus;
};

const INITIAL_CREATE_PROJECT_STATE: CreateProjectState = {
  nome_projeto: "",
  descricao: "",
  responsavel: "",
  tipo_origem: "novo",
  versao_atual: "",
  status_projeto: "ativo",
};

function detailFromPayload(payload: unknown, fallback: string) {
  if (payload && typeof payload === "object" && "detail" in payload && typeof payload.detail === "string") {
    return payload.detail;
  }
  return fallback;
}

function formatDate(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function getOriginBadgeClass() {
  return "border-violet-500/35 bg-violet-500/15 text-violet-300";
}

function getVersionBadgeClass() {
  return "border-blue-500/35 bg-blue-500/15 text-blue-300";
}

function getProjectStatusBadgeClass(status?: string | null) {
  const normalized = (status || "").toLowerCase();
  if (normalized === "ativo") return "border-emerald-500/35 bg-emerald-500/15 text-emerald-300";
  if (normalized === "arquivado") return "border-slate-500/35 bg-slate-500/15 text-slate-300";
  if (normalized === "descontinuado")
    return "border-amber-500/35 bg-amber-500/15 text-amber-300";
  return "border-slate-500/35 bg-slate-500/15 text-slate-300";
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjetoDetalhado[]>([]);
  const [history, setHistory] = useState<ProjetoHistoricoVersao[]>([]);
  const [createState, setCreateState] = useState<CreateProjectState>(INITIAL_CREATE_PROJECT_STATE);
  const [versionLevel, setVersionLevel] = useState<"patch" | "minor" | "major">("patch");
  const [versionReason, setVersionReason] = useState("");
  const [versionUser, setVersionUser] = useState("");
  const [statusValue, setStatusValue] = useState<ProjetoStatus>("ativo");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [modalMode, setModalMode] = useState<ModalMode>(null);
  const [selectedProject, setSelectedProject] = useState<ProjetoDetalhado | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const closeModal = () => {
    setModalMode(null);
    setSelectedProject(null);
    setErrorMessage(null);
  };

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      setErrorMessage(null);
      const response = await fetch("/api/priorizacao/projetos", {
        cache: "no-store",
      });
      const data = await response.json().catch(() => []);
      if (!response.ok) {
        throw new Error(detailFromPayload(data, "Não foi possível carregar os projetos."));
      }
      setProjects(Array.isArray(data) ? (data as ProjetoDetalhado[]) : []);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Não foi possível carregar os projetos.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadProjects();
  }, []);

  const openModal = (mode: Exclude<ModalMode, null>, project?: ProjetoDetalhado) => {
    setSelectedProject(project ?? null);
    setErrorMessage(null);
    if (mode === "create") {
      setCreateState(INITIAL_CREATE_PROJECT_STATE);
    }
    if (mode === "status" && project) {
      setStatusValue((project.status_projeto ?? "ativo") as ProjetoStatus);
    }
    if (mode === "version") {
      setVersionLevel("patch");
      setVersionReason("");
      setVersionUser("");
    }
    setModalMode(mode);
  };

  const handleOpenHistory = async (project: ProjetoDetalhado) => {
    try {
      setSelectedProject(project);
      setErrorMessage(null);
      setModalMode("history");
      const response = await fetch(
        `/api/priorizacao/projetos/${project.id_projeto}/historico-versao?limite=50`,
        { cache: "no-store" },
      );
      const data = await response.json().catch(() => []);
      if (!response.ok) {
        throw new Error(detailFromPayload(data, "Não foi possível carregar o histórico."));
      }
      setHistory(Array.isArray(data) ? (data as ProjetoHistoricoVersao[]) : []);
    } catch (error) {
      setHistory([]);
      setErrorMessage(
        error instanceof Error ? error.message : "Não foi possível carregar o histórico.",
      );
    }
  };

  const refreshAndClose = async (message: string) => {
    setFeedback(message);
    closeModal();
    await loadProjects();
    window.setTimeout(() => setFeedback(null), 4000);
  };

  const handleCreate = async () => {
    try {
      setIsSubmitting(true);
      setErrorMessage(null);
      const response = await fetch("/api/priorizacao/projetos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...createState,
          versao_atual:
            createState.tipo_origem === "existente" ? createState.versao_atual.trim() : undefined,
        }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(detailFromPayload(data, "Não foi possível cadastrar o projeto."));
      }
      await refreshAndClose("Projeto cadastrado com sucesso.");
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Não foi possível cadastrar o projeto.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleStatusUpdate = async () => {
    if (!selectedProject) return;
    try {
      setIsSubmitting(true);
      setErrorMessage(null);
      const response = await fetch(
        `/api/priorizacao/projetos/${selectedProject.id_projeto}/status`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: statusValue }),
        },
      );
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(detailFromPayload(data, "Não foi possível alterar o status do projeto."));
      }
      await refreshAndClose("Status do projeto atualizado.");
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Não foi possível alterar o status do projeto.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVersionUpdate = async () => {
    if (!selectedProject) return;
    try {
      setIsSubmitting(true);
      setErrorMessage(null);
      const response = await fetch(
        `/api/priorizacao/projetos/${selectedProject.id_projeto}/evoluir-versao`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            nivel: versionLevel,
            motivo: versionReason.trim() || undefined,
            usuario_responsavel: versionUser.trim() || undefined,
          }),
        },
      );
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(detailFromPayload(data, "Não foi possível evoluir a versão do projeto."));
      }
      await refreshAndClose("Versão do projeto atualizada.");
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Não foi possível evoluir a versão do projeto.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(projects.length / pageSize));
  const paginatedProjects = useMemo(() => {
    const start = (page - 1) * pageSize;
    return projects.slice(start, start + pageSize);
  }, [projects, page]);

  const rangeStart = projects.length === 0 ? 0 : (page - 1) * pageSize + 1;
  const rangeEnd = Math.min(page * pageSize, projects.length);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  const modalTitle =
    modalMode === "create"
      ? "Cadastrar novo projeto"
      : modalMode === "status"
        ? "Alterar status operacional"
        : modalMode === "version"
          ? "Evoluir versão do projeto"
          : modalMode === "history"
            ? "Histórico de versões"
            : "";

  const modalDescription =
    modalMode === "create"
      ? "O projeto ficará disponível imediatamente no cadastro da atividade."
      : modalMode === "status"
        ? "Altere o estado operacional do projeto."
        : modalMode === "version"
          ? "Registre a evolução semântica da versão."
          : modalMode === "history"
            ? "Auditoria das evoluções gravadas no backend."
            : "";

  return (
    <TooltipProvider>
      <div className="mx-auto w-full max-w-[1440px] space-y-5 pb-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-violet-600/20 ring-1 ring-violet-500/30">
              <FolderKanban className="size-6 text-violet-300" />
            </div>
            <div className="space-y-1">
              <h1 className="text-2xl font-bold tracking-tight">Projetos cadastrados</h1>
              <p className="max-w-2xl text-sm text-muted-foreground">
                Base real do backend, compartilhada com o cadastro de atividades.
              </p>
            </div>
          </div>
          <Button
            onClick={() => openModal("create")}
            className="shrink-0 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-950/30 hover:from-violet-500 hover:to-indigo-500"
          >
            <Plus className="size-4" />
            Cadastrar novo projeto
          </Button>
        </div>

        {feedback ? (
          <p className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-400">
            {feedback}
          </p>
        ) : null}

        {errorMessage && modalMode === null ? (
          <p className="rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-red-400">
            {errorMessage}
          </p>
        ) : null}

        <DashboardPanel className="p-4 sm:p-5">
          <div className="overflow-x-auto rounded-xl border border-white/10">
            <Table className="min-w-[960px]">
              <TableHeader>
                <TableRow className="bg-white/[0.03] hover:bg-white/[0.03]">
                  <TableHead className="w-16">ID</TableHead>
                  <TableHead>Nome</TableHead>
                  <TableHead className="w-28">Origem</TableHead>
                  <TableHead className="w-28">Versão</TableHead>
                  <TableHead className="w-28">Status</TableHead>
                  <TableHead className="w-28">Resp.</TableHead>
                  <TableHead className="w-44">Última evolução</TableHead>
                  <TableHead className="w-36 text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="py-10 text-center text-sm text-muted-foreground">
                      Carregando projetos...
                    </TableCell>
                  </TableRow>
                ) : paginatedProjects.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="py-10 text-center text-sm text-muted-foreground">
                      Nenhum projeto cadastrado.
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedProjects.map((project) => (
                    <TableRow
                      key={project.id_projeto}
                      className="border-white/10 hover:bg-white/[0.03]"
                    >
                      <TableCell className="font-medium">{project.id_projeto}</TableCell>
                      <TableCell className="max-w-[280px] font-medium leading-relaxed">
                        {project.nome_projeto}
                      </TableCell>
                      <TableCell>
                        <span
                          className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold capitalize ${getOriginBadgeClass()}`}
                        >
                          {project.tipo_origem || "—"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span
                          className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold ${getVersionBadgeClass()}`}
                        >
                          {project.versao_atual || "—"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span
                          className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold capitalize ${getProjectStatusBadgeClass(project.status_projeto)}`}
                        >
                          {project.status_projeto || "—"}
                        </span>
                      </TableCell>
                      <TableCell>{project.responsavel || "—"}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatDate(project.ultima_evolucao_em)}
                      </TableCell>
                      <TableCell>
                        <div className="flex justify-end gap-1.5">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="outline"
                                size="icon-sm"
                                className="size-8 rounded-lg border-white/10 bg-white/[0.02] hover:bg-white/[0.06]"
                                onClick={() => openModal("status", project)}
                              >
                                <Settings2 className="size-3.5" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Alterar status</TooltipContent>
                          </Tooltip>

                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="outline"
                                size="icon-sm"
                                className="size-8 rounded-lg border-white/10 bg-white/[0.02] hover:bg-violet-500/10 hover:text-violet-200"
                                onClick={() => openModal("version", project)}
                              >
                                <FolderSync className="size-3.5" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Evoluir versão</TooltipContent>
                          </Tooltip>

                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                variant="outline"
                                size="icon-sm"
                                className="size-8 rounded-lg border-white/10 bg-white/[0.02] hover:bg-white/[0.06]"
                                onClick={() => void handleOpenHistory(project)}
                              >
                                <Clock3 className="size-3.5" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Histórico</TooltipContent>
                          </Tooltip>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          <div className="mt-4 flex flex-col gap-3 border-t border-white/10 pt-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              Mostrando {rangeStart} a {rangeEnd} de {projects.length} projetos
            </p>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="rounded-lg border-white/10 bg-white/[0.02]"
                disabled={page <= 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
              >
                <ChevronLeft className="size-4" />
              </Button>
              <span className="flex size-8 items-center justify-center rounded-lg bg-violet-600/20 text-sm font-semibold text-violet-200 ring-1 ring-violet-500/30">
                {page}
              </span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="rounded-lg border-white/10 bg-white/[0.02]"
                disabled={page >= totalPages}
                onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
              >
                <ChevronRight className="size-4" />
              </Button>
              <span className="ml-2 text-xs text-muted-foreground">{pageSize} / página</span>
            </div>
          </div>
        </DashboardPanel>
      </div>

      <CustomModal
        open={modalMode !== null}
        onOpenChange={(open) => {
          if (!open) closeModal();
        }}
        title={modalTitle}
        description={modalDescription}
      >
        {errorMessage ? (
          <p className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-red-500">
            {errorMessage}
          </p>
        ) : null}

        {modalMode === "create" ? (
          <div className="space-y-3">
            <div className="space-y-1">
              <p className="text-sm font-medium">Nome do projeto</p>
              <Input
                value={createState.nome_projeto}
                onChange={(event) =>
                  setCreateState((prev) => ({ ...prev, nome_projeto: event.target.value }))
                }
                placeholder="Nome do projeto"
              />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium">Descrição</p>
              <Textarea
                value={createState.descricao}
                onChange={(event) =>
                  setCreateState((prev) => ({ ...prev, descricao: event.target.value }))
                }
                placeholder="Descreva o projeto..."
              />
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <p className="text-sm font-medium">Origem</p>
                <Select
                  value={createState.tipo_origem}
                  onValueChange={(value) =>
                    setCreateState((prev) => ({
                      ...prev,
                      tipo_origem: value as ProjetoTipoOrigem,
                    }))
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="novo">Novo</SelectItem>
                    <SelectItem value="existente">Existente</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">Status</p>
                <Select
                  value={createState.status_projeto}
                  onValueChange={(value) =>
                    setCreateState((prev) => ({
                      ...prev,
                      status_projeto: value as ProjetoStatus,
                    }))
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ativo">Ativo</SelectItem>
                    <SelectItem value="arquivado">Arquivado</SelectItem>
                    <SelectItem value="descontinuado">Descontinuado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">Responsável</p>
                <Input
                  value={createState.responsavel}
                  onChange={(event) =>
                    setCreateState((prev) => ({ ...prev, responsavel: event.target.value }))
                  }
                  placeholder="Nome do responsável"
                />
              </div>
            </div>

            {createState.tipo_origem === "existente" ? (
              <div className="space-y-1">
                <p className="text-sm font-medium">Versão atual</p>
                <Input
                  value={createState.versao_atual}
                  onChange={(event) =>
                    setCreateState((prev) => ({ ...prev, versao_atual: event.target.value }))
                  }
                  placeholder="Ex.: 3.11.52"
                />
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Projetos novos começam na versão `1.0.0`.
              </p>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={closeModal}>
                Cancelar
              </Button>
              <Button onClick={() => void handleCreate()} disabled={isSubmitting}>
                Cadastrar projeto
              </Button>
            </div>
          </div>
        ) : null}

        {modalMode === "status" && selectedProject ? (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Projeto selecionado:{" "}
              <span className="font-semibold text-foreground">{selectedProject.nome_projeto}</span>
            </p>
            <Select value={statusValue} onValueChange={(value) => setStatusValue(value as ProjetoStatus)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ativo">Ativo</SelectItem>
                <SelectItem value="arquivado">Arquivado</SelectItem>
                <SelectItem value="descontinuado">Descontinuado</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={closeModal}>
                Cancelar
              </Button>
              <Button onClick={() => void handleStatusUpdate()} disabled={isSubmitting}>
                Guardar status
              </Button>
            </div>
          </div>
        ) : null}

        {modalMode === "version" && selectedProject ? (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Projeto: <span className="font-semibold text-foreground">{selectedProject.nome_projeto}</span>
            </p>
            <div className="space-y-1">
              <p className="text-sm font-medium">Nível da evolução</p>
              <Select
                value={versionLevel}
                onValueChange={(value) => setVersionLevel(value as "patch" | "minor" | "major")}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="patch">Patch</SelectItem>
                  <SelectItem value="minor">Minor</SelectItem>
                  <SelectItem value="major">Major</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium">Motivo</p>
              <Textarea
                value={versionReason}
                onChange={(event) => setVersionReason(event.target.value)}
                placeholder="Ex.: entrega da sprint, demanda concluída, release de produção..."
              />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium">Responsável</p>
              <Input
                value={versionUser}
                onChange={(event) => setVersionUser(event.target.value)}
                placeholder="Quem está registrando a evolução?"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={closeModal}>
                Cancelar
              </Button>
              <Button onClick={() => void handleVersionUpdate()} disabled={isSubmitting}>
                Evoluir versão
              </Button>
            </div>
          </div>
        ) : null}

        {modalMode === "history" ? (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {selectedProject
                ? `Projeto: ${selectedProject.nome_projeto}`
                : "Histórico das evoluções registradas"}
            </p>
            <div className="max-h-[420px] overflow-y-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Quando</TableHead>
                    <TableHead>Versão</TableHead>
                    <TableHead>Nível</TableHead>
                    <TableHead>Responsável</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {history.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="py-8 text-center text-sm text-muted-foreground">
                        Nenhuma evolução registada.
                      </TableCell>
                    </TableRow>
                  ) : history.map((item) => (
                    <TableRow key={item.id_historico}>
                      <TableCell>{formatDate(item.criado_em)}</TableCell>
                      <TableCell>{item.versao_anterior} → {item.versao_nova}</TableCell>
                      <TableCell>{item.nivel_evolucao}</TableCell>
                      <TableCell>{item.usuario_responsavel || "—"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="flex justify-end">
              <Button variant="outline" onClick={closeModal}>
                Fechar
              </Button>
            </div>
          </div>
        ) : null}
      </CustomModal>
    </TooltipProvider>
  );
}

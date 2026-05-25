"use client";

import { useMemo, useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { CustomModal } from "@/components/ui/CustomModal";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

type ProjectRow = {
  id: number;
  nome: string;
  tipo: string;
  versao: string;
  status: string;
  responsavel: string;
};

type ModalMode = "create" | "edit" | "delete" | null;

const MOCK_PROJECTS: ProjectRow[] = [
  {
    id: 1,
    nome: "Plataforma Web de Vendas / E-commerce",
    tipo: "",
    versao: "1.0.1",
    status: "ativo",
    responsavel: "",
  },
  {
    id: 2,
    nome: "Portal de Atendimento Interno",
    tipo: "interno",
    versao: "2.3.0",
    status: "planejado",
    responsavel: "Equipe Produto",
  },
  {
    id: 3,
    nome: "App de Gestão Comercial",
    tipo: "externo",
    versao: "1.8.4",
    status: "ativo",
    responsavel: "Squad Mobile",
  },
];

export default function ProjectsPage() {
  const [originFilter, setOriginFilter] = useState("Todas");
  const [statusFilter, setStatusFilter] = useState("Todos");
  const [nameFilter, setNameFilter] = useState("");

  const [modalMode, setModalMode] = useState<ModalMode>(null);
  const [selectedProject, setSelectedProject] = useState<ProjectRow | null>(null);

  const openModal = (mode: Exclude<ModalMode, null>, project?: ProjectRow) => {
    setSelectedProject(project ?? null);
    setModalMode(mode);
  };
  const closeModal = () => {
    setModalMode(null);
    setSelectedProject(null);
  };

  const filteredProjects = useMemo(() => {
    return MOCK_PROJECTS.filter((project) => {
      const byName =
        nameFilter.trim() === "" ||
        project.nome.toLowerCase().includes(nameFilter.trim().toLowerCase());

      const byStatus =
        statusFilter === "Todos" ||
        project.status.toLowerCase() === statusFilter.toLowerCase();

      const byOrigin =
        originFilter === "Todas" ||
        (project.tipo || "não informado").toLowerCase() === originFilter.toLowerCase();

      return byName && byStatus && byOrigin;
    });
  }, [nameFilter, originFilter, statusFilter]);

  const modalTitle = modalMode === "create"
    ? "Cadastrar novo projeto"
    : modalMode === "edit"
      ? "Editar projeto"
      : modalMode === "delete"
        ? "Confirmar exclusão"
        : "";

  const modalDescription = modalMode === "delete"
    ? "Essa ação não pode ser desfeita."
    : modalMode === "create" || modalMode === "edit"
      ? "Preencha os dados para continuar."
      : "";

  return (
    <TooltipProvider>
      <div className="rounded-xl border bg-card p-5 shadow-sm">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold">Projetos cadastrados</h1>
          </div>
          <Button onClick={() => openModal("create")}>Cadastrar Novo Projeto</Button>
        </div>

        <div className="mb-5 grid grid-cols-1 gap-3 md:grid-cols-3">
          <div className="space-y-1">
            <p className="text-sm font-medium">Filtro origem</p>
            <Select value={originFilter} onValueChange={setOriginFilter}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Todas" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Todas">Todas</SelectItem>
                <SelectItem value="interno">Interno</SelectItem>
                <SelectItem value="externo">Externo</SelectItem>
                <SelectItem value="não informado">Não informado</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <p className="text-sm font-medium">Filtro status</p>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Todos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Todos">Todos</SelectItem>
                <SelectItem value="ativo">Ativo</SelectItem>
                <SelectItem value="planejado">Planejado</SelectItem>
                <SelectItem value="inativo">Inativo</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <p className="text-sm font-medium">Busca nome</p>
            <Input
              value={nameFilter}
              onChange={(event) => setNameFilter(event.target.value)}
              placeholder="nome..."
            />
          </div>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-16">ID</TableHead>
              <TableHead>Nome</TableHead>
              <TableHead className="w-24">Tipo</TableHead>
              <TableHead className="w-24">Versão</TableHead>
              <TableHead className="w-24">Status</TableHead>
              <TableHead className="w-28">Resp.</TableHead>
              <TableHead className="w-24 text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredProjects.map((project) => (
              <TableRow key={project.id}>
                <TableCell>{project.id}</TableCell>
                <TableCell className="font-medium">{project.nome}</TableCell>
                <TableCell>{project.tipo || "-"}</TableCell>
                <TableCell>{project.versao}</TableCell>
                <TableCell>{project.status}</TableCell>
                <TableCell>{project.responsavel || "-"}</TableCell>
                <TableCell>
                  <div className="flex justify-end gap-1">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => openModal("edit", project)}
                        >
                          <Pencil className="size-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Editar Projeto</TooltipContent>
                    </Tooltip>

                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => openModal("delete", project)}
                        >
                          <Trash2 className="size-4 text-red-500" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Deletar Projeto</TooltipContent>
                    </Tooltip>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <CustomModal
        open={modalMode !== null}
        onOpenChange={(open) => {
          if (!open) closeModal();
        }}
        title={modalTitle}
        description={modalDescription}
      >
        {(modalMode === "create" || modalMode === "edit") && (
          <div className="space-y-3">
            <div className="space-y-1">
              <p className="text-sm font-medium">Nome do projeto</p>
              <Input defaultValue={selectedProject?.nome ?? ""} placeholder="Nome do projeto" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium">Descrição</p>
              <Textarea placeholder="Descreva o projeto..." />
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <p className="text-sm font-medium">Versão</p>
                <Input defaultValue={selectedProject?.versao ?? "1.0.0"} />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">Status</p>
                <Select defaultValue={selectedProject?.status ?? "ativo"}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ativo">Ativo</SelectItem>
                    <SelectItem value="planejado">Planejado</SelectItem>
                    <SelectItem value="inativo">Inativo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={closeModal}>
                Cancelar
              </Button>
              <Button onClick={closeModal}>
                {modalMode === "create" ? "Cadastrar projeto" : "Salvar alterações"}
              </Button>
            </div>
          </div>
        )}

        {modalMode === "delete" && (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Deseja realmente deletar o projeto{" "}
              <span className="font-semibold text-foreground">
                {selectedProject?.nome ?? "selecionado"}
              </span>
              ?
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={closeModal}>
                Cancelar
              </Button>
              <Button variant="destructive" onClick={closeModal}>
                Confirmar exclusão
              </Button>
            </div>
          </div>
        )}
      </CustomModal>
    </TooltipProvider>
  );
}

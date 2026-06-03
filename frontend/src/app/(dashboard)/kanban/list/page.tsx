"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Eye, LayoutGrid, ListFilter, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { buildFilaRankMap, compareByFilaRank } from "@/lib/priorizacao/fila-order";
import { KANBAN_COLUMN_ORDER, statusToColumn } from "@/lib/priorizacao/kanban-status";
import type { AtividadePriorizada } from "@/lib/priorizacao/types";

const COLUMN_ORDER = KANBAN_COLUMN_ORDER;

function getTypeBadgeClass(type?: string | null) {
  const normalized = (type || "").toUpperCase();
  if (normalized === "BUG") return "border-rose-500/35 bg-rose-500/15 text-rose-300";
  return "border-indigo-500/35 bg-indigo-500/15 text-indigo-300";
}

function getColumnBadgeClass(column: string) {
  if (column === "BACKLOG") return "border-slate-500/35 bg-slate-500/15 text-slate-200";
  if (column === "TO DO") return "border-blue-500/35 bg-blue-500/15 text-blue-300";
  if (column === "DEVELOP") return "border-violet-500/35 bg-violet-500/15 text-violet-300";
  if (column === "TEST") return "border-emerald-500/35 bg-emerald-500/15 text-emerald-300";
  if (column === "DEPLOY") return "border-amber-500/35 bg-amber-500/15 text-amber-300";
  return "border-cyan-500/35 bg-cyan-500/15 text-cyan-300";
}

function getStatusBadgeClass(status?: string | null) {
  const normalized = (status || "BACKLOG").toUpperCase();
  if (normalized === "BACKLOG") return "border-slate-500/35 bg-slate-500/15 text-slate-200";
  if (normalized === "AVALIADO") return "border-blue-500/35 bg-blue-500/15 text-blue-300";
  if (normalized === "EM_DESENVOLVIMENTO")
    return "border-violet-500/35 bg-violet-500/15 text-violet-300";
  if (normalized === "EM_TESTE") return "border-emerald-500/35 bg-emerald-500/15 text-emerald-300";
  if (normalized === "EM_HOMOLOGACAO")
    return "border-amber-500/35 bg-amber-500/15 text-amber-300";
  return "border-cyan-500/35 bg-cyan-500/15 text-cyan-300";
}

export default function KanbanListPage() {
  const [items, setItems] = useState<AtividadePriorizada[]>([]);
  const [filaRank, setFilaRank] = useState<Map<number, number>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadItems() {
      try {
        setIsLoading(true);
        setErrorMessage(null);
        const [activitiesResponse, filaResponse] = await Promise.all([
          fetch("/api/priorizacao/atividades", { cache: "no-store" }),
          fetch("/api/priorizacao/fila", { cache: "no-store" }),
        ]);
        const [data, filaData] = await Promise.all([
          activitiesResponse.json().catch(() => []),
          filaResponse.json().catch(() => []),
        ]);
        if (!activitiesResponse.ok) {
          throw new Error(
            data && typeof data === "object" && "detail" in data && typeof data.detail === "string"
              ? data.detail
              : "Não foi possível carregar a lista da esteira.",
          );
        }
        if (!cancelled) {
          setItems(Array.isArray(data) ? (data as AtividadePriorizada[]) : []);
          if (filaResponse.ok && Array.isArray(filaData)) {
            setFilaRank(buildFilaRankMap(filaData as { id: number }[]));
          } else {
            setFilaRank(new Map());
          }
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "Não foi possível carregar a lista da esteira.",
          );
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    loadItems();

    return () => {
      cancelled = true;
    };
  }, []);

  const orderedItems = useMemo(
    () =>
      [...items].sort((a, b) => {
        const columnA = statusToColumn(a.status_atual);
        const columnB = statusToColumn(b.status_atual);
        const byColumn = COLUMN_ORDER.indexOf(columnA) - COLUMN_ORDER.indexOf(columnB);
        if (byColumn !== 0) return byColumn;
        if (filaRank.size > 0) return compareByFilaRank(a, b, filaRank);
        return a.id - b.id;
      }),
    [items, filaRank],
  );

  const filteredItems = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    if (!term) return orderedItems;
    return orderedItems.filter((item) =>
      [item.titulo, item.nome_projeto, item.tipo_requisito]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(term)),
    );
  }, [orderedItems, searchTerm]);

  return (
    <div className="mx-auto w-full max-w-[1440px] space-y-5">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">Lista da esteira</h1>
        <p className="text-sm text-muted-foreground">
          Ordem na esteira: prioridade da matriz e distribuição bugs/melhorias da configuração (vazão).
        </p>
        <Button
          asChild
          variant="outline"
          className="mt-2 rounded-lg border-white/10 bg-white/[0.02] hover:bg-white/[0.06]"
        >
          <Link href="/kanban">
            <LayoutGrid className="size-4" />
            Quadro Kanban
          </Link>
        </Button>
      </div>

      {errorMessage ? (
        <p className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-red-500">
          {errorMessage}
        </p>
      ) : null}

      <div className="rounded-2xl border border-white/10 bg-card/70 p-4 shadow-xl shadow-black/25 ring-1 ring-white/5 backdrop-blur-sm sm:p-5">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative w-full sm:max-w-sm">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Buscar por título, projeto ou tipo..."
              className="h-10 w-full rounded-xl border border-white/10 bg-black/20 pl-9 pr-3 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-violet-500/40"
            />
          </div>
          <div className="inline-flex items-center gap-2 rounded-xl border border-violet-500/30 bg-violet-500/10 px-3 py-2 text-xs font-semibold text-violet-200">
            <ListFilter className="size-3.5" />
            Total: {filteredItems.length} atividades
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-white/10">
          <Table className="min-w-[980px]">
          <TableHeader>
            <TableRow className="bg-white/[0.03] hover:bg-white/[0.03]">
              <TableHead>ID</TableHead>
              <TableHead>Título</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Projeto</TableHead>
              <TableHead>Versão</TableHead>
              <TableHead>Coluna</TableHead>
              <TableHead>Score</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Detalhe</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={9} className="py-8 text-center text-sm text-muted-foreground">
                  Carregando lista da esteira...
                </TableCell>
              </TableRow>
            ) : filteredItems.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="py-8 text-center text-sm text-muted-foreground">
                  Nenhuma atividade encontrada para o filtro informado.
                </TableCell>
              </TableRow>
            ) : filteredItems.map((item) => (
              <TableRow key={item.id} className="border-white/10 hover:bg-white/[0.03]">
                <TableCell className="font-medium">{item.id}</TableCell>
                <TableCell className="max-w-[340px] font-medium leading-relaxed">{item.titulo}</TableCell>
                <TableCell>
                  <span className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold ${getTypeBadgeClass(item.tipo_requisito)}`}>
                    {item.tipo_requisito}
                  </span>
                </TableCell>
                <TableCell>{item.nome_projeto || "—"}</TableCell>
                <TableCell>{item.versao_projeto || "—"}</TableCell>
                <TableCell>
                  {(() => {
                    const column = statusToColumn(item.status_atual);
                    return (
                      <span className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold ${getColumnBadgeClass(column)}`}>
                        {column}
                      </span>
                    );
                  })()}
                </TableCell>
                <TableCell className="font-semibold text-amber-300">{item.score}</TableCell>
                <TableCell>
                  <span className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold ${getStatusBadgeClass(item.status_atual)}`}>
                    {item.status_atual || "BACKLOG"}
                  </span>
                </TableCell>
                <TableCell>
                  <Button
                    asChild
                    size="sm"
                    variant="outline"
                    className="h-8 rounded-lg border-white/10 bg-white/[0.02] hover:bg-white/[0.06]"
                  >
                    <Link href={`/kanban/list/${item.id}`}>
                      <Eye className="size-3.5" />
                      Abrir
                    </Link>
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}

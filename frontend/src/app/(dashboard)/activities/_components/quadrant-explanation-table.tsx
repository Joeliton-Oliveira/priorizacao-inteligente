import { cn } from "@/lib/utils";

export type QuadrantExplanationRow = {
  ordem: number;
  condicao: string;
  nome: string;
};

type QuadrantLegendProps = {
  axisHint: string;
  rows: QuadrantExplanationRow[];
  colorByName: Record<string, string>;
  /** Legenda ao lado do gráfico — tipografia mais compacta. */
  compact?: boolean;
  /** Uma linha por quadrante, coluna estreita ao lado do gráfico. */
  layout?: "default" | "sidebar";
};

export function QuadrantLegend({
  axisHint,
  rows,
  colorByName,
  compact,
  layout = "default",
}: QuadrantLegendProps) {
  if (layout === "sidebar") {
    return (
      <div className="flex min-w-0 flex-col justify-center">
        {axisHint ? (
          <p className="mb-2 text-[10px] leading-snug text-muted-foreground">{axisHint}</p>
        ) : null}
        <div className="rounded-lg border border-white/[0.08] bg-white/[0.04] px-2.5 py-1">
          <ul>
            {rows.map((row, index) => (
              <li
                key={row.ordem}
                className={cn(
                  "flex min-w-0 gap-2 py-2",
                  index > 0 && "border-t border-white/[0.06]",
                )}
                title={`${row.nome}: ${row.condicao}`}
              >
                <span
                  className="mt-1 size-2 shrink-0 rounded-full"
                  style={{ backgroundColor: colorByName[row.nome] ?? "#64748b" }}
                  aria-hidden
                />
                <div className="min-w-0">
                  <p className="text-[11px] font-semibold leading-tight text-foreground">
                    {row.nome}
                  </p>
                  <p className="mt-0.5 text-[10px] leading-snug text-muted-foreground">
                    {row.condicao}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex h-full flex-col justify-center",
        compact ? "space-y-2" : "space-y-3",
      )}
    >
      {axisHint ? (
        <p
          className={cn(
            "leading-relaxed text-muted-foreground",
            compact ? "text-[10px] leading-snug" : "text-[11px]",
          )}
        >
          {axisHint}
        </p>
      ) : null}
      <ul className={compact ? "space-y-1.5" : "space-y-2.5"}>
        {rows.map((row) => (
          <li key={row.ordem} className={cn("flex", compact ? "gap-1.5" : "gap-2.5")}>
            <span
              className={cn(
                "shrink-0 rounded-full",
                compact ? "mt-1 size-2" : "mt-1.5 size-2.5",
              )}
              style={{ backgroundColor: colorByName[row.nome] ?? "#64748b" }}
              aria-hidden
            />
            <div className="min-w-0">
              <p className={cn("font-medium text-foreground", compact ? "text-[11px]" : "text-xs")}>
                {row.nome}
              </p>
              <p
                className={cn(
                  "leading-snug text-muted-foreground",
                  compact ? "text-[10px]" : "text-[11px]",
                )}
              >
                {row.condicao}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** @deprecated Use QuadrantLegend — mantido para compatibilidade. */
export function QuadrantExplanationTable({
  axisHint,
  rows,
}: {
  axisHint: string;
  rows: QuadrantExplanationRow[];
}) {
  return (
    <div className="mt-4 border-t pt-4">
      <p className="mb-2 text-xs text-muted-foreground">{axisHint}</p>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b text-muted-foreground">
              <th className="pb-2 pr-3 font-medium">Ordem</th>
              <th className="pb-2 pr-3 font-medium">Condição</th>
              <th className="pb-2 font-medium">Nome conceitual</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.ordem} className="border-b border-border/50 last:border-0">
                <td className="py-2 pr-3 font-medium">{row.ordem}</td>
                <td className="py-2 pr-3 text-muted-foreground">{row.condicao}</td>
                <td className={cn("py-2")}>{row.nome}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export type QuadrantExplanationRow = {
  ordem: number;
  condicao: string;
  nome: string;
};

type QuadrantExplanationTableProps = {
  axisHint: string;
  rows: QuadrantExplanationRow[];
};

export function QuadrantExplanationTable({
  axisHint,
  rows,
}: QuadrantExplanationTableProps) {
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
                <td className="py-2">{row.nome}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

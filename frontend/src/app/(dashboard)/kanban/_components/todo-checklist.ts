export const TODO_CHECKLIST_OPTIONS = [
  { value: "documento_revisado", label: "Documento de requisito revisado" },
  { value: "criterios_existem", label: "Critérios de aceitação existentes / compreendidos" },
  { value: "escopo_entendido", label: "Escopo entendido pela equipa" },
  { value: "responsavel_definido", label: "Responsável pelo desenvolvimento definido" },
] as const;

export type TodoChecklistValue = (typeof TODO_CHECKLIST_OPTIONS)[number]["value"];

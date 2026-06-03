import {
  FREQUENCY_OPTIONS,
  URGENCY_OPTIONS,
} from "@/app/(dashboard)/activities/_components/activity-form/options";
import type { ActivityFormData } from "@/lib/activity-form-draft";

function mapDemandType(value: string): string {
  if (value === "bug") return "BUG";
  if (value === "feature" || value === "melhoria") return "INCREMENTO";
  return "NAO_SEI";
}

function labelFor(
  options: { value: string; label: string }[],
  value: string,
): string {
  return options.find((o) => o.value === value)?.label ?? value;
}

export function buildAnaliseRequestBody(form: ActivityFormData) {
  const workaround = form.temporaryWorkaround.trim() || undefined;

  return {
    texto_original: form.description.trim(),
    tipo_informado_usuario: mapDemandType(form.demandType),
    modulo_afetado: form.systemArea.trim() || undefined,
    contexto_negocio: form.businessImportance.trim() || undefined,
    objetivo_desejado: form.expectedResult.trim() || undefined,
    impacto_percebido_usuario: form.perceivedImpact.trim() || undefined,
    frequencia_ocorrencia: labelFor(FREQUENCY_OPTIONS, form.frequency) || undefined,
    urgencia_percebida: labelFor(URGENCY_OPTIONS, form.urgency) || undefined,
    ha_contorno: workaround,
    sistema_ou_produto: form.systemOrProduct.trim() || undefined,
    perfil_solicitante: form.requesterId.trim() || undefined,
  };
}

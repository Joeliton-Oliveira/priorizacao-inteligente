import { describe, expect, it } from "vitest";
import {
  INITIAL_ACTIVITY_FORM_DATA,
  mergePartialFormData,
  parsePersistedDraftJson,
  serializeDraft,
} from "@/lib/activity-form-draft";

describe("activity-form-draft", () => {
  it("mergePartialFormData preenche omissões com valores iniciais", () => {
    const merged = mergePartialFormData({ description: "Teste" });
    expect(merged.description).toBe("Teste");
    expect(merged.demandType).toBe(INITIAL_ACTIVITY_FORM_DATA.demandType);
    expect(merged.projectId).toBe("");
  });

  it("parsePersistedDraftJson retorna null para entrada vazia", () => {
    expect(parsePersistedDraftJson(null)).toBeNull();
    expect(parsePersistedDraftJson("")).toBeNull();
  });

  it("parsePersistedDraftJson restaura formData e step válido", () => {
    const payload = serializeDraft(
      {
        ...INITIAL_ACTIVITY_FORM_DATA,
        description: "Demanda X",
        systemArea: "checkout",
      },
      2
    );
    const parsed = parsePersistedDraftJson(payload);
    expect(parsed).not.toBeNull();
    expect(parsed!.step).toBe(2);
    expect(parsed!.formData.description).toBe("Demanda X");
    expect(parsed!.formData.systemArea).toBe("checkout");
  });

  it("parsePersistedDraftJson corrige step fora do intervalo para 1", () => {
    const raw = JSON.stringify({ formData: { description: "a" }, step: 99 });
    const parsed = parsePersistedDraftJson(raw);
    expect(parsed?.step).toBe(1);
    expect(parsed?.formData.description).toBe("a");
  });

  it("parsePersistedDraftJson retorna null para JSON inválido", () => {
    expect(parsePersistedDraftJson("{não é json")).toBeNull();
  });

  it("serializeDraft e parse são round-trip", () => {
    const data = {
      ...INITIAL_ACTIVITY_FORM_DATA,
      description: "Round trip",
      urgency: "alta",
    };
    const step = 3;
    const again = parsePersistedDraftJson(serializeDraft(data, step));
    expect(again?.formData).toEqual(data);
    expect(again?.step).toBe(step);
  });
});

export interface ActivityFormData {
  description: string;
  demandType: string;
  systemArea: string;
  businessImportance: string;
  expectedResult: string;
  perceivedImpact: string;
  frequency: string;
  urgency: string;
  temporaryWorkaround: string;
  projectId: string;
  requesterId: string;
}

export const ACTIVITY_FORM_STORAGE_KEY = "intelli-reqs:activity-form-draft";
export const MAX_ACTIVITY_FORM_STEP = 3;

export const INITIAL_ACTIVITY_FORM_DATA: ActivityFormData = {
  description: "",
  demandType: "nao_sei",
  systemArea: "",
  businessImportance: "",
  expectedResult: "",
  perceivedImpact: "",
  frequency: "",
  urgency: "",
  temporaryWorkaround: "",
  projectId: "",
  requesterId: "",
};

type PersistedDraft = {
  formData?: Partial<ActivityFormData>;
  step?: number;
};

export function mergePartialFormData(
  partial: Partial<ActivityFormData> | undefined
): ActivityFormData {
  if (!partial || typeof partial !== "object") return { ...INITIAL_ACTIVITY_FORM_DATA };
  return { ...INITIAL_ACTIVITY_FORM_DATA, ...partial };
}

export function parsePersistedDraftJson(
  raw: string | null
): { formData: ActivityFormData; step: number } | null {
  if (raw === null || raw === "") return null;
  try {
    const parsed = JSON.parse(raw) as PersistedDraft;
    const step =
      typeof parsed.step === "number" &&
      parsed.step >= 1 &&
      parsed.step <= MAX_ACTIVITY_FORM_STEP
        ? parsed.step
        : 1;

    return { formData: mergePartialFormData(parsed.formData), step };
  } catch {
    return null;
  }
}

export function serializeDraft(formData: ActivityFormData, step: number): string {
  return JSON.stringify({ formData, step });
}

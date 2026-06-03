import { ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { DEMAND_TYPE_OPTIONS } from "./options";
import type { Dispatch, SetStateAction } from "react";
import type { ActivityFormData } from "@/lib/activity-form-draft";

interface IdentificationStepProps {
  direction: "next" | "prev";
  formData: ActivityFormData;
  setFormData: Dispatch<SetStateAction<ActivityFormData>>;
  canGoNext: boolean;
}

export function IdentificationStep({
  direction,
  formData,
  setFormData,
  canGoNext,
}: IdentificationStepProps) {
  return (
    <Card
      className={`flex shrink-0 flex-col gap-0 overflow-hidden rounded-xl py-4 ${
        direction === "next"
          ? "animate-in fade-in-0 slide-in-from-right-4 duration-300"
          : "animate-in fade-in-0 slide-in-from-left-4 duration-300"
      }`}
    >
      <CardHeader className="shrink-0 px-4 pb-1 pt-0">
        <h2 className="text-base font-semibold">Identificação da Demanda</h2>
      </CardHeader>
      <CardContent className="grid w-full grid-cols-1 content-start gap-y-4 px-4 pb-5 pt-0 sm:grid-cols-2 sm:gap-x-4">
        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor="description" className="text-sm font-medium">
            Descrição inicial da demanda
          </Label>
          <Textarea
            id="description"
            placeholder="Ex.: Quando o cliente tenta finalizar a compra, o botão não responde..."
            value={formData.description}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, description: e.target.value }))
            }
            rows={3}
            maxLength={2000}
            className="min-h-24 max-h-40 resize-y"
          />
        </div>

        <div className="grid w-full grid-cols-1 gap-y-3 sm:col-span-2 sm:grid-cols-[1fr_1fr] sm:gap-x-4">
          <div className="flex min-w-0 flex-col gap-1.5">
            <Label htmlFor="demandType" className="text-sm font-medium">
              Tipo da demanda
            </Label>
            <Select
              value={formData.demandType}
              onValueChange={(value) =>
                setFormData((prev) => ({ ...prev, demandType: value }))
              }
            >
              <SelectTrigger id="demandType" className="h-9 w-full min-w-0">
                <SelectValue placeholder="Não sei informar" />
              </SelectTrigger>
              <SelectContent>
                {DEMAND_TYPE_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex min-w-0 flex-col gap-1.5">
            <Label htmlFor="systemArea" className="text-sm font-medium">
              Área do sistema envolvida
            </Label>
            <Input
              id="systemArea"
              placeholder="Ex.: checkout"
              value={formData.systemArea}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, systemArea: e.target.value }))
              }
              className="h-9 w-full"
            />
          </div>
        </div>

        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor="businessImportance" className="text-sm font-medium">
            Importância dessa área para o negócio
          </Label>
          <Textarea
            id="businessImportance"
            placeholder="Explique por que essa parte é importante..."
            value={formData.businessImportance}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, businessImportance: e.target.value }))
            }
            rows={2}
            maxLength={2000}
            className="min-h-16 max-h-40 resize-y"
          />
        </div>

        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor="expectedResult" className="text-sm font-medium">
            Resultado esperado
          </Label>
          <Textarea
            id="expectedResult"
            placeholder="O que deveria acontecer corretamente?"
            value={formData.expectedResult}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, expectedResult: e.target.value }))
            }
            rows={2}
            maxLength={2000}
            className="min-h-16 max-h-40 resize-y"
          />
        </div>

        <div className="sm:col-span-2">
          <Button
            type="submit"
            size="sm"
            className="h-11 w-full justify-center gap-2 text-sm font-semibold"
            disabled={!canGoNext}
          >
            Próximo
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

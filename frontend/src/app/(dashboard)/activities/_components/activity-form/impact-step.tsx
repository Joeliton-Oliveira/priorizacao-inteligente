import { ChevronLeft, ChevronRight } from "lucide-react";
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
import { FREQUENCY_OPTIONS, URGENCY_OPTIONS } from "./options";
import type { Dispatch, SetStateAction } from "react";
import type { ActivityFormData } from "@/lib/activity-form-draft";

interface ImpactStepProps {
  direction: "next" | "prev";
  formData: ActivityFormData;
  setFormData: Dispatch<SetStateAction<ActivityFormData>>;
  goToStep: (step: number) => void;
}

export function ImpactStep({
  direction,
  formData,
  setFormData,
  goToStep,
}: ImpactStepProps) {
  return (
    <Card
      className={`flex shrink-0 flex-col gap-0 overflow-hidden rounded-xl py-4 ${
        direction === "next"
          ? "animate-in fade-in-0 slide-in-from-right-4 duration-300"
          : "animate-in fade-in-0 slide-in-from-left-4 duration-300"
      }`}
    >
      <CardHeader className="shrink-0 px-4 pb-1 pt-0">
        <h2 className="text-base font-semibold">Impacto e Priorização</h2>
      </CardHeader>
      <CardContent className="grid w-full grid-cols-1 content-start gap-y-4 px-4 pb-5 pt-0 sm:grid-cols-2 sm:gap-x-4">
        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor="perceivedImpact" className="text-sm font-medium">
            Impacto percebido da demanda
          </Label>
          <Input
            id="perceivedImpact"
            placeholder="Descreva o impacto percebido, se houver."
            value={formData.perceivedImpact}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, perceivedImpact: e.target.value }))
            }
            maxLength={2000}
            className="h-9"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="frequency" className="text-sm font-medium">
            Com que frequência isso acontece?
          </Label>
          <Select
            value={formData.frequency}
            onValueChange={(value) =>
              setFormData((prev) => ({ ...prev, frequency: value }))
            }
          >
            <SelectTrigger id="frequency" className="h-9 w-full min-w-0">
              <SelectValue placeholder="Selecione..." />
            </SelectTrigger>
            <SelectContent>
              {FREQUENCY_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="urgency" className="text-sm font-medium">
            Qual a urgência dessa demanda?
          </Label>
          <Select
            value={formData.urgency}
            onValueChange={(value) =>
              setFormData((prev) => ({ ...prev, urgency: value }))
            }
          >
            <SelectTrigger id="urgency" className="h-9 w-full min-w-0">
              <SelectValue placeholder="Selecione..." />
            </SelectTrigger>
            <SelectContent>
              {URGENCY_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor="temporaryWorkaround" className="text-sm font-medium">
            Existe alguma alternativa temporária ou contorno?
          </Label>
          <Textarea
            id="temporaryWorkaround"
            placeholder="Descreva um workaround ou deixe em branco."
            value={formData.temporaryWorkaround}
            onChange={(e) =>
              setFormData((prev) => ({
                ...prev,
                temporaryWorkaround: e.target.value,
              }))
            }
            rows={3}
            maxLength={2000}
            className="min-h-20 max-h-40 resize-y"
          />
        </div>

        <div className="flex w-full gap-3 sm:col-span-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-11 flex-1 justify-center gap-2 text-sm font-semibold"
            onClick={() => goToStep(1)}
          >
            <ChevronLeft className="size-4" />
            Voltar
          </Button>
          <Button
            type="submit"
            size="sm"
            className="h-11 flex-1 justify-center gap-2 text-sm font-semibold"
          >
            Próximo
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

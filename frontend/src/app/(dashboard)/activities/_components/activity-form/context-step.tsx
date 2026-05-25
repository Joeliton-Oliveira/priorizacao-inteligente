import Link from "next/link";
import { ChevronLeft, FolderPlus, Loader2, Sparkles } from "lucide-react";
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
import type { Dispatch, SetStateAction } from "react";
import type { ActivityFormData } from "@/lib/activity-form-draft";

interface ContextStepProps {
  direction: "next" | "prev";
  formData: ActivityFormData;
  setFormData: Dispatch<SetStateAction<ActivityFormData>>;
  projects: { id: string; name: string }[];
  goToStep: (step: number) => void;
  onAnalyzeWithAI: () => void;
  isAnalyzing?: boolean;
}

export function ContextStep({
  direction,
  formData,
  setFormData,
  projects,
  goToStep,
  onAnalyzeWithAI,
  isAnalyzing = false,
}: ContextStepProps) {
  return (
    <Card
      className={`flex shrink-0 flex-col gap-0 overflow-hidden rounded-xl py-4 ${
        direction === "next"
          ? "animate-in fade-in-0 slide-in-from-right-4 duration-300"
          : "animate-in fade-in-0 slide-in-from-left-4 duration-300"
      }`}
    >
      <CardHeader className="shrink-0 px-4 pb-1 pt-0">
        <h2 className="text-base font-semibold">Contexto</h2>
      </CardHeader>
      <CardContent className="grid w-full grid-cols-1 content-start gap-y-4 px-4 pb-5 pt-0 sm:grid-cols-2 sm:gap-x-4">
        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label className="text-sm font-medium">Sistema ou produto relacionado</Label>
          {projects.length === 0 ? (
            <div className="flex flex-col gap-2">
              <p className="text-sm text-muted-foreground">Nenhum projeto cadastrado.</p>
              <Button
                variant="secondary"
                size="sm"
                className="h-11 w-fit font-semibold"
                asChild
              >
                <Link href="/projects">
                  <FolderPlus className="mr-2 size-4" />
                  Cadastrar um novo projeto
                </Link>
              </Button>
            </div>
          ) : (
            <Select
              value={formData.projectId}
              onValueChange={(value) =>
                setFormData((prev) => ({ ...prev, projectId: value }))
              }
            >
              <SelectTrigger className="h-9 w-full min-w-0">
                <SelectValue placeholder="Selecione um projeto..." />
              </SelectTrigger>
              <SelectContent>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    {project.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        <div className="flex flex-col gap-1.5 sm:col-span-2">
          <Label htmlFor="requester" className="text-sm font-medium">
            Quem está solicitando essa demanda?
          </Label>
          <Input
            id="requester"
            placeholder="Ex.: nome ou email do solicitante"
            value={formData.requesterId}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, requesterId: e.target.value }))
            }
            className="h-9"
          />
        </div>

        <div className="flex w-full gap-3 sm:col-span-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-11 flex-1 justify-center gap-2 text-sm font-semibold"
            onClick={() => goToStep(2)}
          >
            <ChevronLeft className="size-4" />
            Voltar
          </Button>
          <Button
            type="button"
            className="h-11 flex-1 justify-center gap-2 text-sm font-semibold"
            size="sm"
            onClick={onAnalyzeWithAI}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Analisando…
              </>
            ) : (
              <>
                <Sparkles className="size-4" />
                Analisar com IA
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

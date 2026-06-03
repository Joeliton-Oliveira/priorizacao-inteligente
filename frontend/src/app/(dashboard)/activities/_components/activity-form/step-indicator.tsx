import { ChevronRight } from "lucide-react";

type Step = { id: number; title: string };

interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
}

export function StepIndicator({ steps, currentStep }: StepIndicatorProps) {
  return (
    <div className="flex shrink-0 items-center gap-1.5">
      {steps.map((step, i) => (
        <div key={step.id} className="flex items-center gap-2">
          <div
            className={`flex size-6 items-center justify-center rounded-full text-sm font-medium transition-colors ${
              currentStep >= step.id
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {step.id}
          </div>
          {i < steps.length - 1 && (
            <ChevronRight className="size-4 text-muted-foreground" />
          )}
        </div>
      ))}
    </div>
  );
}

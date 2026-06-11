"use client";

import { Check, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { FORM_STEPS } from "./options";

type ActivityFormStepperProps = {
  currentStep: number;
  onStepClick: (step: number) => void;
};

export function ActivityFormStepper({
  currentStep,
  onStepClick,
}: ActivityFormStepperProps) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-stretch">
      {FORM_STEPS.map((step, index) => {
        const isActive = step.id === currentStep;
        const isComplete = step.id < currentStep;
        const isPending = step.id > currentStep;

        return (
          <div key={step.id} className="flex min-w-0 flex-1 flex-col gap-3 lg:flex-row lg:items-center">
            <button
              type="button"
              onClick={() => onStepClick(step.id)}
              className={cn(
                "group flex min-w-0 flex-1 flex-col gap-3 rounded-2xl border p-4 text-left transition-all duration-200 sm:flex-row sm:items-start",
                isActive &&
                  "border-violet-500/40 bg-violet-500/10 shadow-md shadow-violet-950/30",
                isComplete &&
                  "cursor-pointer border-emerald-500/30 bg-emerald-500/5 hover:border-emerald-500/50",
                isPending &&
                  "cursor-pointer border-white/[0.08] bg-white/[0.02] hover:border-white/15 hover:bg-white/[0.04]",
              )}
            >
              <div
                className={cn(
                  "flex size-10 shrink-0 items-center justify-center rounded-full text-sm font-semibold transition-colors",
                  isActive && "bg-violet-500 text-white shadow-lg shadow-violet-500/30",
                  isComplete && "bg-emerald-500/90 text-white",
                  isPending && "bg-muted/80 text-muted-foreground",
                )}
              >
                {isComplete ? <Check className="size-5" /> : step.id}
              </div>
              <div className="min-w-0 flex-1 space-y-1">
                <p
                  className={cn(
                    "text-sm font-semibold",
                    isActive && "text-violet-100",
                    isComplete && "text-emerald-100/90",
                    isPending && "text-muted-foreground",
                  )}
                >
                  {step.progressLabel}
                </p>
                <p className="text-xs leading-relaxed text-muted-foreground line-clamp-2 sm:line-clamp-3">
                  {step.description}
                </p>
              </div>
            </button>

            {index < FORM_STEPS.length - 1 ? (
              <div
                className="flex shrink-0 items-center justify-center px-1 lg:px-2"
                aria-hidden
              >
                <ChevronRight className="size-5 rotate-90 text-muted-foreground/50 lg:rotate-0" />
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

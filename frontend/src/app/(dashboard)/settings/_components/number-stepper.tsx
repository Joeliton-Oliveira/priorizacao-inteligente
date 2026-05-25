"use client";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type NumberStepperProps = {
  value: number;
  onChange?: (value: number) => void;
  min?: number;
  max?: number;
  /** Somente leitura: valor exibido, sem edição (ex.: complemento de 100%). */
  readOnly?: boolean;
  disabled?: boolean;
  className?: string;
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

export function NumberStepper({
  value,
  onChange,
  min = 0,
  max = 100,
  readOnly = false,
  disabled = false,
  className,
}: NumberStepperProps) {
  const isLocked = readOnly || disabled;

  const setValue = (next: number) => {
    if (isLocked || !onChange) return;
    onChange(clamp(next, min, max));
  };

  return (
    <Input
      type="number"
      min={min}
      max={max}
      value={value}
      readOnly={readOnly}
      disabled={disabled && !readOnly}
      aria-readonly={readOnly || undefined}
      onChange={(event) => {
        const parsed = Number.parseInt(event.target.value, 10);
        if (!Number.isNaN(parsed)) setValue(parsed);
      }}
      onBlur={() => setValue(value)}
      className={cn(
        "h-9 w-24 [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none",
        readOnly && "cursor-default bg-muted text-muted-foreground",
        disabled && !readOnly && "bg-muted",
        className,
      )}
    />
  );
}

"use client";

import { useEffect, useState } from "react";
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

function sanitizeDigits(raw: string) {
  return raw.replace(/\D/g, "");
}

/** Limita o texto digitado ao intervalo [min, max] (ex.: 0–100). */
function digitsWithinRange(digits: string, min: number, max: number): string {
  if (digits === "") return "";
  const parsed = Number.parseInt(digits, 10);
  if (Number.isNaN(parsed)) return "";
  if (parsed > max) return String(max);
  if (parsed < min && digits.length >= String(min).length) return String(min);
  return digits;
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
  const [isEditing, setIsEditing] = useState(false);
  const [text, setText] = useState(String(value));

  useEffect(() => {
    if (!isEditing) {
      setText(String(value));
    }
  }, [value, isEditing]);

  const commit = (raw: string) => {
    const digits = sanitizeDigits(raw);
    if (digits === "") {
      const fallback = clamp(value, min, max);
      setText(String(fallback));
      onChange?.(fallback);
      return;
    }
    const parsed = Number.parseInt(digits, 10);
    if (Number.isNaN(parsed)) return;
    const next = clamp(parsed, min, max);
    setText(String(next));
    onChange?.(next);
  };

  const maxLength =
    max !== undefined && Number.isFinite(max) && max >= 0
      ? String(Math.floor(max)).length
      : undefined;

  return (
    <Input
      type="text"
      inputMode="numeric"
      autoComplete="off"
      maxLength={maxLength}
      value={text}
      readOnly={readOnly}
      disabled={disabled && !readOnly}
      aria-readonly={readOnly || undefined}
      aria-valuemin={min}
      aria-valuemax={max}
      onFocus={() => {
        if (!isLocked) setIsEditing(true);
      }}
      onChange={(event) => {
        if (isLocked || !onChange) return;
        const digits = digitsWithinRange(sanitizeDigits(event.target.value), min, max);
        setText(digits);
        if (digits === "") return;
        const parsed = Number.parseInt(digits, 10);
        if (!Number.isNaN(parsed)) {
          onChange(clamp(parsed, min, max));
        }
      }}
      onBlur={() => {
        setIsEditing(false);
        if (!isLocked) commit(text);
      }}
      className={cn(
        "h-9 w-24 [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none",
        readOnly && "cursor-default bg-muted text-muted-foreground",
        disabled && !readOnly && "bg-muted",
        className,
      )}
    />
  );
}

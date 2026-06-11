"use client";

import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function FormSection({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "rounded-2xl border border-white/[0.08] bg-white/[0.02] p-4 shadow-sm shadow-black/10 sm:p-5",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function FormField({
  label,
  htmlFor,
  hint,
  icon: Icon,
  children,
  className,
}: {
  label: string;
  htmlFor?: string;
  hint?: string;
  icon?: LucideIcon;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("space-y-2", className)}>
      <div className="space-y-1">
        <Label htmlFor={htmlFor} className="text-sm font-medium text-foreground">
          {label}
        </Label>
        {hint ? <p className="text-xs leading-relaxed text-muted-foreground">{hint}</p> : null}
      </div>
      {Icon ? (
        <div className="relative">
          <Icon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <div className="[&_[data-slot=input]]:pl-9 [&_[data-slot=select-trigger]]:pl-9">
            {children}
          </div>
        </div>
      ) : (
        children
      )}
    </div>
  );
}

const DEFAULT_MAX_CHARS = 2000;

export function FormTextareaWithCounter({
  id,
  value,
  onChange,
  placeholder,
  maxLength = DEFAULT_MAX_CHARS,
  minHeightClass = "min-h-[140px]",
  className,
}: {
  id: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  maxLength?: number;
  minHeightClass?: string;
  className?: string;
}) {
  const length = value.length;

  return (
    <div className={cn("relative", className)}>
      <Textarea
        id={id}
        value={value}
        maxLength={maxLength}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className={cn(
          "rounded-xl border-white/10 bg-black/20 pb-8 text-sm leading-relaxed transition-colors",
          "focus-visible:border-violet-500/50 focus-visible:ring-violet-500/20",
          minHeightClass,
        )}
      />
      <span className="pointer-events-none absolute right-3 bottom-2.5 text-[11px] tabular-nums text-muted-foreground">
        {length}/{maxLength}
      </span>
    </div>
  );
}

export const formControlClassName =
  "h-10 rounded-xl border-white/10 bg-black/20 transition-colors hover:border-white/20 focus-visible:border-violet-500/50 focus-visible:ring-violet-500/20";

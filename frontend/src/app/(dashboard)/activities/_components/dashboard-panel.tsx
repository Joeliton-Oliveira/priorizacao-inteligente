"use client";

import { Info } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function DashboardPanel({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl border border-white/10 bg-card/70 shadow-xl shadow-black/25 ring-1 ring-white/5 backdrop-blur-sm",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function DashboardPanelHeader({
  title,
  infoText,
  className,
}: {
  title: string;
  infoText?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 border-b border-white/[0.06] bg-white/[0.02] px-5 py-4",
        className,
      )}
    >
      <h3 className="text-base font-semibold tracking-tight">{title}</h3>
      {infoText ? (
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              className="flex size-7 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-muted-foreground transition-colors hover:bg-white/[0.08] hover:text-foreground"
              aria-label={`Informações sobre ${title}`}
            >
              <Info className="size-3.5" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="left" className="max-w-xs text-xs leading-relaxed">
            {infoText}
          </TooltipContent>
        </Tooltip>
      ) : null}
    </div>
  );
}

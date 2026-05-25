"use client";

import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

type NumberedListFieldProps = {
  label: string;
  items: string[];
  onChange: (items: string[]) => void;
  addButtonLabel: string;
};

export function NumberedListField({
  label,
  items,
  onChange,
  addButtonLabel,
}: NumberedListFieldProps) {
  const updateItem = (index: number, value: string) => {
    const next = [...items];
    next[index] = value;
    onChange(next);
  };

  const removeItem = (index: number) => {
    if (items.length <= 1) {
      onChange([""]);
      return;
    }
    onChange(items.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-2">
      <Label className="text-sm font-semibold">{label}</Label>
      <div className="space-y-2">
        {items.map((item, index) => (
          <div key={index} className="flex gap-2">
            <span className="pt-2 text-sm text-muted-foreground">{index + 1}.</span>
            <div className="relative flex-1">
              <Textarea
                value={item}
                onChange={(event) => updateItem(index, event.target.value)}
                className="min-h-[88px] pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-1 top-1 size-7 text-muted-foreground hover:text-foreground"
                onClick={() => removeItem(index)}
                aria-label={`Remover item ${index + 1}`}
              >
                <X className="size-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="text-primary"
        onClick={() => onChange([...items, ""])}
      >
        {addButtonLabel}
      </Button>
    </div>
  );
}

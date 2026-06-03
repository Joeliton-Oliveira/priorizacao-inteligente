"use client";

import { useMemo, useState } from "react";
import { X } from "lucide-react";
import { CustomModal } from "@/components/ui/CustomModal";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

type NumberedListFieldProps = {
  label: string;
  items: string[];
  onChange: (items: string[]) => void;
  addButtonLabel: string;
  tagMode?: boolean;
};

export function NumberedListField({
  label,
  items,
  onChange,
  addButtonLabel,
  tagMode = false,
}: NumberedListFieldProps) {
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editorValue, setEditorValue] = useState("");

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

  const normalizedTags = useMemo(
    () =>
      items
        .map((item, index) => ({ index, text: item.trim() }))
        .filter((item) => item.text.length > 0),
    [items],
  );

  const openEditor = (index: number | null) => {
    setEditingIndex(index);
    setEditorValue(index === null ? "" : (items[index] ?? ""));
    setEditorOpen(true);
  };

  const saveEditor = () => {
    const value = editorValue.trim();
    if (!value) {
      setEditorOpen(false);
      setEditingIndex(null);
      setEditorValue("");
      return;
    }

    if (editingIndex === null) {
      const next = [...items.filter((item) => item.trim().length > 0), value];
      onChange(next);
    } else {
      updateItem(editingIndex, value);
    }

    setEditorOpen(false);
    setEditingIndex(null);
    setEditorValue("");
  };

  if (tagMode) {
    return (
      <div className="space-y-2">
        <Label className="text-sm font-semibold">{label}</Label>
        <div className="space-y-2">
          {normalizedTags.length === 0 ? (
            <p className="text-sm text-muted-foreground">Sem itens adicionados.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {normalizedTags.map((tag, idx) => (
                <div
                  key={`${tag.index}-${idx}`}
                  className="group flex max-w-full items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-2.5 py-1.5"
                  title={tag.text}
                  onDoubleClick={() => openEditor(tag.index)}
                >
                  <span className="text-xs font-semibold text-muted-foreground">{idx + 1}.</span>
                  <span className="max-w-[240px] truncate text-sm">{tag.text}</span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="size-6 text-muted-foreground hover:text-foreground"
                    onClick={() => removeItem(tag.index)}
                    aria-label={`Remover item ${idx + 1}`}
                  >
                    <X className="size-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="text-primary"
          onClick={() => openEditor(null)}
        >
          {addButtonLabel}
        </Button>

        <CustomModal
          open={editorOpen}
          onOpenChange={(open) => {
            setEditorOpen(open);
            if (!open) {
              setEditingIndex(null);
              setEditorValue("");
            }
          }}
          title={editingIndex === null ? "Adicionar requisito" : "Editar requisito"}
          description="Dica: dê duplo clique em uma tag para editar rapidamente."
          contentClassName="max-w-lg sm:max-w-lg"
        >
          <div className="space-y-3">
            <Textarea
              value={editorValue}
              onChange={(event) => setEditorValue(event.target.value)}
              className="min-h-[140px]"
              placeholder="Digite o requisito..."
              autoFocus
            />
            <div className="flex w-full flex-col gap-2 sm:flex-row">
              <Button type="button" variant="outline" className="w-full sm:flex-1" onClick={() => setEditorOpen(false)}>
                Cancelar
              </Button>
              <Button type="button" className="w-full sm:flex-1" onClick={saveEditor}>
                Salvar requisito
              </Button>
            </div>
          </div>
        </CustomModal>
      </div>
    );
  }

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

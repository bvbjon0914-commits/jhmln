import { Check, Info } from "lucide-react";
import type { RequestType } from "../types/matching";
import { TIER0_TYPE_IDS } from "../types/sequencing";

interface Props {
  types: RequestType[];
  selected: string[];
  onChange: (ids: string[]) => void;
  hints?: Record<string, string>;
}

export function RequestTypeSelector({ types, selected, onChange, hints = {} }: Props) {
  const toggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  const addTier0 = () => {
    onChange([...selected, ...TIER0_TYPE_IDS.filter((id) => !selected.includes(id))]);
  };

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-ink">
          Benötigte Auskünfte
        </h3>
        <div className="flex gap-3 text-xs">
          <button
            onClick={() => onChange(types.map((t) => t.request_type_id))}
            className="text-brand hover:underline"
          >
            Alle auswählen
          </button>
          <button
            onClick={() => onChange([])}
            className="text-ink-faint hover:underline"
          >
            Auswahl löschen
          </button>
        </div>
      </div>

      {types.length === 0 ? (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-[52px] animate-pulse rounded-lg border border-line bg-paper/60"
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {types.map((type) => {
            const isSelected = selected.includes(type.request_type_id);
            const hint = hints[type.request_type_id];
            return (
              <div key={type.request_type_id}>
                <button
                  onClick={() => toggle(type.request_type_id)}
                  aria-pressed={isSelected}
                  className={`flex w-full items-center gap-3 rounded-lg border px-3.5 py-3 text-left text-sm transition-all duration-150 ${
                    isSelected
                      ? "border-brand bg-brand-light/50 text-ink shadow-sm"
                      : "border-line bg-surface text-ink-soft hover:border-brand/40 hover:shadow-sm"
                  }`}
                >
                  <span
                    className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-colors duration-150 ${
                      isSelected
                        ? "border-brand bg-brand text-white"
                        : "border-line bg-surface"
                    }`}
                  >
                    {isSelected && <Check size={13} strokeWidth={3} />}
                  </span>
                  {type.name}
                </button>
                {hint && (
                  <div className="mt-1.5 flex items-start gap-1.5 px-1 text-[11px] text-ink-faint">
                    <Info size={12} className="mt-0.5 shrink-0" />
                    <span>
                      {hint}{" "}
                      <button
                        onClick={addTier0}
                        className="font-medium text-brand hover:underline"
                      >
                        + Grundbuch/Kataster mit auswählen
                      </button>
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

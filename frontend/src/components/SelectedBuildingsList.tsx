import { Building2, X } from "lucide-react";
import type { Building } from "../types/building";

interface Props {
  buildings: Building[];
  onRemove: (buildingId: string) => void;
}

export function SelectedBuildingsList({ buildings, onRemove }: Props) {
  if (buildings.length === 0) return null;

  return (
    <div className="space-y-1.5">
      {buildings.map((b) => (
        <div
          key={b.building_id}
          className="flex items-center justify-between gap-3 rounded-md border border-line bg-surface px-3.5 py-2.5"
        >
          <div className="flex items-center gap-2.5 overflow-hidden">
            <Building2 size={15} className="shrink-0 text-brand" />
            <div className="truncate text-sm">
              <span className="text-ink">
                {b.street} {b.house_number}
              </span>
              <span className="ml-2 text-ink-faint">
                {b.postal_code} {b.city}
              </span>
              {b.ags ? (
                <span className="ml-2 font-mono text-xs text-ink-faint">AGS {b.ags}</span>
              ) : (
                <span className="ml-2 text-xs text-status-review">kein AGS</span>
              )}
            </div>
          </div>
          <button
            onClick={() => onRemove(b.building_id)}
            className="shrink-0 rounded p-1 text-ink-faint hover:bg-status-conflictBg hover:text-status-conflict"
            aria-label="Entfernen"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}

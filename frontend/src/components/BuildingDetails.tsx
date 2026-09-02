import { useEffect, useState } from "react";
import { MapPin, Hash, Layers, StickyNote, History } from "lucide-react";
import type { Building } from "../types/building";
import { api } from "../services/api";

export function BuildingDetails({ building }: { building: Building }) {
  const [history, setHistory] = useState<{ total: number; lastCreatedAt: string | null } | null>(
    null
  );

  useEffect(() => {
    setHistory(null);
    api
      .listRequestsPaged({ building_id: building.building_id, limit: 1, offset: 0 })
      .then((res) =>
        setHistory({
          total: res.total,
          lastCreatedAt: res.items[0]?.created_at ?? null,
        })
      )
      .catch(() => setHistory({ total: 0, lastCreatedAt: null }));
  }, [building.building_id]);

  return (
    <div className="rounded-lg border border-line bg-surface p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <div className="font-display text-lg font-semibold text-ink">
            {building.street} {building.house_number}
          </div>
          <div className="mt-0.5 flex items-center gap-1.5 text-sm text-ink-soft">
            <MapPin size={14} />
            {building.postal_code} {building.city}
            {building.district && <span>· {building.district}</span>}
          </div>
        </div>
        {building.property_name && (
          <span className="rounded bg-brand-light px-2.5 py-1 text-xs font-medium text-brand-dark">
            {building.property_name}
          </span>
        )}
      </div>

      {history && (
        <div className="mt-3 flex items-center gap-1.5 text-xs text-ink-faint">
          <History size={13} />
          {history.total === 0 ? (
            <span>Noch keine Anfragen für dieses Gebäude</span>
          ) : (
            <span>
              {history.total} {history.total === 1 ? "Anfrage" : "Anfragen"} bisher
              {history.lastCreatedAt && (
                <>
                  {" "}
                  · zuletzt am{" "}
                  {new Date(history.lastCreatedAt).toLocaleString("de-DE", {
                    dateStyle: "medium",
                    timeStyle: "short",
                  })}
                </>
              )}
            </span>
          )}
        </div>
      )}

      <div className="mt-4 grid grid-cols-2 gap-4 border-t border-line pt-4 sm:grid-cols-4">
        <Field icon={<Hash size={13} />} label="Objekt-ID" value={building.building_id} mono />
        <Field
          icon={<Hash size={13} />}
          label="Interne Referenz"
          value={building.internal_reference || "—"}
          mono
        />
        <Field icon={<Layers size={13} />} label="AGS" value={building.ags || "—"} mono />
        <Field icon={<MapPin size={13} />} label="Bundesland" value={building.state || "—"} />
      </div>

      {building.notes && (
        <div className="mt-4 border-t border-line pt-4">
          <div className="flex items-center gap-1 text-[11px] uppercase tracking-wide text-ink-faint">
            <StickyNote size={13} />
            Notizen
          </div>
          <div className="mt-0.5 text-sm text-ink-soft">{building.notes}</div>
        </div>
      )}
    </div>
  );
}

function Field({
  icon,
  label,
  value,
  mono,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <div className="flex items-center gap-1 text-[11px] uppercase tracking-wide text-ink-faint">
        {icon}
        {label}
      </div>
      <div className={`mt-0.5 text-sm text-ink ${mono ? "font-mono" : ""}`}>{value}</div>
    </div>
  );
}

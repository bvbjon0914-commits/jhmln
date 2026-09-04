import { useEffect, useRef, useState } from "react";
import { Search, Pencil, Trash2, Check, X, Loader2, ListTree } from "lucide-react";
import { api } from "../../services/api";
import { useToast, errorMessage } from "../common/Toast";
import { Pagination } from "../common/Pagination";
import { FilterChip } from "../common/FilterChip";
import { GERMAN_STATES } from "../../types/germanStates";
import type { Building, BuildingUpdateInput } from "../../types/building";
import type { AdminFilterRequest } from "../../types/adminFilter";

const LIMIT = 25;

export function BuildingsAdmin({
  initialFilter,
  onShowRequests,
}: {
  initialFilter?: AdminFilterRequest | null;
  onShowRequests?: (buildingId: string) => void;
} = {}) {
  const { showToast } = useToast();
  const [search, setSearch] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [missingAgsOnly, setMissingAgsOnly] = useState(false);
  const [duplicateOnly, setDuplicateOnly] = useState(false);
  const [reviewRequiredOnly, setReviewRequiredOnly] = useState(false);
  const [offset, setOffset] = useState(0);
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<BuildingUpdateInput>({});
  const [saving, setSaving] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (initialFilter?.key === "missing_ags") setMissingAgsOnly(true);
    else if (initialFilter?.key === "duplicate") setDuplicateOnly(true);
    else if (initialFilter?.key === "review_required") setReviewRequiredOnly(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const load = () => {
    setLoading(true);
    api
      .listBuildingsPaged({
        search: search || undefined,
        state: stateFilter || undefined,
        missing_ags: missingAgsOnly || undefined,
        duplicate_only: duplicateOnly || undefined,
        review_required_only: reviewRequiredOnly || undefined,
        limit: LIMIT,
        offset,
      })
      .then((res) => {
        setBuildings(res.items);
        setTotal(res.total);
      })
      .catch((error) => showToast("error", errorMessage(error, "Gebäude konnten nicht geladen werden.")))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(load, 250);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, stateFilter, missingAgsOnly, duplicateOnly, reviewRequiredOnly, offset]);

  const startEdit = (b: Building) => {
    setEditingId(b.building_id);
    setEditForm({
      street: b.street,
      house_number: b.house_number,
      postal_code: b.postal_code,
      city: b.city,
      state: b.state,
      ags: b.ags,
      property_name: b.property_name,
      internal_reference: b.internal_reference,
    });
  };

  const saveEdit = async (buildingId: string) => {
    setSaving(true);
    try {
      await api.updateBuilding(buildingId, editForm);
      showToast("success", "Gebäude aktualisiert.");
      setEditingId(null);
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Gebäude konnte nicht aktualisiert werden."));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (b: Building) => {
    if (!window.confirm(`"${b.street} ${b.house_number}, ${b.city}" wirklich löschen? Zugehörige Anfragen werden mitgelöscht.`)) {
      return;
    }
    try {
      await api.deleteBuilding(b.building_id);
      showToast("success", "Gebäude gelöscht.");
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Gebäude konnte nicht gelöscht werden."));
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
          <input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setOffset(0);
            }}
            placeholder="Straße, Ort, PLZ, Referenz suchen…"
            className="w-full rounded-lg border border-line bg-surface py-2.5 pl-9 pr-4 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>
        <select
          value={stateFilter}
          onChange={(e) => {
            setStateFilter(e.target.value);
            setOffset(0);
          }}
          className="rounded-lg border border-line bg-surface px-3 py-2.5 text-sm focus:border-brand focus:outline-none"
        >
          <option value="">Alle Bundesländer</option>
          {GERMAN_STATES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-wrap gap-1.5">
        <FilterChip
          active={missingAgsOnly}
          onClick={() => {
            setMissingAgsOnly((v) => !v);
            setOffset(0);
          }}
        >
          Ohne AGS
        </FilterChip>
        <FilterChip
          active={duplicateOnly}
          onClick={() => {
            setDuplicateOnly((v) => !v);
            setOffset(0);
          }}
        >
          Duplikate
        </FilterChip>
        <FilterChip
          active={reviewRequiredOnly}
          onClick={() => {
            setReviewRequiredOnly((v) => !v);
            setOffset(0);
          }}
        >
          Prüfung nötig
        </FilterChip>
      </div>

      <div className="overflow-hidden rounded-lg border border-line bg-surface shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-line bg-paper/50 text-left text-[11px] uppercase tracking-wide text-ink-faint">
                <th className="px-4 py-2.5 font-medium">Adresse</th>
                <th className="px-4 py-2.5 font-medium">AGS</th>
                <th className="px-4 py-2.5 font-medium">Objektname</th>
                <th className="w-24 px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-ink-faint">
                    <Loader2 size={16} className="mx-auto animate-spin" />
                  </td>
                </tr>
              ) : buildings.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-ink-faint">
                    Keine Gebäude gefunden.
                  </td>
                </tr>
              ) : (
                buildings.map((b) =>
                  editingId === b.building_id ? (
                    <tr key={b.building_id} className="border-b border-line bg-paper/30 last:border-0">
                      <td colSpan={4} className="px-4 py-3">
                        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                          <input
                            value={editForm.street ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, street: e.target.value }))}
                            placeholder="Straße"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.house_number ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, house_number: e.target.value }))}
                            placeholder="Nr."
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.postal_code ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, postal_code: e.target.value }))}
                            placeholder="PLZ"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.city ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, city: e.target.value }))}
                            placeholder="Ort"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.ags ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, ags: e.target.value }))}
                            placeholder="AGS"
                            maxLength={8}
                            className="rounded border border-line px-2 py-1.5 font-mono text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.state ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, state: e.target.value }))}
                            placeholder="Bundesland"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.property_name ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, property_name: e.target.value }))}
                            placeholder="Objektname"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.internal_reference ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, internal_reference: e.target.value }))}
                            placeholder="Interne Referenz"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                        </div>
                        <div className="mt-2 flex gap-2">
                          <button
                            onClick={() => saveEdit(b.building_id)}
                            disabled={saving}
                            className="inline-flex items-center gap-1 rounded bg-brand px-2.5 py-1.5 text-xs font-medium text-white hover:bg-brand-dark disabled:opacity-50"
                          >
                            {saving ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
                            Speichern
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="inline-flex items-center gap-1 rounded border border-line px-2.5 py-1.5 text-xs font-medium text-ink-soft hover:border-ink-faint"
                          >
                            <X size={12} />
                            Abbrechen
                          </button>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    <tr key={b.building_id} className="border-b border-line last:border-0 hover:bg-paper/30">
                      <td className="px-4 py-2.5">
                        <div className="text-ink">
                          {b.street} {b.house_number}
                        </div>
                        <div className="text-xs text-ink-faint">
                          {b.postal_code} {b.city}
                        </div>
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs text-ink-soft">{b.ags || "—"}</td>
                      <td className="px-4 py-2.5 text-ink-soft">{b.property_name || "—"}</td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center justify-end gap-1">
                          {onShowRequests && (
                            <button
                              onClick={() => onShowRequests(b.building_id)}
                              className="rounded p-1.5 text-ink-faint hover:bg-brand-light/50 hover:text-brand"
                              aria-label="Anfragen anzeigen"
                              title="Anfragen anzeigen"
                            >
                              <ListTree size={14} />
                            </button>
                          )}
                          <button
                            onClick={() => startEdit(b)}
                            className="rounded p-1.5 text-ink-faint hover:bg-brand-light/50 hover:text-brand"
                            aria-label="Bearbeiten"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(b)}
                            className="rounded p-1.5 text-ink-faint hover:bg-status-conflictBg hover:text-status-conflict"
                            aria-label="Löschen"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                )
              )}
            </tbody>
          </table>
        </div>
        <Pagination offset={offset} limit={LIMIT} total={total} onOffsetChange={setOffset} />
      </div>
    </div>
  );
}

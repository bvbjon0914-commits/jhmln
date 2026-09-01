import { useEffect, useRef, useState } from "react";
import { Search, Pencil, Trash2, Check, X, Loader2 } from "lucide-react";
import { api } from "../../services/api";
import { useToast, errorMessage } from "../common/Toast";
import { Pagination } from "../common/Pagination";
import type { Jurisdiction, JurisdictionUpdateInput } from "../../types/jurisdiction";
import type { Authority } from "../../types/authority";
import type { RequestType } from "../../types/matching";

const LIMIT = 25;

export function JurisdictionsAdmin() {
  const { showToast } = useToast();
  const [requestTypes, setRequestTypes] = useState<RequestType[]>([]);
  const [requestTypeId, setRequestTypeId] = useState("");
  const [agsFilter, setAgsFilter] = useState("");
  const [showInactive, setShowInactive] = useState(false);
  const [offset, setOffset] = useState(0);
  const [jurisdictions, setJurisdictions] = useState<Jurisdiction[]>([]);
  const [authorities, setAuthorities] = useState<Record<string, Authority>>({});
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<JurisdictionUpdateInput>({});
  const [saving, setSaving] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api.listRequestTypes().then(setRequestTypes).catch(() => undefined);
  }, []);

  const load = () => {
    setLoading(true);
    api
      .listJurisdictionsPaged({
        request_type_id: requestTypeId || undefined,
        ags: agsFilter || undefined,
        active_only: !showInactive,
        limit: LIMIT,
        offset,
      })
      .then((res) => {
        setJurisdictions(res.items);
        setTotal(res.total);
        const ids = [...new Set(res.items.map((j) => j.authority_id))];
        if (ids.length > 0) {
          api
            .getAuthorities(ids)
            .then((list) => {
              const map: Record<string, Authority> = {};
              list.forEach((a) => (map[a.authority_id] = a));
              setAuthorities(map);
            })
            .catch(() => undefined);
        }
      })
      .catch((error) => showToast("error", errorMessage(error, "Zuständigkeiten konnten nicht geladen werden.")))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(load, 250);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestTypeId, agsFilter, showInactive, offset]);

  const startEdit = (j: Jurisdiction) => {
    setEditingId(j.jurisdiction_id);
    setEditForm({ ags: j.ags, municipality: j.municipality, priority: j.priority, active: j.active });
  };

  const saveEdit = async (jurisdictionId: string) => {
    setSaving(true);
    try {
      await api.updateJurisdiction(jurisdictionId, editForm);
      showToast("success", "Zuständigkeitsregel aktualisiert.");
      setEditingId(null);
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Regel konnte nicht aktualisiert werden."));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (j: Jurisdiction) => {
    if (!window.confirm("Diese Zuständigkeitsregel wirklich löschen?")) return;
    try {
      await api.deleteJurisdiction(j.jurisdiction_id);
      showToast("success", "Regel gelöscht.");
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Regel konnte nicht gelöscht werden."));
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <select
          value={requestTypeId}
          onChange={(e) => {
            setRequestTypeId(e.target.value);
            setOffset(0);
          }}
          className="rounded-lg border border-line bg-surface px-3 py-2.5 text-sm focus:border-brand focus:outline-none"
        >
          <option value="">Alle Auskunftsarten</option>
          {requestTypes.map((t) => (
            <option key={t.request_type_id} value={t.request_type_id}>
              {t.name}
            </option>
          ))}
        </select>
        <div className="relative flex-1">
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
          <input
            value={agsFilter}
            onChange={(e) => {
              setAgsFilter(e.target.value);
              setOffset(0);
            }}
            placeholder="AGS (Präfix)…"
            className="w-full rounded-lg border border-line bg-surface py-2.5 pl-9 pr-4 font-mono text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>
        <label className="flex items-center gap-1.5 whitespace-nowrap text-xs text-ink-soft">
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => {
              setShowInactive(e.target.checked);
              setOffset(0);
            }}
          />
          auch inaktive anzeigen
        </label>
      </div>

      <div className="overflow-hidden rounded-lg border border-line bg-surface shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-line bg-paper/50 text-left text-[11px] uppercase tracking-wide text-ink-faint">
                <th className="px-4 py-2.5 font-medium">Auskunftsart</th>
                <th className="px-4 py-2.5 font-medium">AGS / Gemeinde</th>
                <th className="px-4 py-2.5 font-medium">Behörde</th>
                <th className="px-4 py-2.5 font-medium">Priorität</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="w-20 px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-ink-faint">
                    <Loader2 size={16} className="mx-auto animate-spin" />
                  </td>
                </tr>
              ) : jurisdictions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-ink-faint">
                    Keine Zuständigkeitsregeln gefunden.
                  </td>
                </tr>
              ) : (
                jurisdictions.map((j) =>
                  editingId === j.jurisdiction_id ? (
                    <tr key={j.jurisdiction_id} className="border-b border-line bg-paper/30 last:border-0">
                      <td colSpan={6} className="px-4 py-3">
                        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                          <input
                            value={editForm.ags ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, ags: e.target.value }))}
                            placeholder="AGS"
                            maxLength={8}
                            className="rounded border border-line px-2 py-1.5 font-mono text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.municipality ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, municipality: e.target.value }))}
                            placeholder="Gemeinde"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            type="number"
                            value={editForm.priority ?? 40}
                            onChange={(e) => setEditForm((f) => ({ ...f, priority: Number(e.target.value) }))}
                            placeholder="Priorität"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <label className="flex items-center gap-1.5 text-sm text-ink-soft">
                            <input
                              type="checkbox"
                              checked={editForm.active ?? true}
                              onChange={(e) => setEditForm((f) => ({ ...f, active: e.target.checked }))}
                            />
                            Aktiv
                          </label>
                        </div>
                        <div className="mt-2 flex gap-2">
                          <button
                            onClick={() => saveEdit(j.jurisdiction_id)}
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
                    <tr key={j.jurisdiction_id} className="border-b border-line last:border-0 hover:bg-paper/30">
                      <td className="px-4 py-2.5 text-ink">
                        {requestTypes.find((t) => t.request_type_id === j.request_type_id)?.name ||
                          j.request_type_id}
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="font-mono text-xs text-ink-soft">{j.ags || "—"}</div>
                        {j.municipality && <div className="text-xs text-ink-faint">{j.municipality}</div>}
                      </td>
                      <td className="px-4 py-2.5 text-ink-soft">
                        {authorities[j.authority_id]?.authority_name || j.authority_id}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs text-ink-faint">{j.priority}</td>
                      <td className="px-4 py-2.5">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                            j.active
                              ? "bg-status-matchedBg text-status-matched"
                              : "bg-status-neutralBg text-status-neutral"
                          }`}
                        >
                          {j.active ? "Aktiv" : "Inaktiv"}
                        </span>
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => startEdit(j)}
                            className="rounded p-1.5 text-ink-faint hover:bg-brand-light/50 hover:text-brand"
                            aria-label="Bearbeiten"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(j)}
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

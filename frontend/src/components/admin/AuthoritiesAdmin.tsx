import { useEffect, useRef, useState } from "react";
import { Search, Pencil, Trash2, Check, X, Loader2, Ban, CheckCircle2, ListTree } from "lucide-react";
import { api } from "../../services/api";
import { useToast, errorMessage } from "../common/Toast";
import { Pagination } from "../common/Pagination";
import { FilterChip } from "../common/FilterChip";
import { GERMAN_STATES } from "../../types/germanStates";
import type { Authority, AuthorityUpdateInput } from "../../types/authority";
import type { AdminFilterRequest } from "../../types/adminFilter";

const LIMIT = 25;

export function AuthoritiesAdmin({
  initialFilter,
  onShowJurisdictions,
}: {
  initialFilter?: AdminFilterRequest | null;
  onShowJurisdictions?: (authorityId: string) => void;
} = {}) {
  const { showToast } = useToast();
  const [search, setSearch] = useState("");
  const [showInactive, setShowInactive] = useState(false);
  const [stateFilter, setStateFilter] = useState("");
  const [withoutEmailOnly, setWithoutEmailOnly] = useState(false);
  const [withoutJurisdictionOnly, setWithoutJurisdictionOnly] = useState(false);
  const [withoutAddressOnly, setWithoutAddressOnly] = useState(false);
  const [duplicateOnly, setDuplicateOnly] = useState(false);
  const [unverifiedOnly, setUnverifiedOnly] = useState(false);
  const [offset, setOffset] = useState(0);
  const [authorities, setAuthorities] = useState<Authority[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<AuthorityUpdateInput>({});
  const [saving, setSaving] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (initialFilter?.key === "without_email") setWithoutEmailOnly(true);
    else if (initialFilter?.key === "without_jurisdiction") setWithoutJurisdictionOnly(true);
    else if (initialFilter?.key === "without_address") setWithoutAddressOnly(true);
    else if (initialFilter?.key === "duplicate") setDuplicateOnly(true);
    else if (initialFilter?.key === "unverified") setUnverifiedOnly(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const load = () => {
    setLoading(true);
    api
      .listAuthoritiesPaged({
        search: search || undefined,
        active_only: !showInactive,
        state: stateFilter || undefined,
        has_email: withoutEmailOnly ? false : undefined,
        without_jurisdiction_only: withoutJurisdictionOnly || undefined,
        without_address_only: withoutAddressOnly || undefined,
        duplicate_only: duplicateOnly || undefined,
        unverified_only: unverifiedOnly || undefined,
        limit: LIMIT,
        offset,
      })
      .then((res) => {
        setAuthorities(res.items);
        setTotal(res.total);
      })
      .catch((error) => showToast("error", errorMessage(error, "Behörden konnten nicht geladen werden.")))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(load, 250);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    search,
    showInactive,
    stateFilter,
    withoutEmailOnly,
    withoutJurisdictionOnly,
    withoutAddressOnly,
    duplicateOnly,
    unverifiedOnly,
    offset,
  ]);

  const startEdit = (a: Authority) => {
    setEditingId(a.authority_id);
    setEditForm({
      authority_name: a.authority_name,
      department_name: a.department_name,
      street: a.street,
      house_number: a.house_number,
      postal_code: a.postal_code,
      city: a.city,
      state: a.state,
      email: a.email,
      phone: a.phone,
      website: a.website,
    });
  };

  const saveEdit = async (authorityId: string) => {
    setSaving(true);
    try {
      await api.updateAuthority(authorityId, editForm);
      showToast("success", "Behörde aktualisiert.");
      setEditingId(null);
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Behörde konnte nicht aktualisiert werden."));
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (a: Authority) => {
    try {
      await api.updateAuthority(a.authority_id, { active: !a.active });
      showToast("success", a.active ? "Behörde deaktiviert." : "Behörde aktiviert.");
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Status konnte nicht geändert werden."));
    }
  };

  const handleDelete = async (a: Authority) => {
    if (!window.confirm(`"${a.authority_name}" wirklich löschen?`)) return;
    try {
      await api.deleteAuthority(a.authority_id);
      showToast("success", "Behörde gelöscht.");
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Behörde konnte nicht gelöscht werden."));
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
            placeholder="Name, Ort, Abteilung suchen…"
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

      <div className="flex flex-wrap gap-1.5">
        <FilterChip
          active={withoutEmailOnly}
          onClick={() => {
            setWithoutEmailOnly((v) => !v);
            setOffset(0);
          }}
        >
          Ohne E-Mail
        </FilterChip>
        <FilterChip
          active={withoutJurisdictionOnly}
          onClick={() => {
            setWithoutJurisdictionOnly((v) => !v);
            setOffset(0);
          }}
        >
          Ohne Zuständigkeit
        </FilterChip>
        <FilterChip
          active={withoutAddressOnly}
          onClick={() => {
            setWithoutAddressOnly((v) => !v);
            setOffset(0);
          }}
        >
          Ohne Adresse
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
          active={unverifiedOnly}
          onClick={() => {
            setUnverifiedOnly((v) => !v);
            setOffset(0);
          }}
        >
          Nicht verifiziert
        </FilterChip>
      </div>

      <div className="overflow-hidden rounded-lg border border-line bg-surface shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-line bg-paper/50 text-left text-[11px] uppercase tracking-wide text-ink-faint">
                <th className="px-4 py-2.5 font-medium">Behörde</th>
                <th className="px-4 py-2.5 font-medium">Ort</th>
                <th className="px-4 py-2.5 font-medium">Kontakt</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="w-28 px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-ink-faint">
                    <Loader2 size={16} className="mx-auto animate-spin" />
                  </td>
                </tr>
              ) : authorities.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-ink-faint">
                    Keine Behörden gefunden.
                  </td>
                </tr>
              ) : (
                authorities.map((a) =>
                  editingId === a.authority_id ? (
                    <tr key={a.authority_id} className="border-b border-line bg-paper/30 last:border-0">
                      <td colSpan={5} className="px-4 py-3">
                        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                          <input
                            value={editForm.authority_name ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, authority_name: e.target.value }))}
                            placeholder="Name"
                            className="col-span-2 rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none sm:col-span-1"
                          />
                          <input
                            value={editForm.department_name ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, department_name: e.target.value }))}
                            placeholder="Abteilung"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.city ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, city: e.target.value }))}
                            placeholder="Ort"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
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
                            value={editForm.email ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, email: e.target.value }))}
                            placeholder="E-Mail"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.phone ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, phone: e.target.value }))}
                            placeholder="Telefon"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                          <input
                            value={editForm.website ?? ""}
                            onChange={(e) => setEditForm((f) => ({ ...f, website: e.target.value }))}
                            placeholder="Website"
                            className="rounded border border-line px-2 py-1.5 text-sm focus:border-brand focus:outline-none"
                          />
                        </div>
                        <div className="mt-2 flex gap-2">
                          <button
                            onClick={() => saveEdit(a.authority_id)}
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
                    <tr key={a.authority_id} className="border-b border-line last:border-0 hover:bg-paper/30">
                      <td className="px-4 py-2.5">
                        <div className="text-ink">{a.authority_name}</div>
                        {a.department_name && (
                          <div className="text-xs text-ink-faint">{a.department_name}</div>
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-ink-soft">{a.city || "—"}</td>
                      <td className="px-4 py-2.5 text-xs text-ink-soft">
                        {a.email || a.phone || "—"}
                      </td>
                      <td className="px-4 py-2.5">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                            a.active
                              ? "bg-status-matchedBg text-status-matched"
                              : "bg-status-neutralBg text-status-neutral"
                          }`}
                        >
                          {a.active ? "Aktiv" : "Inaktiv"}
                        </span>
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center justify-end gap-1">
                          {onShowJurisdictions && (
                            <button
                              onClick={() => onShowJurisdictions(a.authority_id)}
                              className="rounded p-1.5 text-ink-faint hover:bg-brand-light/50 hover:text-brand"
                              aria-label="Zuständigkeiten anzeigen"
                              title="Zuständigkeiten anzeigen"
                            >
                              <ListTree size={14} />
                            </button>
                          )}
                          <button
                            onClick={() => toggleActive(a)}
                            className="rounded p-1.5 text-ink-faint hover:bg-brand-light/50 hover:text-brand"
                            aria-label={a.active ? "Deaktivieren" : "Aktivieren"}
                            title={a.active ? "Deaktivieren" : "Aktivieren"}
                          >
                            {a.active ? <Ban size={14} /> : <CheckCircle2 size={14} />}
                          </button>
                          <button
                            onClick={() => startEdit(a)}
                            className="rounded p-1.5 text-ink-faint hover:bg-brand-light/50 hover:text-brand"
                            aria-label="Bearbeiten"
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => handleDelete(a)}
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

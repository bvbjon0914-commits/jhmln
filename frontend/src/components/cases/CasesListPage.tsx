import { useEffect, useRef, useState } from "react";
import { Search, Loader2, Plus, FolderKanban } from "lucide-react";
import { api } from "../../services/api";
import { Button } from "../common/Button";
import { Pagination } from "../common/Pagination";
import { useToast, errorMessage } from "../common/Toast";
import type { CaseListItem } from "../../types/case";

const LIMIT = 20;

interface Props {
  onOpenCase: (caseId: string) => void;
}

export function CasesListPage({ onOpenCase }: Props) {
  const { showToast } = useToast();
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = () => {
    setLoading(true);
    api
      .listCasesPaged({ search: search || undefined, limit: LIMIT, offset })
      .then((res) => {
        setCases(res.items);
        setTotal(res.total);
      })
      .catch((error) => showToast("error", errorMessage(error, "Aufträge konnten nicht geladen werden.")))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(load, 250);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, offset]);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const created = await api.createCase({ name: newName.trim() });
      setNewName("");
      showToast("success", "Auftrag angelegt.");
      onOpenCase(created.case_id);
    } catch (error) {
      showToast("error", errorMessage(error, "Auftrag konnte nicht angelegt werden."));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display text-lg font-semibold text-ink">Aufträge</h2>
        <p className="mt-1 text-sm text-ink-soft">
          Mehrere Gebäude zu einem Auftrag bündeln und den Fortschritt (beantragt, gesendet,
          Antwort erhalten, geprüft) an einem Ort verfolgen.
        </p>
      </div>

      <div className="flex flex-col gap-2 rounded-lg border border-line bg-surface p-4 shadow-sm sm:flex-row sm:items-center">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          placeholder="Name des neuen Auftrags…"
          className="flex-1 rounded-lg border border-line bg-surface px-3.5 py-2.5 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
        />
        <Button onClick={handleCreate} disabled={!newName.trim() || creating}>
          {creating ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />}
          Neuer Auftrag
        </Button>
      </div>

      <div className="relative">
        <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
        <input
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setOffset(0);
          }}
          placeholder="Auftrag suchen…"
          className="w-full rounded-lg border border-line bg-surface py-2.5 pl-9 pr-4 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
        />
      </div>

      <div className="overflow-hidden rounded-lg border border-line bg-surface shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="border-b border-line bg-paper/50 text-left text-[11px] uppercase tracking-wide text-ink-faint">
                <th className="px-4 py-2.5 font-medium">Auftrag</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="px-4 py-2.5 font-medium">Fortschritt</th>
                <th className="px-4 py-2.5 font-medium">Zuletzt geändert</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-ink-faint">
                    <Loader2 size={16} className="mx-auto animate-spin" />
                  </td>
                </tr>
              ) : cases.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-ink-faint">
                    Noch keine Aufträge angelegt.
                  </td>
                </tr>
              ) : (
                cases.map((c) => (
                  <tr
                    key={c.case_id}
                    onClick={() => onOpenCase(c.case_id)}
                    className="cursor-pointer border-b border-line last:border-0 hover:bg-paper/30"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 text-ink">
                        <FolderKanban size={15} className="shrink-0 text-brand" />
                        {c.name}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                          c.status === "OPEN"
                            ? "bg-status-matchedBg text-status-matched"
                            : "bg-status-neutralBg text-status-neutral"
                        }`}
                      >
                        {c.status === "OPEN" ? "Offen" : "Abgeschlossen"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-ink-soft">
                      {c.items_total === 0 ? "—" : `${c.items_done}/${c.items_total} geprüft`}
                    </td>
                    <td className="px-4 py-3 text-xs text-ink-faint">
                      {new Date(c.updated_at).toLocaleDateString("de-DE")}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <Pagination offset={offset} limit={LIMIT} total={total} onOffsetChange={setOffset} />
      </div>
    </div>
  );
}

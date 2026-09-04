import { useEffect, useState } from "react";
import { Trash2, Loader2, Sparkles, X } from "lucide-react";
import { api } from "../../services/api";
import { useToast, errorMessage } from "../common/Toast";
import { Pagination } from "../common/Pagination";
import { Button } from "../common/Button";
import type { RequestRecord } from "../../types/request";
import type { AdminFilterRequest } from "../../types/adminFilter";

const LIMIT = 25;

const STATUS_OPTIONS = ["PENDING", "COMPLETED", "PARTIALLY_COMPLETED", "FAILED"];

export function RequestsAdmin({ initialFilter }: { initialFilter?: AdminFilterRequest | null } = {}) {
  const { showToast } = useToast();
  const [orphanedOnly, setOrphanedOnly] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [buildingIdFilter, setBuildingIdFilter] = useState("");
  const [offset, setOffset] = useState(0);
  const [requests, setRequests] = useState<RequestRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [purging, setPurging] = useState(false);

  useEffect(() => {
    if (initialFilter?.key === "building_id" && initialFilter.value) {
      setBuildingIdFilter(initialFilter.value);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const load = () => {
    setLoading(true);
    api
      .listRequestsPaged({
        building_id: buildingIdFilter || undefined,
        status: statusFilter || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        orphaned_only: orphanedOnly || undefined,
        limit: LIMIT,
        offset,
      })
      .then((res) => {
        setRequests(res.items);
        setTotal(res.total);
      })
      .catch((error) => showToast("error", errorMessage(error, "Anfragen konnten nicht geladen werden.")))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orphanedOnly, statusFilter, dateFrom, dateTo, buildingIdFilter, offset]);

  const handleDelete = async (r: RequestRecord) => {
    if (!window.confirm("Diese Anfrage wirklich löschen?")) return;
    try {
      await api.deleteRequest(r.request_id);
      showToast("success", "Anfrage gelöscht.");
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Anfrage konnte nicht gelöscht werden."));
    }
  };

  const handlePurge = async () => {
    if (!window.confirm("Alle Anfragen zu nicht mehr existierenden Gebäuden löschen?")) return;
    setPurging(true);
    try {
      const result = await api.purgeOrphanedRequests();
      showToast("success", `${result.deleted} verwaiste Anfrage(n) gelöscht.`);
      setOffset(0);
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Bereinigung fehlgeschlagen."));
    } finally {
      setPurging(false);
    }
  };

  const filteredBuilding = requests.find((r) => r.building_id === buildingIdFilter)?.building;

  return (
    <div className="space-y-4">
      {buildingIdFilter && (
        <div className="flex items-center gap-2 rounded-lg border border-brand/30 bg-brand-light/40 px-3 py-2 text-xs text-ink-soft">
          Gefiltert nach Gebäude:{" "}
          <span className="font-medium text-ink">
            {filteredBuilding
              ? `${filteredBuilding.street} ${filteredBuilding.house_number}, ${filteredBuilding.city}`
              : buildingIdFilter}
          </span>
          <button
            onClick={() => {
              setBuildingIdFilter("");
              setOffset(0);
            }}
            className="ml-auto rounded p-0.5 text-ink-faint hover:text-ink"
            aria-label="Gebäude-Filter entfernen"
          >
            <X size={13} />
          </button>
        </div>
      )}

      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setOffset(0);
          }}
          className="rounded-lg border border-line bg-surface px-3 py-2.5 text-sm focus:border-brand focus:outline-none"
        >
          <option value="">Alle Status</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => {
            setDateFrom(e.target.value);
            setOffset(0);
          }}
          className="rounded-lg border border-line bg-surface px-3 py-2.5 text-sm focus:border-brand focus:outline-none"
        />
        <span className="text-xs text-ink-faint">bis</span>
        <input
          type="date"
          value={dateTo}
          onChange={(e) => {
            setDateTo(e.target.value);
            setOffset(0);
          }}
          className="rounded-lg border border-line bg-surface px-3 py-2.5 text-sm focus:border-brand focus:outline-none"
        />
        <label className="flex items-center gap-1.5 text-xs text-ink-soft">
          <input
            type="checkbox"
            checked={orphanedOnly}
            onChange={(e) => {
              setOrphanedOnly(e.target.checked);
              setOffset(0);
            }}
          />
          nur verwaiste (Gebäude gelöscht)
        </label>
        <Button variant="secondary" onClick={handlePurge} disabled={purging} className="ml-auto text-xs">
          {purging ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
          Alle verwaisten bereinigen
        </Button>
      </div>

      <div className="overflow-hidden rounded-lg border border-line bg-surface shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px] text-sm">
            <thead>
              <tr className="border-b border-line bg-paper/50 text-left text-[11px] uppercase tracking-wide text-ink-faint">
                <th className="px-4 py-2.5 font-medium">Datum</th>
                <th className="px-4 py-2.5 font-medium">Gebäude</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="px-4 py-2.5 font-medium">Items</th>
                <th className="w-16 px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-ink-faint">
                    <Loader2 size={16} className="mx-auto animate-spin" />
                  </td>
                </tr>
              ) : requests.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-ink-faint">
                    Keine Anfragen gefunden.
                  </td>
                </tr>
              ) : (
                requests.map((r) => (
                  <tr key={r.request_id} className="border-b border-line last:border-0 hover:bg-paper/30">
                    <td className="px-4 py-2.5 font-mono text-xs text-ink-faint">
                      {new Date(r.created_at).toLocaleString("de-DE")}
                    </td>
                    <td className="px-4 py-2.5 text-ink-soft">
                      {r.building ? (
                        `${r.building.street} ${r.building.house_number}, ${r.building.city}`
                      ) : (
                        <span className="text-status-conflict">verwaist (Gebäude gelöscht)</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-ink-soft">{r.status}</td>
                    <td className="px-4 py-2.5 text-xs text-ink-faint">
                      {r.completion_status.completed}/{r.completion_status.total} generiert
                    </td>
                    <td className="px-4 py-2.5">
                      <button
                        onClick={() => handleDelete(r)}
                        className="rounded p-1.5 text-ink-faint hover:bg-status-conflictBg hover:text-status-conflict"
                        aria-label="Löschen"
                      >
                        <Trash2 size={14} />
                      </button>
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

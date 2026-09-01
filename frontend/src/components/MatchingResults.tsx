import { useEffect, useRef, useState, Fragment } from "react";
import { ChevronDown, Pencil, Loader2 } from "lucide-react";
import type { MatchingResult } from "../types/matching";
import type { Authority } from "../types/authority";
import { api } from "../services/api";
import { StatusBadge } from "./common/StatusBadge";
import { JurisdictionTrail } from "./JurisdictionTrail";
import { Button } from "./common/Button";
import { useToast, errorMessage } from "./common/Toast";

interface Props {
  results: MatchingResult[];
  requestTypeNames: Record<string, string>;
  onAssigned: (requestItemId: string, authorityId: string) => void;
}

export function MatchingResults({ results, requestTypeNames, onAssigned }: Props) {
  const { showToast } = useToast();
  const [expanded, setExpanded] = useState<string | null>(null);
  const [authorities, setAuthorities] = useState<Record<string, Authority>>({});
  const [authoritiesLoading, setAuthoritiesLoading] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);

  useEffect(() => {
    const idsToLoad = new Set<string>();
    results.forEach((r) => {
      if (r.authority_id) idsToLoad.add(r.authority_id);
      r.alternative_authorities.forEach((a) => idsToLoad.add(a));
    });

    if (idsToLoad.size === 0) {
      setAuthorities({});
      return;
    }

    setAuthoritiesLoading(true);
    api
      .getAuthorities([...idsToLoad])
      .then((loaded) => {
        const map: Record<string, Authority> = {};
        loaded.forEach((a) => {
          map[a.authority_id] = a;
        });
        setAuthorities(map);
      })
      .catch((error) => showToast("error", errorMessage(error, "Behörden konnten nicht geladen werden.")))
      .finally(() => setAuthoritiesLoading(false));
  }, [results, showToast]);

  return (
    <div className="overflow-x-auto rounded-lg border border-line bg-surface shadow-sm">
      <table className="w-full min-w-[560px] text-sm">
        <thead>
          <tr className="border-b border-line bg-paper/50 text-left text-[11px] uppercase tracking-wide text-ink-faint">
            <th className="px-4 py-3 font-medium">Auskunft</th>
            <th className="px-4 py-3 font-medium">Behörde</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="w-10 px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          {results.map((result) => {
            const authority = result.authority_id ? authorities[result.authority_id] : null;
            const isExpanded = expanded === result.request_item_id;
            const isEditing = editing === result.request_item_id;

            return (
              <Fragment key={result.request_item_id}>
                <tr
                  className="cursor-pointer border-b border-line last:border-0 hover:bg-paper/40"
                  onClick={() =>
                    setExpanded(isExpanded ? null : result.request_item_id)
                  }
                >
                  <td className="px-4 py-3.5 font-medium text-ink">
                    {requestTypeNames[result.request_type_id] || result.request_type_id}
                  </td>
                  <td className="px-4 py-3.5 text-ink-soft">
                    {authority ? (
                      <div>
                        <div className="text-ink">{authority.authority_name}</div>
                        {authority.department_name && (
                          <div className="text-xs text-ink-faint">
                            {authority.department_name}
                          </div>
                        )}
                      </div>
                    ) : authoritiesLoading && result.authority_id ? (
                      <Loader2 size={14} className="animate-spin text-ink-faint" />
                    ) : (
                      <span className="text-ink-faint">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5">
                    <StatusBadge status={result.matching_status} />
                  </td>
                  <td className="px-4 py-3.5 text-ink-faint">
                    <ChevronDown
                      size={16}
                      className={`transition-transform ${isExpanded ? "rotate-180" : ""}`}
                    />
                  </td>
                </tr>
                {isExpanded && (
                  <tr className="border-b border-line last:border-0">
                    <td colSpan={4} className="bg-paper/30 px-4 py-4">
                      <JurisdictionTrail
                        matchingLevel={result.matching_level}
                        status={result.matching_status}
                        reason={result.reason}
                      />

                      <div className="mt-3 flex items-center justify-between">
                        {result.matching_status !== "MATCHED" &&
                          result.alternative_authorities.length > 0 && (
                            <div className="text-xs text-ink-soft">
                              Mögliche Behörden:{" "}
                              {result.alternative_authorities
                                .map((id) => authorities[id]?.authority_name || id)
                                .join(", ")}
                            </div>
                          )}
                        <Button
                          variant="secondary"
                          className="ml-auto text-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditing(isEditing ? null : result.request_item_id);
                          }}
                        >
                          <Pencil size={13} />
                          Zuordnung ändern
                        </Button>
                      </div>

                      {isEditing && (
                        <AssignmentPicker
                          currentAuthorityId={result.authority_id}
                          candidateIds={result.alternative_authorities}
                          onAssign={async (authorityId) => {
                            try {
                              await api.assignAuthority(
                                result.request_item_id,
                                authorityId,
                                "Manuell durch Benutzer geändert"
                              );
                              onAssigned(result.request_item_id, authorityId);
                              setEditing(null);
                            } catch (error) {
                              showToast(
                                "error",
                                errorMessage(error, "Zuordnung konnte nicht gespeichert werden.")
                              );
                            }
                          }}
                        />
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function AssignmentPicker({
  candidateIds,
  onAssign,
}: {
  currentAuthorityId: string | null;
  candidateIds: string[];
  onAssign: (authorityId: string) => void;
}) {
  const { showToast } = useToast();
  const [query, setQuery] = useState("");
  const [options, setOptions] = useState<Authority[]>([]);
  const [searching, setSearching] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (candidateIds.length > 0) {
      api
        .getAuthorities(candidateIds)
        .then(setOptions)
        .catch((error) => showToast("error", errorMessage(error, "Behörden konnten nicht geladen werden.")));
      return;
    }

    if (query.length < 2) {
      setOptions([]);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const data = await api.listAuthorities(query);
        setOptions(data);
      } catch (error) {
        showToast("error", errorMessage(error, "Behördensuche fehlgeschlagen."));
      } finally {
        setSearching(false);
      }
    }, 250);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, candidateIds, showToast]);

  return (
    <div className="mt-3 rounded-md border border-line bg-surface p-3">
      {candidateIds.length === 0 && (
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Behörde suchen…"
          className="mb-2 w-full rounded border border-line px-3 py-2 text-sm focus:border-brand focus:outline-none"
        />
      )}
      <div className="max-h-40 overflow-y-auto">
        {options.map((a) => (
          <button
            key={a.authority_id}
            onClick={() => onAssign(a.authority_id)}
            className="block w-full rounded px-2 py-1.5 text-left text-sm hover:bg-brand-light/50"
          >
            <span className="text-ink">{a.authority_name}</span>
            {a.department_name && (
              <span className="ml-1.5 text-xs text-ink-faint">
                · {a.department_name}
              </span>
            )}
          </button>
        ))}
        {searching && (
          <p className="flex items-center gap-1.5 px-2 py-1.5 text-xs text-ink-faint">
            <Loader2 size={12} className="animate-spin" /> Suche…
          </p>
        )}
        {!searching && options.length === 0 && (
          <p className="px-2 py-1.5 text-xs text-ink-faint">
            {candidateIds.length === 0
              ? "Mindestens 2 Zeichen eingeben, um zu suchen."
              : "Keine Alternativen hinterlegt."}
          </p>
        )}
      </div>
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { Search, Building2, Loader2, Plus } from "lucide-react";
import type { Building } from "../types/building";
import { api } from "../services/api";
import { useToast, errorMessage } from "./common/Toast";
import { NewBuildingForm } from "./NewBuildingForm";

interface Props {
  onSelect: (building: Building) => void;
  excludeIds?: string[];
}

export function BuildingSearch({ onSelect, excludeIds = [] }: Props) {
  const { showToast } = useToast();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Building[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [showNewBuilding, setShowNewBuilding] = useState(false);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await api.searchBuildings(query);
        setResults(data);
        setIsOpen(true);
      } catch (error) {
        showToast("error", errorMessage(error, "Gebäudesuche fehlgeschlagen."));
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, showToast]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={containerRef}>
      <div className="relative">
        <Search
          size={18}
          className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-ink-faint"
        />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setIsOpen(true)}
          placeholder="Weiteres Gebäude suchen und hinzufügen…"
          role="combobox"
          aria-expanded={isOpen}
          aria-autocomplete="list"
          className="w-full rounded-lg border border-line bg-surface py-3.5 pl-11 pr-4 text-[15px] text-ink placeholder:text-ink-faint focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
        />
        {loading && (
          <Loader2
            size={16}
            className="absolute right-4 top-1/2 -translate-y-1/2 animate-spin text-ink-faint"
          />
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div
          role="listbox"
          className="absolute z-10 mt-2 w-full overflow-hidden rounded-lg border border-line bg-surface shadow-lg"
        >
          {results.map((b) => {
            const alreadySelected = excludeIds.includes(b.building_id);
            return (
              <button
                key={b.building_id}
                role="option"
                aria-selected={false}
                disabled={alreadySelected}
                onClick={() => {
                  onSelect(b);
                  setIsOpen(false);
                  setQuery("");
                }}
                className="flex w-full items-start gap-3 border-b border-line px-4 py-3 text-left last:border-0 hover:bg-brand-light/40 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent"
              >
                <Building2 size={16} className="mt-0.5 shrink-0 text-brand" />
                <div>
                  <div className="text-sm font-medium text-ink">
                    {b.street} {b.house_number}
                    {alreadySelected && (
                      <span className="ml-2 text-xs font-normal text-ink-faint">
                        bereits ausgewählt
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-ink-soft">
                    {b.postal_code} {b.city}
                    {b.internal_reference && (
                      <span className="ml-2 font-mono text-ink-faint">
                        {b.internal_reference}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {isOpen && results.length === 0 && !loading && query.length >= 2 && (
        <div className="absolute z-10 mt-2 w-full rounded-lg border border-line bg-surface px-4 py-3 text-sm text-ink-soft shadow-lg">
          <div>Kein Gebäude gefunden für „{query}".</div>
          <button
            onClick={() => {
              setIsOpen(false);
              setShowNewBuilding(true);
            }}
            className="mt-2 flex items-center gap-1.5 text-sm font-medium text-brand hover:text-brand-dark"
          >
            <Plus size={14} />
            Neues Gebäude „{query}" anlegen
          </button>
        </div>
      )}

      {!showNewBuilding && (
        <button
          onClick={() => setShowNewBuilding(true)}
          className="mt-2 flex items-center gap-1.5 text-xs font-medium text-ink-faint hover:text-brand"
        >
          <Plus size={13} />
          Neues Gebäude manuell anlegen
        </button>
      )}

      {showNewBuilding && (
        <div className="mt-3">
          <NewBuildingForm
            initialQuery={query}
            onCreated={(building) => {
              setShowNewBuilding(false);
              onSelect(building);
              setQuery("");
            }}
            onCancel={() => setShowNewBuilding(false)}
          />
        </div>
      )}
    </div>
  );
}

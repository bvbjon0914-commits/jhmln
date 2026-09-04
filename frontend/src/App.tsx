import { useEffect, useState } from "react";
import { FileSearch2, Upload, Settings, LogOut, DownloadCloud, FileSpreadsheet, RotateCcw, FolderKanban } from "lucide-react";
import { Stepper } from "./components/Stepper";
import { BuildingSearch } from "./components/BuildingSearch";
import { BuildingDetails } from "./components/BuildingDetails";
import { BuildingMap } from "./components/BuildingMap";
import { SelectedBuildingsList } from "./components/SelectedBuildingsList";
import { RequestTypeSelector } from "./components/RequestTypeSelector";
import { MatchingResults } from "./components/MatchingResults";
import { GeneratedDocuments } from "./components/GeneratedDocuments";
import { Button } from "./components/common/Button";
import { CollapsibleSection } from "./components/common/CollapsibleSection";
import { useToast, errorMessage } from "./components/common/Toast";
import { ImportPage } from "./components/import/ImportPage";
import { AdminPage } from "./components/admin/AdminPage";
import { CasesPage } from "./components/cases/CasesPage";
import { useAuth } from "./components/auth/AuthContext";
import { api } from "./services/api";
import type { Building } from "./types/building";
import type { MatchingResult, GeneratedDocumentInfo, RequestType } from "./types/matching";
import { computeSequencingHints } from "./types/sequencing";

interface FailedDoc {
  request_item_id: string;
  request_type_id: string;
  reason: string;
}

function buildingLabel(b: Building): string {
  return `${b.street} ${b.house_number}, ${b.city}`;
}

function matchSummary(results: MatchingResult[]): { matched: number; total: number } {
  return { matched: results.filter((r) => r.matching_status === "MATCHED").length, total: results.length };
}

const STORAGE_KEY = "zustaendigkeitsfinder:wizard-state:v1";

interface PersistedState {
  buildings: Building[];
  requestTypeIds: string[];
  requestIds: Record<string, string>;
  resultsByBuilding: Record<string, MatchingResult[]>;
  documentsByBuilding: Record<string, GeneratedDocumentInfo[]>;
  failedByBuilding: Record<string, FailedDoc[]>;
}

function loadPersistedState(): PersistedState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as PersistedState) : null;
  } catch {
    return null;
  }
}

function App() {
  const { showToast } = useToast();
  const { isMain, logout } = useAuth();
  const [view, setView] = useState<"wizard" | "import" | "admin" | "cases">("wizard");
  const [buildings, setBuildings] = useState<Building[]>(() => loadPersistedState()?.buildings ?? []);
  const [requestTypeIds, setRequestTypeIds] = useState<string[]>(
    () => loadPersistedState()?.requestTypeIds ?? []
  );
  const [requestTypes, setRequestTypes] = useState<RequestType[]>([]);
  const [requestIds, setRequestIds] = useState<Record<string, string>>(
    () => loadPersistedState()?.requestIds ?? {}
  );
  const [resultsByBuilding, setResultsByBuilding] = useState<Record<string, MatchingResult[]>>(
    () => loadPersistedState()?.resultsByBuilding ?? {}
  );
  const [documentsByBuilding, setDocumentsByBuilding] = useState<
    Record<string, GeneratedDocumentInfo[]>
  >(() => loadPersistedState()?.documentsByBuilding ?? {});
  const [failedByBuilding, setFailedByBuilding] = useState<Record<string, FailedDoc[]>>(
    () => loadPersistedState()?.failedByBuilding ?? {}
  );
  const [retryingByBuilding, setRetryingByBuilding] = useState<Record<string, boolean>>({});
  const [matchingLoading, setMatchingLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    const state: PersistedState = {
      buildings,
      requestTypeIds,
      requestIds,
      resultsByBuilding,
      documentsByBuilding,
      failedByBuilding,
    };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // Speicher voll oder nicht verfügbar (z.B. privater Modus) – Persistenz einfach überspringen
    }
  }, [buildings, requestTypeIds, requestIds, resultsByBuilding, documentsByBuilding, failedByBuilding]);

  useEffect(() => {
    api
      .listRequestTypes()
      .then(setRequestTypes)
      .catch((error) => showToast("error", errorMessage(error, "Auskunftsarten konnten nicht geladen werden.")));
  }, [showToast]);

  const requestTypeNames = Object.fromEntries(
    requestTypes.map((t) => [t.request_type_id, t.name])
  );

  const handleAddBuilding = (b: Building) => {
    setBuildings((prev) => (prev.some((x) => x.building_id === b.building_id) ? prev : [...prev, b]));
  };

  const handleRemoveBuilding = (buildingId: string) => {
    setBuildings((prev) => prev.filter((b) => b.building_id !== buildingId));
    setRequestIds((prev) => {
      const next = { ...prev };
      delete next[buildingId];
      return next;
    });
    setResultsByBuilding((prev) => {
      const next = { ...prev };
      delete next[buildingId];
      return next;
    });
    setDocumentsByBuilding((prev) => {
      const next = { ...prev };
      delete next[buildingId];
      return next;
    });
    setFailedByBuilding((prev) => {
      const next = { ...prev };
      delete next[buildingId];
      return next;
    });
  };

  const hasAnyResults = Object.values(resultsByBuilding).some((r) => r.length > 0);
  const hasAnyDocuments =
    Object.values(documentsByBuilding).some((d) => d.length > 0) ||
    Object.values(failedByBuilding).some((f) => f.length > 0);

  const currentStep = hasAnyDocuments ? 4 : hasAnyResults ? 3 : buildings.length > 0 ? 2 : 1;

  const handleRunMatching = async () => {
    if (buildings.length === 0 || requestTypeIds.length === 0) return;
    setMatchingLoading(true);
    const newRequestIds: Record<string, string> = {};
    const newResults: Record<string, MatchingResult[]> = {};

    await Promise.all(
      buildings.map(async (b) => {
        try {
          const response = await api.runMatching(b.building_id, requestTypeIds);
          newRequestIds[b.building_id] = response.request_id;
          newResults[b.building_id] = response.results;
        } catch (error) {
          showToast(
            "error",
            `${buildingLabel(b)}: ${errorMessage(error, "Zuständigkeiten konnten nicht ermittelt werden.")}`
          );
        }
      })
    );

    setRequestIds((prev) => ({ ...prev, ...newRequestIds }));
    setResultsByBuilding((prev) => ({ ...prev, ...newResults }));
    setDocumentsByBuilding({});
    setFailedByBuilding({});
    setMatchingLoading(false);
  };

  const handleAssigned = (buildingId: string, requestItemId: string, authorityId: string) => {
    setResultsByBuilding((prev) => ({
      ...prev,
      [buildingId]: (prev[buildingId] || []).map((r) =>
        r.request_item_id === requestItemId
          ? { ...r, authority_id: authorityId, matching_status: "MATCHED", matching_confidence: 1.0 }
          : r
      ),
    }));
  };

  const handleGenerate = async () => {
    const entries = Object.entries(requestIds);
    if (entries.length === 0) return;
    setGenerating(true);
    const newDocuments: Record<string, GeneratedDocumentInfo[]> = {};
    const newFailed: Record<string, FailedDoc[]> = {};
    let totalFailed = 0;

    await Promise.all(
      entries.map(async ([buildingId, reqId]) => {
        try {
          const response = await api.generateDocuments(reqId);
          newDocuments[buildingId] = response.documents;
          newFailed[buildingId] = response.failed;
          totalFailed += response.failed.length;
        } catch (error) {
          const b = buildings.find((x) => x.building_id === buildingId);
          showToast(
            "error",
            `${b ? buildingLabel(b) : buildingId}: ${errorMessage(error, "Schreiben konnten nicht generiert werden.")}`
          );
        }
      })
    );

    setDocumentsByBuilding(newDocuments);
    setFailedByBuilding(newFailed);
    if (totalFailed > 0) {
      showToast("error", `${totalFailed} Schreiben konnten nicht generiert werden.`);
    }
    setGenerating(false);
  };

  const handleRetryFailed = async (buildingId: string) => {
    const reqId = requestIds[buildingId];
    if (!reqId) return;
    setRetryingByBuilding((prev) => ({ ...prev, [buildingId]: true }));
    try {
      const response = await api.generateDocuments(reqId, { retryFailedOnly: true });
      setDocumentsByBuilding((prev) => ({
        ...prev,
        [buildingId]: [...(prev[buildingId] || []), ...response.documents],
      }));
      setFailedByBuilding((prev) => ({ ...prev, [buildingId]: response.failed }));
      if (response.failed.length === 0) {
        showToast("success", "Alle Schreiben erfolgreich generiert.");
      } else if (response.documents.length > 0) {
        showToast("success", `${response.documents.length} weitere Schreiben generiert.`);
      } else {
        showToast("error", "Erneuter Versuch hat keine weiteren Schreiben erzeugt.");
      }
    } catch (error) {
      const b = buildings.find((x) => x.building_id === buildingId);
      showToast(
        "error",
        `${b ? buildingLabel(b) : buildingId}: ${errorMessage(error, "Erneuter Versuch fehlgeschlagen.")}`
      );
    } finally {
      setRetryingByBuilding((prev) => ({ ...prev, [buildingId]: false }));
    }
  };

  const handleReset = () => {
    if (!window.confirm("Aktuelle Auswahl und Ergebnisse wirklich verwerfen?")) return;
    setBuildings([]);
    setRequestTypeIds([]);
    setRequestIds({});
    setResultsByBuilding({});
    setDocumentsByBuilding({});
    setFailedByBuilding({});
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignorieren
    }
  };

  const buildingsWithResults = buildings.filter((b) => (resultsByBuilding[b.building_id]?.length ?? 0) > 0);
  const buildingsWithDocuments = buildings.filter(
    (b) =>
      (documentsByBuilding[b.building_id]?.length ?? 0) > 0 ||
      (failedByBuilding[b.building_id]?.length ?? 0) > 0
  );
  const allMatched =
    buildingsWithResults.length > 0 &&
    buildingsWithResults.every((b) =>
      resultsByBuilding[b.building_id].every((r) => r.matching_status === "MATCHED")
    );

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-surface shadow-sm">
        <div className="mx-auto flex max-w-4xl items-center gap-3 px-6 py-4">
          <img src="/brand/mark.png" alt="Civeloq" className="h-9 w-9" />
          <div>
            <h1 className="font-display text-[15px] font-semibold leading-none text-ink">
              Civeloq
            </h1>
            <p className="mt-1 text-xs text-ink-faint">
              Behördenzuordnung & Anschreiben-Generierung
            </p>
          </div>
          <nav className="ml-auto flex items-center gap-1">
            <button
              onClick={() => setView("wizard")}
              aria-current={view === "wizard" ? "page" : undefined}
              className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                view === "wizard"
                  ? "bg-brand-light/60 text-brand"
                  : "text-ink-faint hover:text-ink"
              }`}
            >
              Zuordnung
            </button>
            <button
              onClick={() => setView("cases")}
              aria-current={view === "cases" ? "page" : undefined}
              className={`inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                view === "cases"
                  ? "bg-brand-light/60 text-brand"
                  : "text-ink-faint hover:text-ink"
              }`}
            >
              <FolderKanban size={14} />
              Aufträge
            </button>
            <button
              onClick={() => setView("import")}
              aria-current={view === "import" ? "page" : undefined}
              className={`inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                view === "import"
                  ? "bg-brand-light/60 text-brand"
                  : "text-ink-faint hover:text-ink"
              }`}
            >
              <Upload size={14} />
              Datenimport
            </button>
            <button
              onClick={() => setView("admin")}
              aria-current={view === "admin" ? "page" : undefined}
              className={`inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                view === "admin"
                  ? "bg-brand-light/60 text-brand"
                  : "text-ink-faint hover:text-ink"
              }`}
            >
              <Settings size={14} />
              Verwaltung
            </button>
            <button
              onClick={() => logout()}
              className="inline-flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium text-ink-faint hover:text-ink"
              title="Abmelden"
            >
              <LogOut size={14} />
            </button>
          </nav>
        </div>
      </header>

      {view === "cases" ? (
        <main className="mx-auto max-w-5xl px-6 py-10">
          <CasesPage />
        </main>
      ) : view === "import" ? (
        <main className="mx-auto max-w-4xl px-6 py-10">
          <ImportPage />
        </main>
      ) : view === "admin" ? (
        <main className="mx-auto max-w-5xl px-6 py-10">
          <AdminPage isMain={isMain} />
        </main>
      ) : (
      <main className="mx-auto max-w-4xl px-6 py-10">
        <div className="mb-10 flex items-center gap-4">
          <div className="flex-1 overflow-x-auto">
            <Stepper current={currentStep} />
          </div>
          {buildings.length > 0 && (
            <button
              onClick={handleReset}
              className="inline-flex shrink-0 items-center gap-1.5 text-xs font-medium text-ink-faint hover:text-status-conflict"
            >
              <RotateCcw size={12} />
              Neu starten
            </button>
          )}
        </div>

        <div className="space-y-8">
          {/* Schritt 1: Gebäude suchen */}
          <section>
            <h2 className="mb-3 font-display text-sm font-semibold text-ink">
              1. Gebäude auswählen
              {buildings.length > 0 && (
                <span className="ml-1.5 font-sans text-xs font-normal text-ink-faint">
                  ({buildings.length} ausgewählt)
                </span>
              )}
            </h2>
            <BuildingSearch
              onSelect={handleAddBuilding}
              excludeIds={buildings.map((b) => b.building_id)}
            />
            {buildings.length === 1 && (
              <div className="mt-4 space-y-4">
                <BuildingDetails building={buildings[0]} />
                <BuildingMap building={buildings[0]} />
                <button
                  onClick={() => handleRemoveBuilding(buildings[0].building_id)}
                  className="text-xs font-medium text-ink-faint hover:text-status-conflict"
                >
                  Entfernen
                </button>
              </div>
            )}
            {buildings.length > 1 && (
              <div className="mt-4">
                <SelectedBuildingsList buildings={buildings} onRemove={handleRemoveBuilding} />
              </div>
            )}
          </section>

          {/* Schritt 2: Auskünfte wählen */}
          {buildings.length > 0 && (
            <section>
              <RequestTypeSelector
                types={requestTypes}
                selected={requestTypeIds}
                onChange={setRequestTypeIds}
                hints={computeSequencingHints(requestTypeIds)}
              />
              <div className="mt-4">
                <Button
                  onClick={handleRunMatching}
                  disabled={requestTypeIds.length === 0 || matchingLoading}
                >
                  <FileSearch2 size={16} />
                  {matchingLoading
                    ? "Ermittle Zuständigkeiten…"
                    : buildings.length > 1
                      ? `Zuständige Ämter für ${buildings.length} Gebäude ermitteln`
                      : "Zuständige Ämter ermitteln"}
                </Button>
              </div>
            </section>
          )}

          {/* Schritt 3: Matching-Ergebnisse */}
          {hasAnyResults && (
            <section className="space-y-6">
              <h2 className="font-display text-sm font-semibold text-ink">
                3. Zuständigkeiten prüfen
              </h2>
              <div className="space-y-2">
                {buildingsWithResults.map((b) => {
                  const results = resultsByBuilding[b.building_id];
                  const { matched, total } = matchSummary(results);
                  const done = matched === total;
                  return (
                    <CollapsibleSection
                      key={b.building_id}
                      defaultExpanded={buildingsWithResults.length === 1}
                      title={buildingLabel(b)}
                      summary={
                        <span
                          className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${
                            done
                              ? "bg-status-matchedBg text-status-matched"
                              : "bg-status-reviewBg text-status-review"
                          }`}
                        >
                          {matched}/{total} eindeutig
                        </span>
                      }
                    >
                      <MatchingResults
                        results={results}
                        requestTypeNames={requestTypeNames}
                        onAssigned={(itemId, authorityId) =>
                          handleAssigned(b.building_id, itemId, authorityId)
                        }
                      />
                      <BuildingMap
                        building={b}
                        authorityRefs={results
                          .filter((r) => r.authority_id)
                          .map((r) => ({
                            authorityId: r.authority_id as string,
                            label: requestTypeNames[r.request_type_id] || r.request_type_id,
                          }))}
                      />
                    </CollapsibleSection>
                  );
                })}
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button onClick={handleGenerate} disabled={!allMatched || generating}>
                  {generating ? "Generiere Schreiben…" : "Schreiben generieren"}
                </Button>
                <a
                  href={api.exportResultsCsvUrl(buildingsWithResults.map((b) => requestIds[b.building_id]))}
                  download
                >
                  <Button variant="secondary">
                    <FileSpreadsheet size={16} />
                    Ergebnisse als CSV exportieren
                  </Button>
                </a>
              </div>
              {!allMatched && (
                <p className="-mt-3 text-xs text-ink-faint">
                  Alle Zuständigkeiten müssen eindeutig oder manuell bestätigt sein, bevor
                  Schreiben generiert werden können.
                </p>
              )}
            </section>
          )}

          {/* Schritt 4: Dokumente */}
          {hasAnyDocuments && (
            <section className="space-y-6">
              <h2 className="font-display text-sm font-semibold text-ink">
                4. Schreiben herunterladen
              </h2>
              <div className="space-y-2">
                {buildingsWithDocuments.map((b) => {
                  const docs = documentsByBuilding[b.building_id] || [];
                  const failedDocs = failedByBuilding[b.building_id] || [];
                  return (
                    <CollapsibleSection
                      key={b.building_id}
                      defaultExpanded={buildingsWithDocuments.length === 1}
                      title={buildingLabel(b)}
                      summary={
                        <span
                          className={`shrink-0 text-xs font-medium ${
                            failedDocs.length > 0 ? "text-status-conflict" : "text-ink-faint"
                          }`}
                        >
                          {docs.length} Schreiben
                          {failedDocs.length > 0 ? `, ${failedDocs.length} fehlgeschlagen` : ""}
                        </span>
                      }
                    >
                      <GeneratedDocuments
                        requestId={requestIds[b.building_id]}
                        documents={docs}
                        failed={failedDocs}
                        requestTypeNames={requestTypeNames}
                        onRetryFailed={() => handleRetryFailed(b.building_id)}
                        retrying={!!retryingByBuilding[b.building_id]}
                      />
                    </CollapsibleSection>
                  );
                })}
              </div>
              {buildingsWithDocuments.length > 1 && (
                <div className="flex justify-end">
                  <a
                    href={api.downloadAllCombinedUrl(
                      buildingsWithDocuments.map((b) => requestIds[b.building_id])
                    )}
                    download
                  >
                    <Button>
                      <DownloadCloud size={16} />
                      Alle Schreiben aller Gebäude als ZIP herunterladen
                    </Button>
                  </a>
                </div>
              )}
            </section>
          )}
        </div>
      </main>
      )}
    </div>
  );
}

export default App;

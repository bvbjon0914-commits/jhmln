import { useEffect, useState } from "react";
import { Landmark, FileSearch2, Upload, Settings, LogOut } from "lucide-react";
import { Stepper } from "./components/Stepper";
import { BuildingSearch } from "./components/BuildingSearch";
import { BuildingDetails } from "./components/BuildingDetails";
import { BuildingMap } from "./components/BuildingMap";
import { SelectedBuildingsList } from "./components/SelectedBuildingsList";
import { RequestTypeSelector } from "./components/RequestTypeSelector";
import { MatchingResults } from "./components/MatchingResults";
import { GeneratedDocuments } from "./components/GeneratedDocuments";
import { Button } from "./components/common/Button";
import { useToast, errorMessage } from "./components/common/Toast";
import { ImportPage } from "./components/import/ImportPage";
import { AdminPage } from "./components/admin/AdminPage";
import { useAuth } from "./components/auth/AuthContext";
import { api } from "./services/api";
import type { Building } from "./types/building";
import type { MatchingResult, GeneratedDocumentInfo, RequestType } from "./types/matching";

interface FailedDoc {
  request_item_id: string;
  request_type_id: string;
  reason: string;
}

function buildingLabel(b: Building): string {
  return `${b.street} ${b.house_number}, ${b.city}`;
}

function App() {
  const { showToast } = useToast();
  const { isMain, logout } = useAuth();
  const [view, setView] = useState<"wizard" | "import" | "admin">("wizard");
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [requestTypeIds, setRequestTypeIds] = useState<string[]>([]);
  const [requestTypes, setRequestTypes] = useState<RequestType[]>([]);
  const [requestIds, setRequestIds] = useState<Record<string, string>>({});
  const [resultsByBuilding, setResultsByBuilding] = useState<Record<string, MatchingResult[]>>({});
  const [documentsByBuilding, setDocumentsByBuilding] = useState<
    Record<string, GeneratedDocumentInfo[]>
  >({});
  const [failedByBuilding, setFailedByBuilding] = useState<Record<string, FailedDoc[]>>({});
  const [matchingLoading, setMatchingLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

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

  const buildingsWithResults = buildings.filter((b) => (resultsByBuilding[b.building_id]?.length ?? 0) > 0);
  const allMatched =
    buildingsWithResults.length > 0 &&
    buildingsWithResults.every((b) =>
      resultsByBuilding[b.building_id].every((r) => r.matching_status === "MATCHED")
    );

  return (
    <div className="min-h-screen">
      <header className="relative border-b border-line bg-surface shadow-sm">
        <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-brand via-brand-accent to-brand" />
        <div className="mx-auto flex max-w-4xl items-center gap-3 px-6 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-gradient-to-br from-brand to-brand-dark text-white shadow-sm">
            <Landmark size={18} />
          </div>
          <div>
            <div className="flex items-baseline gap-2">
              <span className="font-display text-[13px] font-bold uppercase tracking-wide text-brand">
                Vonovia
              </span>
              <span className="h-3 w-px bg-line" />
              <h1 className="font-display text-[15px] font-semibold leading-none text-ink">
                Zuständigkeitsfinder
              </h1>
            </div>
            <p className="mt-0.5 text-xs text-ink-faint">
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

      {view === "import" ? (
        <main className="mx-auto max-w-4xl px-6 py-10">
          <ImportPage />
        </main>
      ) : view === "admin" ? (
        <main className="mx-auto max-w-5xl px-6 py-10">
          <AdminPage isMain={isMain} />
        </main>
      ) : (
      <main className="mx-auto max-w-4xl px-6 py-10">
        <div className="mb-10 overflow-x-auto">
          <Stepper current={currentStep} />
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
              {buildingsWithResults.map((b) => (
                <div key={b.building_id}>
                  {buildingsWithResults.length > 1 && (
                    <h3 className="mb-2 text-sm font-medium text-ink-soft">{buildingLabel(b)}</h3>
                  )}
                  <MatchingResults
                    results={resultsByBuilding[b.building_id]}
                    requestTypeNames={requestTypeNames}
                    onAssigned={(itemId, authorityId) =>
                      handleAssigned(b.building_id, itemId, authorityId)
                    }
                  />
                  <div className="mt-3">
                    <BuildingMap
                      building={b}
                      authorityRefs={resultsByBuilding[b.building_id]
                        .filter((r) => r.authority_id)
                        .map((r) => ({
                          authorityId: r.authority_id as string,
                          label: requestTypeNames[r.request_type_id] || r.request_type_id,
                        }))}
                    />
                  </div>
                </div>
              ))}
              <div>
                <Button onClick={handleGenerate} disabled={!allMatched || generating}>
                  {generating ? "Generiere Schreiben…" : "Schreiben generieren"}
                </Button>
                {!allMatched && (
                  <p className="mt-2 text-xs text-ink-faint">
                    Alle Zuständigkeiten müssen eindeutig oder manuell bestätigt sein,
                    bevor Schreiben generiert werden können.
                  </p>
                )}
              </div>
            </section>
          )}

          {/* Schritt 4: Dokumente */}
          {hasAnyDocuments && (
            <section className="space-y-6">
              <h2 className="font-display text-sm font-semibold text-ink">
                4. Schreiben herunterladen
              </h2>
              {buildings
                .filter(
                  (b) =>
                    (documentsByBuilding[b.building_id]?.length ?? 0) > 0 ||
                    (failedByBuilding[b.building_id]?.length ?? 0) > 0
                )
                .map((b) => (
                  <div key={b.building_id}>
                    {buildings.length > 1 && (
                      <h3 className="mb-2 text-sm font-medium text-ink-soft">{buildingLabel(b)}</h3>
                    )}
                    <GeneratedDocuments
                      requestId={requestIds[b.building_id]}
                      documents={documentsByBuilding[b.building_id] || []}
                      failed={failedByBuilding[b.building_id] || []}
                      requestTypeNames={requestTypeNames}
                    />
                  </div>
                ))}
            </section>
          )}
        </div>
      </main>
      )}
    </div>
  );
}

export default App;

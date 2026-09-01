import { useEffect, useState } from "react";
import { Landmark, FileSearch2, Upload, Settings, LogOut } from "lucide-react";
import { Stepper } from "./components/Stepper";
import { BuildingSearch } from "./components/BuildingSearch";
import { BuildingDetails } from "./components/BuildingDetails";
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

function App() {
  const { showToast } = useToast();
  const { isMain, logout } = useAuth();
  const [view, setView] = useState<"wizard" | "import" | "admin">("wizard");
  const [building, setBuilding] = useState<Building | null>(null);
  const [requestTypeIds, setRequestTypeIds] = useState<string[]>([]);
  const [requestTypes, setRequestTypes] = useState<RequestType[]>([]);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [results, setResults] = useState<MatchingResult[]>([]);
  const [documents, setDocuments] = useState<GeneratedDocumentInfo[]>([]);
  const [failedDocuments, setFailedDocuments] = useState<
    { request_item_id: string; request_type_id: string; reason: string }[]
  >([]);
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

  const currentStep =
    documents.length > 0 || failedDocuments.length > 0
      ? 4
      : results.length > 0
        ? 3
        : building
          ? 2
          : 1;

  const handleRunMatching = async () => {
    if (!building || requestTypeIds.length === 0) return;
    setMatchingLoading(true);
    try {
      const response = await api.runMatching(building.building_id, requestTypeIds);
      setRequestId(response.request_id);
      setResults(response.results);
      setDocuments([]);
    } catch (error) {
      showToast("error", errorMessage(error, "Zuständigkeiten konnten nicht ermittelt werden."));
    } finally {
      setMatchingLoading(false);
    }
  };

  const handleAssigned = (requestItemId: string, authorityId: string) => {
    setResults((prev) =>
      prev.map((r) =>
        r.request_item_id === requestItemId
          ? { ...r, authority_id: authorityId, matching_status: "MATCHED", matching_confidence: 1.0 }
          : r
      )
    );
  };

  const handleGenerate = async () => {
    if (!requestId) return;
    setGenerating(true);
    try {
      const response = await api.generateDocuments(requestId);
      setDocuments(response.documents);
      setFailedDocuments(response.failed);
      if (response.failed.length > 0) {
        showToast(
          "error",
          `${response.failed.length} Schreiben konnten nicht generiert werden.`
        );
      }
    } catch (error) {
      showToast("error", errorMessage(error, "Schreiben konnten nicht generiert werden."));
    } finally {
      setGenerating(false);
    }
  };

  const allMatched =
    results.length > 0 && results.every((r) => r.matching_status === "MATCHED");

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
            </h2>
            <BuildingSearch
              onSelect={(b) => {
                setBuilding(b);
                setResults([]);
                setDocuments([]);
                setFailedDocuments([]);
                setRequestId(null);
              }}
            />
            {building && (
              <div className="mt-4">
                <BuildingDetails building={building} />
              </div>
            )}
          </section>

          {/* Schritt 2: Auskünfte wählen */}
          {building && (
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
                  {matchingLoading ? "Ermittle Zuständigkeiten…" : "Zuständige Ämter ermitteln"}
                </Button>
              </div>
            </section>
          )}

          {/* Schritt 3: Matching-Ergebnisse */}
          {results.length > 0 && (
            <section>
              <h2 className="mb-3 font-display text-sm font-semibold text-ink">
                3. Zuständigkeiten prüfen
              </h2>
              <MatchingResults
                results={results}
                requestTypeNames={requestTypeNames}
                onAssigned={handleAssigned}
              />
              <div className="mt-4">
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
          {(documents.length > 0 || failedDocuments.length > 0) && requestId && (
            <section>
              <h2 className="mb-3 font-display text-sm font-semibold text-ink">
                4. Schreiben herunterladen
              </h2>
              <GeneratedDocuments
                requestId={requestId}
                documents={documents}
                failed={failedDocuments}
                requestTypeNames={requestTypeNames}
              />
            </section>
          )}
        </div>
      </main>
      )}
    </div>
  );
}

export default App;

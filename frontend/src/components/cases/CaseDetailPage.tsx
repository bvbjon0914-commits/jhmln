import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  Loader2,
  Send,
  Upload,
  Download,
  CheckCircle2,
  X,
  FileSearch2,
  Mail,
} from "lucide-react";
import { api } from "../../services/api";
import { Button } from "../common/Button";
import { CollapsibleSection } from "../common/CollapsibleSection";
import { BuildingSearch } from "../BuildingSearch";
import { RequestTypeSelector } from "../RequestTypeSelector";
import { useToast, errorMessage } from "../common/Toast";
import { useAuth } from "../auth/AuthContext";
import { ProgressBadge } from "./ProgressBadge";
import type { CaseDetail, CaseRequestItem } from "../../types/case";
import type { RequestType } from "../../types/matching";
import { computeSequencingHints } from "../../types/sequencing";
import type { Building } from "../../types/building";

interface Props {
  caseId: string;
  onBack: () => void;
}

function buildingLabel(b: Building): string {
  return `${b.street} ${b.house_number}, ${b.city}`;
}

export function CaseDetailPage({ caseId, onBack }: Props) {
  const { showToast } = useToast();
  const { isMain } = useAuth();
  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [requestTypes, setRequestTypes] = useState<RequestType[]>([]);
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [savingHeader, setSavingHeader] = useState(false);

  const load = () => {
    api
      .getCase(caseId)
      .then((data) => {
        setDetail(data);
        setName(data.name);
        setNotes(data.notes ?? "");
      })
      .catch((error) => showToast("error", errorMessage(error, "Auftrag konnte nicht geladen werden.")))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    api.listRequestTypes().then(setRequestTypes).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId]);

  const handleSaveHeader = async () => {
    if (!detail) return;
    setSavingHeader(true);
    try {
      await api.updateCase(caseId, { name: name.trim() || detail.name, notes });
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Auftrag konnte nicht gespeichert werden."));
    } finally {
      setSavingHeader(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!detail) return;
    try {
      await api.updateCase(caseId, { status: detail.status === "OPEN" ? "CLOSED" : "OPEN" });
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Status konnte nicht geändert werden."));
    }
  };

  const handleAddBuilding = async (building: Building) => {
    try {
      await api.addBuildingToCase(caseId, building.building_id);
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Gebäude konnte nicht hinzugefügt werden."));
    }
  };

  const handleRemoveBuilding = async (buildingId: string) => {
    if (!window.confirm("Gebäude aus diesem Auftrag entfernen? Anfragen/Dokumente bleiben erhalten.")) return;
    try {
      await api.removeBuildingFromCase(caseId, buildingId);
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Gebäude konnte nicht entfernt werden."));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-16 text-sm text-ink-faint">
        <Loader2 size={18} className="animate-spin" />
        Lade Auftrag…
      </div>
    );
  }

  if (!detail) return null;

  return (
    <div className="space-y-6">
      <button
        onClick={onBack}
        className="inline-flex items-center gap-1.5 text-xs text-ink-faint hover:text-ink"
      >
        <ArrowLeft size={13} /> Zurück zu Aufträgen
      </button>

      <div className="rounded-lg border border-line bg-surface p-5 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={handleSaveHeader}
            className="flex-1 border-none bg-transparent font-display text-lg font-semibold text-ink focus:outline-none"
          />
          <div className="flex shrink-0 items-center gap-2">
            {savingHeader && <Loader2 size={14} className="animate-spin text-ink-faint" />}
            <button
              onClick={handleToggleStatus}
              className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                detail.status === "OPEN"
                  ? "bg-status-matchedBg text-status-matched"
                  : "bg-status-neutralBg text-status-neutral"
              }`}
            >
              {detail.status === "OPEN" ? "Offen" : "Abgeschlossen"}
            </button>
          </div>
        </div>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          onBlur={handleSaveHeader}
          placeholder="Notizen zu diesem Auftrag…"
          rows={2}
          className="mt-2 w-full resize-none rounded-md border border-line bg-paper/30 px-3 py-2 text-sm text-ink-soft focus:border-brand focus:outline-none"
        />
      </div>

      {isMain && <SendBundlesSection caseId={caseId} items={detail.items} onSent={load} />}

      <section>
        <h3 className="mb-2 font-display text-sm font-semibold text-ink">Gebäude</h3>
        <BuildingSearch
          onSelect={handleAddBuilding}
          excludeIds={detail.buildings.map((b) => b.building_id)}
        />

        <div className="mt-4 space-y-2">
          {detail.buildings.length === 0 ? (
            <p className="text-sm text-ink-faint">Noch keine Gebäude in diesem Auftrag.</p>
          ) : (
            detail.buildings.map((building) => (
              <CaseBuildingSection
                key={building.building_id}
                caseId={caseId}
                building={building}
                items={detail.items.filter((i) => i.building_id === building.building_id)}
                requestTypes={requestTypes}
                onRemoveBuilding={() => handleRemoveBuilding(building.building_id)}
                onRequestLinked={load}
                onItemChanged={load}
              />
            ))
          )}
        </div>
      </section>
    </div>
  );
}

function SendBundlesSection({
  caseId,
  items,
  onSent,
}: {
  caseId: string;
  items: CaseRequestItem[];
  onSent: () => void;
}) {
  const { showToast } = useToast();
  const [sendingAuthorityId, setSendingAuthorityId] = useState<string | null>(null);

  const ready = items.filter((i) => i.status === "BEREIT_ZUM_SENDEN" && i.authority_id);
  if (ready.length === 0) return null;

  const groups = new Map<string, CaseRequestItem[]>();
  for (const item of ready) {
    const list = groups.get(item.authority_id!) ?? [];
    list.push(item);
    groups.set(item.authority_id!, list);
  }

  const handleSend = async (authorityId: string, group: CaseRequestItem[]) => {
    const names = group.map((i) => i.request_type_name).join(", ");
    if (
      !window.confirm(
        `E-Mail mit ${group.length} Schreiben (${names}) jetzt an ${group[0].authority_name} senden? Dies versendet eine echte E-Mail.`
      )
    ) {
      return;
    }
    setSendingAuthorityId(authorityId);
    try {
      const result = await api.sendBundle(
        caseId,
        group.map((i) => i.request_item_id)
      );
      showToast(
        "success",
        result.dry_run
          ? `Dry-Run: ${result.sent} Schreiben wären versendet worden (Mailgun nicht konfiguriert/live).`
          : `${result.sent} Schreiben an ${group[0].authority_name} versendet.`
      );
      onSent();
    } catch (error) {
      showToast("error", errorMessage(error, "Versand fehlgeschlagen."));
    } finally {
      setSendingAuthorityId(null);
    }
  };

  return (
    <div className="space-y-2">
      <h3 className="font-display text-sm font-semibold text-ink">Bereit zum Versand</h3>
      {Array.from(groups.entries()).map(([authorityId, group]) => (
        <div
          key={authorityId}
          className="flex items-center justify-between gap-4 rounded-lg border border-line bg-surface p-4 shadow-sm"
        >
          <div className="min-w-0">
            <div className="text-sm font-medium text-ink">{group[0].authority_name}</div>
            <div className="mt-0.5 text-xs text-ink-faint">
              {group.length} Schreiben ·{" "}
              {group.map((i) => i.aktenzeichen || i.request_type_name).join(", ")}
            </div>
            {!group[0].authority_email && (
              <div className="mt-1 text-xs text-status-conflict">Keine E-Mail-Adresse hinterlegt</div>
            )}
          </div>
          <Button
            variant="secondary"
            onClick={() => handleSend(authorityId, group)}
            disabled={!group[0].authority_email || sendingAuthorityId === authorityId}
          >
            {sendingAuthorityId === authorityId ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Mail size={14} />
            )}
            Jetzt per E-Mail senden
          </Button>
        </div>
      ))}
    </div>
  );
}

function CaseBuildingSection({
  caseId,
  building,
  items,
  requestTypes,
  onRemoveBuilding,
  onRequestLinked,
  onItemChanged,
}: {
  caseId: string;
  building: Building;
  items: CaseRequestItem[];
  requestTypes: RequestType[];
  onRemoveBuilding: () => void;
  onRequestLinked: () => void;
  onItemChanged: () => void;
}) {
  const { showToast } = useToast();
  const [selectedTypeIds, setSelectedTypeIds] = useState<string[]>([]);
  const [matching, setMatching] = useState(false);
  const alreadyRequestedTypeIds = new Set(items.map((i) => i.request_type_id));
  const availableTypes = requestTypes.filter((t) => !alreadyRequestedTypeIds.has(t.request_type_id));

  const doneCount = items.filter((i) => i.status === "GEPRUEFT").length;
  const summary = items.length === 0 ? "keine Auskünfte" : `${doneCount}/${items.length} geprüft`;

  const handleRunMatching = async () => {
    if (selectedTypeIds.length === 0) return;
    setMatching(true);
    try {
      const response = await api.runMatching(building.building_id, selectedTypeIds);
      await api.linkRequestToCase(caseId, response.request_id);
      setSelectedTypeIds([]);
      onRequestLinked();
    } catch (error) {
      showToast("error", errorMessage(error, "Zuständigkeiten konnten nicht ermittelt werden."));
    } finally {
      setMatching(false);
    }
  };

  return (
    <CollapsibleSection
      title={buildingLabel(building)}
      defaultExpanded={false}
      summary={
        <span className="shrink-0 text-xs font-medium text-ink-faint">{summary}</span>
      }
    >
      <div className="space-y-4 rounded-lg border border-line bg-surface p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs text-ink-faint">Auftrag</span>
          <button
            onClick={onRemoveBuilding}
            className="inline-flex items-center gap-1 text-xs text-ink-faint hover:text-status-conflict"
          >
            <X size={12} /> Gebäude entfernen
          </button>
        </div>

        {items.length > 0 && (
          <div className="overflow-x-auto rounded-md border border-line">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="border-b border-line bg-paper/50 text-left text-[11px] uppercase tracking-wide text-ink-faint">
                  <th className="px-3 py-2 font-medium">Auskunft</th>
                  <th className="px-3 py-2 font-medium">Behörde</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 font-medium">Aktionen</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <CaseItemRow key={item.request_item_id} item={item} onChanged={onItemChanged} />
                ))}
              </tbody>
            </table>
          </div>
        )}

        {availableTypes.length > 0 && (
          <div>
            <RequestTypeSelector
              types={availableTypes}
              selected={selectedTypeIds}
              onChange={setSelectedTypeIds}
              hints={computeSequencingHints(selectedTypeIds, Array.from(alreadyRequestedTypeIds))}
            />
            <div className="mt-3">
              <Button onClick={handleRunMatching} disabled={selectedTypeIds.length === 0 || matching}>
                <FileSearch2 size={15} />
                {matching ? "Ermittle Zuständigkeiten…" : "Zuständigkeiten ermitteln"}
              </Button>
            </div>
          </div>
        )}
      </div>
    </CollapsibleSection>
  );
}

function CaseItemRow({ item, onChanged }: { item: CaseRequestItem; onChanged: () => void }) {
  const { showToast } = useToast();
  const [busy, setBusy] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const run = async (action: () => Promise<void>, errorMsg: string) => {
    setBusy(true);
    try {
      await action();
      onChanged();
    } catch (error) {
      showToast("error", errorMessage(error, errorMsg));
    } finally {
      setBusy(false);
    }
  };

  return (
    <tr className="border-b border-line last:border-0">
      <td className="px-3 py-2.5">
        <div className="font-medium text-ink">{item.request_type_name}</div>
        {item.aktenzeichen && (
          <div className="mt-0.5 font-mono text-[11px] text-ink-faint">{item.aktenzeichen}</div>
        )}
      </td>
      <td className="px-3 py-2.5 text-ink-soft">{item.authority_name || "—"}</td>
      <td className="px-3 py-2.5">
        <ProgressBadge status={item.status} />
      </td>
      <td className="px-3 py-2.5">
        <div className="flex items-center gap-1">
          {busy && <Loader2 size={13} className="animate-spin text-ink-faint" />}
          {item.status === "NICHT_BEANTRAGT" && item.matching_status === "MATCHED" && !busy && (
            <Button
              variant="ghost"
              className="text-xs"
              onClick={() =>
                run(() => api.generateDocuments(item.request_id).then(() => undefined), "Schreiben konnte nicht generiert werden.")
              }
            >
              <FileSearch2 size={13} /> Schreiben generieren
            </Button>
          )}
          {item.status === "BEREIT_ZUM_SENDEN" && !busy && (
            <Button
              variant="ghost"
              className="text-xs"
              onClick={() => run(() => api.markItemSent(item.request_item_id), "Konnte nicht als gesendet markiert werden.")}
            >
              <Send size={13} /> Als gesendet markieren
            </Button>
          )}
          {(item.status === "GESENDET" || item.status === "ANTWORT_ERHALTEN") && !busy && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  e.target.value = "";
                  if (file) {
                    run(
                      () => api.uploadItemResponse(item.request_item_id, file),
                      "Antwort konnte nicht hochgeladen werden."
                    );
                  }
                }}
              />
              {item.status === "GESENDET" && (
                <Button variant="ghost" className="text-xs" onClick={() => fileInputRef.current?.click()}>
                  <Upload size={13} /> Antwort hochladen
                </Button>
              )}
            </>
          )}
          {item.response_document_filename && !busy && (
            <a href={api.itemResponseDownloadUrl(item.request_item_id)} download>
              <Button variant="ghost" className="text-xs">
                <Download size={13} /> Herunterladen
              </Button>
            </a>
          )}
          {item.status === "ANTWORT_ERHALTEN" && !busy && (
            <Button
              variant="ghost"
              className="text-xs"
              onClick={() =>
                run(() => api.markItemReviewed(item.request_item_id), "Konnte nicht als geprüft markiert werden.")
              }
            >
              <CheckCircle2 size={13} /> Als geprüft markieren
            </Button>
          )}
        </div>
      </td>
    </tr>
  );
}

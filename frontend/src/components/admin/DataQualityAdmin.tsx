import { useEffect, useState } from "react";
import {
  Loader2,
  MailWarning,
  Link2Off,
  MapPinOff,
  FileSpreadsheet,
  Eraser,
  Copy,
  AlertTriangle,
  ShieldQuestion,
  Unlink,
} from "lucide-react";
import { api } from "../../services/api";
import { Button } from "../common/Button";
import { useAuth } from "../auth/AuthContext";
import { useToast, errorMessage } from "../common/Toast";
import type {
  DataQualitySummary,
  DataQualityGroup,
  AuthorityRef,
  BuildingRef,
  JurisdictionRef,
} from "../../types/dataQuality";
import type { Tab } from "./AdminPage";

function GroupCard<T extends { }>({
  icon,
  title,
  description,
  group,
  itemKey,
  renderItem,
  onNavigate,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  group: { count: number; items: T[] };
  itemKey: (item: T) => string;
  renderItem: (item: T) => React.ReactNode;
  onNavigate?: () => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-line bg-surface shadow-sm">
      <div className="flex items-start gap-3 px-4 py-3.5">
        <div className="mt-0.5 text-status-review">{icon}</div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-display text-sm font-semibold text-ink">{title}</h3>
            {group.count > 0 && onNavigate ? (
              <button
                onClick={onNavigate}
                title="In der Verwaltung anzeigen"
                className="rounded-full bg-status-reviewBg px-2 py-0.5 text-xs font-medium text-status-review hover:underline"
              >
                {group.count}
              </button>
            ) : (
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  group.count === 0
                    ? "bg-status-matchedBg text-status-matched"
                    : "bg-status-reviewBg text-status-review"
                }`}
              >
                {group.count}
              </span>
            )}
          </div>
          <p className="mt-0.5 text-xs text-ink-faint">{description}</p>
          {group.count > 0 && (
            <button
              onClick={() => setExpanded((e) => !e)}
              className="mt-2 text-xs font-medium text-brand hover:underline"
            >
              {expanded ? "Liste ausblenden" : "Liste anzeigen"}
            </button>
          )}
        </div>
      </div>
      {expanded && group.count > 0 && (
        <div className="max-h-72 overflow-y-auto border-t border-line">
          {group.items.map((item) => (
            <div
              key={itemKey(item)}
              className="flex items-center justify-between gap-3 border-b border-line px-4 py-2 text-sm last:border-0"
            >
              {renderItem(item)}
            </div>
          ))}
          {group.count > group.items.length && (
            <div className="px-4 py-2 text-xs text-ink-faint">
              … und {group.count - group.items.length} weitere
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function renderAuthorityRow(a: AuthorityRef) {
  return (
    <>
      <span className="text-ink">{a.authority_name}</span>
      <span className="shrink-0 text-xs text-ink-faint">{a.city || "—"}</span>
    </>
  );
}

function renderBuildingRow(b: BuildingRef) {
  const address = [b.street, b.house_number].filter(Boolean).join(" ") || "—";
  return (
    <>
      <span className="text-ink">{address}</span>
      <span className="shrink-0 text-xs text-ink-faint">
        {[b.postal_code, b.city].filter(Boolean).join(" ") || "—"}
      </span>
    </>
  );
}

function renderJurisdictionRow(j: JurisdictionRef) {
  return (
    <>
      <span className="text-ink">
        {j.authority_name} · {j.request_type_name}
      </span>
      <span className="shrink-0 text-xs text-ink-faint">{j.ags || j.municipality || "—"}</span>
    </>
  );
}

export function DataQualityAdmin({
  onNavigate,
}: {
  onNavigate?: (tab: Tab, filterKey: string, value?: string) => void;
} = {}) {
  const { showToast } = useToast();
  const { isMain } = useAuth();
  const [summary, setSummary] = useState<DataQualitySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);
  const [merging, setMerging] = useState(false);
  const [deletingBuildings, setDeletingBuildings] = useState(false);
  const [mergingJurisdictions, setMergingJurisdictions] = useState(false);
  const [mergingBuildings, setMergingBuildings] = useState(false);

  const load = () => {
    api
      .getDataQualitySummary()
      .then(setSummary)
      .catch((error) => showToast("error", errorMessage(error, "Datenqualität konnte nicht geladen werden.")))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleClearBadGeocoding = async () => {
    if (
      !window.confirm(
        "Gecachte Kartenkoordinaten von Behörden ohne Adresse entfernen? Diese könnten fälschlich auf den geografischen Mittelpunkt Deutschlands zeigen."
      )
    ) {
      return;
    }
    setClearing(true);
    try {
      const result = await api.clearBadGeocoding();
      showToast(
        "success",
        result.deleted > 0
          ? `${result.deleted} fehlerhafte Kartenpins entfernt.`
          : "Keine fehlerhaften Kartenpins gefunden."
      );
    } catch (error) {
      showToast("error", errorMessage(error, "Bereinigung fehlgeschlagen."));
    } finally {
      setClearing(false);
    }
  };

  const handleMergeDuplicates = async () => {
    if (
      !window.confirm(
        "Erkannte Behörden-Duplikate zusammenführen? Die jeweils vollständigere Zeile wird gelöscht, nachdem ihre Daten in die verbleibende Behörde übernommen wurden."
      )
    ) {
      return;
    }
    setMerging(true);
    try {
      const result = await api.mergeDuplicateAuthorities();
      showToast(
        "success",
        result.removed > 0
          ? `${result.removed} Duplikate in ${result.merged_groups} Behörden zusammengeführt.`
          : "Keine automatisch auflösbaren Duplikate gefunden."
      );
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Zusammenführen fehlgeschlagen."));
    } finally {
      setMerging(false);
    }
  };

  const handleDeleteReviewRequiredBuildings = async () => {
    if (
      !window.confirm(
        "Gebäude löschen, deren zuletzt ermittelte Zuständigkeit 'Prüfung nötig' ist? Das Gebäude sowie seine Anfrage-Historie werden dabei entfernt. Gebäude mit bereits versendeten Anfragen oder erhaltenen Antworten werden übersprungen."
      )
    ) {
      return;
    }
    setDeletingBuildings(true);
    try {
      const result = await api.deleteReviewRequiredBuildings();
      showToast(
        "success",
        result.deleted > 0
          ? `${result.deleted} Gebäude gelöscht.${result.skipped > 0 ? ` ${result.skipped} übersprungen (bereits in Bearbeitung).` : ""}`
          : "Keine automatisch löschbaren Gebäude gefunden."
      );
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Löschen fehlgeschlagen."));
    } finally {
      setDeletingBuildings(false);
    }
  };

  const handleMergeDuplicateJurisdictions = async () => {
    if (
      !window.confirm(
        "Erkannte Zuständigkeits-Duplikate zusammenführen? Die jeweils neuere, nachweislich identische Regel wird gelöscht."
      )
    ) {
      return;
    }
    setMergingJurisdictions(true);
    try {
      const result = await api.mergeDuplicateJurisdictions();
      showToast(
        "success",
        result.removed > 0
          ? `${result.removed} Duplikate in ${result.merged_groups} Regeln zusammengeführt.`
          : "Keine automatisch auflösbaren Duplikate gefunden."
      );
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Zusammenführen fehlgeschlagen."));
    } finally {
      setMergingJurisdictions(false);
    }
  };

  const handleMergeDuplicateBuildings = async () => {
    if (
      !window.confirm(
        "Erkannte Gebäude-Duplikate zusammenführen? Das referenzierte (bzw. älteste) Gebäude bleibt erhalten, referenzlose Duplikate werden gelöscht."
      )
    ) {
      return;
    }
    setMergingBuildings(true);
    try {
      const result = await api.mergeDuplicateBuildings();
      showToast(
        "success",
        result.removed > 0
          ? `${result.removed} Duplikate in ${result.merged_groups} Gebäuden zusammengeführt.`
          : "Keine automatisch auflösbaren Duplikate gefunden."
      );
      load();
    } catch (error) {
      showToast("error", errorMessage(error, "Zusammenführen fehlgeschlagen."));
    } finally {
      setMergingBuildings(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-10 text-sm text-ink-faint">
        <Loader2 size={16} className="animate-spin" />
        Lade Datenqualität…
      </div>
    );
  }

  if (!summary) return null;

  const hasGaps =
    summary.authorities_without_email.count > 0 ||
    summary.authorities_without_jurisdiction.count > 0 ||
    summary.authorities_without_address.count > 0;

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <p className="text-sm text-ink-soft">
          {summary.total_authorities} aktive Behörden. Lücken hier zu schließen verhindert spätere
          Prüffälle beim Matching und fehlende E-Mail-Buttons.
        </p>
        {hasGaps && (
          <a href={api.exportDataQualityXlsxUrl()} download className="shrink-0">
            <Button variant="secondary">
              <FileSpreadsheet size={15} />
              Als Excel exportieren
            </Button>
          </a>
        )}
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <GroupCard
          icon={<MailWarning size={16} />}
          title="Behörden ohne E-Mail"
          description="Für diese Behörden kann kein „E-Mail öffnen“-Button angezeigt werden."
          group={summary.authorities_without_email}
          itemKey={(a) => a.authority_id}
          renderItem={renderAuthorityRow}
          onNavigate={onNavigate ? () => onNavigate("authorities", "without_email") : undefined}
        />
        <GroupCard
          icon={<Link2Off size={16} />}
          title="Behörden ohne Zuständigkeit"
          description="Diese Behörden sind in keiner Zuständigkeitsregel hinterlegt und werden vom Matching nie gefunden."
          group={summary.authorities_without_jurisdiction}
          itemKey={(a) => a.authority_id}
          renderItem={renderAuthorityRow}
          onNavigate={onNavigate ? () => onNavigate("authorities", "without_jurisdiction") : undefined}
        />
        <GroupCard
          icon={<MapPinOff size={16} />}
          title="Behörden ohne Adresse"
          description="Ohne Straße und Ort kann kein korrekter Kartenpin ermittelt werden."
          group={summary.authorities_without_address}
          itemKey={(a) => a.authority_id}
          renderItem={renderAuthorityRow}
          onNavigate={onNavigate ? () => onNavigate("authorities", "without_address") : undefined}
        />
        <GroupCard
          icon={<Copy size={16} />}
          title="Behörden-Duplikate"
          description="Entstehen z.B., wenn ein Import eine bisher adresslose Behörde nicht wiedererkennt und sie doppelt anlegt."
          group={summary.duplicate_authorities}
          itemKey={(a) => a.authority_id}
          renderItem={renderAuthorityRow}
          onNavigate={onNavigate ? () => onNavigate("authorities", "duplicate") : undefined}
        />
        <GroupCard
          icon={<AlertTriangle size={16} />}
          title="Gebäude mit Prüfung nötig"
          description="Die zuletzt ermittelte Zuständigkeit war nicht eindeutig (keine Behörde gefunden)."
          group={summary.buildings_review_required}
          itemKey={(b) => b.building_id}
          renderItem={renderBuildingRow}
          onNavigate={onNavigate ? () => onNavigate("buildings", "review_required") : undefined}
        />
        <GroupCard
          icon={<ShieldQuestion size={16} />}
          title="Nicht verifizierte Behörden"
          description="Diese Behörden wurden noch nie als aktuell/korrekt bestätigt."
          group={summary.authorities_unverified}
          itemKey={(a) => a.authority_id}
          renderItem={renderAuthorityRow}
          onNavigate={onNavigate ? () => onNavigate("authorities", "unverified") : undefined}
        />
        <GroupCard
          icon={<Unlink size={16} />}
          title="Verwaiste Zuständigkeiten"
          description="Diese Zuständigkeitsregeln verweisen auf eine inzwischen deaktivierte Behörde."
          group={summary.jurisdictions_orphaned}
          itemKey={(j) => j.jurisdiction_id}
          renderItem={renderJurisdictionRow}
          onNavigate={onNavigate ? () => onNavigate("jurisdictions", "orphaned") : undefined}
        />
        <GroupCard
          icon={<Copy size={16} />}
          title="Zuständigkeits-Duplikate"
          description="Mehrere, inhaltlich identische Regeln für dieselbe Behörde und dasselbe Gebiet."
          group={summary.duplicate_jurisdictions}
          itemKey={(j) => j.jurisdiction_id}
          renderItem={renderJurisdictionRow}
          onNavigate={onNavigate ? () => onNavigate("jurisdictions", "duplicate") : undefined}
        />
        <GroupCard
          icon={<Copy size={16} />}
          title="Gebäude-Duplikate"
          description="Mehrere Gebäude-Einträge mit derselben Adresse."
          group={summary.duplicate_buildings}
          itemKey={(b) => b.building_id}
          renderItem={renderBuildingRow}
          onNavigate={onNavigate ? () => onNavigate("buildings", "duplicate") : undefined}
        />
      </div>

      {isMain && summary.duplicate_authorities.count > 0 && (
        <div className="rounded-lg border border-line bg-surface p-4 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="font-display text-sm font-semibold text-ink">Duplikate zusammenführen</h3>
              <p className="mt-0.5 text-xs text-ink-faint">
                {summary.duplicate_authorities.count} Behörden werden als Duplikat einer bestehenden
                Behörde erkannt und können automatisch zusammengeführt werden (Adressdaten werden
                übernommen, die Duplikat-Zeile gelöscht).
                {summary.duplicate_authorities.needs_review_count > 0 &&
                  ` ${summary.duplicate_authorities.needs_review_count} weitere Fälle sind nicht eindeutig und bleiben zur manuellen Prüfung stehen.`}
              </p>
            </div>
            <Button variant="secondary" onClick={handleMergeDuplicates} disabled={merging}>
              {merging ? <Loader2 size={14} className="animate-spin" /> : <Copy size={14} />}
              Zusammenführen
            </Button>
          </div>
        </div>
      )}

      {isMain && summary.duplicate_jurisdictions.count > 0 && (
        <div className="rounded-lg border border-line bg-surface p-4 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="font-display text-sm font-semibold text-ink">
                Zuständigkeits-Duplikate zusammenführen
              </h3>
              <p className="mt-0.5 text-xs text-ink-faint">
                {summary.duplicate_jurisdictions.count} Zuständigkeitsregeln sind inhaltlich identisch zu
                einer bereits vorhandenen Regel und können automatisch entfernt werden.
                {summary.duplicate_jurisdictions.needs_review_count > 0 &&
                  ` ${summary.duplicate_jurisdictions.needs_review_count} weitere Fälle weichen in einzelnen Feldern ab und bleiben zur manuellen Prüfung stehen.`}
              </p>
            </div>
            <Button variant="secondary" onClick={handleMergeDuplicateJurisdictions} disabled={mergingJurisdictions}>
              {mergingJurisdictions ? <Loader2 size={14} className="animate-spin" /> : <Copy size={14} />}
              Zusammenführen
            </Button>
          </div>
        </div>
      )}

      {isMain && summary.duplicate_buildings.count > 0 && (
        <div className="rounded-lg border border-line bg-surface p-4 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="font-display text-sm font-semibold text-ink">Gebäude-Duplikate zusammenführen</h3>
              <p className="mt-0.5 text-xs text-ink-faint">
                {summary.duplicate_buildings.count} Gebäude haben dieselbe Adresse wie ein anderes Gebäude
                und können automatisch zusammengeführt werden (fehlende Angaben werden übernommen, das
                referenzlose Duplikat gelöscht).
                {summary.duplicate_buildings.needs_review_count > 0 &&
                  ` ${summary.duplicate_buildings.needs_review_count} weitere Fälle haben auf beiden Seiten eigene Anfrage-Historien und bleiben zur manuellen Prüfung stehen.`}
              </p>
            </div>
            <Button variant="secondary" onClick={handleMergeDuplicateBuildings} disabled={mergingBuildings}>
              {mergingBuildings ? <Loader2 size={14} className="animate-spin" /> : <Copy size={14} />}
              Zusammenführen
            </Button>
          </div>
        </div>
      )}

      {isMain && summary.buildings_review_required.count > 0 && (
        <div className="rounded-lg border border-line bg-surface p-4 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="font-display text-sm font-semibold text-ink">
                Gebäude mit Prüfung nötig löschen
              </h3>
              <p className="mt-0.5 text-xs text-ink-faint">
                {summary.buildings_review_required.count} Gebäude, deren zuletzt ermittelte
                Zuständigkeit keine eindeutige Behörde ergab, können samt ihrer Anfrage-Historie
                gelöscht werden.
                {summary.buildings_review_required.needs_review_count > 0 &&
                  ` ${summary.buildings_review_required.needs_review_count} davon haben bereits versendete Anfragen oder Antworten und werden übersprungen.`}
              </p>
            </div>
            <Button variant="secondary" onClick={handleDeleteReviewRequiredBuildings} disabled={deletingBuildings}>
              {deletingBuildings ? <Loader2 size={14} className="animate-spin" /> : <AlertTriangle size={14} />}
              Löschen
            </Button>
          </div>
        </div>
      )}

      {isMain && summary.authorities_without_address.count > 0 && (
        <div className="rounded-lg border border-line bg-surface p-4 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="font-display text-sm font-semibold text-ink">
                Fehlerhafte Kartenpins bereinigen
              </h3>
              <p className="mt-0.5 text-xs text-ink-faint">
                Behörden ohne Adresse konnten bisher fälschlich auf den geografischen Mittelpunkt
                Deutschlands (nahe Erfurt) geocodiert werden. Dieser Fehler ist behoben, bereits
                gecachte Fehltreffer bleiben aber bis zur Bereinigung bestehen.
              </p>
            </div>
            <Button variant="secondary" onClick={handleClearBadGeocoding} disabled={clearing}>
              {clearing ? <Loader2 size={14} className="animate-spin" /> : <Eraser size={14} />}
              Bereinigen
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

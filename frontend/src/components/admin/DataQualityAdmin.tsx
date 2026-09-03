import { useEffect, useState } from "react";
import { Loader2, MailWarning, Link2Off, MapPinOff, FileSpreadsheet, Eraser } from "lucide-react";
import { api } from "../../services/api";
import { Button } from "../common/Button";
import { useAuth } from "../auth/AuthContext";
import { useToast, errorMessage } from "../common/Toast";
import type { DataQualitySummary, DataQualityGroup, AuthorityRef } from "../../types/dataQuality";

function GroupCard({
  icon,
  title,
  description,
  group,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  group: DataQualityGroup;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-line bg-surface shadow-sm">
      <div className="flex items-start gap-3 px-4 py-3.5">
        <div className="mt-0.5 text-status-review">{icon}</div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-display text-sm font-semibold text-ink">{title}</h3>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                group.count === 0
                  ? "bg-status-matchedBg text-status-matched"
                  : "bg-status-reviewBg text-status-review"
              }`}
            >
              {group.count}
            </span>
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
          {group.items.map((a: AuthorityRef) => (
            <div
              key={a.authority_id}
              className="flex items-center justify-between gap-3 border-b border-line px-4 py-2 text-sm last:border-0"
            >
              <span className="text-ink">{a.authority_name}</span>
              <span className="shrink-0 text-xs text-ink-faint">{a.city || "—"}</span>
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

export function DataQualityAdmin() {
  const { showToast } = useToast();
  const { isMain } = useAuth();
  const [summary, setSummary] = useState<DataQualitySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);

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
        />
        <GroupCard
          icon={<Link2Off size={16} />}
          title="Behörden ohne Zuständigkeit"
          description="Diese Behörden sind in keiner Zuständigkeitsregel hinterlegt und werden vom Matching nie gefunden."
          group={summary.authorities_without_jurisdiction}
        />
        <GroupCard
          icon={<MapPinOff size={16} />}
          title="Behörden ohne Adresse"
          description="Ohne Straße und Ort kann kein korrekter Kartenpin ermittelt werden."
          group={summary.authorities_without_address}
        />
      </div>

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

import { useEffect, useState } from "react";
import { BuildingsAdmin } from "./BuildingsAdmin";
import { AuthoritiesAdmin } from "./AuthoritiesAdmin";
import { JurisdictionsAdmin } from "./JurisdictionsAdmin";
import { RequestsAdmin } from "./RequestsAdmin";
import { DataQualityAdmin } from "./DataQualityAdmin";
import { MailboxAdmin } from "./MailboxAdmin";
import { SettingsAdmin } from "./SettingsAdmin";
import type { AdminFilterRequest } from "../../types/adminFilter";

export type Tab =
  | "buildings"
  | "authorities"
  | "jurisdictions"
  | "requests"
  | "data-quality"
  | "mailbox"
  | "settings";

export function AdminPage({ isMain }: { isMain: boolean }) {
  const [tab, setTab] = useState<Tab>("buildings");
  const [pendingFilter, setPendingFilter] = useState<AdminFilterRequest | null>(null);

  const navigateWithFilter = (target: Tab, key: string, value?: string) => {
    setTab(target);
    setPendingFilter({ key, value });
  };

  useEffect(() => {
    // Wird von der Ziel-Komponente in ihrem Mount-Effect gelesen (feuert vor
    // diesem Effect); danach zurücksetzen, damit ein späteres manuelles
    // Zurückwechseln auf denselben Tab den Filter nicht erneut erzwingt.
    if (pendingFilter !== null) {
      setPendingFilter(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const tabs: { value: Tab; label: string }[] = [
    { value: "buildings", label: "Gebäude" },
    { value: "authorities", label: "Behörden" },
    { value: "jurisdictions", label: "Zuständigkeiten" },
    { value: "requests", label: "Anfragen" },
    { value: "data-quality", label: "Datenqualität" },
    ...(isMain ? [{ value: "mailbox" as Tab, label: "Postfach" }] : []),
    ...(isMain ? [{ value: "settings" as Tab, label: "Einstellungen" }] : []),
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display text-lg font-semibold text-ink">Verwaltung</h2>
        <p className="mt-1 text-sm text-ink-soft">
          Gebäude, Behörden, Zuständigkeitsregeln und Anfrage-Historie einsehen und pflegen.
        </p>
      </div>

      <div className="flex gap-1 border-b border-line">
        {tabs.map((t) => (
          <button
            key={t.value}
            onClick={() => setTab(t.value)}
            aria-current={tab === t.value ? "page" : undefined}
            className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
              tab === t.value
                ? "border-brand text-brand"
                : "border-transparent text-ink-faint hover:text-ink"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "buildings" && (
        <BuildingsAdmin
          initialFilter={pendingFilter}
          onShowRequests={(buildingId) => navigateWithFilter("requests", "building_id", buildingId)}
        />
      )}
      {tab === "authorities" && (
        <AuthoritiesAdmin
          initialFilter={pendingFilter}
          onShowJurisdictions={(authorityId) => navigateWithFilter("jurisdictions", "authority_id", authorityId)}
        />
      )}
      {tab === "jurisdictions" && <JurisdictionsAdmin initialFilter={pendingFilter} />}
      {tab === "requests" && <RequestsAdmin initialFilter={pendingFilter} />}
      {tab === "data-quality" && <DataQualityAdmin onNavigate={navigateWithFilter} />}
      {tab === "mailbox" && isMain && <MailboxAdmin />}
      {tab === "settings" && isMain && <SettingsAdmin />}
    </div>
  );
}

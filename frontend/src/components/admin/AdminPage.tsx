import { useState } from "react";
import { BuildingsAdmin } from "./BuildingsAdmin";
import { AuthoritiesAdmin } from "./AuthoritiesAdmin";
import { JurisdictionsAdmin } from "./JurisdictionsAdmin";
import { RequestsAdmin } from "./RequestsAdmin";
import { DataQualityAdmin } from "./DataQualityAdmin";
import { SettingsAdmin } from "./SettingsAdmin";

type Tab = "buildings" | "authorities" | "jurisdictions" | "requests" | "data-quality" | "settings";

export function AdminPage({ isMain }: { isMain: boolean }) {
  const [tab, setTab] = useState<Tab>("buildings");

  const tabs: { value: Tab; label: string }[] = [
    { value: "buildings", label: "Gebäude" },
    { value: "authorities", label: "Behörden" },
    { value: "jurisdictions", label: "Zuständigkeiten" },
    { value: "requests", label: "Anfragen" },
    { value: "data-quality", label: "Datenqualität" },
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

      {tab === "buildings" && <BuildingsAdmin />}
      {tab === "authorities" && <AuthoritiesAdmin />}
      {tab === "jurisdictions" && <JurisdictionsAdmin />}
      {tab === "requests" && <RequestsAdmin />}
      {tab === "data-quality" && <DataQualityAdmin />}
      {tab === "settings" && isMain && <SettingsAdmin />}
    </div>
  );
}

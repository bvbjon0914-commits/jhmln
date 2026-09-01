import { useState } from "react";
import { Loader2, MapPinPlus, CheckCircle2 } from "lucide-react";
import type { Building, GeoCandidate } from "../types/building";
import { api } from "../services/api";
import { Button } from "./common/Button";
import { useToast, errorMessage } from "./common/Toast";

interface Props {
  initialQuery?: string;
  onCreated: (building: Building) => void;
  onCancel: () => void;
}

type Stage = "form" | "candidates";

const BUNDESLAENDER = [
  "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg",
  "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen",
  "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt",
  "Schleswig-Holstein", "Thüringen",
];

export function NewBuildingForm({ initialQuery, onCreated, onCancel }: Props) {
  const { showToast } = useToast();
  const [stage, setStage] = useState<Stage>("form");
  const [loading, setLoading] = useState(false);

  const [street, setStreet] = useState("");
  const [houseNumber, setHouseNumber] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [city, setCity] = useState(initialQuery ?? "");
  const [stateFilter, setStateFilter] = useState("");
  const [propertyName, setPropertyName] = useState("");
  const [internalReference, setInternalReference] = useState("");
  const [manualAgs, setManualAgs] = useState("");

  const [candidates, setCandidates] = useState<GeoCandidate[]>([]);
  const [noMatch, setNoMatch] = useState(false);

  const manualAgsValid = /^\d{8}$/.test(manualAgs.trim());
  const canSubmitForm =
    Boolean(street.trim() && houseNumber.trim() && city.trim()) &&
    (manualAgs.trim() === "" || manualAgsValid);

  async function handleSubmit() {
    if (manualAgs.trim()) {
      await createWithAgs(manualAgs.trim(), stateFilter || null, true);
      return;
    }

    setLoading(true);
    try {
      const result = await api.resolveAgs(city.trim(), stateFilter || undefined);
      if (result.status === "MATCHED") {
        await createWithAgs(result.candidates[0].ags, result.candidates[0].state_name, false);
      } else if (result.status === "AMBIGUOUS") {
        setCandidates(result.candidates);
        setNoMatch(false);
        setStage("candidates");
      } else {
        setCandidates([]);
        setNoMatch(true);
        setStage("candidates");
      }
    } catch (error) {
      showToast("error", errorMessage(error, "Ortsauflösung fehlgeschlagen."));
    } finally {
      setLoading(false);
    }
  }

  async function createWithCandidate(candidate: GeoCandidate | null) {
    await createWithAgs(candidate?.ags ?? null, candidate?.state_name ?? (stateFilter || null), false);
  }

  async function createWithAgs(ags: string | null, state: string | null, manual: boolean) {
    setLoading(true);
    try {
      const building = await api.createBuilding({
        street: street.trim(),
        house_number: houseNumber.trim(),
        postal_code: postalCode.trim() || null,
        city: city.trim(),
        state,
        ags,
        property_name: propertyName.trim() || null,
        internal_reference: internalReference.trim() || null,
      });
      showToast(
        "success",
        ags
          ? `Gebäude angelegt, AGS ${ags} ${manual ? "manuell gesetzt" : "automatisch zugeordnet"}.`
          : "Gebäude angelegt (ohne AGS – Zuständigkeit muss ggf. manuell zugeordnet werden)."
      );
      onCreated(building);
    } catch (error) {
      showToast("error", errorMessage(error, "Gebäude konnte nicht angelegt werden."));
    } finally {
      setLoading(false);
    }
  }

  if (stage === "candidates") {
    return (
      <div className="rounded-lg border border-line bg-surface p-5 shadow-sm">
        <div className="mb-3 flex items-center gap-2 text-sm font-medium text-ink">
          <MapPinPlus size={16} className="text-brand" />
          {noMatch ? "Kein amtlicher Ort gefunden" : "Mehrere Orte gefunden – bitte auswählen"}
        </div>

        {noMatch ? (
          <div className="space-y-3">
            <p className="text-sm text-ink-soft">
              Für „{city}" konnte keine Gemeinde in der amtlichen Referenzliste gefunden
              werden. Das Gebäude kann trotzdem angelegt werden, aber die automatische
              Zuständigkeits-Zuordnung wird dann fehlschlagen, bis der AGS manuell gepflegt
              wird.
            </p>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setStage("form")}>
                Zurück
              </Button>
              <Button onClick={() => createWithCandidate(null)} disabled={loading}>
                {loading && <Loader2 size={14} className="animate-spin" />}
                Trotzdem anlegen
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="max-h-72 space-y-1.5 overflow-y-auto">
              {candidates.map((c) => (
                <button
                  key={c.ags}
                  onClick={() => createWithCandidate(c)}
                  disabled={loading}
                  className="flex w-full items-start justify-between gap-3 rounded border border-line px-3 py-2.5 text-left hover:border-brand hover:bg-brand-light/30 disabled:opacity-50"
                >
                  <div>
                    <div className="text-sm font-medium text-ink">
                      {c.municipality_name}
                    </div>
                    <div className="text-xs text-ink-soft">
                      {c.county_name && c.county_name !== c.municipality_name
                        ? `${c.county_name} · `
                        : ""}
                      {c.state_name}
                    </div>
                  </div>
                  <span className="mt-0.5 shrink-0 font-mono text-xs text-ink-faint">
                    {c.ags}
                  </span>
                </button>
              ))}
            </div>
            <Button variant="secondary" onClick={() => setStage("form")}>
              Zurück
            </Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <div className="mb-3 flex items-center gap-2 text-sm font-medium text-ink">
        <MapPinPlus size={16} className="text-brand" />
        Neues Gebäude anlegen
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="col-span-2 sm:col-span-3">
          <label className="mb-1 block text-xs text-ink-faint">Straße *</label>
          <input
            value={street}
            onChange={(e) => setStreet(e.target.value)}
            className="w-full rounded border border-line bg-surface px-3 py-2 text-sm focus:border-brand focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-ink-faint">Nr. *</label>
          <input
            value={houseNumber}
            onChange={(e) => setHouseNumber(e.target.value)}
            className="w-full rounded border border-line bg-surface px-3 py-2 text-sm focus:border-brand focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-ink-faint">PLZ (optional)</label>
          <input
            value={postalCode}
            onChange={(e) => setPostalCode(e.target.value)}
            className="w-full rounded border border-line bg-surface px-3 py-2 text-sm focus:border-brand focus:outline-none"
          />
        </div>
        <div className="col-span-2 sm:col-span-2">
          <label className="mb-1 block text-xs text-ink-faint">Ort *</label>
          <input
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="w-full rounded border border-line bg-surface px-3 py-2 text-sm focus:border-brand focus:outline-none"
          />
        </div>
        <div className="col-span-2 sm:col-span-2">
          <label className="mb-1 block text-xs text-ink-faint">
            Bundesland (optional, zur Eingrenzung)
          </label>
          <select
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            className="w-full rounded border border-line bg-surface px-3 py-2 text-sm focus:border-brand focus:outline-none"
          >
            <option value="">— egal —</option>
            {BUNDESLAENDER.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        </div>
        <div className="col-span-2 sm:col-span-2">
          <label className="mb-1 block text-xs text-ink-faint">
            AGS manuell (optional, überschreibt Ortsauflösung)
          </label>
          <input
            value={manualAgs}
            onChange={(e) => setManualAgs(e.target.value)}
            placeholder="z. B. 05911000"
            maxLength={8}
            inputMode="numeric"
            className={`w-full rounded border bg-surface px-3 py-2 text-sm font-mono focus:outline-none ${
              manualAgs.trim() && !manualAgsValid
                ? "border-status-conflict focus:border-status-conflict"
                : "border-line focus:border-brand"
            }`}
          />
          {manualAgs.trim() && !manualAgsValid && (
            <p className="mt-1 text-xs text-status-conflict">
              AGS muss 8-stellig numerisch sein.
            </p>
          )}
        </div>
        <div className="col-span-2">
          <label className="mb-1 block text-xs text-ink-faint">Objektname (optional)</label>
          <input
            value={propertyName}
            onChange={(e) => setPropertyName(e.target.value)}
            className="w-full rounded border border-line bg-surface px-3 py-2 text-sm focus:border-brand focus:outline-none"
          />
        </div>
        <div className="col-span-2">
          <label className="mb-1 block text-xs text-ink-faint">
            Interne Referenz (optional)
          </label>
          <input
            value={internalReference}
            onChange={(e) => setInternalReference(e.target.value)}
            className="w-full rounded border border-line bg-surface px-3 py-2 text-sm focus:border-brand focus:outline-none"
          />
        </div>
      </div>

      <div className="mt-4 flex items-center gap-2">
        <Button onClick={handleSubmit} disabled={!canSubmitForm || loading}>
          {loading ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />}
          {manualAgs.trim() ? "Gebäude anlegen" : "Ort ermitteln & anlegen"}
        </Button>
        <Button variant="secondary" onClick={onCancel} disabled={loading}>
          Abbrechen
        </Button>
      </div>
    </div>
  );
}

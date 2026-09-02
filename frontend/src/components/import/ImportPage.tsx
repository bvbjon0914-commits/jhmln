import { useEffect, useRef, useState } from "react";
import {
  UploadCloud,
  FileSpreadsheet,
  ArrowLeft,
  Loader2,
  CheckCircle2,
  Copy,
  AlertTriangle,
  XCircle,
} from "lucide-react";
import { api } from "../../services/api";
import { useToast, errorMessage } from "../common/Toast";
import { Button } from "../common/Button";
import type { RequestType } from "../../types/matching";
import {
  AUTHORITY_FIELDS,
  BUILDING_FIELDS,
  JURISDICTION_FIELDS,
  type ImportKind,
  type ImportPreview,
  type ImportSummary,
} from "../../types/import";

type Step = "upload" | "configure" | "result";

const STATUS_META: Record<
  string,
  { label: string; icon: React.ElementType; text: string; bg: string }
> = {
  IMPORTED: { label: "Importiert", icon: CheckCircle2, text: "text-status-matched", bg: "bg-status-matchedBg" },
  DUPLICATE: { label: "Duplikat", icon: Copy, text: "text-status-neutral", bg: "bg-status-neutralBg" },
  NEEDS_REVIEW: { label: "Prüfung nötig", icon: AlertTriangle, text: "text-status-review", bg: "bg-status-reviewBg" },
  ERROR: { label: "Fehler", icon: XCircle, text: "text-status-conflict", bg: "bg-status-conflictBg" },
};

export function ImportPage() {
  const { showToast } = useToast();
  const [step, setStep] = useState<Step>("upload");
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [kind, setKind] = useState<ImportKind>("buildings");
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [requestTypes, setRequestTypes] = useState<RequestType[]>([]);
  const [requestTypeId, setRequestTypeId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [summary, setSummary] = useState<ImportSummary | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.listRequestTypes().then(setRequestTypes).catch(() => undefined);
  }, []);

  const fields =
    kind === "authorities" ? AUTHORITY_FIELDS : kind === "buildings" ? BUILDING_FIELDS : JURISDICTION_FIELDS;

  const loadFile = async (f: File) => {
    setFile(f);
    setLoadingPreview(true);
    try {
      const p = await api.previewImport(f);
      setPreview(p);
      setMapping({});
      setStep("configure");
    } catch (error) {
      showToast("error", errorMessage(error, "Datei konnte nicht gelesen werden."));
      setFile(null);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const f = e.dataTransfer.files?.[0];
    if (f) loadFile(f);
  };

  const missingRequired = fields.filter((f) => f.required && !mapping[f.key]);
  const canSubmit =
    missingRequired.length === 0 && (kind !== "jurisdictions" || requestTypeId !== "");

  const handleSubmit = async () => {
    if (!file || !canSubmit) return;
    setSubmitting(true);
    try {
      const result =
        kind === "authorities"
          ? await api.importAuthorities(file, mapping)
          : kind === "buildings"
            ? await api.importBuildings(file, mapping)
            : await api.importJurisdictions(file, mapping, requestTypeId);
      setSummary(result);
      setStep("result");
    } catch (error) {
      showToast("error", errorMessage(error, "Import fehlgeschlagen."));
    } finally {
      setSubmitting(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setMapping({});
    setRequestTypeId("");
    setSummary(null);
    setStep("upload");
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-display text-lg font-semibold text-ink">Datenimport</h2>
        <p className="mt-1 text-sm text-ink-soft">
          Gebäude, Behörden, Kontaktdaten und AGS-Zuständigkeiten aus einer CSV- oder Excel-Datei
          importieren.
        </p>
      </div>

      {step === "upload" && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          className={`flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-16 text-center transition-all duration-200 ${
            dragActive
              ? "border-brand bg-brand-light/30 shadow-md"
              : "border-line bg-surface hover:border-brand/30"
          }`}
        >
          {loadingPreview ? (
            <Loader2 size={28} className="animate-spin text-brand" />
          ) : (
            <UploadCloud size={28} className="text-ink-faint" />
          )}
          <div>
            <p className="text-sm font-medium text-ink">
              Datei hierher ziehen oder auswählen
            </p>
            <p className="mt-1 text-xs text-ink-faint">CSV oder Excel (.xlsx)</p>
          </div>
          <Button
            variant="secondary"
            onClick={() => fileInputRef.current?.click()}
            disabled={loadingPreview}
          >
            Datei auswählen
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) loadFile(f);
              e.target.value = "";
            }}
          />
        </div>
      )}

      {step === "configure" && preview && (
        <div className="space-y-6">
          <button
            onClick={reset}
            className="inline-flex items-center gap-1.5 text-xs text-ink-faint hover:text-ink"
          >
            <ArrowLeft size={13} /> Andere Datei wählen
          </button>

          <div className="flex items-center gap-3 rounded-lg border border-line bg-surface px-4 py-3 shadow-sm">
            <FileSpreadsheet size={18} className="shrink-0 text-brand" />
            <div className="text-sm">
              <span className="font-medium text-ink">{file?.name}</span>
              <span className="ml-2 text-ink-faint">
                {preview.total_rows} Zeilen · {preview.columns.length} Spalten
              </span>
            </div>
          </div>

          <div>
            <h3 className="mb-2 font-display text-sm font-semibold text-ink">Was wird importiert?</h3>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              {(
                [
                  { value: "buildings" as const, label: "Gebäude", desc: "Adressliste der Gebäude, für die angefragt werden soll" },
                  { value: "authorities" as const, label: "Nur Behörden", desc: "Name & Kontaktdaten, ohne Zuständigkeiten" },
                  { value: "jurisdictions" as const, label: "Zuständigkeiten (Ämter + AGS)", desc: "Behörde, Kontaktdaten und AGS-Zuordnung" },
                ]
              ).map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => {
                    setKind(opt.value);
                    setMapping({});
                  }}
                  className={`rounded-lg border px-3.5 py-3 text-left text-sm transition-all duration-150 ${
                    kind === opt.value
                      ? "border-brand bg-brand-light/50 text-ink shadow-sm"
                      : "border-line bg-surface text-ink-soft hover:border-brand/40 hover:shadow-sm"
                  }`}
                >
                  <div className="font-medium">{opt.label}</div>
                  <div className="mt-0.5 text-xs text-ink-faint">{opt.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {kind === "jurisdictions" && (
            <div>
              <label className="mb-1.5 block text-xs font-medium text-ink-soft">
                Auskunftsart (gilt für die gesamte Datei)
              </label>
              <select
                value={requestTypeId}
                onChange={(e) => setRequestTypeId(e.target.value)}
                className="w-full rounded-lg border border-line bg-surface px-3 py-2.5 text-sm text-ink focus:border-brand focus:outline-none"
              >
                <option value="">— auswählen —</option>
                {requestTypes.map((t) => (
                  <option key={t.request_type_id} value={t.request_type_id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <h3 className="mb-2 font-display text-sm font-semibold text-ink">Spalten zuordnen</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {fields.map((f) => (
                <div key={f.key}>
                  <label className="mb-1.5 block text-xs font-medium text-ink-soft">
                    {f.label}
                    {f.required && <span className="text-status-conflict"> *</span>}
                  </label>
                  <select
                    value={mapping[f.key] || ""}
                    onChange={(e) =>
                      setMapping((prev) => ({ ...prev, [f.key]: e.target.value }))
                    }
                    className="w-full rounded-lg border border-line bg-surface px-3 py-2.5 text-sm text-ink focus:border-brand focus:outline-none"
                  >
                    <option value="">— nicht zuordnen —</option>
                    {preview.columns.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto rounded-lg border border-line">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-line bg-paper/50 text-left uppercase tracking-wide text-ink-faint">
                  {preview.columns.map((c) => (
                    <th key={c} className="whitespace-nowrap px-3 py-2 font-medium">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.preview_rows.map((row, i) => (
                  <tr key={i} className="border-b border-line last:border-0">
                    {preview.columns.map((c) => (
                      <td key={c} className="whitespace-nowrap px-3 py-2 text-ink-soft">
                        {String(row[c] ?? "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <Button onClick={handleSubmit} disabled={!canSubmit || submitting}>
              {submitting ? "Importiere…" : "Import starten"}
            </Button>
            {missingRequired.length > 0 && (
              <p className="mt-2 text-xs text-ink-faint">
                Noch nicht zugeordnet: {missingRequired.map((f) => f.label).join(", ")}
              </p>
            )}
          </div>
        </div>
      )}

      {step === "result" && summary && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: "Importiert", value: summary.imported, className: "text-status-matched" },
              { label: "Duplikate", value: summary.duplicates, className: "text-status-neutral" },
              { label: "Zur Prüfung", value: summary.needs_review, className: "text-status-review" },
              { label: "Fehler", value: summary.errors, className: "text-status-conflict" },
            ].map((s) => (
              <div key={s.label} className="rounded-lg border border-line bg-surface p-4 shadow-sm">
                <div className={`text-2xl font-display font-semibold ${s.className}`}>
                  {s.value}
                </div>
                <div className="mt-0.5 text-xs text-ink-faint">{s.label}</div>
              </div>
            ))}
          </div>

          <div className="overflow-hidden rounded-lg border border-line bg-surface shadow-sm">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line bg-paper/50 text-left text-[11px] uppercase tracking-wide text-ink-faint">
                  <th className="px-4 py-3 font-medium">Zeile</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Meldung</th>
                </tr>
              </thead>
              <tbody>
                {summary.details.map((d) => {
                  const meta = STATUS_META[d.status];
                  const Icon = meta.icon;
                  return (
                    <tr key={d.row_index} className="border-b border-line last:border-0">
                      <td className="px-4 py-2.5 font-mono text-ink-faint">{d.row_index + 1}</td>
                      <td className="px-4 py-2.5">
                        <span
                          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${meta.text} ${meta.bg}`}
                        >
                          <Icon size={13} strokeWidth={2.5} />
                          {meta.label}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-ink-soft">{d.message}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <Button variant="secondary" onClick={reset}>
            Weitere Datei importieren
          </Button>
        </div>
      )}
    </div>
  );
}

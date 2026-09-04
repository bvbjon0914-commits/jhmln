import { useEffect, useState } from "react";
import { Loader2, FileText, CheckCircle2 } from "lucide-react";
import { api } from "../../services/api";
import { Button } from "../common/Button";
import { useToast, errorMessage } from "../common/Toast";
import type { InboundEmailEntry, AktenzeichenLookupResult } from "../../types/mailbox";

function isPdf(filename: string | null, contentType: string | null): boolean {
  if (contentType && contentType.toLowerCase() === "application/pdf") return true;
  return !!filename && filename.toLowerCase().endsWith(".pdf");
}

function InboundEmailCard({
  email,
  onAssigned,
}: {
  email: InboundEmailEntry;
  onAssigned: () => void;
}) {
  const { showToast } = useToast();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<AktenzeichenLookupResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [selectedAttachmentId, setSelectedAttachmentId] = useState<number | null>(null);
  const [assigning, setAssigning] = useState(false);

  const pdfAttachments = email.attachments.filter((a) => isPdf(a.filename, a.content_type));

  useEffect(() => {
    if (query.trim().length < 3) {
      setResults([]);
      return;
    }
    setSearching(true);
    const handle = setTimeout(() => {
      api
        .lookupAktenzeichen(query.trim())
        .then(setResults)
        .catch(() => setResults([]))
        .finally(() => setSearching(false));
    }, 300);
    return () => clearTimeout(handle);
  }, [query]);

  const handleAssign = async () => {
    if (!selectedItemId) return;
    if (pdfAttachments.length > 1 && !selectedAttachmentId) {
      showToast("error", "Bitte zuerst den passenden PDF-Anhang auswählen.");
      return;
    }
    setAssigning(true);
    try {
      await api.assignInboundEmail(email.id, selectedItemId, selectedAttachmentId ?? undefined);
      showToast("success", "E-Mail zugeordnet.");
      onAssigned();
    } catch (error) {
      showToast("error", errorMessage(error, "Zuordnung fehlgeschlagen."));
    } finally {
      setAssigning(false);
    }
  };

  return (
    <div className="space-y-3 rounded-lg border border-line bg-surface p-4 shadow-sm">
      <div className="min-w-0">
        <div className="truncate text-sm font-medium text-ink">{email.subject || "(kein Betreff)"}</div>
        <div className="text-xs text-ink-faint">
          {email.from_address || "unbekannter Absender"} ·{" "}
          {new Date(email.received_at).toLocaleString("de-DE")}
        </div>
      </div>

      {email.attachments.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {email.attachments.map((a) => {
            const pdf = isPdf(a.filename, a.content_type);
            return (
              <label key={a.id} className="flex items-center gap-1.5 text-xs">
                {pdf && pdfAttachments.length > 1 && (
                  <input
                    type="radio"
                    name={`attachment-${email.id}`}
                    checked={selectedAttachmentId === a.id}
                    onChange={() => setSelectedAttachmentId(a.id)}
                  />
                )}
                <a
                  href={api.inboundAttachmentDownloadUrl(a.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-brand hover:underline"
                >
                  <FileText size={12} />
                  {a.filename || `Anhang ${a.id}`}
                </a>
              </label>
            );
          })}
        </div>
      )}

      {pdfAttachments.length > 1 && (
        <p className="text-xs text-status-review">
          Mehrere PDF-Anhänge – der richtige wurde nicht automatisch erkannt. Bitte oben auswählen,
          bevor zugeordnet wird.
        </p>
      )}
      {pdfAttachments.length === 0 && (
        <p className="text-xs text-status-conflict">Kein PDF-Anhang – keine Zuordnung möglich.</p>
      )}

      <div>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Aktenzeichen suchen (z.B. VNV-2026-0114)…"
          className="w-full rounded-md border border-line bg-paper/30 px-3 py-2 text-sm text-ink focus:border-brand focus:outline-none"
        />
        {searching && <div className="mt-1 text-xs text-ink-faint">Suche…</div>}
        {results.length > 0 && (
          <div className="mt-2 space-y-1">
            {results.map((r) => (
              <button
                key={r.request_item_id}
                onClick={() => setSelectedItemId(r.request_item_id)}
                className={`block w-full rounded-md border px-3 py-2 text-left text-xs transition-colors ${
                  selectedItemId === r.request_item_id
                    ? "border-brand bg-brand-light/50"
                    : "border-line hover:border-brand/40"
                }`}
              >
                <div className="font-mono text-ink">{r.aktenzeichen}</div>
                <div className="text-ink-faint">
                  {r.request_type_name} · {r.authority_name || "—"} · {r.building_label || "—"}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      <Button onClick={handleAssign} disabled={!selectedItemId || assigning || pdfAttachments.length === 0}>
        {assigning ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />}
        Zuordnen
      </Button>
    </div>
  );
}

export function MailboxAdmin() {
  const { showToast } = useToast();
  const [emails, setEmails] = useState<InboundEmailEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    api
      .listPendingInboundEmails()
      .then(setEmails)
      .catch((error) => showToast("error", errorMessage(error, "Postfach konnte nicht geladen werden.")))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-10 text-sm text-ink-faint">
        <Loader2 size={16} className="animate-spin" />
        Lade Postfach…
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-ink-soft">
        {emails.length === 0
          ? "Keine eingehenden Antworten warten auf Zuordnung."
          : `${emails.length} eingehende Antwort${emails.length === 1 ? "" : "en"} konnte${
              emails.length === 1 ? "" : "n"
            } nicht automatisch zugeordnet werden.`}
      </p>
      {emails.map((email) => (
        <InboundEmailCard key={email.id} email={email} onAssigned={load} />
      ))}
    </div>
  );
}

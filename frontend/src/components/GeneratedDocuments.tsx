import { useEffect, useState } from "react";
import { FileText, Download, DownloadCloud, AlertTriangle, Mail, Eye } from "lucide-react";
import type { GeneratedDocumentInfo } from "../types/matching";
import type { Authority } from "../types/authority";
import { api } from "../services/api";
import { Button } from "./common/Button";
import { useToast, errorMessage } from "./common/Toast";
import { DocumentPreviewModal } from "./DocumentPreviewModal";

interface FailedDocument {
  request_item_id: string;
  request_type_id: string;
  reason: string;
}

interface Props {
  requestId: string;
  documents: GeneratedDocumentInfo[];
  failed: FailedDocument[];
  requestTypeNames: Record<string, string>;
}

export function GeneratedDocuments({ requestId, documents, failed, requestTypeNames }: Props) {
  const { showToast } = useToast();
  const [authorities, setAuthorities] = useState<Record<string, Authority>>({});
  const [previewDoc, setPreviewDoc] = useState<GeneratedDocumentInfo | null>(null);

  useEffect(() => {
    const ids = [...new Set(documents.map((d) => d.authority_id))];
    if (ids.length === 0) return;
    api
      .getAuthorities(ids)
      .then((list) => {
        const map: Record<string, Authority> = {};
        list.forEach((a) => (map[a.authority_id] = a));
        setAuthorities(map);
      })
      .catch((error) => showToast("error", errorMessage(error, "Behörden konnten nicht geladen werden.")));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documents]);

  const mailtoUrl = (doc: GeneratedDocumentInfo, authority?: Authority) => {
    const requestTypeName = requestTypeNames[doc.request_type_id] || doc.request_type_id;
    const subject = `Anfrage: ${requestTypeName}`;
    const body = [
      "Sehr geehrte Damen und Herren,",
      "",
      `anbei unsere Anfrage betreffend „${requestTypeName}".`,
      `(Bitte das heruntergeladene Dokument „${doc.filename}" an diese E-Mail anhängen.)`,
      "",
      "Mit freundlichen Grüßen",
    ].join("\n");
    return `mailto:${authority?.email ?? ""}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  };

  return (
    <div className="rounded-lg border border-line bg-surface p-5 shadow-sm">
      {failed.length > 0 && (
        <div className="mb-4 rounded-md border border-status-conflict/30 bg-status-conflictBg px-4 py-3">
          <div className="flex items-center gap-2 text-sm font-medium text-status-conflict">
            <AlertTriangle size={15} />
            {failed.length} Schreiben konnten nicht generiert werden
          </div>
          <ul className="mt-1.5 space-y-0.5 text-xs text-status-conflict/90">
            {failed.map((f) => (
              <li key={f.request_item_id}>
                {requestTypeNames[f.request_type_id] || f.request_type_id}: {f.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {documents.length > 0 && (
        <>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-display text-sm font-semibold text-ink">
              Generierte Schreiben ({documents.length})
            </h3>
            <a href={api.downloadAllUrl(requestId)} download>
              <Button variant="secondary">
                <DownloadCloud size={15} />
                Alle als ZIP herunterladen
              </Button>
            </a>
          </div>

          <div className="space-y-2">
            {documents.map((doc) => {
              const authority = authorities[doc.authority_id];
              return (
                <div
                  key={doc.request_item_id}
                  className="flex items-center justify-between gap-3 rounded-md border border-line px-4 py-3"
                >
                  <div className="flex items-center gap-3 overflow-hidden">
                    <FileText size={18} className="shrink-0 text-brand" />
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-ink">
                        {requestTypeNames[doc.request_type_id] || doc.request_type_id}
                      </div>
                      <div className="truncate font-mono text-xs text-ink-faint">{doc.filename}</div>
                      {authority && (
                        <div className="mt-0.5 truncate text-xs text-ink-soft">
                          {authority.authority_name}
                          {authority.email && <span className="text-ink-faint"> · {authority.email}</span>}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
                    {authority?.email ? (
                      <a href={mailtoUrl(doc, authority)}>
                        <Button variant="ghost" className="text-xs" title="E-Mail an die Behörde öffnen">
                          <Mail size={14} />
                          E-Mail
                        </Button>
                      </a>
                    ) : (
                      <span
                        className="px-2 text-xs text-ink-faint"
                        title="Keine E-Mail-Adresse für diese Behörde hinterlegt"
                      >
                        Keine E-Mail
                      </span>
                    )}
                    <Button
                      variant="ghost"
                      className="text-xs"
                      onClick={() => setPreviewDoc(doc)}
                    >
                      <Eye size={14} />
                      Vorschau
                    </Button>
                    <a href={api.downloadDocumentUrl(doc.request_item_id)} download>
                      <Button variant="ghost" className="text-xs">
                        <Download size={14} />
                        Herunterladen
                      </Button>
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {previewDoc && (
        <DocumentPreviewModal
          requestItemId={previewDoc.request_item_id}
          title={requestTypeNames[previewDoc.request_type_id] || previewDoc.request_type_id}
          filename={previewDoc.filename}
          onClose={() => setPreviewDoc(null)}
        />
      )}
    </div>
  );
}

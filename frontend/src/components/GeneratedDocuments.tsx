import { FileText, Download, DownloadCloud, AlertTriangle } from "lucide-react";
import type { GeneratedDocumentInfo } from "../types/matching";
import { api } from "../services/api";
import { Button } from "./common/Button";

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
            {documents.map((doc) => (
              <div
                key={doc.request_item_id}
                className="flex items-center justify-between rounded-md border border-line px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <FileText size={18} className="text-brand" />
                  <div>
                    <div className="text-sm font-medium text-ink">
                      {requestTypeNames[doc.request_type_id] || doc.request_type_id}
                    </div>
                    <div className="font-mono text-xs text-ink-faint">{doc.filename}</div>
                  </div>
                </div>
                <a href={api.downloadDocumentUrl(doc.request_item_id)} download>
                  <Button variant="ghost" className="text-xs">
                    <Download size={14} />
                    Herunterladen
                  </Button>
                </a>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

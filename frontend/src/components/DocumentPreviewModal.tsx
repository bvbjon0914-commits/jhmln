import { useEffect, useRef, useState } from "react";
import { renderAsync } from "docx-preview";
import { Loader2, Download, AlertTriangle } from "lucide-react";
import { api } from "../services/api";
import { Modal } from "./common/Modal";
import { Button } from "./common/Button";
import { errorMessage } from "./common/Toast";

interface Props {
  requestItemId: string;
  title: string;
  filename: string;
  onClose: () => void;
}

export function DocumentPreviewModal({ requestItemId, title, filename, onClose }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const res = await fetch(api.downloadDocumentUrl(requestItemId), { credentials: "include" });
        if (!res.ok) throw new Error(`Dokument konnte nicht geladen werden (${res.status}).`);
        const blob = await res.blob();
        if (cancelled || !containerRef.current) return;
        await renderAsync(blob, containerRef.current, undefined, {
          inWrapper: true,
          ignoreWidth: false,
        });
      } catch (err) {
        if (!cancelled) setError(errorMessage(err, "Vorschau konnte nicht geladen werden."));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [requestItemId]);

  return (
    <Modal
      title={title}
      onClose={onClose}
      headerActions={
        <a href={api.downloadDocumentUrl(requestItemId)} download>
          <Button variant="secondary" className="text-xs">
            <Download size={13} />
            Herunterladen
          </Button>
        </a>
      }
    >
      {loading && (
        <div className="flex items-center justify-center gap-2 py-16 text-ink-faint">
          <Loader2 size={18} className="animate-spin" />
          Lade Vorschau…
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 rounded-md border border-status-conflict/30 bg-status-conflictBg px-4 py-3 text-sm text-status-conflict">
          <AlertTriangle size={16} className="shrink-0" />
          {error}
        </div>
      )}
      <div ref={containerRef} className="docx-preview-container text-ink" />
      <p className="mt-3 text-xs text-ink-faint">{filename}</p>
    </Modal>
  );
}

import { createContext, useCallback, useContext, useState } from "react";
import type { ReactNode } from "react";
import { AlertCircle, CheckCircle2, X } from "lucide-react";

type ToastKind = "error" | "success";

interface ToastItem {
  id: number;
  kind: ToastKind;
  message: string;
}

interface ToastContextValue {
  showToast: (kind: ToastKind, message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let nextId = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (kind: ToastKind, message: string) => {
      const id = nextId++;
      setToasts((prev) => [...prev, { id, kind, message }]);
      setTimeout(() => dismiss(id), 6000);
    },
    [dismiss]
  );

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 top-4 z-50 flex flex-col items-center gap-2 px-4">
        {toasts.map((t) => (
          <div
            key={t.id}
            role="alert"
            className={`pointer-events-auto flex max-w-md items-start gap-2.5 rounded-lg border px-4 py-3 text-sm shadow-lg ${
              t.kind === "error"
                ? "border-status-conflict/30 bg-surface text-status-conflict"
                : "border-status-matched/30 bg-surface text-status-matched"
            }`}
          >
            {t.kind === "error" ? (
              <AlertCircle size={16} className="mt-0.5 shrink-0" />
            ) : (
              <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
            )}
            <span className="text-ink">{t.message}</span>
            <button
              onClick={() => dismiss(t.id)}
              className="ml-auto shrink-0 text-ink-faint hover:text-ink"
              aria-label="Schließen"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within a ToastProvider");
  return ctx;
}

interface PydanticValidationError {
  type?: string;
  loc?: (string | number)[];
  msg?: string;
}

function isValidationErrorList(value: unknown): value is PydanticValidationError[] {
  return (
    Array.isArray(value) &&
    value.every((v) => v && typeof v === "object" && "msg" in v)
  );
}

export function errorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === "object" && "response" in error) {
    const response = (error as { response?: { data?: { detail?: unknown } } }).response;
    const detail = response?.data?.detail;

    if (typeof detail === "string" && detail) return detail;

    if (isValidationErrorList(detail)) {
      return detail
        .map((d) => {
          const field = d.loc?.filter((p) => p !== "body").join(".");
          return field ? `${field}: ${d.msg}` : d.msg;
        })
        .filter(Boolean)
        .join("; ") || fallback;
    }
  }
  if (error instanceof Error) return error.message;
  return fallback;
}

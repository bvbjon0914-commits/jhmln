import { Circle, FileText, Send, Inbox, CheckCircle2 } from "lucide-react";
import type { CaseItemStatus } from "../../types/case";

const CONFIG: Record<
  CaseItemStatus,
  { label: string; icon: React.ElementType; text: string; bg: string }
> = {
  NICHT_BEANTRAGT: {
    label: "Nicht beantragt",
    icon: Circle,
    text: "text-status-neutral",
    bg: "bg-status-neutralBg",
  },
  BEREIT_ZUM_SENDEN: {
    label: "Bereit zum Senden",
    icon: FileText,
    text: "text-status-neutral",
    bg: "bg-status-neutralBg",
  },
  GESENDET: {
    label: "Gesendet",
    icon: Send,
    text: "text-status-review",
    bg: "bg-status-reviewBg",
  },
  ANTWORT_ERHALTEN: {
    label: "Antwort erhalten",
    icon: Inbox,
    text: "text-status-review",
    bg: "bg-status-reviewBg",
  },
  GEPRUEFT: {
    label: "Geprüft",
    icon: CheckCircle2,
    text: "text-status-matched",
    bg: "bg-status-matchedBg",
  },
};

export function ProgressBadge({ status }: { status: CaseItemStatus }) {
  const cfg = CONFIG[status];
  const Icon = cfg.icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${cfg.text} ${cfg.bg}`}
    >
      <Icon size={13} strokeWidth={2.5} />
      {cfg.label}
    </span>
  );
}

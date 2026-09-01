import { Check, AlertTriangle, X, GitBranch } from "lucide-react";
import type { MatchingStatus } from "../../types/matching";

const CONFIG: Record<
  MatchingStatus,
  { label: string; icon: React.ElementType; text: string; bg: string }
> = {
  MATCHED: {
    label: "Eindeutig",
    icon: Check,
    text: "text-status-matched",
    bg: "bg-status-matchedBg",
  },
  REVIEW_REQUIRED: {
    label: "Prüfung nötig",
    icon: AlertTriangle,
    text: "text-status-review",
    bg: "bg-status-reviewBg",
  },
  MULTIPLE_MATCHES: {
    label: "Konflikt",
    icon: GitBranch,
    text: "text-status-conflict",
    bg: "bg-status-conflictBg",
  },
  NO_MATCH: {
    label: "Kein Treffer",
    icon: X,
    text: "text-status-neutral",
    bg: "bg-status-neutralBg",
  },
};

export function StatusBadge({ status }: { status: MatchingStatus }) {
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

import { useState, type ReactNode } from "react";
import { ChevronRight } from "lucide-react";

interface Props {
  title: string;
  summary?: ReactNode;
  defaultExpanded?: boolean;
  children: ReactNode;
}

export function CollapsibleSection({ title, summary, defaultExpanded = false, children }: Props) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <div>
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
        className="flex w-full items-center gap-3 rounded-lg border border-line bg-surface px-4 py-3 text-left shadow-sm transition-colors hover:bg-paper/40"
      >
        <ChevronRight
          size={16}
          className={`shrink-0 text-ink-faint transition-transform ${expanded ? "rotate-90" : ""}`}
        />
        <span className="min-w-0 flex-1 truncate text-sm font-medium text-ink">{title}</span>
        {summary}
      </button>
      {expanded && <div className="mt-2 space-y-3 pl-1">{children}</div>}
    </div>
  );
}

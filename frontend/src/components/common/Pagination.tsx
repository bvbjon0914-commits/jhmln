import { ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  offset: number;
  limit: number;
  total: number;
  onOffsetChange: (offset: number) => void;
}

export function Pagination({ offset, limit, total, onOffsetChange }: Props) {
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);

  return (
    <div className="flex items-center justify-between border-t border-line px-4 py-2.5 text-xs text-ink-faint">
      <span>
        {from}–{to} von {total}
      </span>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
          disabled={offset === 0}
          className="flex h-7 w-7 items-center justify-center rounded border border-line disabled:opacity-30 hover:border-brand/40"
          aria-label="Vorherige Seite"
        >
          <ChevronLeft size={14} />
        </button>
        <button
          onClick={() => onOffsetChange(offset + limit)}
          disabled={offset + limit >= total}
          className="flex h-7 w-7 items-center justify-center rounded border border-line disabled:opacity-30 hover:border-brand/40"
          aria-label="Nächste Seite"
        >
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}

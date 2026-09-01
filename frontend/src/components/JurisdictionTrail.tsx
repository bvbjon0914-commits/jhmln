import type { MatchingLevel, MatchingStatus } from "../types/matching";

const LEVELS: { key: MatchingLevel; label: string }[] = [
  { key: "STREET_NUMBER", label: "Straße + Nr." },
  { key: "STREET", label: "Straße" },
  { key: "DISTRICT", label: "Stadtteil" },
  { key: "MUNICIPALITY", label: "Gemeinde" },
  { key: "COUNTY", label: "Landkreis" },
  { key: "STATE", label: "Bundesland" },
  { key: "POSTAL_CODE", label: "PLZ" },
];

type StepState = "skipped" | "hit" | "conflict" | "unreached";

function computeStates(
  matchingLevel: MatchingLevel | null,
  status: MatchingStatus
): StepState[] {
  if (status === "NO_MATCH" || matchingLevel === null) {
    return LEVELS.map(() => "skipped");
  }

  const hitIndex = LEVELS.findIndex((l) => l.key === matchingLevel);

  return LEVELS.map((_, i) => {
    if (i < hitIndex) return "skipped";
    if (i === hitIndex) return status === "MULTIPLE_MATCHES" ? "conflict" : "hit";
    return "unreached";
  });
}

const DOT_STYLES: Record<StepState, string> = {
  skipped: "bg-surface border-2 border-line",
  hit: "bg-status-matched border-2 border-status-matched",
  conflict: "bg-status-conflict border-2 border-status-conflict",
  unreached: "bg-surface border border-dashed border-line",
};

const LABEL_STYLES: Record<StepState, string> = {
  skipped: "text-ink-faint",
  hit: "text-status-matched font-semibold",
  conflict: "text-status-conflict font-semibold",
  unreached: "text-ink-faint/60",
};

export function JurisdictionTrail({
  matchingLevel,
  status,
  reason,
}: {
  matchingLevel: MatchingLevel | null;
  status: MatchingStatus;
  reason: string;
}) {
  const states = computeStates(matchingLevel, status);

  return (
    <div className="rounded-md border border-line bg-paper/60 p-4">
      <div className="flex items-start">
        {LEVELS.map((level, i) => (
          <div key={level.key} className="flex flex-1 flex-col items-center last:flex-none">
            <div className="flex w-full items-center">
              <div className={`h-2 w-2 shrink-0 rounded-full ${DOT_STYLES[states[i]]}`} />
              {i < LEVELS.length - 1 && (
                <div
                  className={`h-px flex-1 ${
                    states[i] === "skipped" ? "bg-line" : "bg-line/60"
                  }`}
                />
              )}
            </div>
            <div className={`mt-1.5 text-center text-[10.5px] leading-tight ${LABEL_STYLES[states[i]]}`}>
              {level.label}
            </div>
          </div>
        ))}
      </div>

      <p className="mt-3 border-t border-line pt-3 font-mono text-[12px] leading-relaxed text-ink-soft">
        {reason}
      </p>
    </div>
  );
}

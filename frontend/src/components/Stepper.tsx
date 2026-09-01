interface Step {
  label: string;
}

const STEPS: Step[] = [
  { label: "Gebäude" },
  { label: "Auskünfte" },
  { label: "Zuständigkeit" },
  { label: "Schreiben" },
];

export function Stepper({ current }: { current: number }) {
  return (
    <div className="flex items-center">
      {STEPS.map((step, i) => {
        const index = i + 1;
        const isDone = index < current;
        const isActive = index === current;

        return (
          <div
            key={step.label}
            className="flex items-center"
            aria-current={isActive ? "step" : undefined}
          >
            <div className="flex items-center gap-2.5">
              <div
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full font-mono text-xs tabular transition-all duration-300
                  ${
                    isDone
                      ? "bg-brand text-white shadow-sm"
                      : isActive
                      ? "border-2 border-brand text-brand shadow-[0_0_0_4px_theme(colors.brand.light)]"
                      : "border border-line text-ink-faint"
                  }`}
              >
                {index}
              </div>
              <span
                className={`font-display text-sm transition-colors duration-300 ${
                  isActive
                    ? "text-ink font-semibold"
                    : isDone
                    ? "text-ink-soft"
                    : "text-ink-faint"
                }`}
              >
                {step.label}
              </span>
            </div>
            {index < STEPS.length && (
              <div
                className={`mx-3 h-px w-8 transition-colors duration-500 sm:w-16 ${
                  isDone ? "bg-brand" : "bg-line"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

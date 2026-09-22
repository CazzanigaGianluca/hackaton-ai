import { PIPELINE_STAGES, PIPELINE_STAGE_LABELS } from "@/lib/types";

interface AgentProgressProps {
  currentStage: string | null;
  isComplete?: boolean;
}

export default function AgentProgress({ currentStage, isComplete = false }: AgentProgressProps) {
  const currentIndex = currentStage ? PIPELINE_STAGES.indexOf(currentStage) : -1;

  return (
    <ol className="space-y-2">
      {PIPELINE_STAGES.map((stage, index) => {
        const isDone = isComplete || currentIndex > index;
        const isActive = !isComplete && stage === currentStage;
        return (
          <li key={stage} className="flex items-center gap-3">
            <span
              className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition-colors ${
                isDone
                  ? "bg-[var(--success)] text-white"
                  : isActive
                    ? "bg-[var(--primary)] text-white ring-4 ring-[var(--primary-light)]"
                    : "bg-[var(--bg)] text-[var(--text-muted)] ring-1 ring-[var(--border)]"
              }`}
            >
              {isDone ? (
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              ) : isActive ? (
                <span className="block h-2 w-2 animate-pulse rounded-full bg-white" />
              ) : (
                index + 1
              )}
            </span>
            <span className={`text-sm ${isActive ? "font-semibold text-[var(--primary)]" : isDone ? "text-[var(--text-secondary)]" : "text-[var(--text-muted)]"}`}>
              {PIPELINE_STAGE_LABELS[stage]}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

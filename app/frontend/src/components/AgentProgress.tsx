import { PIPELINE_STAGES, PIPELINE_STAGE_LABELS } from "@/lib/types";

interface AgentProgressProps {
  currentStage: string | null;
  isComplete?: boolean;
}

export default function AgentProgress({
  currentStage,
  isComplete = false,
}: AgentProgressProps) {
  const currentIndex = currentStage
    ? PIPELINE_STAGES.indexOf(currentStage)
    : -1;

  return (
    <ol className="space-y-3">
      {PIPELINE_STAGES.map((stage, index) => {
        const isDone = isComplete || currentIndex > index;
        const isActive = !isComplete && stage === currentStage;
        return (
          <li key={stage} className="flex items-center gap-3">
            <span
              className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                isDone
                  ? "bg-emerald-500 text-white"
                  : isActive
                    ? "bg-blue-500 text-white animate-pulse"
                    : "bg-gray-200 text-gray-500"
              }`}
            >
              {isDone ? "✓" : index + 1}
            </span>
            <span
              className={
                isActive ? "font-medium text-blue-700" : "text-gray-600"
              }
            >
              {PIPELINE_STAGE_LABELS[stage]}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

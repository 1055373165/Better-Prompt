import { Loader2, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ContinueActionsProps {
  actions: string[];
  onSelect: (goal: string) => void;
  isLoading?: boolean;
  activeGoal?: string | null;
  completedGoal?: string | null;
  resultLabel?: string | null;
}

export function ContinueActions({
  actions,
  onSelect,
  isLoading,
  activeGoal = null,
  completedGoal = null,
  resultLabel = null,
}: ContinueActionsProps) {
  if (!actions.length) return null;

  const statusText = isLoading && activeGoal
    ? `正在基于“${activeGoal}”继续优化，完成后结果桌面会自动切到新版本。`
    : completedGoal
      ? `已完成“${completedGoal}”，当前结果桌面显示的是${resultLabel ?? '优化后版本'}。`
      : '如果第一版已经可用，直接沿着它继续补强深度、可执行性或表达风格。';

  return (
    <div className="bp-surface overflow-hidden px-5 py-5">
      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
        <Sparkles className="h-4 w-4 text-[var(--bp-clay)]" />
        Continue Optimization
      </div>
      <div
        aria-live="polite"
        className={`mt-3 text-sm leading-7 ${
          isLoading && activeGoal
            ? 'text-[var(--bp-steel)]'
            : completedGoal
              ? 'text-emerald-700'
              : 'text-[var(--bp-ink-soft)]'
        }`}
      >
        {statusText}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {actions.map((action) => (
          <Button
            key={action}
            type="button"
            variant="outline"
            className={`rounded-full border px-4 py-2 text-sm ${
              isLoading && activeGoal === action
                ? 'border-[rgba(53,87,104,0.18)] bg-[rgba(53,87,104,0.1)] text-[var(--bp-steel)] hover:bg-[rgba(53,87,104,0.1)]'
                : !isLoading && completedGoal === action
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-900 hover:bg-emerald-50'
                  : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.78)] text-[var(--bp-ink)] hover:bg-[rgba(255,255,255,0.94)]'
            }`}
            disabled={isLoading}
            onClick={() => onSelect(action)}
          >
            {isLoading && activeGoal === action && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {action}
          </Button>
        ))}
      </div>
    </div>
  );
}

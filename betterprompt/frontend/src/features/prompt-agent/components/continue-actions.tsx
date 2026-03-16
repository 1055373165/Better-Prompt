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
    ? `正在基于“${activeGoal}”继续优化，结果区会在完成后自动切到新版本。`
    : completedGoal
      ? `已完成“${completedGoal}”，当前结果区显示的是${resultLabel ?? '优化后版本'}。`
      : '基于当前结果快速继续迭代，补强深度、可执行性和表达稳定性。';

  return (
    <div className="rounded-[1.75rem] border border-white/70 bg-white/75 p-5 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-900">
        <Sparkles className="h-4 w-4 text-slate-500" />
        下一步可以继续优化
      </div>
      <div
        aria-live="polite"
        className={`mt-2 text-sm leading-6 ${isLoading && activeGoal ? 'text-sky-700' : completedGoal ? 'text-emerald-700' : 'text-slate-500'}`}
      >
        {statusText}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {actions.map((action) => (
          <Button
            key={action}
            type="button"
            variant="outline"
            className={`rounded-full ${
              isLoading && activeGoal === action
                ? 'border-sky-200 bg-sky-50 text-sky-900 hover:bg-sky-50'
                : !isLoading && completedGoal === action
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-900 hover:bg-emerald-50'
                  : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
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

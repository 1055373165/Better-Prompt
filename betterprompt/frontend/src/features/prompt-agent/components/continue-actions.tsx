import { Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ContinueActionsProps {
  actions: string[];
  onSelect: (goal: string) => void;
  isLoading?: boolean;
}

export function ContinueActions({ actions, onSelect, isLoading }: ContinueActionsProps) {
  if (!actions.length) return null;

  return (
    <div className="rounded-[1.75rem] border border-white/70 bg-white/75 p-5 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-900">
        <Sparkles className="h-4 w-4 text-slate-500" />
        下一步可以继续优化
      </div>
      <div className="mt-2 text-sm leading-6 text-slate-500">
        基于当前结果快速继续迭代，补强深度、可执行性和表达稳定性。
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {actions.map((action) => (
          <Button
            key={action}
            type="button"
            variant="outline"
            className="rounded-full border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
            disabled={isLoading}
            onClick={() => onSelect(action)}
          >
            {action}
          </Button>
        ))}
      </div>
    </div>
  );
}

import { Activity, Bug, Sparkles } from 'lucide-react';
import type { PromptAgentMode } from '../types';
import { cn } from '@/lib/utils/cn';

interface ModeSelectorProps {
  value: PromptAgentMode;
  onChange: (mode: PromptAgentMode) => void;
}

const MODES: Array<{
  value: PromptAgentMode;
  label: string;
  description: string;
  badge: string;
  icon: typeof Sparkles;
}> = [
  { value: 'generate', label: 'Generate', description: '把一句需求编译成可直接复用的高质量 Prompt', badge: 'Core', icon: Sparkles },
  { value: 'debug', label: 'Debug', description: '定位当前 Prompt 的结构缺口并给出修复版本', badge: 'Review', icon: Bug },
  { value: 'evaluate', label: 'Evaluate', description: '从多个维度评估 Prompt 或输出质量', badge: 'Score', icon: Activity },
];

export function ModeSelector({ value, onChange }: ModeSelectorProps) {
  return (
    <div className="grid gap-3 lg:grid-cols-3">
      {MODES.map((mode) => (
        <button
          key={mode.value}
          type="button"
          onClick={() => onChange(mode.value)}
          className={cn(
            'group relative overflow-hidden rounded-[1.5rem] border p-4 text-left transition-all duration-300',
            value === mode.value
              ? 'border-slate-900/10 bg-slate-950 text-white shadow-[0_20px_60px_-34px_rgba(15,23,42,0.82)]'
              : 'border-white/70 bg-white/85 shadow-[0_18px_50px_-38px_rgba(15,23,42,0.16)] backdrop-blur-xl hover:-translate-y-0.5 hover:border-slate-200 hover:bg-white'
          )}
        >
          <div
            className={cn(
              'absolute inset-x-0 top-0 h-20 opacity-80 transition-opacity',
              value === mode.value
                ? 'bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.22),transparent_58%)]'
                : 'bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.08),transparent_58%)] group-hover:opacity-100'
            )}
          />
          <div className="relative flex items-start justify-between gap-4">
            <div className="space-y-3">
              <div
                className={cn(
                  'inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em]',
                  value === mode.value
                    ? 'border-white/15 bg-white/10 text-white/80'
                    : 'border-slate-200 bg-slate-50 text-slate-500'
                )}
              >
                {mode.badge}
              </div>
              <div>
                <div className={cn('text-sm font-semibold tracking-tight md:text-base', value === mode.value ? 'text-white' : 'text-slate-900')}>
                  {mode.label}
                </div>
                <div className={cn('mt-1.5 max-w-[30ch] text-sm leading-6', value === mode.value ? 'text-white/70' : 'text-slate-500')}>
                  {mode.description}
                </div>
              </div>
            </div>
            <div
              className={cn(
                'flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border',
                value === mode.value
                  ? 'border-white/15 bg-white/10 text-white'
                  : 'border-slate-200 bg-slate-50 text-slate-700'
              )}
            >
              <mode.icon className="h-5 w-5" />
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}

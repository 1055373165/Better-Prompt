import { Activity, Bug, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils/cn';
import type { PromptAgentMode } from '../types';

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
  {
    value: 'generate',
    label: 'Generate',
    description: '把一句需求编译成可直接复用的高质量 Prompt',
    badge: '01',
    icon: Sparkles,
  },
  {
    value: 'debug',
    label: 'Debug',
    description: '定位当前 Prompt 的结构缺口并给出修复版本',
    badge: '02',
    icon: Bug,
  },
  {
    value: 'evaluate',
    label: 'Evaluate',
    description: '从多个维度评估 Prompt 或输出质量',
    badge: '03',
    icon: Activity,
  },
];

export function ModeSelector({ value, onChange }: ModeSelectorProps) {
  return (
    <div className="grid gap-3 lg:grid-cols-3">
      {MODES.map((mode) => {
        const active = value === mode.value;

        return (
          <button
            key={mode.value}
            type="button"
            onClick={() => onChange(mode.value)}
            className={cn(
              'group relative overflow-hidden rounded-[1.45rem] border px-4 py-4 text-left transition-all duration-300',
              active
                ? 'border-[rgba(31,36,45,0.18)] bg-[linear-gradient(135deg,rgba(30,38,52,0.98),rgba(55,65,78,0.98))] text-[#f8f3eb] shadow-[0_24px_60px_-34px_rgba(24,25,27,0.6)]'
                : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)] text-[var(--bp-ink)] hover:-translate-y-0.5 hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.9)]'
            )}
          >
            <div
              className={cn(
                'absolute inset-x-0 top-0 h-24 transition-opacity',
                active
                  ? 'bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.14),transparent_60%)]'
                  : 'bg-[radial-gradient(circle_at_top_left,rgba(162,74,53,0.08),transparent_62%)] opacity-0 group-hover:opacity-100'
              )}
            />
            <div className="relative flex items-start justify-between gap-4">
              <div>
                <div
                  className={cn(
                    'inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em]',
                    active
                      ? 'border-white/12 bg-white/10 text-[#efe4d8]'
                      : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.78)] text-[var(--bp-ink-soft)]'
                  )}
                >
                  {mode.badge}
                </div>
                <div className="mt-4 flex items-center gap-2">
                  <mode.icon className={cn('h-4 w-4', active ? 'text-[#d7b79e]' : 'text-[var(--bp-clay)]')} />
                  <div className={cn('text-base font-semibold tracking-tight', active ? 'text-[#f8f3eb]' : 'text-[var(--bp-ink)]')}>
                    {mode.label}
                  </div>
                </div>
                <p className={cn('mt-2 max-w-[26ch] text-sm leading-6', active ? 'text-[#d4d8df]' : 'text-[var(--bp-ink-soft)]')}>
                  {mode.description}
                </p>
              </div>
              <div
                className={cn(
                  'rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em]',
                  active
                    ? 'border-white/12 bg-white/10 text-[#efe4d8]'
                    : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.78)] text-[var(--bp-clay)]'
                )}
              >
                {mode.value}
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

import { Activity, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { EvaluateDraft, EvaluateTargetType } from '../types';

export function EvaluatePanel({
  draft,
  onChange,
  onSubmit,
  isLoading,
}: {
  draft: EvaluateDraft;
  onChange: (patch: Partial<EvaluateDraft>) => void;
  onSubmit: (payload: { target_text: string; target_type: EvaluateTargetType }) => void;
  isLoading?: boolean;
}) {
  return (
    <div className="bp-surface overflow-hidden px-5 py-6 md:px-7">
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div>
          <div className="bp-overline">Evaluation Brief</div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[var(--bp-ink)]">先量化判断，再决定下一轮怎么改</h2>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-[var(--bp-ink-soft)]">
            Evaluate 负责把“感觉不太对”变成明确的分数、缺陷和修复方向。你可以评 Prompt，也可以直接评模型输出。
          </p>
        </div>
        <div className="bp-surface-soft px-4 py-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
            <Activity className="h-4 w-4 text-[var(--bp-clay)]" />
            当前评估视角
          </div>
          <div className="mt-3 space-y-3">
            <div className="bp-meta-card">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Target</div>
              <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">
                {draft.targetType === 'prompt' ? '从 Prompt 质量视角评分' : '从输出质量视角评分'}
              </div>
            </div>
            <div className="bp-meta-card text-sm leading-7 text-[var(--bp-ink-soft)]">
              系统会重点看问题拟合度、约束意识、信息密度、可执行性和整体稳定性。
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6">
        <div className="bp-overline">Review Target</div>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {[
            ['prompt', '评估 Prompt'],
            ['output', '评估输出'],
          ].map(([value, label]) => {
            const active = draft.targetType === value;

            return (
              <button
                key={value}
                type="button"
                onClick={() => onChange({ targetType: value as EvaluateTargetType })}
                className={`rounded-[1.25rem] border px-4 py-3 text-left text-sm font-semibold transition ${
                  active
                    ? 'border-[rgba(31,36,45,0.18)] bg-[linear-gradient(135deg,rgba(30,38,52,0.98),rgba(55,65,78,0.98))] text-[#f8f3eb] shadow-[0_18px_42px_-28px_rgba(24,25,27,0.5)]'
                    : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.78)] text-[var(--bp-ink)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)]'
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-5">
        <div className="mb-2 bp-overline">Target Content</div>
        <textarea
          value={draft.targetText}
          onChange={(e) => onChange({ targetText: e.target.value })}
          placeholder="粘贴需要评估的 Prompt 或输出内容"
          className="bp-input min-h-[320px] text-sm leading-8"
        />
      </div>

      <div className="mt-6 flex flex-col gap-4 border-t border-[var(--bp-line)] pt-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="max-w-xl text-sm leading-7 text-[var(--bp-ink-soft)]">
          如果你在比较多个版本，建议逐个评估，再把最低分项带回 Generate 或 Debug 模式继续修。
        </div>
        <Button
          className="bp-action-primary h-12 px-6"
          disabled={isLoading || !draft.targetText.trim()}
          onClick={() => onSubmit({ target_text: draft.targetText.trim(), target_type: draft.targetType })}
        >
          {isLoading ? '评估中...' : '开始评估'}
          {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}

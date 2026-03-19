import { ArrowRight, Bug, FileWarning } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { DebugDraft } from '../types';

export function DebugPanel({
  draft,
  onChange,
  onSubmit,
  isLoading,
}: {
  draft: DebugDraft;
  onChange: (patch: Partial<DebugDraft>) => void;
  onSubmit: (payload: { original_task: string; current_prompt: string; current_output: string }) => void;
  isLoading?: boolean;
}) {
  return (
    <div className="bp-surface overflow-hidden px-5 py-6 md:px-7">
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div>
          <div className="bp-overline">Repair Brief</div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[var(--bp-ink)]">把失效链路摊开，让系统判断哪里坏了</h2>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-[var(--bp-ink-soft)]">
            Debug 最适合处理“结果跑偏、结构失真、约束失效”这种问题。任务目标、当前 Prompt 和实际输出给得越完整，修复建议就越可执行。
          </p>
        </div>
        <div className="bp-surface-soft px-4 py-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
            <FileWarning className="h-4 w-4 text-[var(--bp-clay)]" />
            这次会一起诊断什么
          </div>
          <div className="mt-3 space-y-3 text-sm leading-7 text-[var(--bp-ink-soft)]">
            <div className="bp-meta-card">任务目标是否表达清楚</div>
            <div className="bp-meta-card">Prompt 是否缺失关键控制层</div>
            <div className="bp-meta-card">输出为什么没有按预期执行</div>
          </div>
        </div>
      </div>

      <div className="mt-6 space-y-5">
        <div>
          <div className="mb-2 bp-overline">Original Task</div>
          <textarea
            value={draft.originalTask}
            onChange={(e) => onChange({ originalTask: e.target.value })}
            placeholder="原始任务，例如：帮我分析一个 SaaS 产品的商业模式。"
            className="bp-input min-h-[120px] text-sm leading-8"
          />
        </div>
        <div>
          <div className="mb-2 bp-overline">Current Prompt</div>
          <textarea
            value={draft.currentPrompt}
            onChange={(e) => onChange({ currentPrompt: e.target.value })}
            placeholder="粘贴当前 Prompt"
            className="bp-input min-h-[190px] text-sm leading-8"
          />
        </div>
        <div>
          <div className="mb-2 bp-overline">Current Output</div>
          <textarea
            value={draft.currentOutput}
            onChange={(e) => onChange({ currentOutput: e.target.value })}
            placeholder="粘贴当前输出"
            className="bp-input min-h-[190px] text-sm leading-8"
          />
        </div>
      </div>

      <div className="mt-6 flex flex-col gap-4 border-t border-[var(--bp-line)] pt-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="max-w-xl text-sm leading-7 text-[var(--bp-ink-soft)]">
          至少建议同时提供任务目标、当前 Prompt 和一段实际输出。这样系统才能判断到底是理解偏了、结构少了，还是约束没起效。
        </div>
        <Button
          className="bp-action-primary h-12 px-6"
          disabled={isLoading || !draft.originalTask.trim() || !draft.currentPrompt.trim() || !draft.currentOutput.trim()}
          onClick={() => onSubmit({
            original_task: draft.originalTask.trim(),
            current_prompt: draft.currentPrompt.trim(),
            current_output: draft.currentOutput.trim(),
          })}
        >
          {isLoading ? '调试中...' : '开始调试'}
          {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}

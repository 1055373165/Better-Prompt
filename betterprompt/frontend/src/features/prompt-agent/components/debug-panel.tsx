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
    <div className="overflow-hidden rounded-[2rem] border border-white/80 bg-white/88 shadow-[0_28px_80px_-46px_rgba(15,23,42,0.28)] backdrop-blur-xl">
      <div className="border-b border-slate-200/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.92))] px-6 py-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
              <Bug className="h-3.5 w-3.5" />
              Repair
            </div>
            <h2 className="mt-4 text-lg font-semibold tracking-tight text-slate-950">分析 Prompt 的问题并修复</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
              把任务背景、当前 Prompt 和当前输出一起给我，我会帮你找出结构缺口，并返回一版更稳定的修复结果。
            </p>
          </div>
          <div className="rounded-[1.5rem] border border-slate-200/80 bg-slate-50/80 px-4 py-3 lg:w-[320px]">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-900">
              <FileWarning className="h-4 w-4 text-slate-500" />
              分析范围
            </div>
            <div className="mt-2 text-sm leading-6 text-slate-500">
              从原始任务到最终输出做全链路诊断，尤其适合“结果跑偏、结构失真、约束失效”这类问题。
            </div>
          </div>
        </div>
      </div>
      <div className="space-y-5 px-6 py-6">
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Original Task</div>
          <textarea
            value={draft.originalTask}
            onChange={(e) => onChange({ originalTask: e.target.value })}
            placeholder="原始任务，例如：帮我分析一个 SaaS 产品的商业模式。"
            className="min-h-[110px] w-full rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] px-5 py-4 text-sm leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-sky-200 focus:shadow-[0_0_0_4px_rgba(14,165,233,0.08)]"
          />
        </div>
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Current Prompt</div>
          <textarea
            value={draft.currentPrompt}
            onChange={(e) => onChange({ currentPrompt: e.target.value })}
            placeholder="粘贴当前 Prompt"
            className="min-h-[170px] w-full rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] px-5 py-4 text-sm leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-sky-200 focus:shadow-[0_0_0_4px_rgba(14,165,233,0.08)]"
          />
        </div>
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Current Output</div>
          <textarea
            value={draft.currentOutput}
            onChange={(e) => onChange({ currentOutput: e.target.value })}
            placeholder="粘贴当前输出"
            className="min-h-[170px] w-full rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] px-5 py-4 text-sm leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-sky-200 focus:shadow-[0_0_0_4px_rgba(14,165,233,0.08)]"
          />
        </div>
        <div className="flex flex-col gap-3 border-t border-slate-200/80 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="max-w-xl text-sm leading-6 text-slate-500">
            输入越完整，诊断越准确。至少建议同时提供任务目标、当前 Prompt 和一段实际输出。
          </div>
          <Button
            className="h-12 rounded-full bg-slate-950 px-6 text-white hover:bg-slate-800"
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
    </div>
  );
}

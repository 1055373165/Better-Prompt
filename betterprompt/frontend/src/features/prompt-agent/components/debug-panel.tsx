import { useState } from 'react';
import { ArrowRight, Bug, FileWarning } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function DebugPanel({
  onSubmit,
  isLoading,
}: {
  onSubmit: (payload: { original_task: string; current_prompt: string; current_output: string }) => void;
  isLoading?: boolean;
}) {
  const [originalTask, setOriginalTask] = useState('');
  const [currentPrompt, setCurrentPrompt] = useState('');
  const [currentOutput, setCurrentOutput] = useState('');

  return (
    <div className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/75 shadow-[0_24px_80px_-44px_rgba(15,23,42,0.3)] backdrop-blur-xl">
      <div className="border-b border-slate-200/70 bg-[linear-gradient(180deg,rgba(248,250,252,0.95),rgba(255,255,255,0.85))] px-6 py-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
              <Bug className="h-3.5 w-3.5" />
              Repair
            </div>
            <h2 className="mt-4 text-lg font-semibold tracking-tight text-slate-950">分析 Prompt 的问题并修复</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">粘贴你的任务、当前 Prompt 和当前输出，我们来帮你定位问题。</p>
          </div>
          <div className="rounded-2xl border border-slate-200/80 bg-white/90 px-4 py-3 lg:w-[280px]">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-900">
              <FileWarning className="h-4 w-4 text-slate-500" />
              分析范围
            </div>
            <div className="mt-2 text-sm leading-6 text-slate-500">从原始任务、当前 Prompt 到最终输出，定位结构缺口和失效原因。</div>
          </div>
        </div>
      </div>
      <div className="space-y-5 px-6 py-6">
        <textarea value={originalTask} onChange={(e) => setOriginalTask(e.target.value)} placeholder="原始任务" className="min-h-[110px] w-full rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] px-5 py-4 text-sm leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-sky-200 focus:shadow-[0_0_0_4px_rgba(14,165,233,0.08)]" />
        <textarea value={currentPrompt} onChange={(e) => setCurrentPrompt(e.target.value)} placeholder="当前 Prompt" className="min-h-[170px] w-full rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] px-5 py-4 text-sm leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-sky-200 focus:shadow-[0_0_0_4px_rgba(14,165,233,0.08)]" />
        <textarea value={currentOutput} onChange={(e) => setCurrentOutput(e.target.value)} placeholder="当前输出" className="min-h-[170px] w-full rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] px-5 py-4 text-sm leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-sky-200 focus:shadow-[0_0_0_4px_rgba(14,165,233,0.08)]" />
        <div className="flex justify-end border-t border-slate-200/80 pt-5">
          <Button className="h-12 rounded-full bg-slate-950 px-6 text-white hover:bg-slate-800" disabled={isLoading || !originalTask.trim() || !currentPrompt.trim() || !currentOutput.trim()} onClick={() => onSubmit({ original_task: originalTask.trim(), current_prompt: currentPrompt.trim(), current_output: currentOutput.trim() })}>
            {isLoading ? '调试中...' : '开始调试'}
            {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}

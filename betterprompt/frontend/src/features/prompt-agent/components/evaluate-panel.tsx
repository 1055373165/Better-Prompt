import { useState } from 'react';
import { Activity, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function EvaluatePanel({
  onSubmit,
  isLoading,
}: {
  onSubmit: (payload: { target_text: string; target_type: 'prompt' | 'output' }) => void;
  isLoading?: boolean;
}) {
  const [targetText, setTargetText] = useState('');
  const [targetType, setTargetType] = useState<'prompt' | 'output'>('prompt');

  return (
    <div className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/75 shadow-[0_24px_80px_-44px_rgba(15,23,42,0.3)] backdrop-blur-xl">
      <div className="border-b border-slate-200/70 bg-[linear-gradient(180deg,rgba(248,250,252,0.95),rgba(255,255,255,0.85))] px-6 py-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
              <Activity className="h-3.5 w-3.5" />
              Review
            </div>
            <h2 className="mt-4 text-lg font-semibold tracking-tight text-slate-950">评估 Prompt 或输出质量</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">粘贴一个 Prompt 或输出，我们会帮你判断它是否足够强。</p>
          </div>
        </div>
      </div>
      <div className="space-y-5 px-6 py-6">
        <div className="grid gap-3 sm:grid-cols-2">
          {[
            ['prompt', '评估 Prompt'],
            ['output', '评估输出'],
          ].map(([value, label]) => (
            <button
              key={value}
              type="button"
              onClick={() => setTargetType(value as 'prompt' | 'output')}
              className={`rounded-[1.35rem] border px-4 py-3 text-left text-sm transition ${targetType === value ? 'border-slate-900 bg-slate-950 text-white shadow-[0_18px_50px_-30px_rgba(15,23,42,0.85)]' : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'}`}
            >
              {label}
            </button>
          ))}
        </div>
        <textarea value={targetText} onChange={(e) => setTargetText(e.target.value)} placeholder="粘贴需要评估的内容" className="min-h-[240px] w-full rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] px-5 py-4 text-sm leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-sky-200 focus:shadow-[0_0_0_4px_rgba(14,165,233,0.08)]" />
        <div className="flex justify-end border-t border-slate-200/80 pt-5">
          <Button className="h-12 rounded-full bg-slate-950 px-6 text-white hover:bg-slate-800" disabled={isLoading || !targetText.trim()} onClick={() => onSubmit({ target_text: targetText.trim(), target_type: targetType })}>
            {isLoading ? '评估中...' : '开始评估'}
            {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}

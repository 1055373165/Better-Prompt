import { useState } from 'react';
import { ArrowRight, LayoutTemplate, Settings2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { PromptArtifactType } from '../types';

interface GeneratePanelProps {
  onSubmit: (payload: {
    user_input: string;
    show_diagnosis: boolean;
    output_preference: 'balanced' | 'depth' | 'execution' | 'natural';
    artifact_type: PromptArtifactType;
    prompt_only: boolean;
  }) => void;
  isLoading?: boolean;
}

export function GeneratePanel({ onSubmit, isLoading }: GeneratePanelProps) {
  const [userInput, setUserInput] = useState('');
  const [showDiagnosis, setShowDiagnosis] = useState(true);
  const [promptOnly, setPromptOnly] = useState(false);
  const [artifactType, setArtifactType] = useState<PromptArtifactType>('system_prompt');
  const [outputPreference, setOutputPreference] = useState<'balanced' | 'depth' | 'execution' | 'natural'>('balanced');

  return (
    <div className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/75 shadow-[0_24px_80px_-44px_rgba(15,23,42,0.3)] backdrop-blur-xl">
      <div className="border-b border-slate-200/70 bg-[linear-gradient(180deg,rgba(248,250,252,0.95),rgba(255,255,255,0.85))] px-6 py-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
              <LayoutTemplate className="h-3.5 w-3.5" />
              Compose
            </div>
            <h2 className="mt-4 text-lg font-semibold tracking-tight text-slate-950">描述你想让模型帮你做什么</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
              你不需要写得很专业，先把你的想法写下来，我们会帮你把它整理成更好的 Prompt。
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:w-[280px] lg:grid-cols-1">
            <div className="rounded-2xl border border-slate-200/80 bg-white/90 px-4 py-3">
              <div className="text-[11px] uppercase tracking-[0.16em] text-slate-400">Goal</div>
              <div className="mt-1 text-sm font-medium text-slate-900">从自然语言到可复用 Prompt</div>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-white/90 px-4 py-3">
              <div className="text-[11px] uppercase tracking-[0.16em] text-slate-400">Output</div>
              <div className="mt-1 text-sm font-medium text-slate-900">结构完整、约束明确、可直接使用</div>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6 px-6 py-6">
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Task Brief</div>
          <textarea
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="例如：我想让模型帮我分析一个陌生行业的商业模式，但我不知道应该怎么问。"
            className="min-h-[220px] w-full rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] px-5 py-4 text-sm leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-sky-200 focus:shadow-[0_0_0_4px_rgba(14,165,233,0.08)]"
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <div className="rounded-[1.5rem] border border-slate-200/80 bg-slate-50/80 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-900">
              <Settings2 className="h-4 w-4 text-slate-500" />
              输出控制
            </div>
            <div className="grid gap-3">
              <label className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
                <div>
                  <div className="font-medium text-slate-900">显示诊断摘要</div>
                  <div className="mt-1 text-xs text-slate-500">返回任务判断与潜在失败模式</div>
                </div>
                <input type="checkbox" checked={showDiagnosis} onChange={(e) => setShowDiagnosis(e.target.checked)} />
              </label>
              <label className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
                <div>
                  <div className="font-medium text-slate-900">仅输出 Prompt</div>
                  <div className="mt-1 text-xs text-slate-500">适合直接复制，不附带额外解释</div>
                </div>
                <input type="checkbox" checked={promptOnly} onChange={(e) => setPromptOnly(e.target.checked)} />
              </label>
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-slate-200/80 bg-slate-50/80 p-4">
            <div className="text-sm font-medium text-slate-900">生成策略</div>
            <div className="mt-2 text-sm leading-6 text-slate-500">
              选择目标产物和优化偏好，帮助系统更精准地组织结果结构。
            </div>
          </div>
        </div>

        <div className="grid gap-5 xl:grid-cols-2">
          <div>
            <div className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Artifact Type</div>
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                ['system_prompt', '系统提示词'],
                ['task_prompt', '一次性任务 Prompt'],
                ['analysis_workflow', '分析工作流 Prompt'],
                ['conversation_prompt', '对话协作 Prompt'],
              ].map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setArtifactType(value as PromptArtifactType)}
                  className={`rounded-[1.35rem] border px-4 py-3 text-left text-sm transition ${
                    artifactType === value
                      ? 'border-slate-900 bg-slate-950 text-white shadow-[0_18px_50px_-30px_rgba(15,23,42,0.85)]'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  <div className="font-medium">{label}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Optimization Preference</div>
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                ['balanced', '平衡'],
                ['depth', '深度'],
                ['execution', '可执行性'],
                ['natural', '自然表达'],
              ].map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setOutputPreference(value as 'balanced' | 'depth' | 'execution' | 'natural')}
                  className={`rounded-[1.35rem] border px-4 py-3 text-left text-sm transition ${
                    outputPreference === value
                      ? 'border-sky-200 bg-sky-50 text-sky-900 shadow-[0_18px_50px_-34px_rgba(14,165,233,0.45)]'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  <div className="font-medium">{label}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-3 border-t border-slate-200/80 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm leading-6 text-slate-500">
            生成前会先理解你的需求，再组织成结构更完整、约束更清晰的 Prompt 结果。
          </div>
          <Button
            type="button"
            className="h-12 rounded-full bg-slate-950 px-6 text-white hover:bg-slate-800"
            disabled={isLoading || !userInput.trim()}
            onClick={() => onSubmit({
              user_input: userInput.trim(),
              show_diagnosis: showDiagnosis,
              output_preference: outputPreference,
              artifact_type: artifactType,
              prompt_only: promptOnly,
            })}
          >
            {isLoading ? '生成中...' : '生成更优 Prompt'}
            {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { ArrowRight, ChevronDown, LayoutTemplate, Layers3, Settings2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { GenerateDraft, GenerateOutputPreference, PromptArtifactType } from '../types';

interface GeneratePanelProps {
  draft: GenerateDraft;
  onChange: (patch: Partial<GenerateDraft>) => void;
  onSubmit: (payload: {
    user_input: string;
    show_diagnosis: boolean;
    output_preference: GenerateOutputPreference;
    artifact_type: PromptArtifactType;
    prompt_only: boolean;
  }) => void;
  isLoading?: boolean;
}

const EXAMPLES = [
  '帮我写一个分析 B2B SaaS 商业模式的高质量 Prompt',
  '帮我生成一个用于拆解智能选股策略的系统提示词',
  '帮我写一个让模型输出产品需求分析结论的结构化 Prompt',
];

export function GeneratePanel({
  draft,
  onChange,
  onSubmit,
  isLoading,
}: GeneratePanelProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handlePrimaryAction = () => {
    if (!draft.userInput.trim()) return;

    onSubmit({
      user_input: draft.userInput.trim(),
      show_diagnosis: draft.showDiagnosis,
      output_preference: draft.outputPreference,
      artifact_type: draft.artifactType,
      prompt_only: draft.promptOnly,
    });
  };
  const actionLabel = isLoading ? '生成中...' : '开始生成';

  return (
    <div className="overflow-hidden rounded-[2rem] border border-white/80 bg-white/88 shadow-[0_28px_80px_-46px_rgba(15,23,42,0.28)] backdrop-blur-xl">
      <div className="border-b border-slate-200/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.92))] px-6 py-5">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
              <LayoutTemplate className="h-3.5 w-3.5" />
              Unified Composer
            </div>
            <h2 className="mt-4 text-lg font-semibold tracking-tight text-slate-950">描述你想让模型帮你做什么</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
              不需要先想清楚 Prompt 结构。你只要描述目标和输出预期，系统会按当前的 Generate 模式把它整理成更强的 Prompt 结果。
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => onChange({ userInput: example })}
                  className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-600 transition hover:border-slate-300 hover:bg-white hover:text-slate-900"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:w-[320px] lg:grid-cols-1">
            <div className="rounded-[1.5rem] border border-slate-200/80 bg-slate-50/80 px-4 py-3">
              <div className="text-[11px] uppercase tracking-[0.16em] text-slate-400">当前模式</div>
              <div className="mt-2 text-sm font-medium text-slate-900">Generate</div>
              <div className="mt-1 text-sm leading-6 text-slate-500">按你的主动选择直接生成，不自动跳转到调试或评估。</div>
            </div>
            <div className="rounded-[1.5rem] border border-slate-200/80 bg-white/90 px-4 py-3">
              <div className="text-[11px] uppercase tracking-[0.16em] text-slate-400">输出目标</div>
              <div className="mt-1 text-sm font-medium text-slate-900">可复用、可执行、可继续优化</div>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6 px-6 py-6">
        <div>
          <div className="mb-2 flex items-center justify-between gap-3">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Task Brief</div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Layers3 className="h-3.5 w-3.5" />
              Cmd/Ctrl + Enter 直接生成
            </div>
          </div>
          <textarea
            value={draft.userInput}
            onChange={(e) => onChange({ userInput: e.target.value })}
            placeholder="例如：我想实现一个智能选股功能，应该采用哪些策略？&#10;或者：帮我写一个分析 SaaS 商业模式的高质量系统提示词。&#10;或者：生成一版结构清晰、可直接给其他模型使用的任务 Prompt。"
            className="min-h-[220px] w-full rounded-[1.6rem] border border-slate-200 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] px-5 py-4 text-sm leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-sky-200 focus:shadow-[0_0_0_4px_rgba(14,165,233,0.08)]"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                handlePrimaryAction();
              }
            }}
          />
        </div>

        <div className="flex items-center justify-between border-t border-slate-200/80 pt-1">
          <button
            type="button"
            onClick={() => setShowAdvanced((current) => !current)}
            className="flex items-center gap-2 text-sm text-slate-600 transition hover:text-slate-900"
          >
            <ChevronDown className={`h-4 w-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
            高级选项
          </button>
          <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-500">
            {draft.artifactType === 'system_prompt' ? '系统提示词' : draft.artifactType === 'task_prompt' ? '任务 Prompt' : draft.artifactType === 'analysis_workflow' ? '分析工作流' : '对话协作'}
            {' · '}
            {draft.outputPreference === 'balanced' ? '平衡' : draft.outputPreference === 'depth' ? '深度' : draft.outputPreference === 'execution' ? '可执行性' : '自然表达'}
          </div>
        </div>

        {showAdvanced && (
          <div className="grid gap-4 rounded-[1.6rem] border border-slate-200/80 bg-slate-50/75 p-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
            <div className="rounded-[1.35rem] border border-slate-200/80 bg-white/90 p-4">
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
                  <input
                    type="checkbox"
                    checked={draft.showDiagnosis}
                    onChange={(e) => onChange({ showDiagnosis: e.target.checked })}
                  />
                </label>
                <label className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
                  <div>
                    <div className="font-medium text-slate-900">仅输出 Prompt</div>
                    <div className="mt-1 text-xs text-slate-500">适合直接复制，不附带额外解释</div>
                  </div>
                  <input
                    type="checkbox"
                    checked={draft.promptOnly}
                    onChange={(e) => onChange({ promptOnly: e.target.checked })}
                  />
                </label>
              </div>
            </div>

            <div className="grid gap-4">
              <div>
                <div className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Artifact Type</div>
                <div className="grid gap-2 sm:grid-cols-2">
                  {[
                    ['system_prompt', '系统提示词'],
                    ['task_prompt', '任务 Prompt'],
                    ['analysis_workflow', '分析工作流'],
                    ['conversation_prompt', '对话协作'],
                  ].map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => onChange({ artifactType: value as PromptArtifactType })}
                      className={`rounded-[1.2rem] border px-4 py-3 text-left text-sm transition ${
                        draft.artifactType === value
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
                <div className="grid gap-2 sm:grid-cols-2">
                  {[
                    ['balanced', '平衡'],
                    ['depth', '深度'],
                    ['execution', '可执行性'],
                    ['natural', '自然表达'],
                  ].map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => onChange({ outputPreference: value as GenerateOutputPreference })}
                      className={`rounded-[1.2rem] border px-4 py-3 text-left text-sm transition ${
                        draft.outputPreference === value
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
          </div>
        )}

        <div className="flex flex-col gap-4 border-t border-slate-200/80 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="max-w-xl text-sm leading-6 text-slate-500">
            先写你的目标就好。Generate 模式会直接把你的意图组织成更完整、更稳定、可直接复用的 Prompt 产物。
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden text-xs text-slate-400 sm:block">Cmd/Ctrl + Enter 快速提交</div>
            <Button
              type="button"
              className="h-12 rounded-full bg-slate-950 px-6 text-white hover:bg-slate-800"
              disabled={!draft.userInput.trim() || isLoading}
              onClick={handlePrimaryAction}
            >
              {actionLabel}
              {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

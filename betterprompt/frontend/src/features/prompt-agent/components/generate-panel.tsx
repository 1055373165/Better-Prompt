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
  '帮我写一个用于 PRD 需求分析的一次性任务 Prompt',
  '帮我写一个分析用户留存数据的 Prompt',
  '帮我生成一个用于代码 Review 的任务 Prompt',
  '帮我生成一个适用于英文论文 PDF 中译、排版保真和术语一致的翻译 Prompt',
];

const ARTIFACT_LABELS: Record<PromptArtifactType, string> = {
  task_prompt: '任务 Prompt',
  system_prompt: '系统提示词',
  analysis_workflow: '分析工作流',
  conversation_prompt: '对话协作',
};

const OUTPUT_PREFERENCE_LABELS: Record<GenerateOutputPreference, string> = {
  balanced: '平衡',
  depth: '深度',
  execution: '可执行性',
  natural: '自然表达',
};

const ARTIFACT_OPTIONS: Array<{
  value: PromptArtifactType;
  label: string;
  description: string;
}> = [
  {
    value: 'task_prompt',
    label: '任务 Prompt',
    description: '默认，适合一次性直接发送给目标模型',
  },
  {
    value: 'system_prompt',
    label: '系统提示词',
    description: '适合长期代理、固定角色或工作流底座',
  },
  {
    value: 'analysis_workflow',
    label: '分析工作流',
    description: '适合复杂拆解、阶段推进和验证',
  },
  {
    value: 'conversation_prompt',
    label: '对话协作',
    description: '适合多轮澄清、逐步收敛的任务',
  },
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
              不需要先想清楚 Prompt 结构。你可以直接贴原始 prompt、任务描述或一句模糊想法，系统会识别背后的元需求，并重写成更强的最终 Prompt；只有在你主动切换时，才会改成系统提示词或其他高级产物。
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
              <div className="mt-1 text-sm font-medium text-slate-900">默认重写为最终执行 Prompt</div>
              <div className="mt-1 text-sm leading-6 text-slate-500">重点是优化你原始 prompt，而不是替你发明多余的中间流程。</div>
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
            placeholder="例如：我想实现一个智能选股功能，应该采用哪些策略？&#10;或者：帮我分析一个 SaaS 商业模式。&#10;或者：我会上传英文论文 PDF，需要生成中译版，重点保证排版识别、术语一致和中英对照对齐。"
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
            {ARTIFACT_LABELS[draft.artifactType]}
            {' · '}
            {OUTPUT_PREFERENCE_LABELS[draft.outputPreference]}
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
                  {ARTIFACT_OPTIONS.map(({ value, label, description }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => onChange({ artifactType: value })}
                      className={`rounded-[1.2rem] border px-4 py-3 text-left text-sm transition ${
                        draft.artifactType === value
                          ? 'border-slate-900 bg-slate-950 text-white shadow-[0_18px_50px_-30px_rgba(15,23,42,0.85)]'
                          : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      <div className="font-medium">{label}</div>
                      <div className={`mt-1 text-xs leading-5 ${draft.artifactType === value ? 'text-slate-300' : 'text-slate-500'}`}>
                        {description}
                      </div>
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
            先贴你的原始 prompt 或需求就好。Generate 模式默认会把它重写成更高质量的最终执行 Prompt；如果你确实在搭长期代理，再切到系统提示词。
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

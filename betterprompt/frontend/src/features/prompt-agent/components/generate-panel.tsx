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
    <div className="bp-surface overflow-hidden px-5 py-6 md:px-7">
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div>
          <div className="bp-overline">Intent Draft</div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[var(--bp-ink)]">把你的真实目标写出来</h2>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-[var(--bp-ink-soft)]">
            不需要先想清楚 Prompt 结构。你可以直接贴原始 prompt、任务描述或一句模糊想法，系统会识别背后的元需求，并重写成更强的最终 Prompt。
          </p>
        </div>

        <div className="bp-surface-soft px-4 py-4">
          <div className="bp-overline">Current Defaults</div>
          <div className="mt-4 space-y-3">
            <div className="bp-meta-card">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">输出类型</div>
              <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{ARTIFACT_LABELS[draft.artifactType]}</div>
            </div>
            <div className="bp-meta-card">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">优化偏好</div>
              <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{OUTPUT_PREFERENCE_LABELS[draft.outputPreference]}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,1fr)_280px]">
        <div>
          <div className="mb-2 flex items-center justify-between gap-3">
            <div className="bp-overline">Task Brief</div>
            <div className="flex items-center gap-2 text-xs text-[var(--bp-ink-soft)]">
              <Layers3 className="h-3.5 w-3.5" />
              Cmd/Ctrl + Enter 直接生成
            </div>
          </div>
          <textarea
            value={draft.userInput}
            onChange={(e) => onChange({ userInput: e.target.value })}
            placeholder="例如：我想实现一个智能选股功能，应该采用哪些策略？&#10;&#10;或者：帮我分析一个 SaaS 商业模式。&#10;&#10;或者：我会上传英文论文 PDF，需要生成中译版，重点保证排版识别、术语一致和中英对照对齐。"
            className="bp-input min-h-[320px] text-sm leading-8"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                handlePrimaryAction();
              }
            }}
          />
        </div>

        <div className="space-y-4">
          <div className="bp-surface-soft px-4 py-4">
            <div className="bp-overline">Prompt Starters</div>
            <div className="mt-4 flex flex-wrap gap-2">
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => onChange({ userInput: example })}
                  className="bp-chip w-full justify-start rounded-[1rem] px-3 py-3 text-left text-xs leading-5"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>

          <div className="bp-surface-soft px-4 py-4">
            <div className="bp-overline">Working Note</div>
            <p className="mt-3 text-sm leading-7 text-[var(--bp-ink-soft)]">
              首次输入越接近真实业务目标，系统越容易给出有判断力的成品 Prompt。不要只写“帮我分析一下”，把对象、目标、限制和你在意的结果写进去。
            </p>
          </div>
        </div>
      </div>

      <div className="mt-6 flex items-center justify-between gap-4 border-t border-[var(--bp-line)] pt-5">
        <button
          type="button"
          onClick={() => setShowAdvanced((current) => !current)}
          className="inline-flex items-center gap-2 text-sm font-medium text-[var(--bp-ink-soft)] transition hover:text-[var(--bp-ink)]"
        >
          <ChevronDown className={`h-4 w-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
          高级选项
        </button>
        <div className="rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.7)] px-3 py-1 text-xs text-[var(--bp-ink-soft)]">
          {ARTIFACT_LABELS[draft.artifactType]}
          {' · '}
          {OUTPUT_PREFERENCE_LABELS[draft.outputPreference]}
        </div>
      </div>

      {showAdvanced && (
        <div className="mt-5 grid gap-4 rounded-[1.5rem] border border-[var(--bp-line)] bg-[rgba(255,252,247,0.72)] p-5 xl:grid-cols-[280px_minmax(0,1fr)]">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
              <Settings2 className="h-4 w-4 text-[var(--bp-clay)]" />
              输出控制
            </div>
            <label className="flex items-start justify-between gap-3 rounded-[1.1rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.76)] px-4 py-3">
              <div>
                <div className="text-sm font-semibold text-[var(--bp-ink)]">显示诊断摘要</div>
                <div className="mt-1 text-xs leading-5 text-[var(--bp-ink-soft)]">返回任务判断与潜在失败模式</div>
              </div>
              <input
                type="checkbox"
                checked={draft.showDiagnosis}
                onChange={(e) => onChange({ showDiagnosis: e.target.checked })}
                className="mt-1 h-4 w-4 rounded border-[var(--bp-line-strong)] text-[var(--bp-clay)] focus:ring-[var(--bp-clay)]"
              />
            </label>
            <label className="flex items-start justify-between gap-3 rounded-[1.1rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.76)] px-4 py-3">
              <div>
                <div className="text-sm font-semibold text-[var(--bp-ink)]">仅输出 Prompt</div>
                <div className="mt-1 text-xs leading-5 text-[var(--bp-ink-soft)]">适合直接复制，不附带额外解释</div>
              </div>
              <input
                type="checkbox"
                checked={draft.promptOnly}
                onChange={(e) => onChange({ promptOnly: e.target.checked })}
                className="mt-1 h-4 w-4 rounded border-[var(--bp-line-strong)] text-[var(--bp-clay)] focus:ring-[var(--bp-clay)]"
              />
            </label>
          </div>

          <div className="grid gap-5">
            <div>
              <div className="bp-overline">Artifact Type</div>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {ARTIFACT_OPTIONS.map(({ value, label, description }) => {
                  const active = draft.artifactType === value;

                  return (
                    <button
                      key={value}
                      type="button"
                      onClick={() => onChange({ artifactType: value })}
                      className={`rounded-[1.2rem] border px-4 py-3 text-left transition ${
                        active
                          ? 'border-[rgba(31,36,45,0.18)] bg-[linear-gradient(135deg,rgba(30,38,52,0.98),rgba(55,65,78,0.98))] text-[#f8f3eb] shadow-[0_18px_42px_-28px_rgba(24,25,27,0.5)]'
                          : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.78)] text-[var(--bp-ink)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)]'
                      }`}
                    >
                      <div className="text-sm font-semibold">{label}</div>
                      <div className={`mt-1 text-xs leading-5 ${active ? 'text-[#d4d8df]' : 'text-[var(--bp-ink-soft)]'}`}>
                        {description}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <div className="bp-overline">Optimization Preference</div>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {[
                  ['balanced', '平衡'],
                  ['depth', '深度'],
                  ['execution', '可执行性'],
                  ['natural', '自然表达'],
                ].map(([value, label]) => {
                  const active = draft.outputPreference === value;

                  return (
                    <button
                      key={value}
                      type="button"
                      onClick={() => onChange({ outputPreference: value as GenerateOutputPreference })}
                      className={`rounded-[1.1rem] border px-4 py-3 text-left text-sm font-semibold transition ${
                        active
                          ? 'border-[rgba(162,74,53,0.22)] bg-[rgba(162,74,53,0.12)] text-[var(--bp-clay)]'
                          : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.78)] text-[var(--bp-ink)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)]'
                      }`}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="mt-6 flex flex-col gap-4 border-t border-[var(--bp-line)] pt-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="max-w-xl text-sm leading-7 text-[var(--bp-ink-soft)]">
          默认会把你的原始需求重写成更高质量的最终执行 Prompt。只有当你明确需要长期代理或复杂流程时，再切到系统提示词或分析工作流。
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden text-xs text-[var(--bp-ink-soft)] sm:block">Cmd/Ctrl + Enter 快速提交</div>
          <Button
            type="button"
            className="bp-action-primary h-12 px-6"
            disabled={!draft.userInput.trim() || isLoading}
            onClick={handlePrimaryAction}
          >
            {actionLabel}
            {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}

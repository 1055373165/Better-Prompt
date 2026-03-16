import { useEffect, useState } from 'react';
import { ArrowUpRight, Brain, ChartBar, Code2, GraduationCap, Languages, Layers3, Lightbulb, Megaphone, PenLine, Search, Sparkles, Target, Wand2 } from 'lucide-react';
import promptAgentHeroIllustration from '../../assets/prompt-agent-hero-illustration.svg';
import { DebugPanel } from './components/debug-panel';
import { EvaluatePanel } from './components/evaluate-panel';
import { GeneratePanel } from './components/generate-panel';
import { ModeSelector } from './components/mode-selector';
import { ResultPanel } from './components/result-panel';
import { ContinueActions } from './components/continue-actions';
import { usePromptAgentGenerateStream } from './hooks/use-prompt-agent-generate-stream';
import { usePromptAgentDebug } from './hooks/use-prompt-agent-debug';
import { usePromptAgentEvaluate } from './hooks/use-prompt-agent-evaluate';
import { usePromptAgentContinue } from './hooks/use-prompt-agent-continue';
import type { DebugDraft, EvaluateDraft, GenerateDraft, PromptAgentMode } from './types';

const DEFAULT_CONTINUE_ACTIONS: Record<PromptAgentMode, string[]> = {
  generate: ['再增强深度', '再提高可执行性', '改成更自然的表达风格'],
  debug: ['继续修复结构缺口', '补强边界与约束', '保留原意但增强判断力'],
  evaluate: ['自动修复最低分项', '补强整体稳定性', '基于评估重生成一版'],
};

const INITIAL_GENERATE_DRAFT: GenerateDraft = {
  userInput: '',
  showDiagnosis: true,
  promptOnly: false,
  artifactType: 'task_prompt',
  outputPreference: 'balanced',
};

const INITIAL_DEBUG_DRAFT: DebugDraft = {
  originalTask: '',
  currentPrompt: '',
  currentOutput: '',
};

const INITIAL_EVALUATE_DRAFT: EvaluateDraft = {
  targetText: '',
  targetType: 'prompt',
};

const FIX_LAYER_LABELS: Record<string, string> = {
  problem_redefinition: '问题重定义层',
  cognitive_drill_down: '认知下钻层',
  key_point_priority: '关键点优先层',
  criticality: '批判性分析层',
  information_density: '信息密度层',
  boundary_validation: '边界验证层',
  executability: '可执行性层',
  style_control: '风格控制层',
};

export default function PromptAgentPage() {
  const [mode, setMode] = useState<PromptAgentMode>('generate');
  const [copied, setCopied] = useState(false);
  const [generateDraft, setGenerateDraft] = useState<GenerateDraft>(INITIAL_GENERATE_DRAFT);
  const [debugDraft, setDebugDraft] = useState<DebugDraft>(INITIAL_DEBUG_DRAFT);
  const [evaluateDraft, setEvaluateDraft] = useState<EvaluateDraft>(INITIAL_EVALUATE_DRAFT);

  const generateMutation = usePromptAgentGenerateStream();
  const debugMutation = usePromptAgentDebug();
  const evaluateMutation = usePromptAgentEvaluate();
  const continueMutation = usePromptAgentContinue();

  useEffect(() => {
    continueMutation.reset();
  }, [mode]);

  const baseResultTextByMode: Record<PromptAgentMode, string> = {
    generate: generateMutation.data?.final_prompt || '',
    debug: debugMutation.data?.fixed_prompt || '',
    evaluate: evaluateMutation.data?.top_issue || '',
  };
  const continueSourceTextByMode: Record<PromptAgentMode, string> = {
    generate: generateMutation.data?.final_prompt || '',
    debug: debugMutation.data?.fixed_prompt || '',
    evaluate: evaluateMutation.variables?.target_text || evaluateDraft.targetText.trim(),
  };
  const activeBaseResultText = baseResultTextByMode[mode];
  const activeContinueResult = continueMutation.data?.source_mode === mode ? continueMutation.data : null;
  const activeContinueStreamMeta = continueMutation.meta?.source_mode === mode ? continueMutation.meta : null;
  const activeContinueStreamingText = continueMutation.variables?.mode === mode ? continueMutation.streamingText : '';
  const hasBaseResult = Boolean(activeBaseResultText || activeContinueResult);
  const latestActions = activeContinueResult?.suggested_next_actions
    ?? (hasBaseResult ? DEFAULT_CONTINUE_ACTIONS[mode] : []);
  const currentContinueSourceText = activeContinueResult?.refined_result || continueSourceTextByMode[mode];
  const continueContextNotesByMode: Record<PromptAgentMode, string | undefined> = {
    generate: undefined,
    debug: debugMutation.data
      ? [
        `原始任务：${debugMutation.variables?.original_task || debugDraft.originalTask.trim()}`,
        `最高风险失败模式：${debugMutation.data.top_failure_mode}`,
        debugMutation.data.weaknesses.length ? `当前弱点：${debugMutation.data.weaknesses.join(' / ')}` : '',
        debugMutation.data.missing_control_layers.length
          ? `建议补强控制层：${debugMutation.data.missing_control_layers.map((layer) => FIX_LAYER_LABELS[layer] ?? layer).join(' / ')}`
          : '',
      ].filter(Boolean).join('\n')
      : undefined,
    evaluate: evaluateMutation.data
      ? [
        `当前评估对象：${(evaluateMutation.variables?.target_type || evaluateDraft.targetType) === 'prompt' ? 'Prompt' : '输出内容'}`,
        `最主要缺陷：${evaluateMutation.data.top_issue}`,
        `建议优先修复层：${FIX_LAYER_LABELS[evaluateMutation.data.suggested_fix_layer] ?? evaluateMutation.data.suggested_fix_layer}`,
        `总分：${evaluateMutation.data.total_score}/35`,
        evaluateMutation.data.total_interpretation ? `总分解读：${evaluateMutation.data.total_interpretation}` : '',
      ].filter(Boolean).join('\n')
      : undefined,
  };
  const pendingContinueGoal = continueMutation.isPending && continueMutation.variables?.mode === mode
    ? continueMutation.variables.optimization_goal
    : null;
  const currentContinueError = continueMutation.variables?.mode === mode ? continueMutation.error : null;

  const handleCopy = async (content: string) => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  };

  const currentError =
    (mode === 'generate'
      ? generateMutation.error
      : mode === 'debug'
        ? debugMutation.error
        : evaluateMutation.error) || currentContinueError;
  const nonGenerateFlowCopy = mode === 'debug'
    ? {
      badge: 'Repair Flow',
      accent: '上方诊断，下方修复结果',
      title: '调试工作区',
      description: '先定位 Prompt 的结构缺口和失效模式，再在下方查看修复后版本与继续优化的实时生成内容。',
      stepOne: '分析 Prompt 问题',
      stepTwo: '查看修复与继续优化',
      resultEyebrow: 'Debug Result',
      resultTitle: '调试结果 / 修复后 Prompt',
      resultDescription: '调试诊断、修复后 Prompt 和继续优化生成结果都集中在这里，方便连续阅读和比对。',
    }
    : {
      badge: 'Evaluate Flow',
      accent: '上方评估，下方优化结果',
      title: '评估工作区',
      description: '先完成质量评估，再在下方集中查看评分结论、优化后版本，以及继续优化过程中的实时 LLM 输出。',
      stepOne: '评估 Prompt 或输出',
      stepTwo: '查看评分与优化结果',
      resultEyebrow: 'Evaluate Result',
      resultTitle: '评估结果 / 优化后版本',
      resultDescription: '评分、主要缺陷、建议修复层和优化后的新版本都放在同一列里，避免长文本挤在右侧窄栏。',
    };

  const resultStack = (
    <div className="space-y-4">
      {currentError && (
        <div className="rounded-[1.5rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700 shadow-[0_20px_40px_-34px_rgba(220,38,38,0.75)]">
          {currentError instanceof Error ? currentError.message : '请求失败，请稍后重试'}
        </div>
      )}
      <ResultPanel
        mode={mode}
        generateResult={generateMutation.data ?? null}
        debugResult={debugMutation.data ?? null}
        evaluateResult={evaluateMutation.data ?? null}
        continueResult={activeContinueResult}
        continueStreamingText={activeContinueStreamingText}
        isContinueStreaming={continueMutation.isStreaming && continueMutation.variables?.mode === mode}
        continueStreamMeta={activeContinueStreamMeta}
        onCopy={handleCopy}
        streamingText={generateMutation.streamingText}
        isStreaming={generateMutation.isStreaming}
        streamMeta={generateMutation.meta}
      />
      <ContinueActions
        actions={latestActions}
        isLoading={continueMutation.isPending}
        activeGoal={pendingContinueGoal}
        completedGoal={activeContinueResult?.optimization_goal ?? null}
        resultLabel={activeContinueResult?.result_label ?? null}
        onSelect={(goal) => {
          if (!currentContinueSourceText) return;
          continueMutation.mutate({
            previous_result: currentContinueSourceText,
            optimization_goal: goal,
            mode,
            context_notes: continueContextNotesByMode[mode],
          });
        }}
      />
      {copied && (
        <div className="rounded-[1.5rem] border border-emerald-200/80 bg-emerald-50/90 px-4 py-3 text-sm text-emerald-700 shadow-[0_20px_40px_-34px_rgba(16,185,129,0.65)]">
          已复制到剪贴板
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.14),transparent_28%),linear-gradient(180deg,#f9fbff_0%,#f4f7fb_44%,#edf2f7_100%)]">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 md:px-8 md:py-10">
        <section className="overflow-hidden rounded-[2rem] border border-white/80 bg-[linear-gradient(135deg,rgba(255,255,255,0.92),rgba(248,250,252,0.96)_52%,rgba(239,246,255,0.92))] px-6 py-6 shadow-[0_28px_90px_-52px_rgba(15,23,42,0.28)] backdrop-blur-xl md:px-8">
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_360px] xl:items-end">
            <div>
              <div className="relative mb-6 overflow-hidden rounded-[1.75rem] border border-white/80 bg-[radial-gradient(circle_at_top_left,rgba(125,211,252,0.26),transparent_30%),linear-gradient(135deg,rgba(255,255,255,0.96),rgba(248,250,252,0.94)_52%,rgba(239,246,255,0.9))] p-4 shadow-[0_24px_60px_-44px_rgba(15,23,42,0.34)] sm:p-5">
                <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.3),transparent_46%)]" />
                <div className="relative flex min-h-[220px] items-center justify-center sm:min-h-[250px]">
                  <img
                    src={promptAgentHeroIllustration}
                    alt="Prompt Agent 将原始需求转化为高质量 Prompt 的流程插画"
                    className="h-auto max-h-[210px] w-full max-w-[22rem] object-contain sm:max-h-[238px] sm:max-w-[24rem]"
                  />
                </div>
              </div>
              <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                <Sparkles className="h-3.5 w-3.5" />
                BetterPrompt Workspace
              </div>
              <h1 className="mt-4 text-3xl font-semibold tracking-tight text-slate-950 md:text-[2.4rem]">
                Prompt Agent
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600 md:text-base">
                贴上你准备发给 LLM 的原始 prompt 或模糊需求，系统会识别元需求、激活对应领域的专家视角，并重写成更高质量的最终 Prompt。
              </p>

              <div className="mt-5 flex flex-wrap gap-2">
                {[
                  { icon: Code2, label: '代码分析' },
                  { icon: Target, label: '架构设计' },
                  { icon: ChartBar, label: '数据分析' },
                  { icon: Search, label: '商业洞察' },
                  { icon: Lightbulb, label: '产品设计' },
                  { icon: GraduationCap, label: '教学' },
                  { icon: Megaphone, label: '创意营销' },
                  { icon: Languages, label: '文档翻译' },
                  { icon: PenLine, label: '写作' },
                  { icon: Brain, label: '算法' },
                ].map(({ icon: Icon, label }) => (
                  <div
                    key={label}
                    className="inline-flex items-center gap-1.5 rounded-full border border-slate-200/80 bg-white/70 px-2.5 py-1 text-xs text-slate-500 transition hover:border-slate-300 hover:bg-white hover:text-slate-700"
                  >
                    <Icon className="h-3 w-3" />
                    {label}
                  </div>
                ))}
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
              <div className="rounded-[1.4rem] border border-white/80 bg-white/88 p-4 shadow-[0_16px_40px_-32px_rgba(15,23,42,0.24)]">
                <div className="flex items-center justify-between text-slate-500">
                  <Layers3 className="h-4 w-4" />
                  <span className="text-[11px] uppercase tracking-[0.16em]">Input</span>
                </div>
                <div className="mt-3 text-sm font-semibold text-slate-950">单一输入入口</div>
                <div className="mt-1 text-sm leading-6 text-slate-500">避免重复填写和模式切换后的内容断裂</div>
              </div>
              <div className="rounded-[1.4rem] border border-white/80 bg-white/88 p-4 shadow-[0_16px_40px_-32px_rgba(15,23,42,0.24)]">
                <div className="flex items-center justify-between text-slate-500">
                  <Wand2 className="h-4 w-4" />
                  <span className="text-[11px] uppercase tracking-[0.16em]">Mode</span>
                </div>
                <div className="mt-3 text-sm font-semibold text-slate-950">模式由用户决定</div>
                <div className="mt-1 text-sm leading-6 text-slate-500">选择 Generate 就直接生成，不再自作主张改成调试或评估</div>
              </div>
              <div className="rounded-[1.4rem] border border-white/80 bg-white/88 p-4 shadow-[0_16px_40px_-32px_rgba(15,23,42,0.24)]">
                <div className="flex items-center justify-between text-slate-500">
                  <ArrowUpRight className="h-4 w-4" />
                  <span className="text-[11px] uppercase tracking-[0.16em]">Result</span>
                </div>
                <div className="mt-3 text-sm font-semibold text-slate-950">稳定结果栏</div>
                <div className="mt-1 text-sm leading-6 text-slate-500">清楚告诉你拿到的是最终执行 Prompt 还是高级 Prompt 工件</div>
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-[1.8rem] border border-white/80 bg-white/76 p-5 shadow-[0_24px_70px_-46px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Workflow Mode</div>
              <h2 className="mt-2 text-lg font-semibold tracking-tight text-slate-950">选择当前工作模式</h2>
              <p className="mt-1 text-sm leading-6 text-slate-500">
                生成默认交付最终执行 Prompt，调试负责修复结构缺口，评估负责判断质量和稳定性。
              </p>
            </div>
          </div>
          <div className="mt-5">
            <ModeSelector value={mode} onChange={setMode} />
          </div>
        </section>

        {mode === 'generate' ? (
          <section className="rounded-[2rem] border border-white/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.82),rgba(248,250,252,0.76))] p-4 shadow-[0_28px_80px_-50px_rgba(15,23,42,0.22)] backdrop-blur-xl md:p-6">
            <div className="flex flex-col gap-4 border-b border-slate-200/80 pb-5">
              <div className="flex flex-wrap items-center gap-2">
                <div className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Rewrite Flow
                </div>
                <div className="rounded-full border border-sky-200/80 bg-sky-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-900">
                  上方输入，下方实时生成
                </div>
              </div>
              <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-end">
                <div>
                  <h2 className="text-xl font-semibold tracking-tight text-slate-950">统一工作区</h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
                    按你给的草图，这里改成单列工作流：先在上方整理原始 prompt，再在下方实时查看重写后的系统提示词或任务 Prompt，减少来回扫视。
                  </p>
                </div>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
                  <div className="rounded-[1.3rem] border border-slate-200/80 bg-white/85 px-4 py-3">
                    <div className="text-[11px] uppercase tracking-[0.16em] text-slate-400">Step 1</div>
                    <div className="mt-1 text-sm font-medium text-slate-900">描述你想让模型做什么</div>
                  </div>
                  <div className="rounded-[1.3rem] border border-slate-200/80 bg-white/85 px-4 py-3">
                    <div className="text-[11px] uppercase tracking-[0.16em] text-slate-400">Step 2</div>
                    <div className="mt-1 text-sm font-medium text-slate-900">实时生成并继续优化</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 space-y-5">
              <GeneratePanel
                draft={generateDraft}
                onChange={(patch) => {
                  setGenerateDraft((current) => ({ ...current, ...patch }));
                }}
                isLoading={generateMutation.isPending}
                onSubmit={(payload) => {
                  continueMutation.reset();
                  generateMutation.mutate(payload);
                }}
              />

              <section className="rounded-[1.9rem] border border-slate-200/80 bg-white/72 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.55)] md:p-5">
                <div className="mb-4 flex flex-col gap-2 border-b border-slate-200/80 pb-4 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Live Output</div>
                    <h3 className="mt-2 text-lg font-semibold tracking-tight text-slate-950">系统提示词 / 实时生成区</h3>
                    <p className="mt-1 text-sm leading-6 text-slate-500">
                      生成时结果会在这里连续刷新，生成完成后也可以直接复制、继续优化。
                    </p>
                  </div>
                </div>
                {resultStack}
              </section>
            </div>
          </section>
        ) : (
          <section className="rounded-[2rem] border border-white/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.82),rgba(248,250,252,0.76))] p-4 shadow-[0_28px_80px_-50px_rgba(15,23,42,0.22)] backdrop-blur-xl md:p-6">
            <div className="flex flex-col gap-4 border-b border-slate-200/80 pb-5">
              <div className="flex flex-wrap items-center gap-2">
                <div className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  {nonGenerateFlowCopy.badge}
                </div>
                <div className="rounded-full border border-sky-200/80 bg-sky-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-sky-900">
                  {nonGenerateFlowCopy.accent}
                </div>
              </div>
              <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-end">
                <div>
                  <h2 className="text-xl font-semibold tracking-tight text-slate-950">{nonGenerateFlowCopy.title}</h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
                    {nonGenerateFlowCopy.description}
                  </p>
                </div>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
                  <div className="rounded-[1.3rem] border border-slate-200/80 bg-white/85 px-4 py-3">
                    <div className="text-[11px] uppercase tracking-[0.16em] text-slate-400">Step 1</div>
                    <div className="mt-1 text-sm font-medium text-slate-900">{nonGenerateFlowCopy.stepOne}</div>
                  </div>
                  <div className="rounded-[1.3rem] border border-slate-200/80 bg-white/85 px-4 py-3">
                    <div className="text-[11px] uppercase tracking-[0.16em] text-slate-400">Step 2</div>
                    <div className="mt-1 text-sm font-medium text-slate-900">{nonGenerateFlowCopy.stepTwo}</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 space-y-5">
              {mode === 'debug' && (
                <DebugPanel
                  draft={debugDraft}
                  onChange={(patch) => {
                    setDebugDraft((current) => ({ ...current, ...patch }));
                  }}
                  isLoading={debugMutation.isPending}
                  onSubmit={(payload) => {
                    continueMutation.reset();
                    debugMutation.mutate(payload);
                  }}
                />
              )}

              {mode === 'evaluate' && (
                <EvaluatePanel
                  draft={evaluateDraft}
                  onChange={(patch) => {
                    setEvaluateDraft((current) => ({ ...current, ...patch }));
                  }}
                  isLoading={evaluateMutation.isPending}
                  onSubmit={(payload) => {
                    continueMutation.reset();
                    evaluateMutation.mutate(payload);
                  }}
                />
              )}

              <section className="rounded-[1.9rem] border border-slate-200/80 bg-white/72 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.55)] md:p-5">
                <div className="mb-4 flex flex-col gap-2 border-b border-slate-200/80 pb-4 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{nonGenerateFlowCopy.resultEyebrow}</div>
                    <h3 className="mt-2 text-lg font-semibold tracking-tight text-slate-950">{nonGenerateFlowCopy.resultTitle}</h3>
                    <p className="mt-1 text-sm leading-6 text-slate-500">
                      {nonGenerateFlowCopy.resultDescription}
                    </p>
                  </div>
                </div>
                {resultStack}
              </section>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

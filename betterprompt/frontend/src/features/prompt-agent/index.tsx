import { useEffect, useState } from 'react';
import { ArrowUpRight, Layers3, Sparkles, Wand2 } from 'lucide-react';
import { DebugPanel } from './components/debug-panel';
import { EvaluatePanel } from './components/evaluate-panel';
import { GeneratePanel } from './components/generate-panel';
import { ModeSelector } from './components/mode-selector';
import { ResultPanel } from './components/result-panel';
import { ContinueActions } from './components/continue-actions';
import { usePromptAgentGenerate } from './hooks/use-prompt-agent-generate';
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
  artifactType: 'system_prompt',
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

export default function PromptAgentPage() {
  const [mode, setMode] = useState<PromptAgentMode>('generate');
  const [copied, setCopied] = useState(false);
  const [generateDraft, setGenerateDraft] = useState<GenerateDraft>(INITIAL_GENERATE_DRAFT);
  const [debugDraft, setDebugDraft] = useState<DebugDraft>(INITIAL_DEBUG_DRAFT);
  const [evaluateDraft, setEvaluateDraft] = useState<EvaluateDraft>(INITIAL_EVALUATE_DRAFT);

  const generateMutation = usePromptAgentGenerate();
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
  const activeBaseResultText = baseResultTextByMode[mode];
  const activeContinueResult = continueMutation.data?.source_mode === mode ? continueMutation.data : null;
  const hasBaseResult = Boolean(activeBaseResultText || activeContinueResult);
  const latestActions = activeContinueResult?.suggested_next_actions
    ?? (hasBaseResult ? DEFAULT_CONTINUE_ACTIONS[mode] : []);
  const currentResultText = activeContinueResult?.refined_result || activeBaseResultText;

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
        : evaluateMutation.error) || continueMutation.error;

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.14),transparent_28%),linear-gradient(180deg,#f9fbff_0%,#f4f7fb_44%,#edf2f7_100%)]">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 md:px-8 md:py-10">
        <section className="overflow-hidden rounded-[2rem] border border-white/80 bg-[linear-gradient(135deg,rgba(255,255,255,0.92),rgba(248,250,252,0.96)_52%,rgba(239,246,255,0.92))] px-6 py-6 shadow-[0_28px_90px_-52px_rgba(15,23,42,0.28)] backdrop-blur-xl md:px-8">
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_360px] xl:items-end">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                <Sparkles className="h-3.5 w-3.5" />
                BetterPrompt Workspace
              </div>
              <h1 className="mt-4 text-3xl font-semibold tracking-tight text-slate-950 md:text-[2.4rem]">
                Prompt Agent
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600 md:text-base">
                这页现在聚焦成一个更清晰的工作台: 左侧只保留一个主输入入口，右侧稳定显示结果和后续优化动作，
                减少重复表单，让生成、调试、评估都围绕同一条心智路径展开。
              </p>
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
                <div className="mt-1 text-sm leading-6 text-slate-500">结果、复制和继续优化始终在同一视线区</div>
              </div>
            </div>
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_minmax(360px,420px)]">
          <div className="space-y-5">
            <section className="rounded-[1.8rem] border border-white/80 bg-white/76 p-5 shadow-[0_24px_70px_-46px_rgba(15,23,42,0.22)] backdrop-blur-xl">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Workflow Mode</div>
                  <h2 className="mt-2 text-lg font-semibold tracking-tight text-slate-950">选择当前工作模式</h2>
                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    生成负责从自然语言到高质量 Prompt，调试负责修复结构缺口，评估负责判断质量和稳定性。
                  </p>
                </div>
              </div>
              <div className="mt-5">
                <ModeSelector value={mode} onChange={setMode} />
              </div>
            </section>

            {mode === 'generate' && (
              <GeneratePanel
                draft={generateDraft}
                onChange={(patch) => {
                  setGenerateDraft((current) => ({ ...current, ...patch }));
                }}
                isLoading={generateMutation.isPending}
                onSubmit={(payload) => {
                  generateMutation.mutate(payload);
                }}
              />
            )}

            {mode === 'debug' && (
              <DebugPanel
                draft={debugDraft}
                onChange={(patch) => {
                  setDebugDraft((current) => ({ ...current, ...patch }));
                }}
                isLoading={debugMutation.isPending}
                onSubmit={(payload) => {
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
                  evaluateMutation.mutate(payload);
                }}
              />
            )}
          </div>

          <div className="space-y-4 xl:sticky xl:top-6 xl:self-start">
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
              continueResult={continueMutation.data ?? null}
              onCopy={handleCopy}
            />
            <ContinueActions
              actions={latestActions}
              isLoading={continueMutation.isPending}
              onSelect={(goal) => {
                if (!currentResultText) return;
                continueMutation.mutate({
                  previous_result: currentResultText,
                  optimization_goal: goal,
                  mode,
                });
              }}
            />
            {copied && (
              <div className="rounded-[1.5rem] border border-emerald-200/80 bg-emerald-50/90 px-4 py-3 text-sm text-emerald-700 shadow-[0_20px_40px_-34px_rgba(16,185,129,0.65)]">
                已复制到剪贴板
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

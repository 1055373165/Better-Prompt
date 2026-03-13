import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowRight, ArrowUpRight, ChevronDown, Layers3, Lightbulb, Sparkles, Wand2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
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
import type { PromptAgentMode, PromptArtifactType } from './types';

const DEFAULT_CONTINUE_ACTIONS: Record<PromptAgentMode, string[]> = {
  generate: ['再增强深度', '再提高可执行性', '改成更自然的表达风格'],
  debug: ['继续修复结构缺口', '补强边界与约束', '保留原意但增强判断力'],
  evaluate: ['自动修复最低分项', '补强整体稳定性', '基于评估重生成一版'],
};

export default function PromptAgentPage() {
  const [mode, setMode] = useState<PromptAgentMode>('generate');
  const [copied, setCopied] = useState(false);
  const [userInput, setUserInput] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [artifactType, setArtifactType] = useState<PromptArtifactType>('system_prompt');
  const [outputPreference, setOutputPreference] = useState<'balanced' | 'depth' | 'execution' | 'natural'>('balanced');
  const workflowRef = useRef<HTMLDivElement | null>(null);

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
  const smartSuggestions = useMemo(() => {
    const input = userInput.toLowerCase();
    if (input.includes('修复') || input.includes('问题') || input.includes('不好') || input.includes('debug')) {
      return { mode: 'debug' as PromptAgentMode, label: '建议：进入调试面板', icon: Wand2 };
    }
    if (input.includes('评估') || input.includes('打分') || input.includes('质量') || input.includes('evaluate')) {
      return { mode: 'evaluate' as PromptAgentMode, label: '建议：进入评估面板', icon: Sparkles };
    }
    return { mode: 'generate' as PromptAgentMode, label: '建议：直接生成结果', icon: Layers3 };
  }, [userInput]);

  const handleCopy = async (content: string) => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  };

  const handleQuickSubmit = () => {
    if (!userInput.trim()) return;
    const suggestedMode = smartSuggestions.mode;
    setMode(suggestedMode);

    if (suggestedMode !== 'generate') {
      workflowRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }

    generateMutation.mutate({
      user_input: userInput.trim(),
      show_diagnosis: true,
      output_preference: outputPreference,
      artifact_type: artifactType,
      prompt_only: false,
    });
  };

  const currentError =
    (mode === 'generate'
      ? generateMutation.error
      : mode === 'debug'
        ? debugMutation.error
        : evaluateMutation.error) || continueMutation.error;

  const quickActionLabel = smartSuggestions.mode === 'generate'
    ? (generateMutation.isPending ? '处理中...' : '开始生成')
    : smartSuggestions.mode === 'debug'
      ? '切到调试面板'
      : '切到评估面板';

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.12),transparent_28%),linear-gradient(180deg,#f8fbff_0%,#f6f7fb_42%,#eef2f7_100%)]">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 md:px-8 md:py-10">
        <section className="relative overflow-hidden rounded-[2rem] border border-white/70 bg-[linear-gradient(135deg,rgba(15,23,42,0.98),rgba(30,41,59,0.94)_55%,rgba(15,23,42,0.92))] px-6 py-8 text-white shadow-[0_30px_100px_-45px_rgba(15,23,42,0.95)] md:px-8 md:py-10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(125,211,252,0.25),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(129,140,248,0.18),transparent_30%)]" />
          <div className="relative grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_360px] xl:items-end">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-white/75">
                <Sparkles className="h-3.5 w-3.5" />
                BetterPrompt Workspace
              </div>
              <h1 className="mt-5 max-w-4xl text-3xl font-semibold leading-tight tracking-tight md:text-[2.65rem]">
                Prompt Agent
              </h1>
              <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 md:text-base">
                你负责表达意图，我负责把它升级成更专业、更稳定、更适合直接落地的 Prompt 结果。
                当前界面已升级为更接近产品化工作台的结构，便于持续生成、调试与评估。
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 backdrop-blur-xl">
                  <div className="text-[11px] uppercase tracking-[0.16em] text-white/45">Focus</div>
                  <div className="mt-1 text-sm font-medium text-white">Professional Prompt Workflow</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 backdrop-blur-xl">
                  <div className="text-[11px] uppercase tracking-[0.16em] text-white/45">Smart Mode</div>
                  <div className="mt-1 text-sm font-medium text-white">Auto-Detect Intent</div>
                </div>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
              <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4 backdrop-blur-xl">
                <div className="flex items-center justify-between text-white/70">
                  <Layers3 className="h-4 w-4" />
                  <span className="text-[11px] uppercase tracking-[0.16em]">Structure</span>
                </div>
                <div className="mt-3 text-lg font-semibold text-white">3 模式</div>
                <div className="mt-1 text-sm leading-6 text-slate-300">Generate / Debug / Evaluate 一体化工作流</div>
              </div>
              <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4 backdrop-blur-xl">
                <div className="flex items-center justify-between text-white/70">
                  <Wand2 className="h-4 w-4" />
                  <span className="text-[11px] uppercase tracking-[0.16em]">Output</span>
                </div>
                <div className="mt-3 text-lg font-semibold text-white">高密度结果</div>
                <div className="mt-1 text-sm leading-6 text-slate-300">强调边界、约束、可执行性和复用性</div>
              </div>
              <div className="rounded-[1.5rem] border border-white/10 bg-white/5 p-4 backdrop-blur-xl">
                <div className="flex items-center justify-between text-white/70">
                  <ArrowUpRight className="h-4 w-4" />
                  <span className="text-[11px] uppercase tracking-[0.16em]">UX</span>
                </div>
                <div className="mt-3 text-lg font-semibold text-white">现代工作台</div>
                <div className="mt-1 text-sm leading-6 text-slate-300">更清晰的输入区、结果区与后续优化动作</div>
              </div>
            </div>
          </div>
        </section>

        <section className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/75 shadow-[0_24px_80px_-44px_rgba(15,23,42,0.3)] backdrop-blur-xl">
          <div className="border-b border-slate-200/70 bg-[linear-gradient(180deg,rgba(248,250,252,0.95),rgba(255,255,255,0.85))] px-6 py-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  <Lightbulb className="h-3.5 w-3.5" />
                  Quick Start
                </div>
                <h2 className="mt-4 text-lg font-semibold tracking-tight text-slate-950">快速描述你的目标</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                  生成类需求可以在这里直接提交；如果内容更像调试或评估，系统会引导你切换到下方对应面板。
                </p>
              </div>
              {userInput && (
                <div className="flex items-center gap-2 rounded-2xl border border-slate-200/80 bg-white/90 px-4 py-2">
                  <smartSuggestions.icon className="h-4 w-4 text-slate-500" />
                  <span className="text-sm font-medium text-slate-700">{smartSuggestions.label}</span>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-5 px-6 py-6">
            <div>
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="例如：我想让模型帮我分析商业模式，但不知道怎么问&#10;或：这个 Prompt 有问题，帮我修复一下&#10;或：评估一下这个输出质量如何"
                className="min-h-[180px] w-full rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] px-5 py-4 text-sm leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-sky-200 focus:shadow-[0_0_0_4px_rgba(14,165,233,0.08)]"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    e.preventDefault();
                    handleQuickSubmit();
                  }
                }}
              />
            </div>

            <div className="flex items-center justify-between border-t border-slate-200/80 pt-5">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-2 text-sm text-slate-600 transition hover:text-slate-900"
              >
                <ChevronDown className={`h-4 w-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
                高级选项
              </button>
              <div className="flex items-center gap-3">
                <div className="text-xs text-slate-400">
                  {smartSuggestions.mode === 'generate' ? '⌘ + Enter 快速提交' : '将定位到下方结构化面板'}
                </div>
                <Button
                  onClick={handleQuickSubmit}
                  disabled={!userInput.trim() || (smartSuggestions.mode === 'generate' && generateMutation.isPending)}
                  className="h-12 rounded-full bg-slate-950 px-6 text-white hover:bg-slate-800"
                >
                  {quickActionLabel}
                  {!(smartSuggestions.mode === 'generate' && generateMutation.isPending) && <ArrowRight className="ml-2 h-4 w-4" />}
                </Button>
              </div>
            </div>

            {showAdvanced && (
              <div className="grid gap-4 rounded-[1.5rem] border border-slate-200/80 bg-slate-50/80 p-5 lg:grid-cols-2">
                <div>
                  <div className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">输出类型</div>
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
                        onClick={() => setArtifactType(value as PromptArtifactType)}
                        className={`rounded-xl border px-3 py-2 text-left text-sm transition ${
                          artifactType === value
                            ? 'border-slate-900 bg-slate-950 text-white'
                            : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">优化偏好</div>
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
                        onClick={() => setOutputPreference(value as 'balanced' | 'depth' | 'execution' | 'natural')}
                        className={`rounded-xl border px-3 py-2 text-left text-sm transition ${
                          outputPreference === value
                            ? 'border-sky-200 bg-sky-50 text-sky-900'
                            : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        <div ref={workflowRef} className="grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_minmax(360px,420px)]">
          <div className="space-y-6">
            <ModeSelector value={mode} onChange={setMode} />
            {mode === 'generate' && (
              <GeneratePanel
                isLoading={generateMutation.isPending}
                onSubmit={(payload) => {
                  generateMutation.mutate(payload);
                }}
              />
            )}
            {mode === 'debug' && (
              <DebugPanel
                isLoading={debugMutation.isPending}
                onSubmit={(payload) => {
                  debugMutation.mutate(payload);
                }}
              />
            )}
            {mode === 'evaluate' && (
              <EvaluatePanel
                isLoading={evaluateMutation.isPending}
                onSubmit={(payload) => {
                  evaluateMutation.mutate(payload);
                }}
              />
            )}
          </div>

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

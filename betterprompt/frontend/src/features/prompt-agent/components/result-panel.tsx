import { Copy, Loader2, Sparkles, Wand2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DiagnosisCard } from './diagnosis-card';
import { ScoreCard } from './score-card';
import type {
  ContinuePromptResponse,
  DebugPromptResponse,
  EvaluatePromptResponse,
  GeneratePromptResponse,
  PromptAgentMode,
  PromptArtifactType,
  PromptDiagnosis,
  PromptIterationRef,
  RunContextSnapshot,
} from '../types';

const ARTIFACT_TYPE_LABELS: Record<string, string> = {
  system_prompt: '系统提示词',
  task_prompt: '一次性任务 Prompt',
  analysis_workflow: '分析工作流 Prompt',
  conversation_prompt: '对话协作 Prompt',
};

const ARTIFACT_RESULT_TITLES: Record<string, string> = {
  system_prompt: '系统提示词',
  task_prompt: '最终执行 Prompt',
  analysis_workflow: '分析工作流 Prompt',
  conversation_prompt: '对话协作 Prompt',
};

const ARTIFACT_NEXT_STEP_HINTS: Record<string, string> = {
  system_prompt: '下一步：把这段系统提示词接到你的代理或工作流配置里。',
  task_prompt: '下一步：把这段 Prompt 直接发送给目标模型执行。',
  analysis_workflow: '下一步：把这段工作流 Prompt 发给模型，按阶段推进复杂任务。',
  conversation_prompt: '下一步：把这段 Prompt 作为多轮协作开场指令交给目标模型。',
};

const EXPERT_DOMAIN_LABELS: Record<string, string> = {
  algorithm_analysis: '算法与数据结构专家',
  source_code_analysis: '源码理解与代码审查专家',
  architecture_spec: '系统架构专家',
  business_insight: '商业分析专家',
  product_design: '产品设计专家',
  data_analysis: '数据分析专家',
  education_learning: '教学设计专家',
  creative_marketing: '创意营销专家',
  writing_generation: '写作与编辑专家',
  document_translation: '文档翻译与本地化专家',
  general_deep_analysis: '通用问题分析专家',
};

const META_NEED_LABELS: Record<string, string> = {
  algorithm_analysis: '算法推理、复杂度分析和解题过程表达',
  source_code_analysis: '源码理解、问题定位和修复判断',
  architecture_spec: '系统设计、方案权衡和边界定义',
  business_insight: '商业洞察、关键判断和优先级分析',
  product_design: '需求拆解、交互目标和落地约束',
  data_analysis: '指标解读、分析路径和结论表达',
  education_learning: '教学讲解、知识拆解和学习路径设计',
  creative_marketing: '创意表达、品牌语气和传播目标',
  writing_generation: '内容生成、风格控制和表达质量',
  document_translation: '英文文档中译、版面保真和对照一致性',
  general_deep_analysis: '模糊问题澄清、关键约束识别和高质量表达',
};

const TASK_HIGHLIGHT_LABELS: Record<string, string[]> = {
  algorithm_analysis: ['问题拆解', '复杂度约束', '关键步骤'],
  source_code_analysis: ['源码上下文', '问题定位', '修复判断'],
  architecture_spec: ['方案权衡', '边界定义', '落地约束'],
  business_insight: ['关键判断', '优先级', '失效条件'],
  product_design: ['用户目标', '约束补齐', '交付清晰度'],
  data_analysis: ['指标定义', '分析路径', '结论可执行性'],
  education_learning: ['知识拆解', '学习路径', '表达清晰度'],
  creative_marketing: ['品牌语气', '创意表达', '传播目标'],
  writing_generation: ['风格统一', '信息密度', '表达自然度'],
  document_translation: ['版面保真', '块级对齐', '术语一致', '异常回退'],
  general_deep_analysis: ['元需求识别', '关键约束', '表达质量'],
};

const MODULE_HIGHLIGHT_LABELS: Record<string, string> = {
  problem_redefinition: '把任务说清楚',
  cognitive_drill_down: '补强深层判断',
  key_point_priority: '突出关键约束',
  criticality: '补足边界与代价',
  information_density: '压缩空话提密度',
  boundary_validation: '补足边界与回退',
  executability: '强化执行步骤',
  style_control: '统一表达风格',
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

const CONTINUE_SOURCE_LABELS: Record<PromptAgentMode, string> = {
  generate: 'Generate',
  debug: 'Debug',
  evaluate: 'Evaluate',
};

const CONTINUE_SOURCE_HINTS: Record<PromptAgentMode, string> = {
  generate: '已基于上一版生成结果继续重写，当前显示的是新的最终执行 Prompt。',
  debug: '已基于上一版修复结果继续补强，当前显示的是新的修复后 Prompt。',
  evaluate: '已基于被评估内容和评估结论继续重写，当前显示的是新的优化后版本。',
};

interface StreamMeta {
  diagnosis: PromptDiagnosis | null;
  artifact_type: PromptArtifactType;
  applied_modules: string[];
  optimization_strategy: string;
  optimized_input: string;
  prompt_only: boolean;
  diagnosis_visible: boolean;
}

interface ResultPanelProps {
  mode: PromptAgentMode;
  generateResult: GeneratePromptResponse | null;
  debugResult: DebugPromptResponse | null;
  evaluateResult: EvaluatePromptResponse | null;
  continueResult: ContinuePromptResponse | null;
  continueStreamingText?: string;
  isContinueStreaming?: boolean;
  continueStreamMeta?: {
    source_mode: PromptAgentMode;
    optimization_goal: string;
    result_label: string;
  } | null;
  onCopy: (content: string) => void;
  streamingText?: string;
  isStreaming?: boolean;
  streamMeta?: StreamMeta | null;
  runContext?: RunContextSnapshot | null;
  currentIteration?: PromptIterationRef | null;
}

function buildRewriteSummary(
  diagnosis: PromptDiagnosis,
  appliedModules: string[],
  artifactType: PromptArtifactType,
): {
  expertLabel: string;
  metaNeed: string;
  highlights: string[];
} {
  const expertLabel = EXPERT_DOMAIN_LABELS[diagnosis.task_type] ?? '领域专家';
  const metaNeedBase = META_NEED_LABELS[diagnosis.task_type] ?? '任务目标澄清与高质量表达';
  const artifactLabel = ARTIFACT_RESULT_TITLES[artifactType] ?? 'Prompt';
  const taskHighlights = TASK_HIGHLIGHT_LABELS[diagnosis.task_type] ?? [];
  const moduleHighlights = appliedModules
    .map((module) => MODULE_HIGHLIGHT_LABELS[module])
    .filter((value): value is string => Boolean(value));
  const highlights = Array.from(new Set([...taskHighlights, ...moduleHighlights])).slice(0, 5);

  return {
    expertLabel,
    metaNeed: `系统判断你真正需要的是一份面向${metaNeedBase}的高质量${artifactLabel}。`,
    highlights,
  };
}

function Surface({
  title,
  subtitle,
  action,
  children,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Card className="rounded-[1.7rem] border-[var(--bp-line)] bg-[rgba(255,252,247,0.78)] shadow-[var(--bp-shadow-soft)]">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="text-sm font-semibold text-[var(--bp-ink)]">{title}</CardTitle>
            {subtitle && <div className="mt-2 text-sm leading-6 text-[var(--bp-ink-soft)]">{subtitle}</div>}
          </div>
          {action}
        </div>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function MetaPill({
  children,
  tone = 'neutral',
}: {
  children: React.ReactNode;
  tone?: 'neutral' | 'accent';
}) {
  return (
    <div
      className={
        tone === 'accent'
          ? 'rounded-full border border-[rgba(162,74,53,0.2)] bg-[rgba(162,74,53,0.1)] px-3 py-1 text-xs text-[var(--bp-clay)]'
          : 'rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] px-3 py-1 text-xs text-[var(--bp-ink-soft)]'
      }
    >
      {children}
    </div>
  );
}

function InfoBlock({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bp-meta-card">
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">{label}</div>
      <div className="mt-2 text-sm leading-6 text-[var(--bp-ink)]">{children}</div>
    </div>
  );
}

function TextSurface({ text }: { text: string }) {
  return (
    <div className="rounded-[1.45rem] border border-[var(--bp-line)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(249,243,235,0.96))] p-5 text-sm leading-8 whitespace-pre-wrap text-[var(--bp-ink)]">
      {text}
    </div>
  );
}

function ProvenanceCard({
  runContext,
  currentIteration,
}: {
  runContext: RunContextSnapshot;
  currentIteration: PromptIterationRef | null;
}) {
  const hasBindings = Boolean(
    runContext.workspace_scope?.domain_workspace_id
      || runContext.workspace_scope?.subject_id
      || runContext.run_preset_label
      || runContext.workflow_recipe_label
      || runContext.evaluation_profile_label
      || runContext.context_pack_labels.length,
  );
  const workspaceLabel = runContext.workspace_scope?.domain_workspace_label || runContext.workspace_scope?.domain_workspace_id;
  const subjectLabel = runContext.workspace_scope?.subject_label || runContext.workspace_scope?.subject_id;

  return (
    <Surface
      title="Run Provenance"
      subtitle="这次结果来自哪条运行链路，以及绑定了哪些 workflow assets 与 workspace scope。"
    >
      <div className="grid gap-3 text-sm md:grid-cols-[minmax(0,1fr)_240px]">
        <InfoBlock label="启动来源">{runContext.launch_label}</InfoBlock>
        <div className="bp-meta-card">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Session / Iteration</div>
          <div className="mt-2 font-mono text-xs leading-6 text-[var(--bp-ink)]">
            session: {currentIteration?.session_id ?? '未写入'}
            <br />
            iteration: {currentIteration?.iteration_id ?? '未写入'}
          </div>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {workspaceLabel && <MetaPill tone="accent">Workspace · {workspaceLabel}</MetaPill>}
        {subjectLabel && <MetaPill>Subject · {subjectLabel}</MetaPill>}
        {runContext.run_preset_label && <MetaPill tone="accent">{runContext.run_preset_label}</MetaPill>}
        {runContext.workflow_recipe_label && <MetaPill>{runContext.workflow_recipe_label}</MetaPill>}
        {runContext.evaluation_profile_label && <MetaPill>{runContext.evaluation_profile_label}</MetaPill>}
        {runContext.context_pack_labels.map((label) => (
          <MetaPill key={label}>{label}</MetaPill>
        ))}
        {!hasBindings && <MetaPill>未绑定 workflow assets 或 workspace scope</MetaPill>}
      </div>
    </Surface>
  );
}

function RewriteSummaryCard({
  diagnosis,
  appliedModules,
  artifactType,
}: {
  diagnosis: PromptDiagnosis;
  appliedModules: string[];
  artifactType: PromptArtifactType;
}) {
  const summary = buildRewriteSummary(diagnosis, appliedModules, artifactType);

  return (
    <Surface title="专家重写摘要">
      <div className="grid gap-3 text-sm md:grid-cols-2">
        <InfoBlock label="识别到的专家视角">{summary.expertLabel}</InfoBlock>
        <div className="bp-meta-card">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">本次重点补强</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {summary.highlights.map((highlight) => (
              <MetaPill key={highlight} tone="accent">{highlight}</MetaPill>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-3 rounded-[1.25rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.66)] p-4 text-sm leading-7 text-[var(--bp-ink-soft)]">
        <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">识别到的元需求</div>
        <div className="mt-2 text-[var(--bp-ink)]">{summary.metaNeed}</div>
      </div>
    </Surface>
  );
}

export function ResultPanel({
  mode,
  generateResult,
  debugResult,
  evaluateResult,
  continueResult,
  continueStreamingText = '',
  isContinueStreaming = false,
  continueStreamMeta = null,
  onCopy,
  streamingText = '',
  isStreaming = false,
  streamMeta = null,
  runContext = null,
  currentIteration = null,
}: ResultPanelProps) {
  const continueSourceLabel = continueResult ? CONTINUE_SOURCE_LABELS[continueResult.source_mode] : null;
  const emptyStateTitle = mode === 'generate'
    ? '生成结果会显示在这里'
    : mode === 'debug'
      ? '调试诊断会显示在这里'
      : '评估结果会显示在这里';
  const emptyStateDescription = mode === 'generate'
    ? '先描述真实业务目标。Generate 默认会返回可直接发送给目标模型的最终 Prompt。'
    : mode === 'debug'
      ? '补充任务、当前 Prompt 和当前输出后，这里会展示问题诊断与修复版本。'
      : '粘贴 Prompt 或输出后，这里会显示评分拆解、主要问题和建议修复方向。';
  const emptyStateHighlights = mode === 'generate'
    ? ['诊断摘要', '成品 Prompt', '继续优化动作']
    : mode === 'debug'
      ? ['失败模式', '修复后 Prompt', '下一轮补强方向']
      : ['评分拆解', '主要缺陷', '建议修复层'];

  const continueStreamingCard = isContinueStreaming && continueStreamMeta ? (
    <Surface
      title={continueStreamMeta.result_label}
      subtitle={`正在基于「${continueStreamMeta.optimization_goal}」持续生成新版本，完成后会自动切到优化结果。`}
      action={<MetaPill>Continue · {CONTINUE_SOURCE_LABELS[continueStreamMeta.source_mode]}</MetaPill>}
    >
      <div className="rounded-[1.45rem] border border-[var(--bp-line)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(249,243,235,0.96))] p-5 text-sm leading-8 whitespace-pre-wrap text-[var(--bp-ink)]">
        {continueStreamingText || '正在等待模型返回首个文本片段...'}
        {continueStreamingText && <span className="pulse-live ml-1 inline-block h-4 w-0.5 bg-[var(--bp-clay)] align-text-bottom" />}
      </div>
    </Surface>
  ) : null;

  if (mode === 'generate' && isStreaming && streamingText) {
    return (
      <div className="space-y-4">
        {streamMeta?.diagnosis && (
          <RewriteSummaryCard
            diagnosis={streamMeta.diagnosis}
            appliedModules={streamMeta.applied_modules}
            artifactType={streamMeta.artifact_type}
          />
        )}
        {streamMeta?.diagnosis_visible && streamMeta?.diagnosis && (
          <DiagnosisCard diagnosis={streamMeta.diagnosis} />
        )}
        <Surface
          title={ARTIFACT_RESULT_TITLES[streamMeta?.artifact_type ?? 'task_prompt'] ?? '生成中...'}
          subtitle={ARTIFACT_NEXT_STEP_HINTS[streamMeta?.artifact_type ?? 'task_prompt'] ?? '生成完成后可直接复制使用。'}
        >
          {streamMeta && (
            <div className="mb-4 flex flex-wrap gap-2">
              <MetaPill>{ARTIFACT_TYPE_LABELS[streamMeta.artifact_type] ?? 'Prompt'}</MetaPill>
            </div>
          )}
          <div className="rounded-[1.45rem] border border-[var(--bp-line)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(249,243,235,0.96))] p-5 text-sm leading-8 whitespace-pre-wrap text-[var(--bp-ink)]">
            {streamingText}
            <span className="pulse-live ml-1 inline-block h-4 w-0.5 bg-[var(--bp-clay)] align-text-bottom" />
          </div>
        </Surface>
      </div>
    );
  }

  if (mode === 'generate' && isStreaming && !streamingText) {
    return (
      <Surface title="正在分析并生成">
        <div className="flex items-center justify-center gap-3 py-12 text-sm text-[var(--bp-ink-soft)]">
          <Loader2 className="h-5 w-5 animate-spin text-[var(--bp-clay)]" />
          正在分析任务并生成最终 Prompt...
        </div>
      </Surface>
    );
  }

  if (continueResult) {
    const continueTitle = continueResult.source_mode === 'generate'
      ? `${ARTIFACT_RESULT_TITLES[generateResult?.artifact_type ?? 'task_prompt'] ?? '最终执行 Prompt'} · 优化后版本`
      : continueResult.source_mode === 'debug'
        ? '修复后 Prompt · 优化后版本'
        : '优化后版本';

    return (
      <div className="space-y-4">
        {runContext && <ProvenanceCard runContext={runContext} currentIteration={currentIteration} />}
        {continueResult.source_mode === 'generate' && generateResult?.diagnosis && (
          <RewriteSummaryCard
            diagnosis={generateResult.diagnosis}
            appliedModules={generateResult.applied_modules}
            artifactType={generateResult.artifact_type}
          />
        )}
        {continueResult.source_mode === 'generate' && generateResult?.diagnosis_visible && generateResult.diagnosis && (
          <DiagnosisCard diagnosis={generateResult.diagnosis} />
        )}
        <Surface title="继续优化结果">
          <div className="grid gap-3 text-sm md:grid-cols-[minmax(0,1fr)_220px]">
            <InfoBlock label="结果关系">
              <>
                基础结果来源：{continueSourceLabel}
                <br />
                本轮优化目标：{continueResult.optimization_goal}
              </>
            </InfoBlock>
            <div className="bp-meta-card">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">当前显示内容</div>
              <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{continueResult.result_label}</div>
              <div className="mt-3 inline-flex">
                <MetaPill>
                  {continueResult.generation_backend === 'llm'
                    ? `LLM${continueResult.generation_model ? ` · ${continueResult.generation_model}` : ''}`
                    : '模板回退'}
                </MetaPill>
              </div>
              <div className="mt-3 text-sm leading-6 text-[var(--bp-ink-soft)]">
                {CONTINUE_SOURCE_HINTS[continueResult.source_mode]}
              </div>
            </div>
          </div>
        </Surface>
        <Surface
          title={continueTitle}
          action={(
            <Button
              variant="ghost"
              size="sm"
              className="rounded-full text-[var(--bp-ink-soft)] hover:bg-[rgba(255,255,255,0.8)] hover:text-[var(--bp-ink)]"
              onClick={() => onCopy(continueResult.refined_result)}
            >
              <Copy className="mr-2 h-4 w-4" />
              复制
            </Button>
          )}
        >
          <TextSurface text={continueResult.refined_result} />
        </Surface>
      </div>
    );
  }

  if (mode === 'generate' && generateResult) {
    return (
      <div className="space-y-4">
        {runContext && <ProvenanceCard runContext={runContext} currentIteration={currentIteration} />}
        {generateResult.diagnosis && (
          <RewriteSummaryCard
            diagnosis={generateResult.diagnosis}
            appliedModules={generateResult.applied_modules}
            artifactType={generateResult.artifact_type}
          />
        )}
        {generateResult.diagnosis_visible && generateResult.diagnosis && (
          <DiagnosisCard diagnosis={generateResult.diagnosis} />
        )}
        <Surface
          title={ARTIFACT_RESULT_TITLES[generateResult.artifact_type] ?? '生成结果'}
          subtitle={ARTIFACT_NEXT_STEP_HINTS[generateResult.artifact_type] ?? '复制后即可继续使用。'}
          action={(
            <Button
              variant="ghost"
              size="sm"
              className="rounded-full text-[var(--bp-ink-soft)] hover:bg-[rgba(255,255,255,0.8)] hover:text-[var(--bp-ink)]"
              onClick={() => onCopy(generateResult.final_prompt)}
            >
              <Copy className="mr-2 h-4 w-4" />
              复制
            </Button>
          )}
        >
          <div className="mb-4 flex flex-wrap gap-2">
            <MetaPill>{ARTIFACT_TYPE_LABELS[generateResult.artifact_type] ?? 'Prompt'}</MetaPill>
            <MetaPill>
              {generateResult.generation_backend === 'llm'
                ? `LLM${generateResult.generation_model ? ` · ${generateResult.generation_model}` : ''}`
                : '模板回退'}
            </MetaPill>
            {generateResult.prompt_only && <MetaPill tone="accent">仅输出 Prompt</MetaPill>}
          </div>
          <TextSurface text={generateResult.final_prompt} />
        </Surface>
        {continueStreamingCard}
      </div>
    );
  }

  if (mode === 'debug' && debugResult) {
    return (
      <div className="space-y-4">
        {runContext && <ProvenanceCard runContext={runContext} currentIteration={currentIteration} />}
        <Surface title="调试诊断">
          <div className="grid gap-3 text-sm md:grid-cols-2">
            <InfoBlock label="最高风险失败模式">{debugResult.top_failure_mode}</InfoBlock>
            <InfoBlock label="优势">{debugResult.strengths.join(' / ')}</InfoBlock>
            <InfoBlock label="弱点">{debugResult.weaknesses.join(' / ')}</InfoBlock>
            <InfoBlock label="建议补强控制层">
              {debugResult.missing_control_layers.map((layer) => FIX_LAYER_LABELS[layer] ?? layer).join(' / ') || '—'}
            </InfoBlock>
          </div>
        </Surface>
        <Surface
          title="修复后 Prompt"
          action={(
            <Button
              variant="ghost"
              size="sm"
              className="rounded-full text-[var(--bp-ink-soft)] hover:bg-[rgba(255,255,255,0.8)] hover:text-[var(--bp-ink)]"
              onClick={() => onCopy(debugResult.fixed_prompt)}
            >
              <Copy className="mr-2 h-4 w-4" />
              复制
            </Button>
          )}
        >
          <div className="mb-4">
            <InfoBlock label="最小修复动作">{debugResult.minimal_fix.join(' / ')}</InfoBlock>
          </div>
          <TextSurface text={debugResult.fixed_prompt} />
        </Surface>
        {continueStreamingCard}
      </div>
    );
  }

  if (mode === 'evaluate' && evaluateResult) {
    return (
      <div className="space-y-4">
        {runContext && <ProvenanceCard runContext={runContext} currentIteration={currentIteration} />}
        <ScoreCard scoreBreakdown={evaluateResult.score_breakdown} totalScore={evaluateResult.total_score} />
        <Surface title="评估建议">
          <div className="space-y-3 text-sm">
            <InfoBlock label="最主要缺陷">{evaluateResult.top_issue}</InfoBlock>
            <InfoBlock label="建议优先修复层">
              {FIX_LAYER_LABELS[evaluateResult.suggested_fix_layer] ?? evaluateResult.suggested_fix_layer}
            </InfoBlock>
            {evaluateResult.total_interpretation && (
              <InfoBlock label="总分解读">{evaluateResult.total_interpretation}</InfoBlock>
            )}
            <div className="rounded-[1.2rem] border border-[rgba(162,74,53,0.18)] bg-[rgba(162,74,53,0.1)] p-4 text-sm leading-7 text-[var(--bp-clay)]">
              建议先围绕“{FIX_LAYER_LABELS[evaluateResult.suggested_fix_layer] ?? evaluateResult.suggested_fix_layer}”修一轮，再使用 Continue Optimization 继续迭代。
            </div>
          </div>
        </Surface>
        {continueStreamingCard}
      </div>
    );
  }

  if (continueStreamingCard) {
    return continueStreamingCard;
  }

  return (
    <div className="rounded-[1.7rem] border border-dashed border-[var(--bp-line-strong)] bg-[rgba(255,252,247,0.66)] p-6 shadow-[var(--bp-shadow-soft)]">
      <div className="bp-overline">Desk Standby</div>
      <div className="mt-3 text-lg font-semibold text-[var(--bp-ink)]">{emptyStateTitle}</div>
      <div className="mt-2 max-w-[42ch] text-sm leading-7 text-[var(--bp-ink-soft)]">{emptyStateDescription}</div>
      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        {emptyStateHighlights.map((item) => (
          <div key={item} className="bp-meta-card">
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Incoming</div>
            <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{item}</div>
          </div>
        ))}
      </div>
      <div className="mt-5 inline-flex rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.78)] px-3 py-1 text-xs text-[var(--bp-ink-soft)]">
        <Sparkles className="mr-2 h-4 w-4 text-[var(--bp-clay)]" />
        结果桌面会在你提交后自动填充
      </div>
    </div>
  );
}

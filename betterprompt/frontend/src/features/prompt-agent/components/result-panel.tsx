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
  system_prompt: '下一步：把这段系统提示词挂到你的代理或工作流配置里。',
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
    <Card className="rounded-[1.75rem] border-white/70 bg-white/78 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-slate-900">
          <Sparkles className="h-4 w-4 text-sky-500" />
          专家重写摘要
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-200/80 bg-slate-50/85 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">识别到的专家视角</div>
            <div className="mt-2 font-medium text-slate-900">{summary.expertLabel}</div>
          </div>
          <div className="rounded-2xl border border-slate-200/80 bg-slate-50/85 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">本次重点补强</div>
            <div className="mt-3 flex flex-wrap gap-2">
              {summary.highlights.map((highlight) => (
                <div
                  key={highlight}
                  className="rounded-full border border-sky-200/80 bg-sky-50 px-3 py-1 text-xs text-sky-900"
                >
                  {highlight}
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200/80 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] p-4 leading-6 text-slate-600">
          <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">识别到的元需求</div>
          <div className="mt-2">{summary.metaNeed}</div>
        </div>
      </CardContent>
    </Card>
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
}: ResultPanelProps) {
  const continueSourceLabel = continueResult ? CONTINUE_SOURCE_LABELS[continueResult.source_mode] : null;
  const emptyStateTitle = mode === 'generate'
    ? '生成结果会显示在这里'
    : mode === 'debug'
      ? '调试诊断会显示在这里'
      : '评估结果会显示在这里';
  const emptyStateDescription = mode === 'generate'
    ? '先在左侧描述真实业务目标。Generate 默认会返回可直接发送给目标模型的最终 Prompt；高级选项里才切到系统提示词或工作流。'
    : mode === 'debug'
      ? '补充任务、当前 Prompt 和当前输出后，这里会展示问题诊断与修复版本。'
      : '粘贴 Prompt 或输出后，这里会显示评分拆解、主要问题和建议修复方向。';

  const continueStreamingCard = isContinueStreaming && continueStreamMeta ? (
    <Card className="rounded-[1.75rem] border-white/70 bg-white/82 shadow-[0_22px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-slate-900">
              <Loader2 className="h-4 w-4 animate-spin text-sky-500" />
              {continueStreamMeta.result_label}
            </CardTitle>
            <div className="mt-2 text-xs leading-5 text-slate-500">
              正在基于「{continueStreamMeta.optimization_goal}」持续生成新版本，完成后会自动切到优化结果。
            </div>
          </div>
          <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
            Continue · {CONTINUE_SOURCE_LABELS[continueStreamMeta.source_mode]}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-[1.5rem] border border-slate-200/80 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] p-5 text-sm leading-7 whitespace-pre-wrap text-slate-800">
          {continueStreamingText || '正在等待模型返回首个文本片段...'}
          {continueStreamingText && <span className="inline-block h-4 w-0.5 animate-pulse bg-sky-500 align-text-bottom" />}
        </div>
      </CardContent>
    </Card>
  ) : null;

  // Streaming state: show progressive output while generating
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
        <Card className="rounded-[1.85rem] border-white/70 bg-white/82 shadow-[0_22px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-slate-900">
              <Loader2 className="h-4 w-4 animate-spin text-sky-500" />
              {ARTIFACT_RESULT_TITLES[streamMeta?.artifact_type ?? 'task_prompt'] ?? '生成中...'}
            </CardTitle>
            <div className="mt-2 text-xs leading-5 text-slate-500">
              {ARTIFACT_NEXT_STEP_HINTS[streamMeta?.artifact_type ?? 'task_prompt'] ?? '生成完成后可直接复制使用。'}
            </div>
          </CardHeader>
          <CardContent>
            {streamMeta && (
              <div className="mb-4 flex flex-wrap gap-2">
                <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
                  {ARTIFACT_TYPE_LABELS[streamMeta.artifact_type] ?? 'Prompt'}
                </div>
              </div>
            )}
            <div className="rounded-[1.5rem] border border-slate-200/80 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] p-5 text-sm leading-7 whitespace-pre-wrap text-slate-800">
              {streamingText}
              <span className="inline-block h-4 w-0.5 animate-pulse bg-sky-500 align-text-bottom" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Streaming in progress but no text yet — show a loading skeleton
  if (mode === 'generate' && isStreaming && !streamingText) {
    return (
      <Card className="rounded-[1.85rem] border-white/70 bg-white/82 shadow-[0_22px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
        <CardContent className="flex items-center justify-center py-16">
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <Loader2 className="h-5 w-5 animate-spin text-sky-500" />
            正在分析任务并生成最终 Prompt...
          </div>
        </CardContent>
      </Card>
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
        <Card className="rounded-[1.75rem] border-white/70 bg-white/75 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-900">继续优化结果</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm md:grid-cols-[minmax(0,1fr)_220px]">
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">结果关系</div>
              <div className="mt-2 leading-6 text-slate-700">
                基础结果来源：{continueSourceLabel}
                <br />
                本轮优化目标：{continueResult.optimization_goal}
              </div>
              <div className="mt-3 rounded-xl border border-sky-200/80 bg-sky-50/80 px-3 py-2 text-sm text-sky-900">
                {CONTINUE_SOURCE_HINTS[continueResult.source_mode]}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">当前显示内容</div>
              <div className="mt-2 font-medium text-slate-900">{continueResult.result_label}</div>
              <div className="mt-3 inline-flex rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600">
                {continueResult.generation_backend === 'llm'
                  ? `LLM${continueResult.generation_model ? ` · ${continueResult.generation_model}` : ''}`
                  : '模板回退'}
              </div>
              <div className="mt-2 text-sm leading-6 text-slate-500">
                如果还想继续迭代，可以直接使用下方动作按钮在当前版本上继续打磨。
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="rounded-[1.75rem] border-white/70 bg-white/75 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-slate-900">
              <Wand2 className="h-4 w-4" />{continueTitle}
            </CardTitle>
            <Button variant="ghost" size="sm" className="text-slate-600 hover:bg-slate-100 hover:text-slate-900" onClick={() => onCopy(continueResult.refined_result)}>
              <Copy className="mr-2 h-4 w-4" />复制
            </Button>
          </CardHeader>
          <CardContent>
            <div className="rounded-[1.5rem] border border-slate-200/80 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] p-5 text-sm whitespace-pre-wrap leading-7 text-slate-800">
              {continueResult.refined_result}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (mode === 'generate' && generateResult) {
    return (
      <div className="space-y-4">
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
        <Card className="rounded-[1.85rem] border-white/70 bg-white/82 shadow-[0_22px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle className="text-sm font-medium text-slate-900">
                  {ARTIFACT_RESULT_TITLES[generateResult.artifact_type] ?? '生成结果'}
                </CardTitle>
                <div className="mt-2 text-xs leading-5 text-slate-500">
                  {ARTIFACT_NEXT_STEP_HINTS[generateResult.artifact_type] ?? '复制后即可继续使用。'}
                </div>
              </div>
              <Button variant="ghost" size="sm" className="text-slate-600 hover:bg-slate-100 hover:text-slate-900" onClick={() => onCopy(generateResult.final_prompt)}>
                <Copy className="mr-2 h-4 w-4" />复制
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="mb-4 flex flex-wrap gap-2">
              <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
                {ARTIFACT_TYPE_LABELS[generateResult.artifact_type] ?? 'Prompt'}
              </div>
              <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
                {generateResult.generation_backend === 'llm'
                  ? `LLM${generateResult.generation_model ? ` · ${generateResult.generation_model}` : ''}`
                  : '模板回退'}
              </div>
              {generateResult.prompt_only && (
                <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
                  仅输出 Prompt
                </div>
              )}
            </div>
            <div className="rounded-[1.5rem] border border-slate-200/80 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] p-5 text-sm leading-7 whitespace-pre-wrap text-slate-800">
              {generateResult.final_prompt}
            </div>
          </CardContent>
        </Card>
        {continueStreamingCard}
      </div>
    );
  }

  if (mode === 'debug' && debugResult) {
    return (
      <div className="space-y-4">
        <Card className="rounded-[1.75rem] border-white/70 bg-white/75 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-900">调试诊断</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm md:grid-cols-2">
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">最高风险失败模式</div>
              <div className="mt-2 font-medium text-slate-900">{debugResult.top_failure_mode}</div>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">优势</div>
              <div className="mt-2 leading-6 text-slate-700">{debugResult.strengths.join(' / ')}</div>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">弱点</div>
              <div className="mt-2 leading-6 text-slate-700">{debugResult.weaknesses.join(' / ')}</div>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">建议补强控制层</div>
              <div className="mt-2 leading-6 text-slate-700">
                {debugResult.missing_control_layers.map((layer) => FIX_LAYER_LABELS[layer] ?? layer).join(' / ') || '—'}
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="rounded-[1.75rem] border-white/70 bg-white/75 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm font-medium text-slate-900">修复后 Prompt</CardTitle>
            <Button variant="ghost" size="sm" className="text-slate-600 hover:bg-slate-100 hover:text-slate-900" onClick={() => onCopy(debugResult.fixed_prompt)}>
              <Copy className="mr-2 h-4 w-4" />复制
            </Button>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">最小修复动作</div>
              <div className="mt-2 leading-6 text-slate-700">{debugResult.minimal_fix.join(' / ')}</div>
            </div>
            <div className="rounded-[1.5rem] border border-slate-200/80 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] p-5 whitespace-pre-wrap leading-7 text-slate-800">{debugResult.fixed_prompt}</div>
          </CardContent>
        </Card>
        {continueStreamingCard}
      </div>
    );
  }

  if (mode === 'evaluate' && evaluateResult) {
    return (
      <div className="space-y-4">
        <ScoreCard scoreBreakdown={evaluateResult.score_breakdown} totalScore={evaluateResult.total_score} />
        <Card className="rounded-[1.75rem] border-white/70 bg-white/75 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-900">评估建议</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">最主要缺陷</div>
              <div className="mt-2 font-medium text-slate-900">{evaluateResult.top_issue}</div>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">建议优先修复层</div>
              <div className="mt-2 font-medium text-slate-900">{FIX_LAYER_LABELS[evaluateResult.suggested_fix_layer] ?? evaluateResult.suggested_fix_layer}</div>
            </div>
            {evaluateResult.total_interpretation && (
              <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">总分解读</div>
                <div className="mt-2 text-sm leading-6 text-slate-700">{evaluateResult.total_interpretation}</div>
              </div>
            )}
            <div className="rounded-[1.5rem] border border-sky-200/80 bg-sky-50/80 p-4 text-slate-600">
              建议先围绕"{FIX_LAYER_LABELS[evaluateResult.suggested_fix_layer] ?? evaluateResult.suggested_fix_layer}"修一轮，再使用 Continue Optimization 继续迭代。
            </div>
          </CardContent>
        </Card>
        {continueStreamingCard}
      </div>
    );
  }

  if (continueStreamingCard) {
    return continueStreamingCard;
  }

  return (
    <div className="rounded-[1.85rem] border border-dashed border-slate-300 bg-white/65 p-10 text-center shadow-[0_20px_70px_-42px_rgba(15,23,42,0.16)] backdrop-blur-xl">
      <div className="text-sm font-medium text-slate-900">{emptyStateTitle}</div>
      <div className="mt-2 text-sm leading-6 text-slate-500">{emptyStateDescription}</div>
    </div>
  );
}

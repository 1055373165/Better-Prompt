import { useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  ArrowUpRight,
  Brain,
  ChartBar,
  Code2,
  GraduationCap,
  Languages,
  Layers3,
  Lightbulb,
  Megaphone,
  PenLine,
  Search,
  Target,
  Wand2,
} from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '@/lib/api/client';
import { ContinueActions } from './components/continue-actions';
import { DebugPanel } from './components/debug-panel';
import { EvaluatePanel } from './components/evaluate-panel';
import { GeneratePanel } from './components/generate-panel';
import { ModeSelector } from './components/mode-selector';
import { ResultPanel } from './components/result-panel';
import { WorkflowAssetsPanel } from './components/workflow-assets-panel';
import { usePromptAgentContinue } from './hooks/use-prompt-agent-continue';
import { usePromptAgentDebug } from './hooks/use-prompt-agent-debug';
import { usePromptAgentEvaluate } from './hooks/use-prompt-agent-evaluate';
import { usePromptAgentGenerateStream } from './hooks/use-prompt-agent-generate-stream';
import { useRunPresetDetail } from './hooks/use-run-preset-detail';
import { useRunPresetLaunch } from './hooks/use-run-preset-launch';
import { useWorkflowAssetCatalog } from './hooks/use-workflow-asset-catalog';
import type {
  ContinuePromptResponse,
  ContextPackSummary,
  DebugDraft,
  DebugPromptResponse,
  EvaluateDraft,
  EvaluatePromptResponse,
  EvaluationProfileSummary,
  GenerateDraft,
  GeneratePromptResponse,
  PromptAgentMode,
  RunContextSnapshot,
  RunPresetDetail,
  RunPresetLaunchResponse,
  WorkspaceScopeSelection,
  WorkflowRecipeSummary,
  WorkflowRefSelection,
} from './types';

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

const INITIAL_WORKFLOW_REFS: WorkflowRefSelection = {
  context_pack_version_ids: [],
  evaluation_profile_version_id: null,
  workflow_recipe_version_id: null,
  run_preset_id: null,
};

const INITIAL_WORKSPACE_SCOPE: WorkspaceScopeSelection = {
  domain_workspace_id: null,
  subject_id: null,
  domain_workspace_label: null,
  subject_label: null,
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

const DOMAIN_CHIPS = [
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
];

const WORKBENCH_PRINCIPLES = [
  {
    icon: Layers3,
    title: '单一工作台',
    description: '输入、判断、结果和继续优化都在同一张桌面上完成，不需要在聊天流里捞信息。',
  },
  {
    icon: Wand2,
    title: '模式由你决定',
    description: 'Generate、Debug、Evaluate 明确分流，系统不再替你擅自切模式。',
  },
  {
    icon: ArrowUpRight,
    title: '结果永远是主角',
    description: '右侧结果桌面固定承接成品、评分和继续优化，让下一步动作始终可见。',
  },
];

const MODE_CANVAS_COPY: Record<
  PromptAgentMode,
  {
    badge: string;
    title: string;
    description: string;
    resultEyebrow: string;
    resultDescription: string;
    firstStep: string;
    secondStep: string;
  }
> = {
  generate: {
    badge: 'Rewrite Flow',
    title: '从模糊需求到可直接发送的 Prompt',
    description: '先写清你真正要解决的业务意图，再让系统把它编译成更清晰、更有判断力的成品 Prompt。',
    resultEyebrow: 'Result Desk',
    resultDescription: '生成中的文本会实时落在这里；完成后可以直接复制，或者继续在当前版本上打磨。',
    firstStep: '写下真实目标',
    secondStep: '查看并继续优化成品 Prompt',
  },
  debug: {
    badge: 'Repair Flow',
    title: '定位 Prompt 失效点，再给出修复版',
    description: '把任务、当前 Prompt 和输出一并摊开，系统会判断最可能的失败模式，并给你一版更稳定的修复结果。',
    resultEyebrow: 'Repair Desk',
    resultDescription: '这里集中展示问题诊断、修复后 Prompt 和继续优化生成结果，方便一眼比对前后差异。',
    firstStep: '交代任务与失败现象',
    secondStep: '查看诊断并拿走修复版',
  },
  evaluate: {
    badge: 'Score Flow',
    title: '先判断质量，再决定下一轮该怎么改',
    description: '把 Prompt 或输出贴进来，系统会给出评分、主要缺陷和优先修复层，帮你停止凭感觉迭代。',
    resultEyebrow: 'Review Desk',
    resultDescription: '分数、解释、重点缺陷和优化结果都会集中放在结果桌面，下一步该修什么会更清楚。',
    firstStep: '贴入待评估内容',
    secondStep: '根据分数继续重写',
  },
};

type WorkflowCatalogData = {
  contextPacks: ContextPackSummary[];
  evaluationProfiles: EvaluationProfileSummary[];
  workflowRecipes: WorkflowRecipeSummary[];
};

function hasWorkflowBindings(refs: WorkflowRefSelection): boolean {
  return Boolean(
    refs.workflow_recipe_version_id
      || refs.evaluation_profile_version_id
      || refs.context_pack_version_ids.length
      || refs.run_preset_id,
  );
}

function asString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0);
}

function findWorkflowRecipeLabel(catalog: WorkflowCatalogData | undefined, versionId: string | null): string | null {
  if (!catalog || !versionId) {
    return null;
  }
  for (const item of catalog.workflowRecipes) {
    if (item.current_version?.id === versionId) {
      return `${item.name} · v${item.current_version.version_number}`;
    }
  }
  return null;
}

function findEvaluationProfileLabel(catalog: WorkflowCatalogData | undefined, versionId: string | null): string | null {
  if (!catalog || !versionId) {
    return null;
  }
  for (const item of catalog.evaluationProfiles) {
    if (item.current_version?.id === versionId) {
      return `${item.name} · v${item.current_version.version_number}`;
    }
  }
  return null;
}

function findContextPackLabels(catalog: WorkflowCatalogData | undefined, versionIds: string[]): string[] {
  if (!catalog || versionIds.length === 0) {
    return [];
  }
  const labels: string[] = [];
  for (const versionId of versionIds) {
    const matched = catalog.contextPacks.find((item) => item.current_version?.id === versionId);
    if (matched?.current_version) {
      labels.push(`${matched.name} · v${matched.current_version.version_number}`);
    }
  }
  return labels;
}

function buildRunContextSnapshot(
  refs: WorkflowRefSelection,
  workspaceScope: WorkspaceScopeSelection,
  catalog: WorkflowCatalogData | undefined,
  launchLabel: string,
  runPreset: RunPresetDetail | null = null,
): RunContextSnapshot {
  return {
    launch_label: launchLabel,
    refs,
    workspace_scope: workspaceScope.domain_workspace_id || workspaceScope.subject_id
      ? workspaceScope
      : null,
    workflow_recipe_label: findWorkflowRecipeLabel(catalog, refs.workflow_recipe_version_id),
    evaluation_profile_label: findEvaluationProfileLabel(catalog, refs.evaluation_profile_version_id),
    context_pack_labels: findContextPackLabels(catalog, refs.context_pack_version_ids),
    run_preset_label: runPreset ? `Preset · ${runPreset.name}` : null,
  };
}

function buildDirectRunContext(
  refs: WorkflowRefSelection,
  workspaceScope: WorkspaceScopeSelection,
  catalog: WorkflowCatalogData | undefined,
): RunContextSnapshot {
  return buildRunContextSnapshot(
    refs,
    workspaceScope,
    catalog,
    hasWorkflowBindings(refs) ? 'Workbench Direct Run · Workflow Assets' : 'Workbench Direct Run',
  );
}

function buildPresetRunContext(
  runPreset: RunPresetDetail,
  workspaceScope: WorkspaceScopeSelection,
  catalog: WorkflowCatalogData | undefined,
  launchLabel: string,
): RunContextSnapshot {
  return buildRunContextSnapshot(
    {
      context_pack_version_ids: asStringArray(runPreset.definition.context_pack_version_ids),
      evaluation_profile_version_id: asString(runPreset.definition.evaluation_profile_version_id),
      workflow_recipe_version_id: asString(runPreset.definition.workflow_recipe_version_id),
      run_preset_id: runPreset.id,
    },
    workspaceScope,
    catalog,
    launchLabel,
    runPreset,
  );
}

function buildContinueRunContext(runContext: RunContextSnapshot | null): RunContextSnapshot | null {
  if (!runContext) {
    return null;
  }
  return {
    ...runContext,
    launch_label: `Continue Optimization · ${runContext.launch_label}`,
  };
}

function getLaunchOverridePreview(
  mode: PromptAgentMode,
  generateDraft: GenerateDraft,
  debugDraft: DebugDraft,
  evaluateDraft: EvaluateDraft,
): string | null {
  if (mode === 'generate') {
    return generateDraft.userInput.trim() || null;
  }
  if (mode === 'debug') {
    return debugDraft.originalTask.trim() || null;
  }
  return evaluateDraft.targetText.trim() || null;
}

function getLaunchResponseMode(response: RunPresetLaunchResponse): PromptAgentMode {
  return response.mode === 'continue' ? response.source_mode : response.mode;
}

function buildRunPresetDefinition(
  mode: PromptAgentMode,
  workflowRefs: WorkflowRefSelection,
  generateDraft: GenerateDraft,
  debugDraft: DebugDraft,
  evaluateDraft: EvaluateDraft,
): Record<string, unknown> {
  const definition: Record<string, unknown> = {
    mode,
    context_pack_version_ids: workflowRefs.context_pack_version_ids,
    run_settings: {},
  };
  if (workflowRefs.evaluation_profile_version_id) {
    definition.evaluation_profile_version_id = workflowRefs.evaluation_profile_version_id;
  }
  if (workflowRefs.workflow_recipe_version_id) {
    definition.workflow_recipe_version_id = workflowRefs.workflow_recipe_version_id;
  }

  const runSettings = definition.run_settings as Record<string, unknown>;

  if (mode === 'generate') {
    const userInput = generateDraft.userInput.trim();
    if (!userInput) {
      throw new Error('保存 Generate preset 前，先填写当前要生成的用户输入。');
    }
    runSettings.user_input = userInput;
    runSettings.show_diagnosis = generateDraft.showDiagnosis;
    runSettings.output_preference = generateDraft.outputPreference;
    runSettings.artifact_type = generateDraft.artifactType;
    runSettings.prompt_only = generateDraft.promptOnly;
    return definition;
  }

  if (mode === 'debug') {
    const originalTask = debugDraft.originalTask.trim();
    const currentPrompt = debugDraft.currentPrompt.trim();
    const currentOutput = debugDraft.currentOutput.trim();
    if (!originalTask || !currentPrompt || !currentOutput) {
      throw new Error('保存 Debug preset 前，需要先填完 original task、current prompt 和 current output。');
    }
    runSettings.original_task = originalTask;
    runSettings.current_prompt = currentPrompt;
    runSettings.current_output = currentOutput;
    runSettings.output_preference = 'balanced';
    return definition;
  }

  const targetText = evaluateDraft.targetText.trim();
  if (!targetText) {
    throw new Error('保存 Evaluate preset 前，先填写当前待评估内容。');
  }
  runSettings.target_text = targetText;
  runSettings.target_type = evaluateDraft.targetType;
  return definition;
}

export default function PromptAgentPage() {
  const [searchParams] = useSearchParams();
  const [mode, setMode] = useState<PromptAgentMode>('generate');
  const [copied, setCopied] = useState(false);
  const [showWorkflowAssets, setShowWorkflowAssets] = useState(false);
  const [generateDraft, setGenerateDraft] = useState<GenerateDraft>(INITIAL_GENERATE_DRAFT);
  const [debugDraft, setDebugDraft] = useState<DebugDraft>(INITIAL_DEBUG_DRAFT);
  const [evaluateDraft, setEvaluateDraft] = useState<EvaluateDraft>(INITIAL_EVALUATE_DRAFT);
  const [workflowRefs, setWorkflowRefs] = useState<WorkflowRefSelection>(INITIAL_WORKFLOW_REFS);
  const [workspaceScope, setWorkspaceScope] = useState<WorkspaceScopeSelection>(INITIAL_WORKSPACE_SCOPE);
  const [selectedRunPresetId, setSelectedRunPresetId] = useState<string | null>(null);
  const [savePresetDraft, setSavePresetDraft] = useState({ name: '', description: '' });
  const [savePresetError, setSavePresetError] = useState<string | null>(null);
  const [generateRunContext, setGenerateRunContext] = useState<RunContextSnapshot | null>(null);
  const [debugRunContext, setDebugRunContext] = useState<RunContextSnapshot | null>(null);
  const [evaluateRunContext, setEvaluateRunContext] = useState<RunContextSnapshot | null>(null);
  const [continueRunContext, setContinueRunContext] = useState<RunContextSnapshot | null>(null);
  const [manualGenerateResult, setManualGenerateResult] = useState<GeneratePromptResponse | null>(null);
  const [manualDebugResult, setManualDebugResult] = useState<DebugPromptResponse | null>(null);
  const [manualEvaluateResult, setManualEvaluateResult] = useState<EvaluatePromptResponse | null>(null);
  const [manualContinueResult, setManualContinueResult] = useState<ContinuePromptResponse | null>(null);

  const workflowCatalogQuery = useWorkflowAssetCatalog();
  const selectedRunPresetQuery = useRunPresetDetail(selectedRunPresetId);
  const launchPresetMutation = useRunPresetLaunch();
  const savePresetMutation = useMutation({
    mutationFn: async () => {
      setSavePresetError(null);
      if (!savePresetDraft.name.trim()) {
        throw new Error('请输入 preset 名称。');
      }
      const definition = buildRunPresetDefinition(mode, workflowRefs, generateDraft, debugDraft, evaluateDraft);
      const { data } = await api.post<RunPresetDetail>('/run-presets', {
        name: savePresetDraft.name.trim(),
        description: savePresetDraft.description.trim() || null,
        definition,
      });
      return data;
    },
    onSuccess: async (data) => {
      await workflowCatalogQuery.refetch();
      setSelectedRunPresetId(data.id);
      setSavePresetDraft({ name: '', description: '' });
      setSavePresetError(null);
    },
    onError: (error) => {
      setSavePresetError(error instanceof Error ? error.message : '保存 run preset 失败。');
    },
  });
  const generateMutation = usePromptAgentGenerateStream();
  const debugMutation = usePromptAgentDebug();
  const evaluateMutation = usePromptAgentEvaluate();
  const continueMutation = usePromptAgentContinue();

  useEffect(() => {
    continueMutation.reset();
  }, [mode]);

  useEffect(() => {
    const requestedMode = searchParams.get('mode');
    if (requestedMode === 'generate' || requestedMode === 'debug' || requestedMode === 'evaluate') {
      setMode(requestedMode);
    }

    const requestedPresetId = searchParams.get('preset');
    if (requestedPresetId) {
      setSelectedRunPresetId(requestedPresetId);
      setShowWorkflowAssets(true);
    }

    setWorkspaceScope({
      domain_workspace_id: searchParams.get('workspace_id'),
      subject_id: searchParams.get('subject_id'),
      domain_workspace_label: searchParams.get('workspace_name'),
      subject_label: searchParams.get('subject_name'),
    });
  }, [searchParams]);

  useEffect(() => {
    if (
      hasWorkflowBindings(workflowRefs)
      || Boolean(selectedRunPresetId)
      || Boolean(workflowCatalogQuery.error)
    ) {
      setShowWorkflowAssets(true);
    }
  }, [selectedRunPresetId, workflowCatalogQuery.error, workflowRefs]);

  const workflowCatalogData = workflowCatalogQuery.data;
  const selectedRunPreset = selectedRunPresetQuery.data ?? null;

  useEffect(() => {
    if (!selectedRunPreset) {
      setWorkflowRefs((current) => (
        current.run_preset_id
          ? { ...current, run_preset_id: null }
          : current
      ));
      return;
    }

    setWorkflowRefs({
      context_pack_version_ids: asStringArray(selectedRunPreset.definition.context_pack_version_ids),
      evaluation_profile_version_id: asString(selectedRunPreset.definition.evaluation_profile_version_id),
      workflow_recipe_version_id: asString(selectedRunPreset.definition.workflow_recipe_version_id),
      run_preset_id: selectedRunPreset.id,
    });
  }, [selectedRunPreset]);

  const displayGenerateResult = manualGenerateResult ?? generateMutation.data ?? null;
  const displayDebugResult = manualDebugResult ?? debugMutation.data ?? null;
  const displayEvaluateResult = manualEvaluateResult ?? evaluateMutation.data ?? null;
  const directContinueResult = continueMutation.data?.source_mode === mode ? continueMutation.data : null;
  const activeContinueResult = manualContinueResult?.source_mode === mode
    ? manualContinueResult
    : directContinueResult;
  const activeContinueStreamMeta = manualContinueResult ? null : (continueMutation.meta?.source_mode === mode ? continueMutation.meta : null);
  const activeContinueStreamingText = manualContinueResult ? '' : (continueMutation.variables?.mode === mode ? continueMutation.streamingText : '');
  const baseResultByMode: Record<PromptAgentMode, GeneratePromptResponse | DebugPromptResponse | EvaluatePromptResponse | null> = {
    generate: displayGenerateResult,
    debug: displayDebugResult,
    evaluate: displayEvaluateResult,
  };
  const activeBaseResult = baseResultByMode[mode];
  const baseRunContextByMode: Record<PromptAgentMode, RunContextSnapshot | null> = {
    generate: generateRunContext,
    debug: debugRunContext,
    evaluate: evaluateRunContext,
  };
  const activeRunContext = activeContinueResult ? continueRunContext : baseRunContextByMode[mode];
  const activeIteration = activeContinueResult?.iteration ?? activeBaseResult?.iteration ?? null;
  const baseResultTextByMode: Record<PromptAgentMode, string> = {
    generate: displayGenerateResult?.final_prompt || '',
    debug: displayDebugResult?.fixed_prompt || '',
    evaluate: displayEvaluateResult?.top_issue || '',
  };
  const continueSourceTextByMode: Record<PromptAgentMode, string> = {
    generate: displayGenerateResult?.final_prompt || '',
    debug: displayDebugResult?.fixed_prompt || '',
    evaluate: evaluateMutation.variables?.target_text || evaluateDraft.targetText.trim(),
  };
  const activeBaseResultText = baseResultTextByMode[mode];
  const hasBaseResult = Boolean(activeBaseResultText || activeContinueResult);
  const latestActions = activeContinueResult?.suggested_next_actions ?? (hasBaseResult ? DEFAULT_CONTINUE_ACTIONS[mode] : []);
  const currentContinueSourceText = activeContinueResult?.refined_result || continueSourceTextByMode[mode];
  const continueContextNotesByMode: Record<PromptAgentMode, string | undefined> = {
    generate: undefined,
    debug: displayDebugResult
      ? [
        debugMutation.variables?.original_task || debugDraft.originalTask.trim()
          ? `原始任务：${debugMutation.variables?.original_task || debugDraft.originalTask.trim()}`
          : '',
        `最高风险失败模式：${displayDebugResult.top_failure_mode}`,
        displayDebugResult.weaknesses.length ? `当前弱点：${displayDebugResult.weaknesses.join(' / ')}` : '',
        displayDebugResult.missing_control_layers.length
          ? `建议补强控制层：${displayDebugResult.missing_control_layers.map((layer) => FIX_LAYER_LABELS[layer] ?? layer).join(' / ')}`
          : '',
      ].filter(Boolean).join('\n')
      : undefined,
    evaluate: displayEvaluateResult
      ? [
        `当前评估对象：${(evaluateMutation.variables?.target_type || evaluateDraft.targetType) === 'prompt' ? 'Prompt' : '输出内容'}`,
        `最主要缺陷：${displayEvaluateResult.top_issue}`,
        `建议优先修复层：${FIX_LAYER_LABELS[displayEvaluateResult.suggested_fix_layer] ?? displayEvaluateResult.suggested_fix_layer}`,
        `总分：${displayEvaluateResult.total_score}/35`,
        displayEvaluateResult.total_interpretation ? `总分解读：${displayEvaluateResult.total_interpretation}` : '',
      ].filter(Boolean).join('\n')
      : undefined,
  };
  const pendingContinueGoal = continueMutation.isPending && continueMutation.variables?.mode === mode
    ? continueMutation.variables.optimization_goal
    : null;
  const currentContinueError = continueMutation.variables?.mode === mode ? continueMutation.error : null;
  const launchOverridePreview = getLaunchOverridePreview(mode, generateDraft, debugDraft, evaluateDraft);
  const workspaceFocusHref = (() => {
    if (!workspaceScope.domain_workspace_id && !workspaceScope.subject_id) {
      return null;
    }
    const params = new URLSearchParams();
    if (workspaceScope.domain_workspace_id) {
      params.set('workspace_id', workspaceScope.domain_workspace_id);
    }
    if (workspaceScope.subject_id) {
      params.set('subject_id', workspaceScope.subject_id);
    }
    return `/workspaces?${params.toString()}`;
  })();

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
        : evaluateMutation.error) || currentContinueError || launchPresetMutation.error;

  const activeModeCopy = MODE_CANVAS_COPY[mode];

  const clearManualResultForMode = (targetMode: PromptAgentMode) => {
    if (targetMode === 'generate') {
      setManualGenerateResult(null);
      return;
    }
    if (targetMode === 'debug') {
      setManualDebugResult(null);
      return;
    }
    setManualEvaluateResult(null);
  };

  const resultStack = (
    <div className="space-y-4">
      {currentError && (
        <div className="rounded-[1.5rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700 shadow-[0_18px_42px_-32px_rgba(220,38,38,0.38)]">
          {currentError instanceof Error ? currentError.message : '请求失败，请稍后重试'}
        </div>
      )}
      <ResultPanel
        mode={mode}
        generateResult={displayGenerateResult}
        debugResult={displayDebugResult}
        evaluateResult={displayEvaluateResult}
        continueResult={activeContinueResult}
        continueStreamingText={activeContinueStreamingText}
        isContinueStreaming={continueMutation.isStreaming && continueMutation.variables?.mode === mode}
        continueStreamMeta={activeContinueStreamMeta}
        onCopy={handleCopy}
        streamingText={generateMutation.streamingText}
        isStreaming={generateMutation.isStreaming}
        streamMeta={generateMutation.meta}
        runContext={activeRunContext}
        currentIteration={activeIteration}
      />
      <ContinueActions
        actions={latestActions}
        isLoading={continueMutation.isPending}
        activeGoal={pendingContinueGoal}
        completedGoal={activeContinueResult?.optimization_goal ?? null}
        resultLabel={activeContinueResult?.result_label ?? null}
        onSelect={(goal) => {
          if (!currentContinueSourceText) return;
          const nextRunContext = buildContinueRunContext(activeRunContext);
          setManualContinueResult(null);
          setContinueRunContext(nextRunContext);
          continueMutation.mutate({
            previous_result: currentContinueSourceText,
            optimization_goal: goal,
            mode,
            context_notes: continueContextNotesByMode[mode],
            session_id: activeIteration?.session_id ?? undefined,
            parent_iteration_id: activeIteration?.iteration_id ?? undefined,
            domain_workspace_id: activeRunContext?.workspace_scope?.domain_workspace_id ?? workspaceScope.domain_workspace_id ?? undefined,
            subject_id: activeRunContext?.workspace_scope?.subject_id ?? workspaceScope.subject_id ?? undefined,
            context_pack_version_ids: activeRunContext?.refs.context_pack_version_ids ?? [],
            evaluation_profile_version_id: activeRunContext?.refs.evaluation_profile_version_id ?? undefined,
            workflow_recipe_version_id: activeRunContext?.refs.workflow_recipe_version_id ?? undefined,
            run_preset_id: activeRunContext?.refs.run_preset_id ?? undefined,
          });
        }}
      />
      {copied && (
        <div className="rounded-[1.5rem] border border-emerald-200/80 bg-emerald-50/90 px-4 py-3 text-sm text-emerald-700 shadow-[0_18px_42px_-32px_rgba(16,185,129,0.34)]">
          已复制到剪贴板
        </div>
      )}
    </div>
  );

  return (
    <div className="bp-shell pb-10 pt-3 md:pt-6">
      <section className="bp-surface bp-fade-up overflow-hidden px-5 py-6 md:px-8 md:py-8">
        <div className="grid gap-8 xl:grid-cols-[minmax(0,1.08fr)_360px]">
          <div>
            <div className="bp-overline">BetterPrompt / Prompt Agent</div>
            <h1 className="bp-display mt-4 max-w-4xl text-[var(--bp-ink)]">
              把半成型需求，
              <br />
              写成能开工的 Prompt。
            </h1>
            <p className="bp-subtitle mt-5 max-w-3xl text-[1.02rem]">
              这不是一个聊天窗口，而是一张 prompt workbench。你先说清想让模型替你完成什么，系统再负责把任务结构化、重写、修复或评估，最后交付一个真正能用于工作的结果。
            </p>

            <div className="mt-6 flex flex-wrap gap-2">
              {DOMAIN_CHIPS.map(({ icon: Icon, label }) => (
                <div key={label} className="bp-chip">
                  <Icon className="h-3.5 w-3.5" />
                  {label}
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-4">
            <div className="bp-surface-soft px-5 py-5">
              <div className="bp-overline">{activeModeCopy.badge}</div>
              <h2 className="bp-title mt-3 text-[2rem]">{activeModeCopy.title}</h2>
              <p className="mt-3 text-sm leading-7 text-[var(--bp-ink-soft)]">
                {activeModeCopy.description}
              </p>
            </div>

            <div className="bp-surface-soft px-5 py-5">
              <div className="bp-overline">Why It Feels Different</div>
              <div className="mt-4 space-y-4">
                {WORKBENCH_PRINCIPLES.map(({ icon: Icon, title, description }) => (
                  <div key={title} className="flex gap-3">
                    <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] text-[var(--bp-clay)]">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-[var(--bp-ink)]">{title}</div>
                      <div className="mt-1 text-sm leading-6 text-[var(--bp-ink-soft)]">{description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bp-surface mt-6 px-5 py-6 md:px-7">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-end">
          <div>
            <div className="bp-overline">Workflow Mode</div>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[var(--bp-ink)]">先选工作流，再进入专注输入</h2>
            <p className="mt-2 max-w-3xl text-sm leading-7 text-[var(--bp-ink-soft)]">
              Generate 负责把需求改写成成品 Prompt，Debug 负责修复失效结构，Evaluate 负责判断质量和下一轮优先动作。
            </p>
            <div className="mt-5">
              <ModeSelector value={mode} onChange={setMode} />
            </div>
          </div>

          <div className="bp-surface-soft px-5 py-5">
            <div className="bp-overline">Current Flow</div>
            <div className="mt-4 space-y-3">
              <div className="bp-meta-card">
                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Step 1</div>
                <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{activeModeCopy.firstStep}</div>
              </div>
              <div className="bp-meta-card">
                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Step 2</div>
                <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{activeModeCopy.secondStep}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-6 grid items-start gap-6 xl:grid-cols-[minmax(0,1.04fr)_minmax(360px,0.82fr)]">
        <div className="space-y-6">
          {(workspaceScope.domain_workspace_id || workspaceScope.subject_id) && (
            <section className="bp-surface px-5 py-5 md:px-6">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <div className="bp-overline">Workspace Focus</div>
                  <h2 className="mt-3 text-xl font-semibold tracking-tight text-[var(--bp-ink)]">当前运行绑定了 V3 workspace scope</h2>
                  <p className="mt-2 max-w-3xl text-sm leading-7 text-[var(--bp-ink-soft)]">
                    接下来的 Generate / Debug / Evaluate / Continue 以及 preset launch，都会把当前 workspace 与 subject refs 一起写入 session provenance。
                  </p>
                </div>
                {workspaceFocusHref && (
                  <Link
                    to={workspaceFocusHref}
                    className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                  >
                    返回 Workspace
                    <ArrowUpRight className="h-4 w-4" />
                  </Link>
                )}
              </div>

              <div className="mt-5 flex flex-wrap gap-3">
                <div className="bp-meta-card min-w-[220px]">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Domain Workspace</div>
                  <div className="mt-2 break-all text-sm leading-6 text-[var(--bp-ink)]">
                    {workspaceScope.domain_workspace_label || workspaceScope.domain_workspace_id || '—'}
                  </div>
                </div>
                <div className="bp-meta-card min-w-[220px]">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Subject</div>
                  <div className="mt-2 break-all text-sm leading-6 text-[var(--bp-ink)]">
                    {workspaceScope.subject_label || workspaceScope.subject_id || '—'}
                  </div>
                </div>
              </div>
            </section>
          )}

          <WorkflowAssetsPanel
            mode={mode}
            contextPacks={workflowCatalogData?.contextPacks ?? []}
            evaluationProfiles={workflowCatalogData?.evaluationProfiles ?? []}
            workflowRecipes={workflowCatalogData?.workflowRecipes ?? []}
            runPresets={workflowCatalogQuery.data?.runPresets ?? []}
            selectedContextPackVersionIds={workflowRefs.context_pack_version_ids}
            selectedEvaluationProfileVersionId={workflowRefs.evaluation_profile_version_id}
            selectedWorkflowRecipeVersionId={workflowRefs.workflow_recipe_version_id}
            selectedRunPresetId={selectedRunPresetId}
            selectedRunPreset={selectedRunPreset}
            launchOverridePreview={launchOverridePreview}
            savePresetName={savePresetDraft.name}
            savePresetDescription={savePresetDraft.description}
            savePresetError={savePresetError}
            isCatalogLoading={workflowCatalogQuery.isLoading}
            catalogError={workflowCatalogQuery.error instanceof Error ? workflowCatalogQuery.error.message : null}
            isPresetLoading={selectedRunPresetQuery.isLoading}
            isPresetLaunching={launchPresetMutation.isPending}
            isSavingPreset={savePresetMutation.isPending}
            collapsed={!showWorkflowAssets}
            onToggleCollapsed={() => setShowWorkflowAssets((current) => !current)}
            onToggleContextPack={(versionId) => {
              setWorkflowRefs((current) => {
                const exists = current.context_pack_version_ids.includes(versionId);
                return {
                  ...current,
                  context_pack_version_ids: exists
                    ? current.context_pack_version_ids.filter((item) => item !== versionId)
                    : [...current.context_pack_version_ids, versionId],
                };
              });
            }}
            onSelectEvaluationProfile={(versionId) => {
              setWorkflowRefs((current) => ({
                ...current,
                evaluation_profile_version_id: versionId,
              }));
            }}
            onSelectWorkflowRecipe={(versionId) => {
              setWorkflowRefs((current) => ({
                ...current,
                workflow_recipe_version_id: versionId,
              }));
            }}
            onSelectRunPreset={setSelectedRunPresetId}
            onChangeSavePreset={(patch) => {
              setSavePresetDraft((current) => ({ ...current, ...patch }));
            }}
            onLaunchPreset={(modeBehavior) => {
              if (!selectedRunPreset) return;
              continueMutation.reset();
              setManualContinueResult(null);
              setContinueRunContext(null);
              const launchModeLabel = modeBehavior === 'current'
                ? `Run Preset · 当前工作流 ${mode.toUpperCase()}`
                : 'Run Preset · Preset Default Mode';
              const nextRunContext = buildPresetRunContext(selectedRunPreset, workspaceScope, workflowCatalogData, launchModeLabel);
              launchPresetMutation.mutate({
                runPresetId: selectedRunPreset.id,
                payload: {
                  session_id: activeIteration?.session_id ?? undefined,
                  parent_iteration_id: activeIteration?.iteration_id ?? undefined,
                  domain_workspace_id: workspaceScope.domain_workspace_id ?? undefined,
                  subject_id: workspaceScope.subject_id ?? undefined,
                  mode_override: modeBehavior === 'current' ? mode : undefined,
                  user_input_override: launchOverridePreview || undefined,
                },
              }, {
                onSuccess: (response) => {
                  const nextMode = getLaunchResponseMode(response);
                  if (response.mode === 'generate') {
                    setManualGenerateResult(response);
                    setGenerateRunContext(nextRunContext);
                  } else if (response.mode === 'debug') {
                    setManualDebugResult(response);
                    setDebugRunContext(nextRunContext);
                  } else if (response.mode === 'evaluate') {
                    setManualEvaluateResult(response);
                    setEvaluateRunContext(nextRunContext);
                  } else {
                    continueMutation.reset();
                    setManualContinueResult(response);
                    setContinueRunContext(buildContinueRunContext(nextRunContext));
                  }
                  setMode(nextMode);
                },
              });
            }}
            onSaveCurrentAsPreset={() => {
              savePresetMutation.mutate();
            }}
          />

          {mode === 'generate' && (
            <GeneratePanel
              draft={generateDraft}
              onChange={(patch) => {
                setGenerateDraft((current) => ({ ...current, ...patch }));
              }}
              isLoading={generateMutation.isPending}
              onSubmit={(payload) => {
                continueMutation.reset();
                setManualContinueResult(null);
                setContinueRunContext(null);
                clearManualResultForMode('generate');
                setGenerateRunContext(buildDirectRunContext(workflowRefs, workspaceScope, workflowCatalogData));
                generateMutation.mutate({
                  ...payload,
                  session_id: activeIteration?.session_id ?? undefined,
                  domain_workspace_id: workspaceScope.domain_workspace_id ?? undefined,
                  subject_id: workspaceScope.subject_id ?? undefined,
                  context_pack_version_ids: workflowRefs.context_pack_version_ids,
                  evaluation_profile_version_id: workflowRefs.evaluation_profile_version_id,
                  workflow_recipe_version_id: workflowRefs.workflow_recipe_version_id,
                });
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
                continueMutation.reset();
                setManualContinueResult(null);
                setContinueRunContext(null);
                clearManualResultForMode('debug');
                setDebugRunContext(buildDirectRunContext(workflowRefs, workspaceScope, workflowCatalogData));
                debugMutation.mutate({
                  ...payload,
                  session_id: activeIteration?.session_id ?? undefined,
                  domain_workspace_id: workspaceScope.domain_workspace_id ?? undefined,
                  subject_id: workspaceScope.subject_id ?? undefined,
                  context_pack_version_ids: workflowRefs.context_pack_version_ids,
                  evaluation_profile_version_id: workflowRefs.evaluation_profile_version_id,
                  workflow_recipe_version_id: workflowRefs.workflow_recipe_version_id,
                });
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
                setManualContinueResult(null);
                setContinueRunContext(null);
                clearManualResultForMode('evaluate');
                setEvaluateRunContext(buildDirectRunContext(workflowRefs, workspaceScope, workflowCatalogData));
                evaluateMutation.mutate({
                  ...payload,
                  session_id: activeIteration?.session_id ?? undefined,
                  domain_workspace_id: workspaceScope.domain_workspace_id ?? undefined,
                  subject_id: workspaceScope.subject_id ?? undefined,
                  context_pack_version_ids: workflowRefs.context_pack_version_ids,
                  evaluation_profile_version_id: workflowRefs.evaluation_profile_version_id,
                  workflow_recipe_version_id: workflowRefs.workflow_recipe_version_id,
                });
              }}
            />
          )}
        </div>

        <aside className="space-y-4 xl:sticky xl:top-6">
          <section className="bp-surface px-5 py-5 md:px-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="bp-overline">{activeModeCopy.resultEyebrow}</div>
                <h2 className="bp-title mt-3 text-[2rem]">结果桌面</h2>
                <p className="mt-3 text-sm leading-7 text-[var(--bp-ink-soft)]">
                  {activeModeCopy.resultDescription}
                </p>
              </div>
              <div className="hidden rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-clay)] sm:block">
                {activeModeCopy.badge}
              </div>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <div className="bp-meta-card">
                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Primary Output</div>
                <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">
                  {mode === 'generate' ? '最终执行 Prompt' : mode === 'debug' ? '修复后 Prompt' : '评分与优化建议'}
                </div>
              </div>
              <div className="bp-meta-card">
                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Next Move</div>
                <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">
                  {hasBaseResult ? '继续沿结果优化' : '先完成当前输入'}
                </div>
              </div>
            </div>
          </section>

          {resultStack}
        </aside>
      </section>
    </div>
  );
}

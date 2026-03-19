import { useDeferredValue, useEffect, useState } from 'react';
import {
  BarChart3,
  Bookmark,
  BookmarkCheck,
  ChevronDown,
  ChevronRight,
  Clipboard,
  FolderPlus,
  FolderTree,
  LoaderCircle,
  PencilLine,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Trash2,
  Wand2,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  useCreatePromptAsset,
  useCreatePromptAssetVersion,
  useCreatePromptCategory,
  useDeletePromptAsset,
  useDeletePromptCategory,
  usePromptAssetDetail,
  usePromptLibrary,
  useUpdatePromptAsset,
} from './hooks/use-prompt-library';
import { usePromptAgentDebug } from './hooks/use-prompt-agent-debug';
import { usePromptAgentEvaluate } from './hooks/use-prompt-agent-evaluate';
import { usePromptAgentGenerateStream } from './hooks/use-prompt-agent-generate-stream';
import type {
  DebugDraft,
  EvaluateDraft,
  GenerateStrategy,
  PromptAgentMode,
  PromptAssetDetail,
  PromptAssetSummary,
  PromptCategoryTreeItem,
} from './types';

const MODE_COPY: Record<
  PromptAgentMode,
  {
    label: string;
    title: string;
    description: string;
    icon: typeof Wand2;
    cta: string;
  }
> = {
  generate: {
    label: 'Prompt Generate',
    title: '把需求压缩成专业、完整、可直接发送的 Prompt',
    description: '输入你的原始诉求，系统会结合已选提示词，把它整理成更稳、更清晰的成品。',
    icon: Wand2,
    cta: '开始生成',
  },
  debug: {
    label: 'Debug',
    title: '拆开失败现场，给出一版更可靠的修复 Prompt',
    description: '贴入任务、当前 Prompt 与输出，让系统判断最可能的结构问题。',
    icon: ShieldCheck,
    cta: '开始调试',
  },
  evaluate: {
    label: 'Evaluate',
    title: '先判断质量，再决定下一轮该怎么改',
    description: '对 Prompt 或输出做结构化评估，直接看到最该优先修的地方。',
    icon: BarChart3,
    cta: '开始评估',
  },
};

const GENERATE_STRATEGY_COPY: Record<
  GenerateStrategy,
  {
    title: string;
    description: string;
    badge: string;
  }
> = {
  optimize: {
    title: '提示词优化模式',
    description: '用户已经描述了大意，但还不够完整专业。系统会保留原意，并主动补齐约束、上下文和执行标准。',
    badge: 'Refine',
  },
  research: {
    title: '研究模式',
    description: '用户需求仍然模糊。系统会先识别研究领域，再以内化的专家视角产出一份可工作的研究型 Prompt。',
    badge: 'Research',
  },
};

const FIX_LAYER_LABELS: Record<string, string> = {
  problem_redefinition: '问题定义',
  cognitive_drill_down: '认知下钻',
  key_point_priority: '关键点优先级',
  criticality: '批判性分析',
  information_density: '信息密度',
  boundary_validation: '边界验证',
  executability: '可执行性',
  style_control: '表达风格',
};

const EMPTY_DEBUG_DRAFT: DebugDraft = {
  originalTask: '',
  currentPrompt: '',
  currentOutput: '',
};

const EMPTY_EVALUATE_DRAFT: EvaluateDraft = {
  targetText: '',
  targetType: 'prompt',
};

type PromptEditorState = {
  name: string;
  description: string;
  content: string;
  tags: string;
  categoryId: string | null;
};

type PromptPanelMode = 'hidden' | 'view' | 'create' | 'edit';

const SELECTED_PROMPT_STORAGE_KEY = 'betterprompt:selected-prompt-id';

function createEmptyEditor(categoryId: string | null = null): PromptEditorState {
  return {
    name: '',
    description: '',
    content: '',
    tags: '',
    categoryId,
  };
}

function toEditorState(detail: PromptAssetDetail): PromptEditorState {
  return {
    name: detail.name,
    description: detail.description ?? '',
    content: detail.current_version?.content ?? '',
    tags: detail.tags.join(', '),
    categoryId: detail.category_id,
  };
}

function splitTags(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function matchesSearchText(value: string | null | undefined, searchText: string): boolean {
  if (!searchText.trim()) {
    return true;
  }
  return (value ?? '').toLowerCase().includes(searchText.trim().toLowerCase());
}

function flattenCategoryOptions(
  items: PromptCategoryTreeItem[],
  options: Array<{ id: string; label: string }> = [],
) {
  for (const item of items) {
    options.push({
      id: item.id,
      label: item.path,
    });
    flattenCategoryOptions(item.children, options);
  }
  return options;
}

function formatTime(value: string | null | undefined): string {
  if (!value) {
    return '刚刚';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '刚刚';
  }
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function getErrorMessage(error: unknown): string | null {
  if (!error) {
    return null;
  }
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const maybeResponse = error as {
      response?: {
        data?: {
          detail?: string | { message?: string };
        };
      };
    };
    const detail = maybeResponse.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
    if (detail && typeof detail === 'object' && typeof detail.message === 'string') {
      return detail.message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return '请求失败，请稍后再试。';
}

function buildGenerateContextNotes(strategy: GenerateStrategy, promptName: string | null): string {
  const blocks = [
    strategy === 'optimize'
      ? [
        '当前运行模式：提示词优化模式。',
        '默认用户已经基本说明了需求，但表达仍然不够完整、专业或严格。',
        '请保留用户原意，主动补足背景、约束、边界、执行步骤、输出格式与质量标准。',
      ].join('\n')
      : [
        '当前运行模式：研究模式。',
        '默认用户的描述仍然比较模糊。',
        '请先判断最可能的研究领域、关键视角与专家方法论，再把这些认知内化成一份研究型 Prompt。',
        '如果关键信息缺失，不要停在泛泛建议，要把应如何澄清、如何验证写进最终 Prompt。',
      ].join('\n'),
  ];

  if (promptName) {
    blocks.push(`当前已选中的参考提示词是「${promptName}」。请吸收它的结构与约束，但不要机械复刻。`);
  }

  return blocks.join('\n\n');
}

function FieldLabel({
  title,
  hint,
}: {
  title: string;
  hint?: string;
}) {
  return (
    <div className="space-y-1">
      <div className="text-sm font-semibold text-[var(--bp-ink)]">{title}</div>
      {hint ? <div className="text-xs leading-6 text-[var(--bp-ink-soft)]">{hint}</div> : null}
    </div>
  );
}

function ModeCard({
  active,
  icon: Icon,
  label,
  title,
  description,
  onClick,
}: {
  active: boolean;
  icon: typeof Wand2;
  label: string;
  title: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-[1.6rem] border px-4 py-4 text-left transition-all ${
        active
          ? 'border-[rgba(31,36,45,0.14)] bg-[linear-gradient(135deg,rgba(28,34,43,0.98),rgba(56,63,75,0.98))] text-[#f8f3eb] shadow-[0_20px_44px_-30px_rgba(25,27,31,0.46)]'
          : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.76)] text-[var(--bp-ink)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)]'
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <span className={`rounded-full p-2 ${active ? 'bg-[rgba(255,255,255,0.14)]' : 'bg-[rgba(162,74,53,0.1)] text-[var(--bp-clay)]'}`}>
          <Icon className="h-4 w-4" />
        </span>
        <span className={`text-[10px] font-semibold uppercase tracking-[0.22em] ${active ? 'text-[rgba(248,243,235,0.68)]' : 'text-[var(--bp-ink-soft)]'}`}>
          {label}
        </span>
      </div>
      <div className="mt-4 text-base font-semibold leading-6">{title}</div>
      <div className={`mt-2 text-sm leading-7 ${active ? 'text-[rgba(248,243,235,0.78)]' : 'text-[var(--bp-ink-soft)]'}`}>
        {description}
      </div>
    </button>
  );
}

export default function PromptAgentPage() {
  const promptLibraryQuery = usePromptLibrary();
  const createCategoryMutation = useCreatePromptCategory();
  const deleteCategoryMutation = useDeletePromptCategory();
  const createAssetMutation = useCreatePromptAsset();
  const updateAssetMutation = useUpdatePromptAsset();
  const deleteAssetMutation = useDeletePromptAsset();
  const createAssetVersionMutation = useCreatePromptAssetVersion();
  const generateMutation = usePromptAgentGenerateStream();
  const debugMutation = usePromptAgentDebug();
  const evaluateMutation = usePromptAgentEvaluate();

  const [mode, setMode] = useState<PromptAgentMode>('generate');
  const [generateStrategy, setGenerateStrategy] = useState<GenerateStrategy>('optimize');
  const [generateInput, setGenerateInput] = useState('');
  const [debugDraft, setDebugDraft] = useState<DebugDraft>(EMPTY_DEBUG_DRAFT);
  const [evaluateDraft, setEvaluateDraft] = useState<EvaluateDraft>(EMPTY_EVALUATE_DRAFT);
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);
  const [promptPanelMode, setPromptPanelMode] = useState<PromptPanelMode>('hidden');
  const [promptEditor, setPromptEditor] = useState<PromptEditorState>(createEmptyEditor());
  const [editorFeedback, setEditorFeedback] = useState<string | null>(null);
  const [searchText, setSearchText] = useState('');
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
  const [groupFormOpen, setGroupFormOpen] = useState(false);
  const [groupName, setGroupName] = useState('');
  const [groupParentId, setGroupParentId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const deferredSearchText = useDeferredValue(searchText);
  const selectedPromptDetailQuery = usePromptAssetDetail(selectedPromptId);

  const promptLibrary = promptLibraryQuery.data;
  const libraryCategories = promptLibrary?.categories ?? [];
  const libraryAssets = promptLibrary?.assets ?? [];
  const categoryOptions = flattenCategoryOptions(libraryCategories);

  useEffect(() => {
    if (!libraryCategories.length) {
      return;
    }
    setExpandedCategories((current) => {
      const next = { ...current };
      for (const option of categoryOptions) {
        if (next[option.id] === undefined) {
          next[option.id] = true;
        }
      }
      return next;
    });
  }, [categoryOptions.length, libraryCategories.length]);

  useEffect(() => {
    if (!selectedPromptDetailQuery.data || promptPanelMode !== 'edit') {
      return;
    }
    setPromptEditor(toEditorState(selectedPromptDetailQuery.data));
    setEditorFeedback(null);
  }, [selectedPromptDetailQuery.data?.id, promptPanelMode]);

  useEffect(() => {
    if (promptLibraryQuery.isLoading) {
      return;
    }
    if (selectedPromptId && !libraryAssets.some((item) => item.id === selectedPromptId)) {
      setSelectedPromptId(null);
      setPromptPanelMode('hidden');
    }
  }, [libraryAssets, promptLibraryQuery.isLoading, selectedPromptId]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    const savedPromptId = window.localStorage.getItem(SELECTED_PROMPT_STORAGE_KEY);
    if (savedPromptId) {
      setSelectedPromptId(savedPromptId);
      setPromptPanelMode('view');
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    if (selectedPromptId) {
      window.localStorage.setItem(SELECTED_PROMPT_STORAGE_KEY, selectedPromptId);
      return;
    }
    window.localStorage.removeItem(SELECTED_PROMPT_STORAGE_KEY);
  }, [selectedPromptId]);

  const visibleAssets = libraryAssets.filter((asset) => {
    if (favoritesOnly && !asset.is_favorite) {
      return false;
    }
    const haystack = [asset.name, asset.description ?? '', asset.tags.join(' ')].join(' ');
    return matchesSearchText(haystack, deferredSearchText);
  });

  const assetsByCategory: Record<string, PromptAssetSummary[]> = {};
  for (const asset of visibleAssets) {
    const key = asset.category_id ?? '__ungrouped__';
    if (!assetsByCategory[key]) {
      assetsByCategory[key] = [];
    }
    assetsByCategory[key].push(asset);
  }

  const selectedPrompt = libraryAssets.find((item) => item.id === selectedPromptId) ?? null;
  const selectedPromptCategoryLabel = selectedPrompt?.category_id
    ? categoryOptions.find((item) => item.id === selectedPrompt.category_id)?.label ?? '未归类'
    : '未归类';
  const selectedPromptDetail = selectedPromptDetailQuery.data ?? null;
  const selectedPromptContent = selectedPromptDetail?.current_version?.content ?? '';

  const activeErrorMessage = getErrorMessage(
    promptLibraryQuery.error
      || createCategoryMutation.error
      || deleteCategoryMutation.error
      || createAssetMutation.error
      || updateAssetMutation.error
      || deleteAssetMutation.error
      || createAssetVersionMutation.error
      || generateMutation.error
      || debugMutation.error
      || evaluateMutation.error,
  );

  const generateResult = generateMutation.data;
  const debugResult = debugMutation.data;
  const evaluateResult = evaluateMutation.data;

  const outputText = mode === 'generate'
    ? (generateMutation.streamingText || generateResult?.final_prompt || '')
    : mode === 'debug'
      ? (debugResult?.fixed_prompt || '')
      : evaluateResult
        ? [
          `总分 ${evaluateResult.total_score}/35`,
          '',
          `最主要问题`,
          evaluateResult.top_issue,
          '',
          `建议优先修复层`,
          FIX_LAYER_LABELS[evaluateResult.suggested_fix_layer] ?? evaluateResult.suggested_fix_layer,
          '',
          `评分说明`,
          evaluateResult.total_interpretation,
        ].join('\n')
        : '';

  const isStreaming = mode === 'generate' && generateMutation.isStreaming;
  const activeModeCopy = MODE_COPY[mode];
  const ActiveModeIcon = activeModeCopy.icon;

  function toggleCategory(categoryId: string) {
    setExpandedCategories((current) => ({
      ...current,
      [categoryId]: !(current[categoryId] ?? true),
    }));
  }

  function categoryBranchHasContent(category: PromptCategoryTreeItem): boolean {
    if (matchesSearchText(category.name, deferredSearchText)) {
      return true;
    }
    if ((assetsByCategory[category.id] ?? []).length > 0) {
      return true;
    }
    return category.children.some(categoryBranchHasContent);
  }

  function categoryBranchCount(category: PromptCategoryTreeItem): number {
    let count = (assetsByCategory[category.id] ?? []).length;
    for (const child of category.children) {
      count += categoryBranchCount(child);
    }
    return count;
  }

  function openPromptViewer(assetId: string) {
    setSelectedPromptId(assetId);
    setPromptPanelMode('view');
    setEditorFeedback(null);
  }

  function startCreatePrompt(categoryId: string | null = null) {
    setSelectedPromptId(null);
    setPromptEditor(createEmptyEditor(categoryId));
    setPromptPanelMode('create');
    setEditorFeedback(null);
  }

  function startEditSelectedPrompt() {
    if (!selectedPromptDetail) {
      return;
    }
    setPromptEditor(toEditorState(selectedPromptDetail));
    setPromptPanelMode('edit');
    setEditorFeedback(null);
  }

  async function handleSaveGroup() {
    if (!groupName.trim()) {
      setEditorFeedback('父级名称不能为空。');
      return;
    }
    const created = await createCategoryMutation.mutateAsync({
      name: groupName.trim(),
      parent_id: groupParentId,
      sort_order: 0,
    });
    setExpandedCategories((current) => ({
      ...current,
      [created.id]: true,
    }));
    setGroupName('');
    setGroupParentId(null);
    setGroupFormOpen(false);
    setEditorFeedback('已创建新的父级提示词组。');
  }

  async function handleDeleteCategory(categoryId: string) {
    if (!window.confirm('删除这个父级提示词组？它必须先清空子提示词。')) {
      return;
    }
    await deleteCategoryMutation.mutateAsync(categoryId);
  }

  async function handleToggleFavorite(asset: PromptAssetSummary) {
    await updateAssetMutation.mutateAsync({
      assetId: asset.id,
      is_favorite: !asset.is_favorite,
    });
  }

  async function handleDeletePrompt(assetId: string) {
    if (!window.confirm('删除这条提示词？')) {
      return;
    }
    await deleteAssetMutation.mutateAsync(assetId);
    if (selectedPromptId === assetId) {
      setSelectedPromptId(null);
    }
    setPromptPanelMode('hidden');
  }

  async function handleSavePrompt() {
    if (!promptEditor.name.trim() || !promptEditor.content.trim()) {
      setEditorFeedback('提示词名称和正文都不能为空。');
      return;
    }

    const normalizedTags = splitTags(promptEditor.tags);

    if (promptPanelMode === 'create') {
      const created = await createAssetMutation.mutateAsync({
        category_id: promptEditor.categoryId,
        name: promptEditor.name.trim(),
        description: promptEditor.description.trim() || null,
        content: promptEditor.content.trim(),
        tags: normalizedTags,
        change_summary: '首次创建',
      });
      setSelectedPromptId(created.id);
      setPromptPanelMode('view');
      setPromptEditor(toEditorState(created));
      setEditorFeedback('提示词已创建并选中。');
      return;
    }

    if (!selectedPromptId || !selectedPromptDetail) {
      return;
    }

    const currentDetail = selectedPromptDetail;
    const currentTags = currentDetail.tags.join(',');
    const nextTags = normalizedTags.join(',');
    const metadataChanged = (
      promptEditor.name.trim() !== currentDetail.name
      || (promptEditor.description.trim() || null) !== currentDetail.description
      || promptEditor.categoryId !== currentDetail.category_id
      || currentTags !== nextTags
    );
    const contentChanged = promptEditor.content.trim() !== (currentDetail.current_version?.content ?? '');

    if (!metadataChanged && !contentChanged) {
      setEditorFeedback('没有需要保存的变更。');
      return;
    }

    let latestDetail = currentDetail;

    if (metadataChanged) {
      latestDetail = await updateAssetMutation.mutateAsync({
        assetId: selectedPromptId,
        category_id: promptEditor.categoryId,
        name: promptEditor.name.trim(),
        description: promptEditor.description.trim() || null,
        tags: normalizedTags,
      });
    }

    if (contentChanged) {
      latestDetail = await createAssetVersionMutation.mutateAsync({
        assetId: selectedPromptId,
        content: promptEditor.content.trim(),
        source_asset_version_id: currentDetail.current_version?.id ?? null,
        change_summary: '编辑提示词内容',
      });
    }

    setPromptEditor(toEditorState(latestDetail));
    setPromptPanelMode('view');
    setEditorFeedback('提示词已保存。');
  }

  async function handleSubmit() {
    if (mode === 'generate') {
      if (!generateInput.trim()) {
        return;
      }
      generateMutation.mutate({
        user_input: generateInput.trim(),
        show_diagnosis: false,
        output_preference: 'balanced',
        artifact_type: generateStrategy === 'research' ? 'conversation_prompt' : 'task_prompt',
        prompt_only: false,
        source_asset_version_id: selectedPrompt?.current_version?.id,
        context_notes: buildGenerateContextNotes(generateStrategy, selectedPrompt?.name ?? null),
      });
      return;
    }

    if (mode === 'debug') {
      if (!debugDraft.originalTask.trim() || !debugDraft.currentPrompt.trim() || !debugDraft.currentOutput.trim()) {
        return;
      }
      debugMutation.mutate({
        original_task: debugDraft.originalTask.trim(),
        current_prompt: debugDraft.currentPrompt.trim(),
        current_output: debugDraft.currentOutput.trim(),
        output_preference: 'balanced',
      });
      return;
    }

    if (!evaluateDraft.targetText.trim()) {
      return;
    }
    evaluateMutation.mutate({
      target_text: evaluateDraft.targetText.trim(),
      target_type: evaluateDraft.targetType,
    });
  }

  async function handleCopyOutput() {
    if (!outputText.trim() || !navigator.clipboard) {
      return;
    }
    await navigator.clipboard.writeText(outputText);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  }

  function renderPromptRow(asset: PromptAssetSummary) {
    const selected = selectedPromptId === asset.id;
    const activeForEdit = selectedPromptId === asset.id && promptPanelMode === 'edit';

    return (
      <div
        key={asset.id}
        className={`group rounded-[1.2rem] border px-3 py-3 transition-all ${
          selected
            ? 'border-[rgba(162,74,53,0.24)] bg-[rgba(162,74,53,0.1)] shadow-[0_14px_34px_-26px_rgba(162,74,53,0.34)]'
            : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.66)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.9)]'
        }`}
      >
        <div className="flex items-start gap-3">
          <button
            type="button"
            onClick={() => openPromptViewer(asset.id)}
            className="flex min-w-0 flex-1 items-start gap-3 text-left"
          >
            <div className={`mt-1 h-2.5 w-2.5 rounded-full ${selected ? 'bg-[var(--bp-clay)]' : 'bg-[rgba(53,87,104,0.22)]'}`} />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm font-semibold text-[var(--bp-ink)]">{asset.name}</span>
                {asset.is_favorite ? <Star className="h-3.5 w-3.5 fill-[var(--bp-clay)] text-[var(--bp-clay)]" /> : null}
              </div>
              <div className="mt-1 line-clamp-2 text-xs leading-6 text-[var(--bp-ink-soft)]">
                {asset.description || '这条提示词还没有补充说明。'}
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-[rgba(93,100,112,0.78)]">
                <span>v{asset.current_version?.version_number ?? 0}</span>
                <span>{formatTime(asset.updated_at)}</span>
                {selected ? <span className="text-[var(--bp-clay)]">已选中</span> : null}
                {activeForEdit ? <span className="text-[var(--bp-clay)]">正在编辑</span> : null}
              </div>
            </div>
          </button>

          <div className="flex items-center gap-1 opacity-100 xl:opacity-0 xl:transition-opacity xl:group-hover:opacity-100">
            <Button
              type="button"
              size="icon-sm"
              variant="ghost"
              onClick={() => {
                openPromptViewer(asset.id);
                setPromptPanelMode('edit');
              }}
              aria-label="编辑提示词"
            >
              <PencilLine className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              size="icon-sm"
              variant="ghost"
              onClick={() => handleToggleFavorite(asset)}
              aria-label={asset.is_favorite ? '取消收藏' : '收藏'}
            >
              {asset.is_favorite ? <BookmarkCheck className="h-4 w-4 text-[var(--bp-clay)]" /> : <Bookmark className="h-4 w-4" />}
            </Button>
            <Button
              type="button"
              size="icon-sm"
              variant="ghost"
              onClick={() => handleDeletePrompt(asset.id)}
              aria-label="删除提示词"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  function renderCategoryBranch(category: PromptCategoryTreeItem): JSX.Element | null {
    if (!categoryBranchHasContent(category)) {
      return null;
    }

    const branchAssets = assetsByCategory[category.id] ?? [];
    const expanded = expandedCategories[category.id] ?? true;
    const count = categoryBranchCount(category);

    return (
      <div key={category.id} className="space-y-3">
        <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.58)] p-3">
          <div className="flex items-start justify-between gap-3">
            <button
              type="button"
              onClick={() => toggleCategory(category.id)}
              className="flex min-w-0 flex-1 items-center gap-2 text-left"
            >
              {expanded ? <ChevronDown className="h-4 w-4 text-[var(--bp-ink-soft)]" /> : <ChevronRight className="h-4 w-4 text-[var(--bp-ink-soft)]" />}
              <FolderTree className="h-4 w-4 text-[var(--bp-clay)]" />
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold text-[var(--bp-ink)]">{category.name}</div>
                <div className="text-[11px] uppercase tracking-[0.18em] text-[rgba(93,100,112,0.78)]">
                  {count} 条子提示词
                </div>
              </div>
            </button>

            <div className="flex items-center gap-1">
              <Button
                type="button"
                size="icon-sm"
                variant="ghost"
                onClick={() => startCreatePrompt(category.id)}
                aria-label="在当前父级下新建提示词"
              >
                <Plus className="h-4 w-4" />
              </Button>
              <Button
                type="button"
                size="icon-sm"
                variant="ghost"
                onClick={() => handleDeleteCategory(category.id)}
                aria-label="删除父级提示词组"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {expanded ? (
            <div className="mt-3 space-y-3 border-t border-[var(--bp-line)] pt-3">
              {branchAssets.map(renderPromptRow)}
              {category.children.map((child) => (
                <div key={child.id} className="pl-4">
                  {renderCategoryBranch(child)}
                </div>
              ))}
              {branchAssets.length === 0 && category.children.every((child) => !categoryBranchHasContent(child)) ? (
                <div className="rounded-[1rem] border border-dashed border-[var(--bp-line)] px-3 py-3 text-xs leading-6 text-[var(--bp-ink-soft)]">
                  这个父级下还没有子提示词。
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    );
  }

  const isPromptModalOpen = promptPanelMode === 'create' || promptPanelMode === 'edit';

  function closePromptModal() {
    setPromptPanelMode(selectedPromptId ? 'view' : 'hidden');
    setEditorFeedback(null);
  }

  function clearSelectedPrompt() {
    setSelectedPromptId(null);
    setPromptPanelMode('hidden');
    setEditorFeedback(null);
  }

  useEffect(() => {
    if (!isPromptModalOpen || typeof window === 'undefined') {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setPromptPanelMode(selectedPromptId ? 'view' : 'hidden');
        setEditorFeedback(null);
      }
    };

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isPromptModalOpen, selectedPromptId]);

  return (
    <div className="mx-auto flex w-full max-w-[96rem] flex-col gap-6 px-4 pb-10 pt-8">
      <section className="bp-surface bp-fade-up overflow-hidden px-6 py-7 md:px-8 md:py-9">
        <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="bp-overline">Prompt Workbench</div>
            <h1 className="mt-3 max-w-2xl font-[var(--font-display)] text-[clamp(2.5rem,5vw,4.5rem)] leading-[0.95] tracking-[-0.05em] text-[var(--bp-ink)]">
              让提示词管理、生成与实时输出回到一张更干净的工作台。
            </h1>
            <p className="mt-4 max-w-2xl text-[15px] leading-8 text-[var(--bp-ink-soft)]">
              这个版本把多余展示收起来，只保留真正会影响结果质量的三件事：
              管理提示词、切换模式、把用户输入编译成更好的 Prompt。
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-[1.4rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.6)] px-4 py-4">
              <div className="text-[11px] uppercase tracking-[0.2em] text-[rgba(93,100,112,0.78)]">Prompt Tree</div>
              <div className="mt-2 text-2xl font-semibold text-[var(--bp-ink)]">{libraryAssets.length}</div>
              <div className="mt-1 text-sm text-[var(--bp-ink-soft)]">可复用子提示词</div>
            </div>
            <div className="rounded-[1.4rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.6)] px-4 py-4">
              <div className="text-[11px] uppercase tracking-[0.2em] text-[rgba(93,100,112,0.78)]">Modes</div>
              <div className="mt-2 text-2xl font-semibold text-[var(--bp-ink)]">3</div>
              <div className="mt-1 text-sm text-[var(--bp-ink-soft)]">Generate / Debug / Evaluate</div>
            </div>
            <div className="rounded-[1.4rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.6)] px-4 py-4">
              <div className="text-[11px] uppercase tracking-[0.2em] text-[rgba(93,100,112,0.78)]">Output</div>
              <div className="mt-2 text-2xl font-semibold text-[var(--bp-ink)]">{isStreaming ? 'Live' : 'Ready'}</div>
              <div className="mt-1 text-sm text-[var(--bp-ink-soft)]">实时结果落在右侧输出区</div>
            </div>
          </div>
        </div>
      </section>

      {activeErrorMessage ? (
        <div className="rounded-[1.4rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700 shadow-[0_18px_42px_-32px_rgba(220,38,38,0.38)]">
          {activeErrorMessage}
        </div>
      ) : null}

      <section className="bp-surface overflow-hidden px-5 py-5 md:px-6 md:py-6">
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="bp-overline">Prompt Library</div>
                <h2 className="mt-2 text-xl font-semibold tracking-tight text-[var(--bp-ink)]">嵌套提示词管理</h2>
                <p className="mt-2 text-sm leading-7 text-[var(--bp-ink-soft)]">
                  用父级提示词组组织子提示词；支持收藏、删除与选中参与生成。
                </p>
              </div>
              <div className="rounded-full border border-[rgba(162,74,53,0.16)] bg-[rgba(162,74,53,0.08)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--bp-clay)]">
                Library
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 xl:min-w-[28rem]">
              <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.62)] px-4 py-4">
                <div className="text-[11px] uppercase tracking-[0.2em] text-[rgba(93,100,112,0.78)]">Prompt Tree</div>
                <div className="mt-2 text-2xl font-semibold text-[var(--bp-ink)]">{libraryAssets.length}</div>
                <div className="mt-1 text-sm text-[var(--bp-ink-soft)]">可复用子提示词</div>
              </div>
              <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.62)] px-4 py-4">
                <div className="text-[11px] uppercase tracking-[0.2em] text-[rgba(93,100,112,0.78)]">Selection</div>
                <div className="mt-2 text-2xl font-semibold text-[var(--bp-ink)]">{selectedPrompt ? '1' : '0'}</div>
                <div className="mt-1 text-sm text-[var(--bp-ink-soft)]">当前选中的提示词</div>
              </div>
              <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.62)] px-4 py-4">
                <div className="text-[11px] uppercase tracking-[0.2em] text-[rgba(93,100,112,0.78)]">Edit</div>
                <div className="mt-2 text-2xl font-semibold text-[var(--bp-ink)]">Modal</div>
                <div className="mt-1 text-sm text-[var(--bp-ink-soft)]">编辑时以弹窗弹出</div>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="w-full lg:max-w-[28rem]">
              <div className="flex items-center gap-2 rounded-[1.25rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.76)] px-3 py-2.5">
                <Search className="h-4 w-4 text-[var(--bp-ink-soft)]" />
                <input
                  value={searchText}
                  onChange={(event) => setSearchText(event.target.value)}
                  placeholder="搜索提示词或标签"
                  className="w-full bg-transparent text-sm text-[var(--bp-ink)] outline-none placeholder:text-[rgba(93,100,112,0.72)]"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant={favoritesOnly ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFavoritesOnly((current) => !current)}
                className={favoritesOnly ? 'bp-action-primary border-0' : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)]'}
              >
                <Star className="mr-2 h-3.5 w-3.5" />
                {favoritesOnly ? '只看收藏中' : '全部提示词'}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setGroupFormOpen((current) => !current);
                  setGroupParentId(null);
                  setGroupName('');
                  setEditorFeedback(null);
                }}
                className="border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)]"
              >
                <FolderPlus className="mr-2 h-3.5 w-3.5" />
                新建父级
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => startCreatePrompt(selectedPrompt?.category_id ?? null)}
                className="border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)]"
              >
                <PencilLine className="mr-2 h-3.5 w-3.5" />
                新建子提示词
              </Button>
            </div>
          </div>

          <div className="rounded-[1.4rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.62)] px-4 py-4">
            <div className="bp-overline">Selected Prompt</div>
            {selectedPrompt ? (
              selectedPromptDetailQuery.isLoading ? (
                <div className="mt-3 text-sm leading-7 text-[var(--bp-ink-soft)]">正在读取提示词内容...</div>
              ) : (
                <div className="mt-3 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="text-lg font-semibold text-[var(--bp-ink)]">{selectedPrompt.name}</div>
                        <div className="mt-1 text-sm leading-7 text-[var(--bp-ink-soft)]">
                          {selectedPromptDetail?.description || '这条提示词还没有补充说明。'}
                        </div>
                      </div>
                      {selectedPrompt.is_favorite ? <Star className="mt-1 h-4 w-4 fill-[var(--bp-clay)] text-[var(--bp-clay)]" /> : null}
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <span className="bp-chip">{selectedPromptCategoryLabel}</span>
                      <span className="bp-chip">v{selectedPrompt.current_version?.version_number ?? 0}</span>
                      <span className="bp-chip">更新于 {formatTime(selectedPrompt.updated_at)}</span>
                    </div>
                    <div className="mt-3 rounded-[1.15rem] border border-[var(--bp-line)] bg-[linear-gradient(180deg,rgba(255,255,255,0.88),rgba(247,241,232,0.72))] px-4 py-4 text-sm leading-7 text-[var(--bp-ink)]">
                      <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-[rgba(93,100,112,0.78)]">
                        当前持久化版本预览
                      </div>
                      <div className="max-h-[11rem] overflow-y-auto whitespace-pre-wrap break-words">
                        {selectedPromptDetail?.current_version?.content ?? '当前还没有提示词正文。'}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 xl:w-[16rem] xl:justify-end">
                    <Button type="button" onClick={startEditSelectedPrompt} className="bp-action-primary border-0">
                      <PencilLine className="mr-2 h-4 w-4" />
                      编辑当前提示词
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => void handleToggleFavorite(selectedPrompt)}
                      className="border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)]"
                    >
                      {selectedPrompt.is_favorite ? '取消收藏' : '加入收藏'}
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={clearSelectedPrompt}
                      className="border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)]"
                    >
                      取消选中
                    </Button>
                  </div>
                </div>
              )
            ) : (
              <div className="mt-3 text-sm leading-7 text-[var(--bp-ink-soft)]">
                选中任意一条提示词后，会在这里展示它的完整预览；点击编辑时会以弹窗方式打开，不再占用主工作区。
              </div>
            )}
          </div>

          {groupFormOpen ? (
            <div className="rounded-[1.4rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.62)] p-4">
              <div className="text-sm font-semibold text-[var(--bp-ink)]">创建父级提示词组</div>
              <div className="mt-3 grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(16rem,0.7fr)_auto] md:items-end">
                <div className="space-y-2">
                  <FieldLabel title="父级名称" />
                  <input
                    value={groupName}
                    onChange={(event) => setGroupName(event.target.value)}
                    placeholder="例如：市场研究"
                    className="bp-input rounded-[1.1rem] px-4 py-3 text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <FieldLabel title="上级分组" hint="留空则创建为顶层父级。" />
                  <select
                    value={groupParentId ?? ''}
                    onChange={(event) => setGroupParentId(event.target.value || null)}
                    className="bp-input rounded-[1.1rem] px-4 py-3 text-sm"
                  >
                    <option value="">顶层父级</option>
                    {categoryOptions.map((option) => (
                      <option key={option.id} value={option.id}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center gap-2 md:justify-end">
                  <Button type="button" onClick={() => void handleSaveGroup()} disabled={createCategoryMutation.isPending}>
                    {createCategoryMutation.isPending ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                    保存父级
                  </Button>
                  <Button type="button" variant="ghost" onClick={() => setGroupFormOpen(false)}>
                    取消
                  </Button>
                </div>
              </div>
            </div>
          ) : null}

          <div className="max-h-[34rem] space-y-3 overflow-y-auto pr-1">
            {promptLibraryQuery.isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="skeleton h-20 rounded-[1.2rem]" />
                ))}
              </div>
            ) : (
              <>
                {libraryCategories.map((category) => renderCategoryBranch(category))}

                {(assetsByCategory.__ungrouped__ ?? []).length > 0 ? (
                  <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.58)] p-3">
                    <div className="mb-3 text-sm font-semibold text-[var(--bp-ink)]">未归类提示词</div>
                    <div className="space-y-3">
                      {(assetsByCategory.__ungrouped__ ?? []).map(renderPromptRow)}
                    </div>
                  </div>
                ) : null}

                {!libraryCategories.length && !(assetsByCategory.__ungrouped__ ?? []).length ? (
                  <div className="rounded-[1.35rem] border border-dashed border-[var(--bp-line)] px-4 py-6 text-sm leading-7 text-[var(--bp-ink-soft)]">
                    还没有可用提示词。先创建一个父级，再在下面放入子提示词。
                  </div>
                ) : null}
              </>
            )}
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.12fr)_minmax(360px,0.88fr)]">
        <section className="bp-surface overflow-hidden px-5 py-5 md:px-6 md:py-6">
          <div className="flex flex-col gap-5">
            <div>
              <div className="bp-overline">Composer</div>
              <div className="mt-2 flex items-center gap-3">
                <span className="rounded-full bg-[rgba(162,74,53,0.1)] p-2 text-[var(--bp-clay)]">
                  <ActiveModeIcon className="h-4 w-4" />
                </span>
                <div>
                  <h2 className="text-[1.65rem] font-semibold tracking-tight text-[var(--bp-ink)]">{activeModeCopy.title}</h2>
                  <p className="mt-1 text-sm leading-7 text-[var(--bp-ink-soft)]">{activeModeCopy.description}</p>
                </div>
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-3">
              {Object.entries(MODE_COPY).map(([entryMode, entry]) => (
                <ModeCard
                  key={entryMode}
                  active={mode === entryMode}
                  icon={entry.icon}
                  label={entry.label}
                  title={entry.title}
                  description={entry.description}
                  onClick={() => setMode(entryMode as PromptAgentMode)}
                />
              ))}
            </div>

            {mode === 'generate' ? (
              <div className="rounded-[1.55rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.62)] p-4">
                <div className="bp-overline">Generate Strategy</div>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  {Object.entries(GENERATE_STRATEGY_COPY).map(([key, entry]) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setGenerateStrategy(key as GenerateStrategy)}
                      className={`rounded-[1.35rem] border px-4 py-4 text-left transition-all ${
                        generateStrategy === key
                          ? 'border-[rgba(162,74,53,0.22)] bg-[rgba(162,74,53,0.1)] shadow-[0_18px_42px_-30px_rgba(162,74,53,0.32)]'
                          : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)]'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm font-semibold text-[var(--bp-ink)]">{entry.title}</div>
                        <span className="rounded-full border border-[rgba(162,74,53,0.14)] bg-[rgba(162,74,53,0.08)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-clay)]">
                          {entry.badge}
                        </span>
                      </div>
                      <div className="mt-2 text-sm leading-7 text-[var(--bp-ink-soft)]">{entry.description}</div>
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="rounded-[1.55rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.64)] p-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="bp-overline">Selected Prompt</div>
                  {selectedPrompt ? (
                    <>
                      <div className="mt-2 text-lg font-semibold text-[var(--bp-ink)]">{selectedPrompt.name}</div>
                      <div className="mt-1 text-sm leading-7 text-[var(--bp-ink-soft)]">
                        位于 {selectedPromptCategoryLabel}，生成时会把这条提示词的结构与约束一起吸收进去。
                      </div>
                    </>
                  ) : (
                    <div className="mt-2 text-sm leading-7 text-[var(--bp-ink-soft)]">
                      当前没有选中的提示词。你仍然可以直接生成，但上方选中后会得到更稳定的结果。
                    </div>
                  )}
                </div>

                {selectedPrompt ? (
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={clearSelectedPrompt}
                      className="border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)]"
                    >
                      取消选中
                    </Button>
                    {mode === 'debug' && selectedPromptContent ? (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setDebugDraft((current) => ({ ...current, currentPrompt: selectedPromptContent }))}
                        className="border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)]"
                      >
                        填入当前 Prompt
                      </Button>
                    ) : null}
                    {mode === 'evaluate' && selectedPromptContent ? (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setEvaluateDraft({ targetText: selectedPromptContent, targetType: 'prompt' })}
                        className="border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)]"
                      >
                        作为待评估 Prompt
                      </Button>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </div>

            <div className="space-y-4">
              {mode === 'generate' ? (
                <div className="space-y-2">
                  <FieldLabel
                    title="用户输入"
                    hint={generateStrategy === 'optimize'
                      ? '把你当前已经想到的需求写出来，系统会继续把它扩成更专业的 Prompt。'
                      : '把模糊的方向写出来，系统会先判断研究领域，再把专家视角和研究方法写进结果。'}
                  />
                  <textarea
                    value={generateInput}
                    onChange={(event) => setGenerateInput(event.target.value)}
                    placeholder={generateStrategy === 'optimize'
                      ? '例如：帮我写一个用于分析竞品官网信息架构的 Prompt。'
                      : '例如：我想研究一个新行业，但目前还不知道应该从哪些角度切入。'}
                    className="bp-input min-h-[260px] rounded-[1.45rem] px-5 py-4 text-[15px] leading-8"
                  />
                </div>
              ) : null}

              {mode === 'debug' ? (
                <div className="grid gap-4">
                  <div className="space-y-2">
                    <FieldLabel title="原始任务" hint="你真正想让模型完成什么？" />
                    <textarea
                      value={debugDraft.originalTask}
                      onChange={(event) => setDebugDraft((current) => ({ ...current, originalTask: event.target.value }))}
                      placeholder="例如：帮我写一个多因素框架来分析某个 SaaS 产品的商业模式。"
                      className="bp-input min-h-[120px] rounded-[1.35rem] px-4 py-3 text-sm leading-7"
                    />
                  </div>
                  <div className="space-y-2">
                    <FieldLabel title="当前 Prompt" hint="贴入正在失败的提示词。" />
                    <textarea
                      value={debugDraft.currentPrompt}
                      onChange={(event) => setDebugDraft((current) => ({ ...current, currentPrompt: event.target.value }))}
                      placeholder="把你当前在用的 Prompt 粘贴到这里。"
                      className="bp-input min-h-[160px] rounded-[1.35rem] px-4 py-3 text-sm leading-7"
                    />
                  </div>
                  <div className="space-y-2">
                    <FieldLabel title="当前输出" hint="贴入模型给出的失败结果。" />
                    <textarea
                      value={debugDraft.currentOutput}
                      onChange={(event) => setDebugDraft((current) => ({ ...current, currentOutput: event.target.value }))}
                      placeholder="把模型当前输出粘贴到这里。"
                      className="bp-input min-h-[140px] rounded-[1.35rem] px-4 py-3 text-sm leading-7"
                    />
                  </div>
                </div>
              ) : null}

              {mode === 'evaluate' ? (
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant={evaluateDraft.targetType === 'prompt' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setEvaluateDraft((current) => ({ ...current, targetType: 'prompt' }))}
                      className={evaluateDraft.targetType === 'prompt' ? 'bp-action-primary border-0' : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)]'}
                    >
                      评估 Prompt
                    </Button>
                    <Button
                      type="button"
                      variant={evaluateDraft.targetType === 'output' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setEvaluateDraft((current) => ({ ...current, targetType: 'output' }))}
                      className={evaluateDraft.targetType === 'output' ? 'bp-action-primary border-0' : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)]'}
                    >
                      评估输出
                    </Button>
                  </div>

                  <div className="space-y-2">
                    <FieldLabel
                      title={evaluateDraft.targetType === 'prompt' ? '待评估 Prompt' : '待评估输出'}
                      hint="贴入你想判断质量的内容。"
                    />
                    <textarea
                      value={evaluateDraft.targetText}
                      onChange={(event) => setEvaluateDraft((current) => ({ ...current, targetText: event.target.value }))}
                      placeholder={evaluateDraft.targetType === 'prompt'
                        ? '把要评估的 Prompt 粘贴到这里。'
                        : '把要评估的输出内容粘贴到这里。'}
                      className="bp-input min-h-[280px] rounded-[1.45rem] px-5 py-4 text-[15px] leading-8"
                    />
                  </div>
                </div>
              ) : null}
            </div>

            <div className="flex flex-wrap items-center gap-3 border-t border-[var(--bp-line)] pt-4">
              <Button
                type="button"
                onClick={() => void handleSubmit()}
                disabled={
                  generateMutation.isPending
                  || debugMutation.isPending
                  || evaluateMutation.isPending
                }
                className="bp-action-primary border-0 px-6"
              >
                {generateMutation.isPending || debugMutation.isPending || evaluateMutation.isPending
                  ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />
                  : <Sparkles className="mr-2 h-4 w-4" />}
                {activeModeCopy.cta}
              </Button>
              <div className="text-sm leading-7 text-[var(--bp-ink-soft)]">
                {mode === 'generate'
                  ? `${GENERATE_STRATEGY_COPY[generateStrategy].title}已启用。`
                  : mode === 'debug'
                    ? '系统会返回诊断结论与修复版 Prompt。'
                    : '系统会返回评分、解释和优先修复建议。'}
              </div>
            </div>
          </div>
        </section>

        <aside className="bp-surface flex min-h-[42rem] flex-col overflow-hidden px-5 py-5 md:px-6 md:py-6 xl:sticky xl:top-24 xl:self-start">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="bp-overline">Live Output</div>
              <h2 className="mt-2 text-xl font-semibold tracking-tight text-[var(--bp-ink)]">优化后提示词实时输出区</h2>
              <p className="mt-2 text-sm leading-7 text-[var(--bp-ink-soft)]">
                生成中的文本会直接落在这里；Debug 和 Evaluate 结果也会在同一区域收敛展示。
              </p>
            </div>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void handleCopyOutput()}
              disabled={!outputText.trim()}
              className="border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)]"
            >
              <Clipboard className="mr-2 h-3.5 w-3.5" />
              {copied ? '已复制' : '复制'}
            </Button>
          </div>

          <div className="mt-5 rounded-[1.75rem] border border-[var(--bp-line)] bg-[linear-gradient(180deg,rgba(255,255,255,0.88),rgba(247,241,232,0.72))] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.7)]">
            <div className="flex items-center justify-between gap-3 border-b border-[var(--bp-line)] pb-3">
              <div className="flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${isStreaming ? 'bg-[var(--bp-clay)] pulse-live' : 'bg-[rgba(53,87,104,0.36)]'}`} />
                <span className="text-sm font-medium text-[var(--bp-ink)]">
                  {isStreaming ? '正在实时生成...' : outputText ? '结果已准备好' : '等待本轮输出'}
                </span>
              </div>
              <div className="text-[11px] uppercase tracking-[0.18em] text-[rgba(93,100,112,0.78)]">
                {mode === 'generate' ? GENERATE_STRATEGY_COPY[generateStrategy].badge : MODE_COPY[mode].label}
              </div>
            </div>

            <div className="min-h-[25rem] pt-4">
              {outputText ? (
                <div className="bp-fade-up whitespace-pre-wrap break-words font-[var(--font-body)] text-[15px] leading-8 text-[var(--bp-ink)]">
                  {outputText}
                  {isStreaming ? <span className="ml-1 inline-block h-2.5 w-2.5 rounded-full bg-[var(--bp-clay)] pulse-live align-middle" /> : null}
                </div>
              ) : (
                <div className="flex min-h-[24rem] flex-col justify-center rounded-[1.4rem] border border-dashed border-[var(--bp-line)] px-5 py-6 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[rgba(162,74,53,0.1)] text-[var(--bp-clay)]">
                    {mode === 'generate' ? <Sparkles className="h-5 w-5" /> : mode === 'debug' ? <ShieldCheck className="h-5 w-5" /> : <BarChart3 className="h-5 w-5" />}
                  </div>
                  <div className="mt-4 text-base font-semibold text-[var(--bp-ink)]">结果会在这里连续落下</div>
                  <div className="mt-2 text-sm leading-7 text-[var(--bp-ink-soft)]">
                    {mode === 'generate'
                      ? '上方选中提示词，中间输入需求，然后开始生成。'
                      : mode === 'debug'
                        ? '贴入任务、Prompt 和失败输出后，系统会返回修复版 Prompt。'
                        : '贴入待评估内容后，系统会返回评分、主要问题和下一步建议。'}
                  </div>
                </div>
              )}
            </div>
          </div>

          {mode === 'generate' && (generateMutation.meta || generateResult) ? (
            <div className="mt-4 grid gap-3">
              <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.62)] px-4 py-4">
                <div className="text-[11px] uppercase tracking-[0.2em] text-[rgba(93,100,112,0.78)]">策略说明</div>
                <div className="mt-2 text-sm leading-7 text-[var(--bp-ink-soft)]">
                  {(generateMutation.meta?.optimization_strategy || generateResult?.optimization_strategy || '系统已按当前模式优化用户输入。')}
                </div>
              </div>
              {(generateMutation.meta?.optimized_input || generateResult?.optimized_input) ? (
                <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.62)] px-4 py-4">
                  <div className="text-[11px] uppercase tracking-[0.2em] text-[rgba(93,100,112,0.78)]">重构后的任务简报</div>
                  <div className="mt-2 whitespace-pre-wrap text-sm leading-7 text-[var(--bp-ink-soft)]">
                    {generateMutation.meta?.optimized_input || generateResult?.optimized_input}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {mode === 'debug' && debugResult ? (
            <div className="mt-4 grid gap-3">
              <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.62)] px-4 py-4">
                <div className="text-[11px] uppercase tracking-[0.2em] text-[rgba(93,100,112,0.78)]">主要失效模式</div>
                <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{debugResult.top_failure_mode}</div>
                {debugResult.weaknesses.length ? (
                  <div className="mt-2 text-sm leading-7 text-[var(--bp-ink-soft)]">
                    当前弱点：{debugResult.weaknesses.join(' / ')}
                  </div>
                ) : null}
              </div>
              {debugResult.missing_control_layers.length ? (
                <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.62)] px-4 py-4">
                  <div className="text-[11px] uppercase tracking-[0.2em] text-[rgba(93,100,112,0.78)]">建议补强层</div>
                  <div className="mt-2 text-sm leading-7 text-[var(--bp-ink-soft)]">
                    {debugResult.missing_control_layers.map((item) => FIX_LAYER_LABELS[item] ?? item).join(' / ')}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {mode === 'evaluate' && evaluateResult ? (
            <div className="mt-4 grid gap-3">
              <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.62)] px-4 py-4">
                <div className="text-[11px] uppercase tracking-[0.2em] text-[rgba(93,100,112,0.78)]">分数</div>
                <div className="mt-2 text-3xl font-semibold tracking-tight text-[var(--bp-ink)]">{evaluateResult.total_score}/35</div>
                <div className="mt-2 text-sm leading-7 text-[var(--bp-ink-soft)]">{evaluateResult.total_interpretation}</div>
              </div>
              <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.62)] px-4 py-4">
                <div className="text-[11px] uppercase tracking-[0.2em] text-[rgba(93,100,112,0.78)]">优先修复项</div>
                <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{evaluateResult.top_issue}</div>
                <div className="mt-2 text-sm leading-7 text-[var(--bp-ink-soft)]">
                  建议先补强 {FIX_LAYER_LABELS[evaluateResult.suggested_fix_layer] ?? evaluateResult.suggested_fix_layer}
                </div>
              </div>
            </div>
          ) : null}
        </aside>
      </section>

      {isPromptModalOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(28,34,43,0.42)] px-4 py-6 backdrop-blur-sm"
          onClick={closePromptModal}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="prompt-modal-title"
            aria-describedby="prompt-modal-description"
            className="bp-surface max-h-[calc(100vh-3rem)] w-full max-w-[52rem] overflow-y-auto px-5 py-5 md:px-6 md:py-6"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="bp-overline">{promptPanelMode === 'create' ? 'New Prompt' : 'Edit Prompt'}</div>
                <h3 id="prompt-modal-title" className="mt-2 text-xl font-semibold text-[var(--bp-ink)]">
                  {promptPanelMode === 'create' ? '新建子提示词' : '编辑当前提示词'}
                </h3>
                <p id="prompt-modal-description" className="mt-2 text-sm leading-7 text-[var(--bp-ink-soft)]">
                  保存后会立即持久化到提示词库；如果正文改动，会自动创建新版本。
                </p>
              </div>
              <Button type="button" variant="ghost" size="icon-sm" onClick={closePromptModal} aria-label="关闭编辑弹窗">
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="mt-5 space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <FieldLabel title="提示词名称" />
                  <input
                    value={promptEditor.name}
                    onChange={(event) => {
                      setPromptEditor((current) => ({ ...current, name: event.target.value }));
                      setEditorFeedback(null);
                    }}
                    placeholder="例如：行业研究深挖"
                    className="bp-input rounded-[1.15rem] px-4 py-3 text-sm"
                  />
                </div>

                <div className="space-y-2">
                  <FieldLabel title="所在父级" />
                  <select
                    value={promptEditor.categoryId ?? ''}
                    onChange={(event) => {
                      setPromptEditor((current) => ({ ...current, categoryId: event.target.value || null }));
                      setEditorFeedback(null);
                    }}
                    className="bp-input rounded-[1.15rem] px-4 py-3 text-sm"
                  >
                    <option value="">未归类</option>
                    {categoryOptions.map((option) => (
                      <option key={option.id} value={option.id}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <FieldLabel title="说明" hint="一句话告诉自己这条提示词适合什么任务。" />
                <textarea
                  value={promptEditor.description}
                  onChange={(event) => {
                    setPromptEditor((current) => ({ ...current, description: event.target.value }));
                    setEditorFeedback(null);
                  }}
                  placeholder="例如：适合拿来把模糊的行业问题扩成研究型 Prompt。"
                  className="bp-input min-h-[92px] rounded-[1.15rem] px-4 py-3 text-sm leading-7"
                />
              </div>

              <div className="space-y-2">
                <FieldLabel title="标签" hint="用逗号分隔，例如：研究, 商业, 深挖" />
                <input
                  value={promptEditor.tags}
                  onChange={(event) => {
                    setPromptEditor((current) => ({ ...current, tags: event.target.value }));
                    setEditorFeedback(null);
                  }}
                  placeholder="研究, 商业, 深挖"
                  className="bp-input rounded-[1.15rem] px-4 py-3 text-sm"
                />
              </div>

              <div className="space-y-2">
                <FieldLabel title="提示词正文" />
                <textarea
                  value={promptEditor.content}
                  onChange={(event) => {
                    setPromptEditor((current) => ({ ...current, content: event.target.value }));
                    setEditorFeedback(null);
                  }}
                  placeholder="把这条子提示词的核心结构写在这里。"
                  className="bp-input min-h-[260px] rounded-[1.15rem] px-4 py-3 text-sm leading-7"
                />
              </div>

              {selectedPromptDetailQuery.isLoading && promptPanelMode === 'edit' ? (
                <div className="text-xs leading-6 text-[var(--bp-ink-soft)]">正在读取提示词详情...</div>
              ) : null}

              {selectedPromptDetail?.current_version && promptPanelMode === 'edit' ? (
                <div className="rounded-[1.15rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.56)] px-4 py-3 text-xs leading-6 text-[var(--bp-ink-soft)]">
                  当前版本 v{selectedPromptDetail.current_version.version_number} · 最近更新 {formatTime(selectedPromptDetail.current_version.created_at)}
                </div>
              ) : null}

              {editorFeedback ? (
                <div className="rounded-[1rem] border border-[rgba(162,74,53,0.16)] bg-[rgba(162,74,53,0.08)] px-3 py-2 text-xs leading-6 text-[var(--bp-clay)]">
                  {editorFeedback}
                </div>
              ) : null}

              <div className="flex flex-wrap items-center gap-2 border-t border-[var(--bp-line)] pt-4">
                <Button
                  type="button"
                  onClick={() => void handleSavePrompt()}
                  disabled={createAssetMutation.isPending || updateAssetMutation.isPending || createAssetVersionMutation.isPending}
                  className="bp-action-primary border-0"
                >
                  {createAssetMutation.isPending || updateAssetMutation.isPending || createAssetVersionMutation.isPending
                    ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />
                    : <Sparkles className="mr-2 h-4 w-4" />}
                  {promptPanelMode === 'create' ? '创建提示词' : '保存修改'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={closePromptModal}
                  className="border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)]"
                >
                  取消
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

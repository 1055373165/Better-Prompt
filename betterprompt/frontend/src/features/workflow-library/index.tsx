import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowUpRight, Boxes, Clock3, FilePlus2, Layers3, PackageCheck, Search, Sparkles } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api/client';
import { useWorkflowAssetCatalog } from '@/features/prompt-agent/hooks/use-workflow-asset-catalog';
import type {
  ContextPackDetail,
  ContextPackSummary,
  ContextPackVersionDetail,
  EvaluationProfileDetail,
  EvaluationProfileSummary,
  EvaluationProfileVersionDetail,
  RunPresetDetail,
  RunPresetSummary,
  WorkflowRecipeDetail,
  WorkflowRecipeSummary,
  WorkflowRecipeVersionDetail,
} from '@/features/prompt-agent/types';

type WorkflowAssetKind = 'context_pack' | 'evaluation_profile' | 'workflow_recipe' | 'run_preset';
type AssetSummary = ContextPackSummary | EvaluationProfileSummary | WorkflowRecipeSummary | RunPresetSummary;
type AssetDetail = ContextPackDetail | EvaluationProfileDetail | WorkflowRecipeDetail | RunPresetDetail;
type AssetVersion = ContextPackVersionDetail | EvaluationProfileVersionDetail | WorkflowRecipeVersionDetail;

const KIND_CONFIG: Record<
  WorkflowAssetKind,
  {
    label: string;
    shortLabel: string;
    description: string;
    emptyCopy: string;
    createLabel: string;
    versionLabel: string;
    jsonLabel: string;
  }
> = {
  context_pack: {
    label: 'Context Packs',
    shortLabel: 'Context',
    description: '把可复用上下文、约束和素材打包，供 workbench 与 preset 绑定。',
    emptyCopy: '先创建第一个 context pack，把常用背景资料和执行边界收进去。',
    createLabel: '新建 Context Pack',
    versionLabel: '新增 Context Pack 版本',
    jsonLabel: 'Payload JSON',
  },
  evaluation_profile: {
    label: 'Evaluation Profiles',
    shortLabel: 'Profiles',
    description: '定义评估规则、评分权重和修复偏好，稳定地约束 Evaluate 链路。',
    emptyCopy: '先创建第一个 evaluation profile，把评估标准沉淀成资产。',
    createLabel: '新建 Evaluation Profile',
    versionLabel: '新增 Evaluation Profile 版本',
    jsonLabel: 'Rules JSON',
  },
  workflow_recipe: {
    label: 'Workflow Recipes',
    shortLabel: 'Recipes',
    description: '把 workflow 的步骤、模式和域提示保存成 recipe，作为 run preset 的骨架。',
    emptyCopy: '先创建第一个 workflow recipe，把稳定的执行结构收进去。',
    createLabel: '新建 Workflow Recipe',
    versionLabel: '新增 Workflow Recipe 版本',
    jsonLabel: 'Definition JSON',
  },
  run_preset: {
    label: 'Run Presets',
    shortLabel: 'Presets',
    description: '把 prompt version、context packs、profile、recipe 和 run settings 绑成一键启动入口。',
    emptyCopy: '先创建第一个 run preset，把常用启动组合固化下来。',
    createLabel: '新建 Run Preset',
    versionLabel: '更新 Run Preset',
    jsonLabel: 'Definition JSON',
  },
};

const DEFAULT_DRAFT = {
  name: '',
  description: '',
  tags: '',
  domainHint: '',
  jsonText: '{\n  \n}',
  changeSummary: '',
  sourceIterationId: '',
};

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return '—';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function formatJson(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2);
}

function parseObjectJson(text: string, label: string): Record<string, unknown> {
  const trimmed = text.trim();
  if (!trimmed) {
    return {};
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch {
    throw new Error(`${label} 不是合法 JSON。`);
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error(`${label} 必须是 JSON object。`);
  }
  return parsed as Record<string, unknown>;
}

function splitTags(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function itemVersionLabel(item: AssetSummary): string {
  if ('current_version' in item && item.current_version) {
    return `v${item.current_version.version_number}`;
  }
  return '无版本';
}

function itemMetaLine(item: AssetSummary): string {
  if ('domain_hint' in item && item.domain_hint) {
    return item.domain_hint;
  }
  if ('tags' in item && item.tags.length > 0) {
    return item.tags.slice(0, 3).join(' / ');
  }
  if ('last_used_at' in item && item.last_used_at) {
    return `上次使用 ${formatDateTime(item.last_used_at)}`;
  }
  return item.description || '暂时还没有补充说明。';
}

function matchesAssetSearch(item: AssetSummary, searchText: string): boolean {
  const normalized = searchText.trim().toLowerCase();
  if (!normalized) {
    return true;
  }
  const fragments = [
    item.name,
    item.description ?? '',
    'tags' in item ? item.tags.join(' ') : '',
    'domain_hint' in item ? item.domain_hint ?? '' : '',
  ];
  return fragments.join(' ').toLowerCase().includes(normalized);
}

function getItemsByKind(
  kind: WorkflowAssetKind,
  catalog: ReturnType<typeof useWorkflowAssetCatalog>['data'] | undefined,
): AssetSummary[] {
  if (!catalog) {
    return [];
  }
  if (kind === 'context_pack') {
    return catalog.contextPacks;
  }
  if (kind === 'evaluation_profile') {
    return catalog.evaluationProfiles;
  }
  if (kind === 'workflow_recipe') {
    return catalog.workflowRecipes;
  }
  return catalog.runPresets;
}

function getDetailQueryKey(kind: WorkflowAssetKind, id: string | null) {
  return ['workflow-library', kind, id, 'detail'];
}

function getVersionsQueryKey(kind: WorkflowAssetKind, id: string | null) {
  return ['workflow-library', kind, id, 'versions'];
}

function getCurrentJsonText(kind: WorkflowAssetKind, detail: AssetDetail | null): string {
  if (!detail) {
    return formatJson({});
  }
  if (kind === 'context_pack') {
    return formatJson((detail as ContextPackDetail).current_version?.payload ?? {});
  }
  if (kind === 'evaluation_profile') {
    return formatJson((detail as EvaluationProfileDetail).current_version?.rules ?? {});
  }
  if (kind === 'workflow_recipe') {
    return formatJson((detail as WorkflowRecipeDetail).current_version?.definition ?? {});
  }
  return formatJson((detail as RunPresetDetail).definition ?? {});
}

function buildUpdateDraft(kind: WorkflowAssetKind, detail: AssetDetail | null) {
  if (!detail) {
    return DEFAULT_DRAFT;
  }
  if (kind === 'context_pack') {
    const contextPack = detail as ContextPackDetail;
    return {
      name: contextPack.name,
      description: contextPack.description ?? '',
      tags: contextPack.tags.join(', '),
      domainHint: '',
      jsonText: formatJson(contextPack.current_version?.payload ?? {}),
      changeSummary: '',
      sourceIterationId: contextPack.current_version?.source_iteration_id ?? '',
    };
  }
  if (kind === 'evaluation_profile') {
    const profile = detail as EvaluationProfileDetail;
    return {
      name: profile.name,
      description: profile.description ?? '',
      tags: '',
      domainHint: '',
      jsonText: formatJson(profile.current_version?.rules ?? {}),
      changeSummary: '',
      sourceIterationId: '',
    };
  }
  if (kind === 'workflow_recipe') {
    const recipe = detail as WorkflowRecipeDetail;
    return {
      name: recipe.name,
      description: recipe.description ?? '',
      tags: '',
      domainHint: recipe.domain_hint ?? '',
      jsonText: formatJson(recipe.current_version?.definition ?? {}),
      changeSummary: '',
      sourceIterationId: recipe.current_version?.source_iteration_id ?? '',
    };
  }
  const preset = detail as RunPresetDetail;
  return {
    name: preset.name,
    description: preset.description ?? '',
    tags: '',
    domainHint: '',
    jsonText: formatJson(preset.definition ?? {}),
    changeSummary: '',
    sourceIterationId: '',
  };
}

function buildVersionItems(kind: WorkflowAssetKind, versions: AssetVersion[]): Array<{ id: string; title: string; subtitle: string }> {
  if (kind === 'run_preset') {
    return [];
  }
  return versions.map((version) => ({
    id: version.id,
    title: `Version ${version.version_number}`,
    subtitle: `${version.change_summary || '无 change summary'} · ${formatDateTime(version.created_at)}`,
  }));
}

function extractPromptAssetRefSummary(definition: Record<string, unknown>) {
  const contextPackVersionIds = Array.isArray(definition.context_pack_version_ids)
    ? definition.context_pack_version_ids.filter((item): item is string => typeof item === 'string')
    : [];
  return {
    promptAssetVersionId: typeof definition.prompt_asset_version_id === 'string' ? definition.prompt_asset_version_id : null,
    workflowRecipeVersionId: typeof definition.workflow_recipe_version_id === 'string' ? definition.workflow_recipe_version_id : null,
    evaluationProfileVersionId: typeof definition.evaluation_profile_version_id === 'string' ? definition.evaluation_profile_version_id : null,
    contextPackCount: contextPackVersionIds.length,
  };
}

function SectionCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="bp-surface px-5 py-5 md:px-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="bp-overline">{title}</div>
          {subtitle && <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--bp-ink-soft)]">{subtitle}</p>}
        </div>
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

export default function WorkflowLibraryPage() {
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const catalogQuery = useWorkflowAssetCatalog();
  const [kind, setKind] = useState<WorkflowAssetKind>('context_pack');
  const [searchText, setSearchText] = useState('');
  const [selectedIds, setSelectedIds] = useState<Record<WorkflowAssetKind, string | null>>({
    context_pack: null,
    evaluation_profile: null,
    workflow_recipe: null,
    run_preset: null,
  });
  const [createDraft, setCreateDraft] = useState(DEFAULT_DRAFT);
  const [updateDraft, setUpdateDraft] = useState(DEFAULT_DRAFT);
  const [versionDraft, setVersionDraft] = useState(DEFAULT_DRAFT);
  const [createError, setCreateError] = useState<string | null>(null);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [versionError, setVersionError] = useState<string | null>(null);

  const items = getItemsByKind(kind, catalogQuery.data);
  const filteredItems = items.filter((item) => matchesAssetSearch(item, searchText));
  const selectedId = selectedIds[kind];

  useEffect(() => {
    const requestedKind = searchParams.get('kind');
    if (
      requestedKind === 'context_pack'
      || requestedKind === 'evaluation_profile'
      || requestedKind === 'workflow_recipe'
      || requestedKind === 'run_preset'
    ) {
      setKind(requestedKind);
    }

    setSearchText(searchParams.get('q') ?? '');

    const requestedId = searchParams.get('id');
    if (
      requestedId
      && (
        requestedKind === 'context_pack'
        || requestedKind === 'evaluation_profile'
        || requestedKind === 'workflow_recipe'
        || requestedKind === 'run_preset'
      )
    ) {
      setSelectedIds((current) => ({
        ...current,
        [requestedKind]: requestedId,
      }));
    }
  }, [searchParams]);

  useEffect(() => {
    const requestedRecipeVersion = searchParams.get('recipe_version');
    if (!requestedRecipeVersion || !catalogQuery.data) {
      return;
    }
    const matched = catalogQuery.data.workflowRecipes.find((item) => item.current_version?.id === requestedRecipeVersion);
    if (!matched) {
      return;
    }
    setKind('workflow_recipe');
    setSelectedIds((current) => ({
      ...current,
      workflow_recipe: matched.id,
    }));
  }, [catalogQuery.data, searchParams]);

  useEffect(() => {
    if (filteredItems.length === 0) {
      return;
    }
    if (selectedId && filteredItems.some((item) => item.id === selectedId)) {
      return;
    }
    setSelectedIds((current) => ({
      ...current,
      [kind]: filteredItems[0].id,
    }));
  }, [filteredItems, kind, selectedId]);

  useEffect(() => {
    setCreateDraft(DEFAULT_DRAFT);
    setCreateError(null);
    setUpdateError(null);
    setVersionError(null);
  }, [kind]);

  const detailQuery = useQuery({
    queryKey: getDetailQueryKey(kind, selectedId),
    enabled: Boolean(selectedId),
    queryFn: async () => {
      if (!selectedId) {
        throw new Error('missing selected asset id');
      }
      if (kind === 'context_pack') {
        const { data } = await api.get<ContextPackDetail>(`/context-packs/${selectedId}`);
        return data as AssetDetail;
      }
      if (kind === 'evaluation_profile') {
        const { data } = await api.get<EvaluationProfileDetail>(`/evaluation-profiles/${selectedId}`);
        return data as AssetDetail;
      }
      if (kind === 'workflow_recipe') {
        const { data } = await api.get<WorkflowRecipeDetail>(`/workflow-recipes/${selectedId}`);
        return data as AssetDetail;
      }
      const { data } = await api.get<RunPresetDetail>(`/run-presets/${selectedId}`);
      return data as AssetDetail;
    },
  });

  const versionsQuery = useQuery({
    queryKey: getVersionsQueryKey(kind, selectedId),
    enabled: Boolean(selectedId) && kind !== 'run_preset',
    queryFn: async () => {
      if (!selectedId) {
        throw new Error('missing selected asset id');
      }
      if (kind === 'context_pack') {
        const { data } = await api.get<{ items: ContextPackVersionDetail[] }>(`/context-packs/${selectedId}/versions`);
        return data.items as AssetVersion[];
      }
      if (kind === 'evaluation_profile') {
        const { data } = await api.get<{ items: EvaluationProfileVersionDetail[] }>(`/evaluation-profiles/${selectedId}/versions`);
        return data.items as AssetVersion[];
      }
      const { data } = await api.get<{ items: WorkflowRecipeVersionDetail[] }>(`/workflow-recipes/${selectedId}/versions`);
      return data.items as AssetVersion[];
    },
  });

  useEffect(() => {
    setUpdateDraft(buildUpdateDraft(kind, detailQuery.data ?? null));
    setVersionDraft({
      ...DEFAULT_DRAFT,
      jsonText: getCurrentJsonText(kind, detailQuery.data ?? null),
      sourceIterationId: kind === 'context_pack'
        ? (detailQuery.data as ContextPackDetail | undefined)?.current_version?.source_iteration_id ?? ''
        : kind === 'workflow_recipe'
          ? (detailQuery.data as WorkflowRecipeDetail | undefined)?.current_version?.source_iteration_id ?? ''
          : '',
    });
  }, [detailQuery.data, kind]);

  const createMutation = useMutation({
    mutationFn: async () => {
      setCreateError(null);
      if (!createDraft.name.trim()) {
        throw new Error('名称不能为空。');
      }
      if (kind === 'context_pack') {
        const payload = parseObjectJson(createDraft.jsonText, 'Payload JSON');
        const { data } = await api.post<ContextPackDetail>('/context-packs', {
          name: createDraft.name.trim(),
          description: createDraft.description.trim() || null,
          tags: splitTags(createDraft.tags),
          payload,
          source_iteration_id: createDraft.sourceIterationId.trim() || null,
          change_summary: createDraft.changeSummary.trim() || null,
        });
        return data;
      }
      if (kind === 'evaluation_profile') {
        const rules = parseObjectJson(createDraft.jsonText, 'Rules JSON');
        const { data } = await api.post<EvaluationProfileDetail>('/evaluation-profiles', {
          name: createDraft.name.trim(),
          description: createDraft.description.trim() || null,
          rules,
          change_summary: createDraft.changeSummary.trim() || null,
        });
        return data;
      }
      if (kind === 'workflow_recipe') {
        const definition = parseObjectJson(createDraft.jsonText, 'Definition JSON');
        const { data } = await api.post<WorkflowRecipeDetail>('/workflow-recipes', {
          name: createDraft.name.trim(),
          description: createDraft.description.trim() || null,
          domain_hint: createDraft.domainHint.trim() || null,
          definition,
          source_iteration_id: createDraft.sourceIterationId.trim() || null,
          change_summary: createDraft.changeSummary.trim() || null,
        });
        return data;
      }
      const definition = parseObjectJson(createDraft.jsonText, 'Definition JSON');
      const { data } = await api.post<RunPresetDetail>('/run-presets', {
        name: createDraft.name.trim(),
        description: createDraft.description.trim() || null,
        definition,
      });
      return data;
    },
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['workflow-asset-catalog'] });
      setSelectedIds((current) => ({
        ...current,
        [kind]: data.id,
      }));
      setCreateDraft(DEFAULT_DRAFT);
    },
    onError: (error) => {
      setCreateError(error instanceof Error ? error.message : '创建失败。');
    },
  });

  const updateMutation = useMutation({
    mutationFn: async () => {
      setUpdateError(null);
      if (!selectedId) {
        throw new Error('请先选择一个资产。');
      }
      if (!updateDraft.name.trim()) {
        throw new Error('名称不能为空。');
      }
      if (kind === 'context_pack') {
        const { data } = await api.patch<ContextPackDetail>(`/context-packs/${selectedId}`, {
          name: updateDraft.name.trim(),
          description: updateDraft.description.trim() || null,
          tags: splitTags(updateDraft.tags),
        });
        return data;
      }
      if (kind === 'evaluation_profile') {
        const { data } = await api.patch<EvaluationProfileDetail>(`/evaluation-profiles/${selectedId}`, {
          name: updateDraft.name.trim(),
          description: updateDraft.description.trim() || null,
        });
        return data;
      }
      if (kind === 'workflow_recipe') {
        const { data } = await api.patch<WorkflowRecipeDetail>(`/workflow-recipes/${selectedId}`, {
          name: updateDraft.name.trim(),
          description: updateDraft.description.trim() || null,
          domain_hint: updateDraft.domainHint.trim() || null,
        });
        return data;
      }
      const definition = parseObjectJson(updateDraft.jsonText, 'Definition JSON');
      const { data } = await api.patch<RunPresetDetail>(`/run-presets/${selectedId}`, {
        name: updateDraft.name.trim(),
        description: updateDraft.description.trim() || null,
        definition,
      });
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['workflow-asset-catalog'] });
      await queryClient.invalidateQueries({ queryKey: getDetailQueryKey(kind, selectedId) });
      if (kind === 'run_preset') {
        await queryClient.invalidateQueries({ queryKey: ['run-preset-detail', selectedId] });
      }
    },
    onError: (error) => {
      setUpdateError(error instanceof Error ? error.message : '更新失败。');
    },
  });

  const versionMutation = useMutation({
    mutationFn: async () => {
      setVersionError(null);
      if (!selectedId) {
        throw new Error('请先选择一个资产。');
      }
      if (kind === 'run_preset') {
        throw new Error('run preset 不支持新建版本。');
      }
      if (kind === 'context_pack') {
        const payload = parseObjectJson(versionDraft.jsonText, 'Payload JSON');
        const { data } = await api.post<ContextPackDetail>(`/context-packs/${selectedId}/versions`, {
          payload,
          source_iteration_id: versionDraft.sourceIterationId.trim() || null,
          change_summary: versionDraft.changeSummary.trim() || null,
        });
        return data;
      }
      if (kind === 'evaluation_profile') {
        const rules = parseObjectJson(versionDraft.jsonText, 'Rules JSON');
        const { data } = await api.post<EvaluationProfileDetail>(`/evaluation-profiles/${selectedId}/versions`, {
          rules,
          change_summary: versionDraft.changeSummary.trim() || null,
        });
        return data;
      }
      const definition = parseObjectJson(versionDraft.jsonText, 'Definition JSON');
      const { data } = await api.post<WorkflowRecipeDetail>(`/workflow-recipes/${selectedId}/versions`, {
        definition,
        source_iteration_id: versionDraft.sourceIterationId.trim() || null,
        change_summary: versionDraft.changeSummary.trim() || null,
      });
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['workflow-asset-catalog'] });
      await queryClient.invalidateQueries({ queryKey: getDetailQueryKey(kind, selectedId) });
      await queryClient.invalidateQueries({ queryKey: getVersionsQueryKey(kind, selectedId) });
      setVersionDraft({
        ...DEFAULT_DRAFT,
        jsonText: getCurrentJsonText(kind, detailQuery.data ?? null),
      });
    },
    onError: (error) => {
      setVersionError(error instanceof Error ? error.message : '创建版本失败。');
    },
  });

  const activeDetail = detailQuery.data ?? null;
  const activeVersions = versionsQuery.data ?? [];
  const versionItems = buildVersionItems(kind, activeVersions);
  const presetRefSummary = kind === 'run_preset' && activeDetail
    ? extractPromptAssetRefSummary((activeDetail as RunPresetDetail).definition)
    : null;
  const runPresetDefaultMode = kind === 'run_preset' && activeDetail
    ? typeof (activeDetail as RunPresetDetail).definition.mode === 'string'
      ? String((activeDetail as RunPresetDetail).definition.mode)
      : 'generate'
    : 'generate';

  return (
    <div className="bp-shell pb-10 pt-4 md:pt-8">
      <section className="bp-surface overflow-hidden px-5 py-6 md:px-8 md:py-8">
        <div className="grid gap-8 xl:grid-cols-[minmax(0,1.06fr)_360px]">
          <div>
            <div className="bp-overline">Workflow Library / V2 Assets</div>
            <h1 className="bp-display mt-4 max-w-4xl text-[var(--bp-ink)]">
              把 recipe、
              <br />
              profile、preset 管起来。
            </h1>
            <p className="bp-subtitle mt-5 max-w-3xl text-[1.02rem]">
              这里不是结果桌面，而是 workflow assets 的管理层。你可以在这里沉淀 context packs、evaluation profiles、workflow recipes 和 run presets，再把它们带回 Prompt Agent Workbench 使用。
            </p>
          </div>

          <div className="grid gap-3">
            <div className="bp-meta-card">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Assets Loaded</div>
              <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">
                {(catalogQuery.data?.contextPacks.length ?? 0)
                  + (catalogQuery.data?.evaluationProfiles.length ?? 0)
                  + (catalogQuery.data?.workflowRecipes.length ?? 0)
                  + (catalogQuery.data?.runPresets.length ?? 0)} items
              </div>
            </div>
            <div className="bp-meta-card">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Current Focus</div>
              <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{KIND_CONFIG[kind].label}</div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        <div className="space-y-6">
          <SectionCard
            title="Asset Types"
            subtitle="先选你现在要管理的资产类型，再进入右侧详情和编辑区。"
          >
            <div className="grid gap-3">
              {(Object.keys(KIND_CONFIG) as WorkflowAssetKind[]).map((itemKind) => {
                const isActive = kind === itemKind;
                const count = getItemsByKind(itemKind, catalogQuery.data).length;

                return (
                  <button
                    key={itemKind}
                    type="button"
                    onClick={() => setKind(itemKind)}
                    className={`rounded-[1.25rem] border px-4 py-4 text-left transition ${
                      isActive
                        ? 'border-[rgba(31,36,45,0.18)] bg-[linear-gradient(135deg,rgba(30,38,52,0.98),rgba(55,65,78,0.98))] text-[#f8f3eb] shadow-[0_18px_42px_-28px_rgba(24,25,27,0.5)]'
                        : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.78)] text-[var(--bp-ink)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)]'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold">{KIND_CONFIG[itemKind].label}</div>
                      <div className={`rounded-full px-2 py-1 text-[11px] font-semibold ${isActive ? 'bg-[rgba(255,255,255,0.14)] text-[#f8f3eb]' : 'bg-[rgba(162,74,53,0.1)] text-[var(--bp-clay)]'}`}>
                        {count}
                      </div>
                    </div>
                    <div className={`mt-2 text-xs leading-6 ${isActive ? 'text-[#d4d8df]' : 'text-[var(--bp-ink-soft)]'}`}>
                      {KIND_CONFIG[itemKind].description}
                    </div>
                  </button>
                );
              })}
            </div>
          </SectionCard>

          <SectionCard
            title="Asset List"
            subtitle={KIND_CONFIG[kind].emptyCopy}
          >
            <label className="mb-4 block space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                <Search className="h-4 w-4 text-[var(--bp-clay)]" />
                搜索当前资产类型
              </div>
              <input
                value={searchText}
                onChange={(event) => setSearchText(event.target.value)}
                className="bp-input h-12"
                placeholder={`在 ${KIND_CONFIG[kind].label} 中按名称或说明搜索`}
              />
            </label>
            {catalogQuery.isLoading && (
              <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
                正在加载 assets...
              </div>
            )}
            {!catalogQuery.isLoading && items.length === 0 && (
              <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm leading-7 text-[var(--bp-ink-soft)]">
                {KIND_CONFIG[kind].emptyCopy}
              </div>
            )}
            {!catalogQuery.isLoading && items.length > 0 && filteredItems.length === 0 && (
              <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm leading-7 text-[var(--bp-ink-soft)]">
                没有匹配“{searchText}”的资产。
              </div>
            )}
            <div className="space-y-3">
              {filteredItems.map((item) => {
                const isActive = selectedId === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setSelectedIds((current) => ({ ...current, [kind]: item.id }))}
                    className={`w-full rounded-[1.2rem] border px-4 py-4 text-left transition ${
                      isActive
                        ? 'border-[rgba(162,74,53,0.2)] bg-[rgba(162,74,53,0.1)]'
                        : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="text-sm font-semibold text-[var(--bp-ink)]">{item.name}</div>
                      <div className="rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.74)] px-3 py-1 text-[11px] font-semibold text-[var(--bp-ink-soft)]">
                        {itemVersionLabel(item)}
                      </div>
                    </div>
                    <div className="mt-2 text-xs leading-6 text-[var(--bp-ink-soft)]">{itemMetaLine(item)}</div>
                  </button>
                );
              })}
            </div>
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            title="Detail Desk"
            subtitle="查看当前资产的主信息、当前版本和时间线。"
          >
            {!selectedId && (
              <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
                先从左侧选择一个资产。
              </div>
            )}

            {selectedId && detailQuery.isLoading && (
              <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
                正在读取详情...
              </div>
            )}

            {activeDetail && (
              <div className="space-y-4">
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="bp-meta-card">
                    <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                      <PackageCheck className="h-4 w-4 text-[var(--bp-clay)]" />
                      {activeDetail.name}
                    </div>
                    <div className="mt-2 text-sm leading-6 text-[var(--bp-ink-soft)]">
                      {activeDetail.description || '暂时还没有描述。'}
                    </div>
                  </div>
                  <div className="bp-meta-card">
                    <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                      <Clock3 className="h-4 w-4 text-[var(--bp-clay)]" />
                      更新时间
                    </div>
                    <div className="mt-2 text-sm leading-6 text-[var(--bp-ink-soft)]">{formatDateTime(activeDetail.updated_at)}</div>
                  </div>
                  <div className="bp-meta-card">
                    <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                      <Layers3 className="h-4 w-4 text-[var(--bp-clay)]" />
                      当前版本
                    </div>
                    <div className="mt-2 text-sm leading-6 text-[var(--bp-ink-soft)]">
                      {'current_version' in activeDetail && activeDetail.current_version
                        ? `v${activeDetail.current_version.version_number}`
                        : '非版本化对象'}
                    </div>
                  </div>
                </div>

                {'tags' in activeDetail && activeDetail.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {activeDetail.tags.map((tag) => (
                      <div
                        key={tag}
                        className="rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.74)] px-3 py-1 text-xs text-[var(--bp-ink-soft)]"
                      >
                        {tag}
                      </div>
                    ))}
                  </div>
                )}

                {'domain_hint' in activeDetail && activeDetail.domain_hint && (
                  <div className="rounded-[1.2rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
                    Domain Hint: <span className="font-semibold text-[var(--bp-ink)]">{activeDetail.domain_hint}</span>
                  </div>
                )}

                {presetRefSummary && (
                  <div className="grid gap-3 md:grid-cols-4">
                    <div className="bp-meta-card">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Prompt Version</div>
                      <div className="mt-2 text-sm leading-6 text-[var(--bp-ink)]">{presetRefSummary.promptAssetVersionId || '—'}</div>
                    </div>
                    <div className="bp-meta-card">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Recipe Ref</div>
                      <div className="mt-2 text-sm leading-6 text-[var(--bp-ink)]">{presetRefSummary.workflowRecipeVersionId || '—'}</div>
                    </div>
                    <div className="bp-meta-card">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Profile Ref</div>
                      <div className="mt-2 text-sm leading-6 text-[var(--bp-ink)]">{presetRefSummary.evaluationProfileVersionId || '—'}</div>
                    </div>
                    <div className="bp-meta-card">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Context Packs</div>
                      <div className="mt-2 text-sm leading-6 text-[var(--bp-ink)]">{presetRefSummary.contextPackCount}</div>
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap gap-2">
                  {kind === 'run_preset' && (
                    <>
                      <Link
                        to={`/prompt-agent?preset=${activeDetail.id}&mode=${runPresetDefaultMode}`}
                        className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                      >
                        在 Workbench 打开
                        <ArrowUpRight className="h-4 w-4" />
                      </Link>
                      <Link
                        to={`/sessions?run_preset_id=${activeDetail.id}`}
                        className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                      >
                        查看相关 Sessions
                        <ArrowUpRight className="h-4 w-4" />
                      </Link>
                    </>
                  )}
                  {kind === 'workflow_recipe' && 'current_version' in activeDetail && activeDetail.current_version && (
                    <Link
                      to={`/sessions?workflow_recipe_version_id=${activeDetail.current_version.id}`}
                      className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                    >
                      查看相关 Sessions
                      <ArrowUpRight className="h-4 w-4" />
                    </Link>
                  )}
                </div>

                <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(249,243,235,0.96))] p-5">
                  <div className="bp-overline">{KIND_CONFIG[kind].jsonLabel}</div>
                  <pre className="mt-4 overflow-x-auto whitespace-pre-wrap break-all text-sm leading-7 text-[var(--bp-ink)]">{getCurrentJsonText(kind, activeDetail)}</pre>
                </div>

                {kind !== 'run_preset' && (
                  <div className="space-y-3">
                    <div className="bp-overline">Version History</div>
                    {versionsQuery.isLoading && (
                      <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
                        正在读取版本列表...
                      </div>
                    )}
                    {versionItems.length === 0 && !versionsQuery.isLoading && (
                      <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
                        暂时还没有版本记录。
                      </div>
                    )}
                    <div className="grid gap-3 md:grid-cols-2">
                      {versionItems.map((version) => (
                        <div key={version.id} className="bp-meta-card">
                          <div className="text-sm font-semibold text-[var(--bp-ink)]">{version.title}</div>
                          <div className="mt-2 text-xs leading-6 text-[var(--bp-ink-soft)]">{version.subtitle}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </SectionCard>

          <div className="grid gap-6 xl:grid-cols-2">
            <SectionCard
              title={KIND_CONFIG[kind].createLabel}
              subtitle="用最小字段先把资产立起来，后续再逐步补齐结构。"
            >
              <div className="space-y-4">
                {createError && (
                  <div className="rounded-[1.2rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700">
                    {createError}
                  </div>
                )}
                <label className="block space-y-2">
                  <div className="bp-overline">Name</div>
                  <input
                    value={createDraft.name}
                    onChange={(event) => setCreateDraft((current) => ({ ...current, name: event.target.value }))}
                    className="bp-input h-12"
                    placeholder="输入资产名称"
                  />
                </label>
                <label className="block space-y-2">
                  <div className="bp-overline">Description</div>
                  <textarea
                    value={createDraft.description}
                    onChange={(event) => setCreateDraft((current) => ({ ...current, description: event.target.value }))}
                    className="bp-input min-h-[110px] text-sm leading-7"
                    placeholder="补充这类资产的用途、边界和适用场景"
                  />
                </label>

                {kind === 'context_pack' && (
                  <label className="block space-y-2">
                    <div className="bp-overline">Tags</div>
                    <input
                      value={createDraft.tags}
                      onChange={(event) => setCreateDraft((current) => ({ ...current, tags: event.target.value }))}
                      className="bp-input h-12"
                      placeholder="tag1, tag2, tag3"
                    />
                  </label>
                )}

                {kind === 'workflow_recipe' && (
                  <label className="block space-y-2">
                    <div className="bp-overline">Domain Hint</div>
                    <input
                      value={createDraft.domainHint}
                      onChange={(event) => setCreateDraft((current) => ({ ...current, domainHint: event.target.value }))}
                      className="bp-input h-12"
                      placeholder="例如：research / code-review / translation"
                    />
                  </label>
                )}

                {kind !== 'run_preset' && (
                  <>
                    <label className="block space-y-2">
                      <div className="bp-overline">Source Iteration Id</div>
                      <input
                        value={createDraft.sourceIterationId}
                        onChange={(event) => setCreateDraft((current) => ({ ...current, sourceIterationId: event.target.value }))}
                        className="bp-input h-12"
                        placeholder="可选，来自某次 prompt iteration"
                      />
                    </label>
                    <label className="block space-y-2">
                      <div className="bp-overline">Change Summary</div>
                      <input
                        value={createDraft.changeSummary}
                        onChange={(event) => setCreateDraft((current) => ({ ...current, changeSummary: event.target.value }))}
                        className="bp-input h-12"
                        placeholder="可选，本次创建的变更摘要"
                      />
                    </label>
                  </>
                )}

                <label className="block space-y-2">
                  <div className="bp-overline">{KIND_CONFIG[kind].jsonLabel}</div>
                  <textarea
                    value={createDraft.jsonText}
                    onChange={(event) => setCreateDraft((current) => ({ ...current, jsonText: event.target.value }))}
                    className="bp-input min-h-[220px] text-sm leading-7 font-mono"
                  />
                </label>

                <Button
                  className="bp-action-primary h-11 w-full justify-center rounded-[1.1rem]"
                  disabled={createMutation.isPending}
                  onClick={() => createMutation.mutate()}
                >
                  {createMutation.isPending ? '创建中...' : KIND_CONFIG[kind].createLabel}
                  {!createMutation.isPending && <FilePlus2 className="ml-2 h-4 w-4" />}
                </Button>
              </div>
            </SectionCard>

            <SectionCard
              title={kind === 'run_preset' ? 'Update Run Preset' : 'Manage Selected Asset'}
              subtitle={kind === 'run_preset' ? 'run preset 直接更新 definition。' : '基础信息和版本内容分开管理，避免混淆。'}
            >
              {!selectedId && (
                <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
                  先选择一个资产，再编辑或新增版本。
                </div>
              )}

              {selectedId && (
                <div className="space-y-5">
                  {updateError && (
                    <div className="rounded-[1.2rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700">
                      {updateError}
                    </div>
                  )}
                  <label className="block space-y-2">
                    <div className="bp-overline">Name</div>
                    <input
                      value={updateDraft.name}
                      onChange={(event) => setUpdateDraft((current) => ({ ...current, name: event.target.value }))}
                      className="bp-input h-12"
                    />
                  </label>
                  <label className="block space-y-2">
                    <div className="bp-overline">Description</div>
                    <textarea
                      value={updateDraft.description}
                      onChange={(event) => setUpdateDraft((current) => ({ ...current, description: event.target.value }))}
                      className="bp-input min-h-[100px] text-sm leading-7"
                    />
                  </label>

                  {kind === 'context_pack' && (
                    <label className="block space-y-2">
                      <div className="bp-overline">Tags</div>
                      <input
                        value={updateDraft.tags}
                        onChange={(event) => setUpdateDraft((current) => ({ ...current, tags: event.target.value }))}
                        className="bp-input h-12"
                      />
                    </label>
                  )}

                  {kind === 'workflow_recipe' && (
                    <label className="block space-y-2">
                      <div className="bp-overline">Domain Hint</div>
                      <input
                        value={updateDraft.domainHint}
                        onChange={(event) => setUpdateDraft((current) => ({ ...current, domainHint: event.target.value }))}
                        className="bp-input h-12"
                      />
                    </label>
                  )}

                  {kind === 'run_preset' && (
                    <label className="block space-y-2">
                      <div className="bp-overline">Definition JSON</div>
                      <textarea
                        value={updateDraft.jsonText}
                        onChange={(event) => setUpdateDraft((current) => ({ ...current, jsonText: event.target.value }))}
                        className="bp-input min-h-[220px] text-sm leading-7 font-mono"
                      />
                    </label>
                  )}

                  <Button
                    variant="ghost"
                    className="h-11 w-full justify-center rounded-[1.1rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.78)] text-[var(--bp-ink-soft)] hover:bg-[rgba(255,255,255,0.92)] hover:text-[var(--bp-ink)]"
                    disabled={updateMutation.isPending}
                    onClick={() => updateMutation.mutate()}
                  >
                    {updateMutation.isPending ? '保存中...' : kind === 'run_preset' ? '更新 Run Preset' : '更新基础信息'}
                  </Button>

                  {kind !== 'run_preset' && (
                    <div className="space-y-4 rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,252,247,0.72)] p-4">
                      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                        <Sparkles className="h-4 w-4 text-[var(--bp-clay)]" />
                        {KIND_CONFIG[kind].versionLabel}
                      </div>

                      {versionError && (
                        <div className="rounded-[1.2rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700">
                          {versionError}
                        </div>
                      )}

                      <label className="block space-y-2">
                        <div className="bp-overline">Change Summary</div>
                        <input
                          value={versionDraft.changeSummary}
                          onChange={(event) => setVersionDraft((current) => ({ ...current, changeSummary: event.target.value }))}
                          className="bp-input h-12"
                          placeholder="本次新版本主要改了什么"
                        />
                      </label>

                      {(kind === 'context_pack' || kind === 'workflow_recipe') && (
                        <label className="block space-y-2">
                          <div className="bp-overline">Source Iteration Id</div>
                          <input
                            value={versionDraft.sourceIterationId}
                            onChange={(event) => setVersionDraft((current) => ({ ...current, sourceIterationId: event.target.value }))}
                            className="bp-input h-12"
                            placeholder="可选，关联某次 prompt iteration"
                          />
                        </label>
                      )}

                      <label className="block space-y-2">
                        <div className="bp-overline">{KIND_CONFIG[kind].jsonLabel}</div>
                        <textarea
                          value={versionDraft.jsonText}
                          onChange={(event) => setVersionDraft((current) => ({ ...current, jsonText: event.target.value }))}
                          className="bp-input min-h-[220px] text-sm leading-7 font-mono"
                        />
                      </label>

                      <Button
                        className="bp-action-primary h-11 w-full justify-center rounded-[1.1rem]"
                        disabled={versionMutation.isPending}
                        onClick={() => versionMutation.mutate()}
                      >
                        {versionMutation.isPending ? '创建版本中...' : KIND_CONFIG[kind].versionLabel}
                        {!versionMutation.isPending && <Boxes className="ml-2 h-4 w-4" />}
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </SectionCard>
          </div>
        </div>
      </section>
    </div>
  );
}

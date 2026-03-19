import { ChevronDown, FilePlus2, Loader2, Play, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type {
  ContextPackSummary,
  EvaluationProfileSummary,
  PromptAgentMode,
  RunPresetDetail,
  RunPresetSummary,
  WorkflowRecipeSummary,
} from '../types';

interface WorkflowAssetsPanelProps {
  mode: PromptAgentMode;
  contextPacks: ContextPackSummary[];
  evaluationProfiles: EvaluationProfileSummary[];
  workflowRecipes: WorkflowRecipeSummary[];
  runPresets: RunPresetSummary[];
  selectedContextPackVersionIds: string[];
  selectedEvaluationProfileVersionId: string | null;
  selectedWorkflowRecipeVersionId: string | null;
  selectedRunPresetId: string | null;
  selectedRunPreset: RunPresetDetail | null;
  launchOverridePreview: string | null;
  savePresetName: string;
  savePresetDescription: string;
  savePresetError?: string | null;
  isCatalogLoading?: boolean;
  catalogError?: string | null;
  isPresetLoading?: boolean;
  isPresetLaunching?: boolean;
  isSavingPreset?: boolean;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
  onToggleContextPack: (versionId: string) => void;
  onSelectEvaluationProfile: (versionId: string | null) => void;
  onSelectWorkflowRecipe: (versionId: string | null) => void;
  onSelectRunPreset: (runPresetId: string | null) => void;
  onChangeSavePreset: (patch: { name?: string; description?: string }) => void;
  onLaunchPreset: (modeBehavior: 'current' | 'preset_default') => void;
  onSaveCurrentAsPreset: () => void;
}

const MODE_LABELS: Record<PromptAgentMode, string> = {
  generate: 'Generate',
  debug: 'Debug',
  evaluate: 'Evaluate',
};

function asString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0);
}

function formatPresetSummary(runPreset: RunPresetDetail | null) {
  if (!runPreset) {
    return {
      workflowRecipeVersionId: null,
      evaluationProfileVersionId: null,
      contextPackVersionIds: [] as string[],
      runSettingsKeys: [] as string[],
    };
  }

  const definition = runPreset.definition ?? {};
  const runSettings = definition.run_settings;
  const runSettingsKeys = runSettings && typeof runSettings === 'object' && !Array.isArray(runSettings)
    ? Object.keys(runSettings as Record<string, unknown>)
    : [];

  return {
    workflowRecipeVersionId: asString(definition.workflow_recipe_version_id),
    evaluationProfileVersionId: asString(definition.evaluation_profile_version_id),
    contextPackVersionIds: asStringArray(definition.context_pack_version_ids),
    runSettingsKeys,
  };
}

function formatLastUsedAt(value: string | null): string {
  if (!value) {
    return '尚未使用';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '最近使用时间未知';
  }
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function WorkflowAssetsPanel({
  mode,
  contextPacks,
  evaluationProfiles,
  workflowRecipes,
  runPresets,
  selectedContextPackVersionIds,
  selectedEvaluationProfileVersionId,
  selectedWorkflowRecipeVersionId,
  selectedRunPresetId,
  selectedRunPreset,
  launchOverridePreview,
  savePresetName,
  savePresetDescription,
  savePresetError = null,
  isCatalogLoading = false,
  catalogError = null,
  isPresetLoading = false,
  isPresetLaunching = false,
  isSavingPreset = false,
  collapsed = false,
  onToggleCollapsed,
  onToggleContextPack,
  onSelectEvaluationProfile,
  onSelectWorkflowRecipe,
  onSelectRunPreset,
  onChangeSavePreset,
  onLaunchPreset,
  onSaveCurrentAsPreset,
}: WorkflowAssetsPanelProps) {
  const selectedContextPackSet = new Set(selectedContextPackVersionIds);
  const presetSummary = formatPresetSummary(selectedRunPreset);
  const hasLaunchablePreset = Boolean(selectedRunPresetId) && !isPresetLoading;
  const selectedAssetsSummary = [
    selectedWorkflowRecipeVersionId ? '1 Recipe' : '0 Recipe',
    selectedEvaluationProfileVersionId ? '1 Profile' : '0 Profile',
    `${selectedContextPackVersionIds.length} Context Packs`,
  ].join(' · ');

  return (
    <section className="bp-surface-soft px-5 py-5">
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div>
          <div className="bp-overline">Workflow Assets</div>
          <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-2xl font-semibold tracking-tight text-[var(--bp-ink)]">把 recipe、profile、context pack 接到这张桌面上</h3>
              <p className="mt-2 max-w-3xl text-sm leading-7 text-[var(--bp-ink-soft)]">
                这里负责给当前 workbench 绑定 V2 workflow assets。你可以继续手动提交 Generate / Debug / Evaluate，也可以直接用 run preset 一键启动。
              </p>
            </div>
            {onToggleCollapsed && (
              <button
                type="button"
                onClick={onToggleCollapsed}
                className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.78)] px-4 py-2 text-sm font-medium text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)] hover:text-[var(--bp-ink)]"
              >
                {collapsed ? '展开 V2 assets' : '收起 V2 assets'}
                <ChevronDown className={`h-4 w-4 transition-transform ${collapsed ? '' : 'rotate-180'}`} />
              </button>
            )}
          </div>
        </div>

        <div className="grid gap-3">
          <div className="bp-meta-card">
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Current Flow</div>
            <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{MODE_LABELS[mode]}</div>
          </div>
          <div className="bp-meta-card">
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Selected Assets</div>
            <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{selectedAssetsSummary}</div>
          </div>
        </div>
      </div>

      {catalogError && (
        <div className="mt-5 rounded-[1.3rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700">
          {catalogError}
        </div>
      )}

      {collapsed && !catalogError && (
        <div className="mt-5 grid gap-3 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)] px-4 py-4">
            <div className="bp-overline">Compact Summary</div>
            <div className="mt-3 flex flex-wrap gap-2">
              <div className="rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-3 py-1 text-xs text-[var(--bp-ink-soft)]">
                {MODE_LABELS[mode]}
              </div>
              <div className="rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-3 py-1 text-xs text-[var(--bp-ink-soft)]">
                {selectedAssetsSummary}
              </div>
              {selectedRunPreset ? (
                <div className="rounded-full border border-[rgba(162,74,53,0.2)] bg-[rgba(162,74,53,0.1)] px-3 py-1 text-xs text-[var(--bp-clay)]">
                  Preset · {selectedRunPreset.name}
                </div>
              ) : null}
            </div>
            <div className="mt-3 text-sm leading-7 text-[var(--bp-ink-soft)]">
              {isCatalogLoading
                ? 'V2 assets 目录正在加载。需要时展开即可继续选择 recipe、profile、context pack 或 run preset。'
                : '首屏先把注意力留给当前工作流。需要更复杂的绑定能力时，再展开这里配置 V2 assets。'}
            </div>
          </div>

          <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)] px-4 py-4">
            <div className="bp-overline">Launch Readiness</div>
            <div className="mt-3 text-sm leading-7 text-[var(--bp-ink-soft)]">
              {selectedRunPreset
                ? '已选 run preset。展开后可以查看绑定详情，并决定按当前工作流还是按 preset 默认模式启动。'
                : '当前仍以手动 workbench 运行为主；如果想一键启动复杂流程，再展开并选择 run preset。'}
            </div>
          </div>
        </div>
      )}

      {collapsed && !catalogError ? null : (
        <>

      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <label className="space-y-2">
          <div className="bp-overline">Workflow Recipe</div>
          <select
            value={selectedWorkflowRecipeVersionId ?? ''}
            onChange={(event) => onSelectWorkflowRecipe(event.target.value || null)}
            disabled={isCatalogLoading}
            className="w-full rounded-[1.15rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-3 text-sm text-[var(--bp-ink)] outline-none transition focus:border-[var(--bp-line-strong)]"
          >
            <option value="">不绑定 workflow recipe</option>
            {workflowRecipes
              .filter((item) => item.current_version)
              .map((item) => (
                <option key={item.id} value={item.current_version?.id ?? ''}>
                  {item.name}
                  {item.current_version ? ` · v${item.current_version.version_number}` : ''}
                </option>
              ))}
          </select>
        </label>

        <label className="space-y-2">
          <div className="bp-overline">Evaluation Profile</div>
          <select
            value={selectedEvaluationProfileVersionId ?? ''}
            onChange={(event) => onSelectEvaluationProfile(event.target.value || null)}
            disabled={isCatalogLoading}
            className="w-full rounded-[1.15rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-3 text-sm text-[var(--bp-ink)] outline-none transition focus:border-[var(--bp-line-strong)]"
          >
            <option value="">不绑定 evaluation profile</option>
            {evaluationProfiles
              .filter((item) => item.current_version)
              .map((item) => (
                <option key={item.id} value={item.current_version?.id ?? ''}>
                  {item.name}
                  {item.current_version ? ` · v${item.current_version.version_number}` : ''}
                </option>
              ))}
          </select>
        </label>
      </div>

      <div className="mt-5">
        <div className="bp-overline">Context Packs</div>
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          {contextPacks
            .filter((item) => item.current_version)
            .map((item) => {
              const versionId = item.current_version?.id ?? '';
              const active = selectedContextPackSet.has(versionId);

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onToggleContextPack(versionId)}
                  className={`rounded-[1.2rem] border px-4 py-3 text-left transition ${
                    active
                      ? 'border-[rgba(162,74,53,0.2)] bg-[rgba(162,74,53,0.1)] text-[var(--bp-clay)]'
                      : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] text-[var(--bp-ink)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)]'
                  }`}
                >
                  <div className="text-sm font-semibold">{item.name}</div>
                  <div className={`mt-1 text-xs leading-5 ${active ? 'text-[var(--bp-clay)]' : 'text-[var(--bp-ink-soft)]'}`}>
                    {item.current_version ? `当前版本 v${item.current_version.version_number}` : '暂无可用版本'}
                    {item.tags.length > 0 ? ` · ${item.tags.slice(0, 3).join(' / ')}` : ''}
                  </div>
                </button>
              );
            })}
          {!isCatalogLoading && contextPacks.filter((item) => item.current_version).length === 0 && (
            <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm leading-7 text-[var(--bp-ink-soft)]">
              还没有可选的 context pack。
            </div>
          )}
          {isCatalogLoading && (
            <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
              正在加载 workflow assets...
            </div>
          )}
        </div>
      </div>

      <div className="mt-6 rounded-[1.6rem] border border-[var(--bp-line)] bg-[rgba(255,252,247,0.78)] p-5">
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_300px] lg:items-start">
          <div>
            <div className="bp-overline">Run Preset</div>
            <div className="mt-3">
              <select
                value={selectedRunPresetId ?? ''}
                onChange={(event) => onSelectRunPreset(event.target.value || null)}
                disabled={isCatalogLoading}
                className="w-full rounded-[1.15rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.88)] px-4 py-3 text-sm text-[var(--bp-ink)] outline-none transition focus:border-[var(--bp-line-strong)]"
              >
                <option value="">不使用 run preset</option>
                {runPresets.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </div>

            {selectedRunPreset && (
              <div className="mt-4 space-y-3">
                <div className="bp-meta-card">
                  <div className="text-sm font-semibold text-[var(--bp-ink)]">{selectedRunPreset.name}</div>
                  <div className="mt-2 text-sm leading-6 text-[var(--bp-ink-soft)]">
                    {selectedRunPreset.description || '这个 preset 暂时还没有描述。'}
                  </div>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="bp-meta-card">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Preset Bindings</div>
                    <div className="mt-2 text-sm leading-6 text-[var(--bp-ink)]">
                      {(presetSummary.workflowRecipeVersionId ? 1 : 0) + (presetSummary.evaluationProfileVersionId ? 1 : 0) + presetSummary.contextPackVersionIds.length}
                      {' 个 workflow refs'}
                    </div>
                  </div>
                  <div className="bp-meta-card">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Last Used</div>
                    <div className="mt-2 text-sm leading-6 text-[var(--bp-ink)]">{formatLastUsedAt(selectedRunPreset.last_used_at)}</div>
                  </div>
                </div>
                {presetSummary.runSettingsKeys.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {presetSummary.runSettingsKeys.slice(0, 6).map((key) => (
                      <div
                        key={key}
                        className="rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.78)] px-3 py-1 text-xs text-[var(--bp-ink-soft)]"
                      >
                        {key}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {selectedRunPresetId && isPresetLoading && (
              <div className="mt-4 flex items-center gap-2 text-sm text-[var(--bp-ink-soft)]">
                <Loader2 className="h-4 w-4 animate-spin text-[var(--bp-clay)]" />
                正在读取 preset 详情...
              </div>
            )}
          </div>

          <div className="bp-surface-soft px-4 py-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
              <Sparkles className="h-4 w-4 text-[var(--bp-clay)]" />
              启动方式
            </div>
            <div className="mt-3 space-y-3 text-sm leading-7 text-[var(--bp-ink-soft)]">
              <div className="bp-meta-card">
                当前工作流：{MODE_LABELS[mode]}
                <br />
                当前选中的 workflow assets 会用于手动提交。
              </div>
              <div className="bp-meta-card">
                如果你点击 run preset，当前表单里的文本会优先作为 override 传进去。
                <br />
                {launchOverridePreview ? `当前已准备 override。` : '当前没有额外 override，会完全按 preset 定义启动。'}
              </div>
            </div>
            <div className="mt-4 grid gap-2">
              <Button
                className="bp-action-primary h-11 justify-center rounded-[1.1rem]"
                disabled={!hasLaunchablePreset || isPresetLaunching}
                onClick={() => onLaunchPreset('current')}
              >
                {isPresetLaunching ? '启动中...' : '按当前工作流启动'}
                {!isPresetLaunching && <Play className="ml-2 h-4 w-4" />}
              </Button>
              <Button
                variant="ghost"
                className="h-11 justify-center rounded-[1.1rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.78)] text-[var(--bp-ink-soft)] hover:bg-[rgba(255,255,255,0.92)] hover:text-[var(--bp-ink)]"
                disabled={!hasLaunchablePreset || isPresetLaunching}
                onClick={() => onLaunchPreset('preset_default')}
              >
                按 preset 默认模式启动
              </Button>
            </div>
          </div>
        </div>

        <div className="mt-5 rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] p-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
            <FilePlus2 className="h-4 w-4 text-[var(--bp-clay)]" />
            Save Current Setup as Run Preset
          </div>
          <div className="mt-2 text-sm leading-7 text-[var(--bp-ink-soft)]">
            把当前工作流模式、表单输入和已选 workflow refs 一起固化成一个新 preset，后面可以直接回到这里一键启动。
          </div>

          {savePresetError && (
            <div className="mt-4 rounded-[1.2rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700">
              {savePresetError}
            </div>
          )}

          <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_220px]">
            <label className="space-y-2">
              <div className="bp-overline">Preset Name</div>
              <input
                value={savePresetName}
                onChange={(event) => onChangeSavePreset({ name: event.target.value })}
                className="bp-input h-12"
                placeholder="例如：代码评审 Debug Run"
              />
            </label>

            <label className="space-y-2">
              <div className="bp-overline">Description</div>
              <input
                value={savePresetDescription}
                onChange={(event) => onChangeSavePreset({ description: event.target.value })}
                className="bp-input h-12"
                placeholder="说明这个 preset 适合什么场景"
              />
            </label>

            <div className="space-y-2">
              <div className="bp-overline">Ready To Save</div>
              <Button
                className="bp-action-primary h-12 w-full justify-center rounded-[1.1rem]"
                disabled={isSavingPreset}
                onClick={onSaveCurrentAsPreset}
              >
                {isSavingPreset ? '保存中...' : '保存为 Run Preset'}
                {!isSavingPreset && <FilePlus2 className="ml-2 h-4 w-4" />}
              </Button>
            </div>
          </div>
        </div>
      </div>
        </>
      )}
    </section>
  );
}

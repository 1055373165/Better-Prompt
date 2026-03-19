import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowUpRight, Clock3, Filter, History, Layers3, PlayCircle, Search, Telescope } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '@/lib/api/client';
import { useWorkflowAssetCatalog } from '@/features/prompt-agent/hooks/use-workflow-asset-catalog';

type PromptSessionRunKind = 'manual_workbench' | 'preset_run' | 'workspace_run' | 'agent_run';
type PromptSessionEntryMode = 'generate' | 'debug' | 'evaluate';
type PromptSessionStatus = 'active' | 'archived';

interface PromptSessionSummary {
  id: string;
  title: string;
  entry_mode: PromptSessionEntryMode;
  status: PromptSessionStatus;
  run_kind: PromptSessionRunKind | null;
  domain_workspace_id: string | null;
  subject_id: string | null;
  agent_monitor_id: string | null;
  trigger_kind: string | null;
  run_preset_id: string | null;
  run_preset_name: string | null;
  workflow_recipe_version_id: string | null;
  workflow_recipe_name: string | null;
  workflow_recipe_version_number: number | null;
  latest_iteration_id: string | null;
  created_at: string;
  updated_at: string;
}

interface PromptSessionDetail extends PromptSessionSummary {
  metadata: Record<string, unknown>;
}

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

function runKindLabel(value: PromptSessionRunKind | null): string {
  if (value === 'preset_run') {
    return 'Preset Run';
  }
  if (value === 'manual_workbench') {
    return 'Manual Workbench';
  }
  if (value === 'workspace_run') {
    return 'Workspace Run';
  }
  if (value === 'agent_run') {
    return 'Agent Run';
  }
  return 'Unknown';
}

function entryModeLabel(value: PromptSessionEntryMode): string {
  return value === 'generate' ? 'Generate' : value === 'debug' ? 'Debug' : 'Evaluate';
}

function findRunPresetLabel(
  session: PromptSessionSummary,
  catalog: ReturnType<typeof useWorkflowAssetCatalog>['data'] | undefined,
): string {
  if (session.run_preset_name) {
    return session.run_preset_name;
  }
  if (!session.run_preset_id || !catalog) {
    return '—';
  }
  const matched = catalog.runPresets.find((item) => item.id === session.run_preset_id);
  return matched?.name ?? session.run_preset_id;
}

function findWorkflowRecipeLabel(
  session: PromptSessionSummary,
  catalog: ReturnType<typeof useWorkflowAssetCatalog>['data'] | undefined,
): string {
  if (session.workflow_recipe_name) {
    const suffix = session.workflow_recipe_version_number ? ` · v${session.workflow_recipe_version_number}` : '';
    return `${session.workflow_recipe_name}${suffix}`;
  }
  if (!session.workflow_recipe_version_id || !catalog) {
    return '—';
  }
  const matched = catalog.workflowRecipes.find((item) => item.current_version?.id === session.workflow_recipe_version_id);
  return matched?.current_version ? `${matched.name} · v${matched.current_version.version_number}` : session.workflow_recipe_version_id;
}

function matchesSessionSearch(
  session: PromptSessionSummary,
  searchText: string,
  catalog: ReturnType<typeof useWorkflowAssetCatalog>['data'] | undefined,
): boolean {
  const normalized = searchText.trim().toLowerCase();
  if (!normalized) {
    return true;
  }
  const fragments = [
    session.title,
    session.id,
    session.latest_iteration_id ?? '',
    session.domain_workspace_id ?? '',
    session.subject_id ?? '',
    session.agent_monitor_id ?? '',
    session.trigger_kind ?? '',
    session.run_preset_name ?? '',
    session.workflow_recipe_name ?? '',
    findRunPresetLabel(session, catalog),
    findWorkflowRecipeLabel(session, catalog),
    runKindLabel(session.run_kind),
    entryModeLabel(session.entry_mode),
  ];
  return fragments.join(' ').toLowerCase().includes(normalized);
}

function buildWorkbenchHref(session: PromptSessionSummary): string {
  const params = new URLSearchParams();
  params.set('mode', session.entry_mode);
  if (session.run_preset_id) {
    params.set('preset', session.run_preset_id);
  }
  if (session.domain_workspace_id) {
    params.set('workspace_id', session.domain_workspace_id);
  }
  if (session.subject_id) {
    params.set('subject_id', session.subject_id);
  }
  return `/prompt-agent?${params.toString()}`;
}

function buildWorkspaceHref(session: PromptSessionSummary): string | null {
  if (!session.domain_workspace_id) {
    return null;
  }
  const params = new URLSearchParams();
  params.set('workspace_id', session.domain_workspace_id);
  if (session.subject_id) {
    params.set('subject_id', session.subject_id);
  }
  return `/workspaces?${params.toString()}`;
}

export default function SessionHistoryPage() {
  const [searchParams] = useSearchParams();
  const catalogQuery = useWorkflowAssetCatalog();
  const [runKind, setRunKind] = useState<PromptSessionRunKind | ''>('');
  const [domainWorkspaceId, setDomainWorkspaceId] = useState('');
  const [subjectId, setSubjectId] = useState('');
  const [runPresetId, setRunPresetId] = useState('');
  const [workflowRecipeVersionId, setWorkflowRecipeVersionId] = useState('');
  const [searchText, setSearchText] = useState('');
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  const sessionsQuery = useQuery({
    queryKey: ['prompt-sessions', runKind, domainWorkspaceId, subjectId, runPresetId, workflowRecipeVersionId],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (runKind) {
        params.run_kind = runKind;
      }
      if (domainWorkspaceId) {
        params.domain_workspace_id = domainWorkspaceId;
      }
      if (subjectId) {
        params.subject_id = subjectId;
      }
      if (runPresetId) {
        params.run_preset_id = runPresetId;
      }
      if (workflowRecipeVersionId) {
        params.workflow_recipe_version_id = workflowRecipeVersionId;
      }
      const { data } = await api.get<{ items: PromptSessionSummary[] }>('/prompt-sessions', { params });
      return data.items;
    },
  });

  useEffect(() => {
    const requestedRunKind = searchParams.get('run_kind');
    setRunKind(
      requestedRunKind === 'manual_workbench'
        || requestedRunKind === 'preset_run'
        || requestedRunKind === 'workspace_run'
        || requestedRunKind === 'agent_run'
        ? requestedRunKind
        : '',
    );
    setDomainWorkspaceId(searchParams.get('domain_workspace_id') ?? '');
    setSubjectId(searchParams.get('subject_id') ?? '');
    setRunPresetId(searchParams.get('run_preset_id') ?? '');
    setWorkflowRecipeVersionId(searchParams.get('workflow_recipe_version_id') ?? '');
    setSearchText(searchParams.get('q') ?? '');
  }, [searchParams]);

  const sessions = sessionsQuery.data ?? [];
  const filteredSessions = sessions.filter((session) => matchesSessionSearch(session, searchText, catalogQuery.data));

  useEffect(() => {
    const firstId = filteredSessions[0]?.id ?? null;
    if (!selectedSessionId || !filteredSessions.some((item) => item.id === selectedSessionId)) {
      setSelectedSessionId(firstId);
    }
  }, [filteredSessions, selectedSessionId]);

  const detailQuery = useQuery({
    queryKey: ['prompt-session-detail', selectedSessionId],
    enabled: Boolean(selectedSessionId),
    queryFn: async () => {
      const { data } = await api.get<PromptSessionDetail>(`/prompt-sessions/${selectedSessionId}`);
      return data;
    },
  });

  const selectedSession = selectedSessionId ? detailQuery.data ?? null : null;
  const selectedWorkspaceHref = selectedSession ? buildWorkspaceHref(selectedSession) : null;

  return (
    <div className="bp-shell pb-10 pt-4 md:pt-8">
      <section className="bp-surface overflow-hidden px-5 py-6 md:px-8 md:py-8">
        <div className="grid gap-8 xl:grid-cols-[minmax(0,1.06fr)_360px]">
          <div>
            <div className="bp-overline">Runs History / Prompt Sessions</div>
            <h1 className="bp-display mt-4 max-w-4xl text-[var(--bp-ink)]">
              把每一次运行，
              <br />
              放回可追溯的时间线。
            </h1>
            <p className="bp-subtitle mt-5 max-w-3xl text-[1.02rem]">
              这里展示 workbench、preset run、workspace run 和 agent run 产生的 prompt sessions。你可以按 run kind、workspace、preset、workflow recipe 过滤，再查看每条 session 的入口模式、最新 iteration、trigger provenance 和 metadata。
            </p>
          </div>

          <div className="grid gap-3">
            <div className="bp-meta-card">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Visible Sessions</div>
              <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{filteredSessions.length}</div>
            </div>
            <div className="bp-meta-card">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Selected Session</div>
              <div className="mt-2 text-sm font-semibold text-[var(--bp-ink)]">{selectedSession?.title || '尚未选择'}</div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
        <section className="bp-surface px-5 py-5 md:px-6">
          <div className="bp-overline">Filters</div>
          <div className="mt-5 space-y-4">
            <label className="block space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                <Filter className="h-4 w-4 text-[var(--bp-clay)]" />
                Run Kind
              </div>
              <select
                value={runKind}
                onChange={(event) => setRunKind(event.target.value as PromptSessionRunKind | '')}
                className="w-full rounded-[1.15rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-3 text-sm text-[var(--bp-ink)] outline-none transition focus:border-[var(--bp-line-strong)]"
              >
                <option value="">全部</option>
                <option value="manual_workbench">Manual Workbench</option>
                <option value="preset_run">Preset Run</option>
                <option value="workspace_run">Workspace Run</option>
                <option value="agent_run">Agent Run</option>
              </select>
            </label>

            <label className="block space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                <Telescope className="h-4 w-4 text-[var(--bp-clay)]" />
                Domain Workspace
              </div>
              <input
                value={domainWorkspaceId}
                onChange={(event) => setDomainWorkspaceId(event.target.value)}
                className="bp-input h-12"
                placeholder="按 workspace id 过滤"
              />
            </label>

            <label className="block space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                <Telescope className="h-4 w-4 text-[var(--bp-clay)]" />
                Subject
              </div>
              <input
                value={subjectId}
                onChange={(event) => setSubjectId(event.target.value)}
                className="bp-input h-12"
                placeholder="按 subject id 过滤"
              />
            </label>

            <label className="block space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                <PlayCircle className="h-4 w-4 text-[var(--bp-clay)]" />
                Run Preset
              </div>
              <select
                value={runPresetId}
                onChange={(event) => setRunPresetId(event.target.value)}
                className="w-full rounded-[1.15rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-3 text-sm text-[var(--bp-ink)] outline-none transition focus:border-[var(--bp-line-strong)]"
              >
                <option value="">全部</option>
                {(catalogQuery.data?.runPresets ?? []).map((preset) => (
                  <option key={preset.id} value={preset.id}>{preset.name}</option>
                ))}
              </select>
            </label>

            <label className="block space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                <Layers3 className="h-4 w-4 text-[var(--bp-clay)]" />
                Workflow Recipe
              </div>
              <select
                value={workflowRecipeVersionId}
                onChange={(event) => setWorkflowRecipeVersionId(event.target.value)}
                className="w-full rounded-[1.15rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-3 text-sm text-[var(--bp-ink)] outline-none transition focus:border-[var(--bp-line-strong)]"
              >
                <option value="">全部</option>
                {(catalogQuery.data?.workflowRecipes ?? [])
                  .filter((recipe) => recipe.current_version)
                  .map((recipe) => (
                    <option key={recipe.id} value={recipe.current_version?.id ?? ''}>
                      {recipe.name}
                      {recipe.current_version ? ` · v${recipe.current_version.version_number}` : ''}
                    </option>
                  ))}
              </select>
            </label>

            <label className="block space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                <Search className="h-4 w-4 text-[var(--bp-clay)]" />
                搜索当前结果
              </div>
              <input
                value={searchText}
                onChange={(event) => setSearchText(event.target.value)}
                className="bp-input h-12"
                placeholder="按 session、workspace、subject、preset、recipe 或 iteration 搜索"
              />
            </label>
          </div>

          <div className="mt-6 border-t border-[var(--bp-line)] pt-5">
            <div className="bp-overline">Session List</div>
            <div className="mt-4 space-y-3">
              {sessionsQuery.isLoading && (
                <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
                  正在加载 session 列表...
                </div>
              )}
              {!sessionsQuery.isLoading && sessions.length === 0 && (
                <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
                  当前筛选条件下还没有 session。
                </div>
              )}
              {!sessionsQuery.isLoading && sessions.length > 0 && filteredSessions.length === 0 && (
                <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
                  没有匹配“{searchText}”的 session。
                </div>
              )}
              {filteredSessions.map((session) => {
                const isActive = session.id === selectedSessionId;
                const presetLabel = findRunPresetLabel(session, catalogQuery.data);
                return (
                  <button
                    key={session.id}
                    type="button"
                    onClick={() => setSelectedSessionId(session.id)}
                    className={`w-full rounded-[1.2rem] border px-4 py-4 text-left transition ${
                      isActive
                        ? 'border-[rgba(162,74,53,0.2)] bg-[rgba(162,74,53,0.1)]'
                        : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="text-sm font-semibold text-[var(--bp-ink)]">{session.title}</div>
                      <div className="rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.74)] px-3 py-1 text-[11px] font-semibold text-[var(--bp-ink-soft)]">
                        {entryModeLabel(session.entry_mode)}
                      </div>
                    </div>
                    <div className="mt-2 text-xs leading-6 text-[var(--bp-ink-soft)]">
                      {runKindLabel(session.run_kind)}
                      {session.trigger_kind ? ` · trigger ${session.trigger_kind}` : ''}
                      {presetLabel !== '—' ? ` · ${presetLabel}` : ''}
                      {session.domain_workspace_id ? ` · workspace ${session.domain_workspace_id}` : ''}
                      {session.subject_id ? ` · subject ${session.subject_id}` : ''}
                      {' · '}
                      {formatDateTime(session.updated_at)}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        <section className="bp-surface px-5 py-5 md:px-6">
          <div className="bp-overline">Session Detail</div>
          {!selectedSessionId && (
            <div className="mt-5 rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
              先从左侧选择一个 session。
            </div>
          )}
          {selectedSessionId && detailQuery.isLoading && (
            <div className="mt-5 rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm text-[var(--bp-ink-soft)]">
              正在加载 session 详情...
            </div>
          )}

          {selectedSession && (
            <div className="mt-5 space-y-5">
              <div className="grid gap-3 md:grid-cols-3">
                <div className="bp-meta-card">
                  <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                    <History className="h-4 w-4 text-[var(--bp-clay)]" />
                    {selectedSession.title}
                  </div>
                  <div className="mt-2 text-sm leading-6 text-[var(--bp-ink-soft)]">
                    {runKindLabel(selectedSession.run_kind)}
                  </div>
                </div>
                <div className="bp-meta-card">
                  <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                    <PlayCircle className="h-4 w-4 text-[var(--bp-clay)]" />
                    Entry Mode
                  </div>
                  <div className="mt-2 text-sm leading-6 text-[var(--bp-ink-soft)]">{entryModeLabel(selectedSession.entry_mode)}</div>
                </div>
                <div className="bp-meta-card">
                  <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                    <Clock3 className="h-4 w-4 text-[var(--bp-clay)]" />
                    Updated At
                  </div>
                  <div className="mt-2 text-sm leading-6 text-[var(--bp-ink-soft)]">{formatDateTime(selectedSession.updated_at)}</div>
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                <div className="bp-meta-card">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Domain Workspace</div>
                  <div className="mt-2 break-all text-sm leading-6 text-[var(--bp-ink)]">{selectedSession.domain_workspace_id || '—'}</div>
                </div>
                <div className="bp-meta-card">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Subject</div>
                  <div className="mt-2 break-all text-sm leading-6 text-[var(--bp-ink)]">{selectedSession.subject_id || '—'}</div>
                </div>
                <div className="bp-meta-card">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Agent Monitor</div>
                  <div className="mt-2 break-all text-sm leading-6 text-[var(--bp-ink)]">{selectedSession.agent_monitor_id || '—'}</div>
                </div>
                <div className="bp-meta-card">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Trigger Kind</div>
                  <div className="mt-2 break-all text-sm leading-6 text-[var(--bp-ink)]">{selectedSession.trigger_kind || '—'}</div>
                </div>
                <div className="bp-meta-card">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Latest Iteration</div>
                  <div className="mt-2 break-all text-sm leading-6 text-[var(--bp-ink)]">{selectedSession.latest_iteration_id || '—'}</div>
                </div>
                <div className="bp-meta-card">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Run Preset</div>
                  <div className="mt-2 text-sm leading-6 text-[var(--bp-ink)]">{findRunPresetLabel(selectedSession, catalogQuery.data)}</div>
                </div>
                <div className="bp-meta-card">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Workflow Recipe</div>
                  <div className="mt-2 text-sm leading-6 text-[var(--bp-ink)]">{findWorkflowRecipeLabel(selectedSession, catalogQuery.data)}</div>
                </div>
                <div className="bp-meta-card">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">Session Status</div>
                  <div className="mt-2 text-sm leading-6 text-[var(--bp-ink)]">{selectedSession.status}</div>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <Link
                  to={buildWorkbenchHref(selectedSession)}
                  className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                >
                  在 Workbench 复现
                  <ArrowUpRight className="h-4 w-4" />
                </Link>
                {selectedWorkspaceHref && (
                  <Link
                    to={selectedWorkspaceHref}
                    className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                  >
                    打开对应 Workspace
                    <ArrowUpRight className="h-4 w-4" />
                  </Link>
                )}
                {selectedSession.run_preset_id && (
                  <Link
                    to={`/library?kind=run_preset&id=${selectedSession.run_preset_id}`}
                    className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                  >
                    打开对应 Preset
                    <ArrowUpRight className="h-4 w-4" />
                  </Link>
                )}
                {selectedSession.workflow_recipe_version_id && (
                  <Link
                    to={`/library?kind=workflow_recipe&recipe_version=${selectedSession.workflow_recipe_version_id}`}
                    className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                  >
                    打开对应 Recipe
                    <ArrowUpRight className="h-4 w-4" />
                  </Link>
                )}
              </div>

              <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(249,243,235,0.96))] p-5">
                <div className="bp-overline">Metadata JSON</div>
                <pre className="mt-4 overflow-x-auto whitespace-pre-wrap break-all text-sm leading-7 text-[var(--bp-ink)]">
                  {JSON.stringify(selectedSession.metadata ?? {}, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </section>
      </section>
    </div>
  );
}

import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowUpRight,
  BookOpenText,
  Boxes,
  FileClock,
  FilePlus2,
  FileText,
  FolderKanban,
  Search,
  Sparkles,
  Users,
} from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '@/lib/api/client';
import type {
  DomainWorkspaceDetail,
  DomainWorkspaceSummary,
  ResearchReportDetail,
  ResearchReportSummary,
  ResearchReportVersionDetail,
  ResearchSourceDetail,
  ResearchSourceSummary,
  WorkspaceSubjectDetail,
  WorkspaceSubjectSummary,
} from '@/features/prompt-agent/types';

interface ListResponse<TItem> {
  items: TItem[];
}

const DEFAULT_WORKSPACE_DRAFT = {
  workspaceType: 'research_workspace',
  name: '',
  description: '',
  configText: '{\n  \n}',
};

const DEFAULT_SUBJECT_DRAFT = {
  subjectType: 'company',
  displayName: '',
  externalKey: '',
  metadataText: '{\n  \n}',
};

const DEFAULT_SOURCE_DRAFT = {
  sourceType: 'article',
  title: '',
  canonicalUri: '',
  sourceTimestamp: '',
  contentText: '{\n  \n}',
};

const DEFAULT_REPORT_DRAFT = {
  reportType: 'research_memo',
  title: '',
  summaryText: '',
  confidenceScore: '',
  sourceSessionId: '',
  sourceIterationId: '',
  contentText: '{\n  \n}',
};

const DEFAULT_VERSION_DRAFT = {
  summaryText: '',
  confidenceScore: '',
  sourceSessionId: '',
  sourceIterationId: '',
  contentText: '{\n  \n}',
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

function parseOptionalNumber(value: string, label: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const parsed = Number(trimmed);
  if (Number.isNaN(parsed)) {
    throw new Error(`${label} 必须是数字。`);
  }
  return parsed;
}

function matchesWorkspaceSearch(item: DomainWorkspaceSummary, searchText: string): boolean {
  const normalized = searchText.trim().toLowerCase();
  if (!normalized) {
    return true;
  }
  return [item.name, item.description ?? '', item.workspace_type, item.status]
    .join(' ')
    .toLowerCase()
    .includes(normalized);
}

function summaryLineForWorkspace(item: DomainWorkspaceSummary): string {
  return [item.workspace_type, item.status, formatDateTime(item.updated_at)].filter(Boolean).join(' · ');
}

function subjectLine(item: WorkspaceSubjectSummary): string {
  return [item.subject_type, item.external_key ?? '', formatDateTime(item.updated_at)].filter(Boolean).join(' · ');
}

function sourceLine(item: ResearchSourceSummary): string {
  return [
    item.source_type,
    item.ingest_status,
    item.title ?? '',
    item.source_timestamp ? formatDateTime(item.source_timestamp) : '',
  ].filter(Boolean).join(' · ');
}

function reportLine(item: ResearchReportSummary): string {
  return [
    item.report_type,
    item.status,
    item.latest_version ? `v${item.latest_version.version_number}` : '无版本',
    formatDateTime(item.updated_at),
  ].filter(Boolean).join(' · ');
}

function extractConfigString(config: Record<string, unknown>, key: string): string | null {
  const value = config[key];
  return typeof value === 'string' && value.trim() ? value : null;
}

function extractConfigStringArray(config: Record<string, unknown>, key: string): string[] {
  const value = config[key];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0);
}

function buildSourceSessionHref({
  workspaceId,
  subjectId,
  sessionId,
  iterationId,
}: {
  workspaceId: string | null;
  subjectId: string | null;
  sessionId: string | null | undefined;
  iterationId: string | null | undefined;
}): string | null {
  if (!workspaceId) {
    return null;
  }
  const searchToken = sessionId?.trim() || iterationId?.trim();
  if (!searchToken) {
    return null;
  }
  const params = new URLSearchParams();
  params.set('domain_workspace_id', workspaceId);
  if (subjectId) {
    params.set('subject_id', subjectId);
  }
  params.set('q', searchToken);
  return `/sessions?${params.toString()}`;
}

function SectionCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
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

function MetaCard({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="bp-meta-card">
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">{label}</div>
      <div className="mt-2 text-sm leading-6 text-[var(--bp-ink)]">{children}</div>
    </div>
  );
}

function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-[1.2rem] border border-dashed border-[var(--bp-line)] px-4 py-4 text-sm leading-7 text-[var(--bp-ink-soft)]">
      {children}
    </div>
  );
}

export default function WorkspaceShellPage() {
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const [workspaceType, setWorkspaceType] = useState('');
  const [searchText, setSearchText] = useState('');
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [subjectSearchText, setSubjectSearchText] = useState('');

  const [workspaceDraft, setWorkspaceDraft] = useState(DEFAULT_WORKSPACE_DRAFT);
  const [subjectDraft, setSubjectDraft] = useState(DEFAULT_SUBJECT_DRAFT);
  const [sourceDraft, setSourceDraft] = useState(DEFAULT_SOURCE_DRAFT);
  const [reportDraft, setReportDraft] = useState(DEFAULT_REPORT_DRAFT);
  const [versionDraft, setVersionDraft] = useState(DEFAULT_VERSION_DRAFT);

  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [subjectError, setSubjectError] = useState<string | null>(null);
  const [sourceError, setSourceError] = useState<string | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);
  const [versionError, setVersionError] = useState<string | null>(null);

  useEffect(() => {
    setWorkspaceType(searchParams.get('workspace_type') ?? '');
    setSearchText(searchParams.get('q') ?? '');
    setSelectedWorkspaceId(searchParams.get('workspace_id'));
    setSelectedSubjectId(searchParams.get('subject_id'));
  }, [searchParams]);

  const workspacesQuery = useQuery({
    queryKey: ['domain-workspaces', workspaceType],
    queryFn: async () => {
      const params: Record<string, string | number> = { page: 1, page_size: 100 };
      if (workspaceType.trim()) {
        params.workspace_type = workspaceType.trim();
      }
      const { data } = await api.get<ListResponse<DomainWorkspaceSummary>>('/domain-workspaces', { params });
      return data.items;
    },
  });

  const workspaces = workspacesQuery.data ?? [];
  const filteredWorkspaces = workspaces.filter((item) => matchesWorkspaceSearch(item, searchText));

  useEffect(() => {
    if (filteredWorkspaces.length === 0) {
      setSelectedWorkspaceId(null);
      return;
    }
    if (selectedWorkspaceId && filteredWorkspaces.some((item) => item.id === selectedWorkspaceId)) {
      return;
    }
    setSelectedWorkspaceId(filteredWorkspaces[0].id);
  }, [filteredWorkspaces, selectedWorkspaceId]);

  const workspaceDetailQuery = useQuery({
    queryKey: ['domain-workspace-detail', selectedWorkspaceId],
    enabled: Boolean(selectedWorkspaceId),
    queryFn: async () => {
      const { data } = await api.get<DomainWorkspaceDetail>(`/domain-workspaces/${selectedWorkspaceId}`);
      return data;
    },
  });

  const subjectsQuery = useQuery({
    queryKey: ['workspace-subjects', selectedWorkspaceId, subjectSearchText],
    enabled: Boolean(selectedWorkspaceId),
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (subjectSearchText.trim()) {
        params.q = subjectSearchText.trim();
      }
      const { data } = await api.get<ListResponse<WorkspaceSubjectDetail>>(
        `/domain-workspaces/${selectedWorkspaceId}/subjects`,
        { params },
      );
      return data.items;
    },
  });

  const subjects = subjectsQuery.data ?? [];

  useEffect(() => {
    if (!selectedWorkspaceId) {
      setSelectedSubjectId(null);
      return;
    }
    if (subjects.length === 0) {
      setSelectedSubjectId(null);
      return;
    }
    if (selectedSubjectId && subjects.some((item) => item.id === selectedSubjectId)) {
      return;
    }
    setSelectedSubjectId(subjects[0].id);
  }, [selectedWorkspaceId, selectedSubjectId, subjects]);

  const sourcesQuery = useQuery({
    queryKey: ['research-sources', selectedWorkspaceId, selectedSubjectId],
    enabled: Boolean(selectedWorkspaceId),
    queryFn: async () => {
      const params: Record<string, string | number> = { page: 1, page_size: 100 };
      if (selectedSubjectId) {
        params.subject_id = selectedSubjectId;
      }
      const { data } = await api.get<ListResponse<ResearchSourceDetail>>(
        `/domain-workspaces/${selectedWorkspaceId}/sources`,
        { params },
      );
      return data.items;
    },
  });

  const reportsQuery = useQuery({
    queryKey: ['research-reports', selectedWorkspaceId, selectedSubjectId],
    enabled: Boolean(selectedWorkspaceId),
    queryFn: async () => {
      const params: Record<string, string | number> = { page: 1, page_size: 100 };
      if (selectedSubjectId) {
        params.subject_id = selectedSubjectId;
      }
      const { data } = await api.get<ListResponse<ResearchReportDetail>>(
        `/domain-workspaces/${selectedWorkspaceId}/reports`,
        { params },
      );
      return data.items;
    },
  });

  const reports = reportsQuery.data ?? [];

  useEffect(() => {
    if (reports.length === 0) {
      setSelectedReportId(null);
      return;
    }
    if (selectedReportId && reports.some((item) => item.id === selectedReportId)) {
      return;
    }
    setSelectedReportId(reports[0].id);
  }, [reports, selectedReportId]);

  const reportDetailQuery = useQuery({
    queryKey: ['research-report-detail', selectedReportId],
    enabled: Boolean(selectedReportId),
    queryFn: async () => {
      const { data } = await api.get<ResearchReportDetail>(`/research-reports/${selectedReportId}`);
      return data;
    },
  });

  const reportVersionsQuery = useQuery({
    queryKey: ['research-report-versions', selectedReportId],
    enabled: Boolean(selectedReportId),
    queryFn: async () => {
      const { data } = await api.get<ListResponse<ResearchReportVersionDetail>>(`/research-reports/${selectedReportId}/versions`);
      return data.items;
    },
  });

  const selectedWorkspace = workspaceDetailQuery.data ?? null;
  const selectedWorkspaceSummary = workspaces.find((item) => item.id === selectedWorkspaceId) ?? null;
  const selectedSubject = subjects.find((item) => item.id === selectedSubjectId) ?? null;
  const selectedReport = reportDetailQuery.data ?? null;
  const reportVersions = reportVersionsQuery.data ?? [];

  const defaultRunPresetId = selectedWorkspace ? extractConfigString(selectedWorkspace.config, 'default_run_preset_id') : null;
  const defaultRecipeVersionId = selectedWorkspace ? extractConfigString(selectedWorkspace.config, 'default_recipe_version_id') : null;
  const defaultContextPackIds = selectedWorkspace ? extractConfigStringArray(selectedWorkspace.config, 'default_context_pack_ids') : [];
  const defaultEvaluationProfileId = selectedWorkspace ? extractConfigString(selectedWorkspace.config, 'default_evaluation_profile_id') : null;
  const latestVersionSessionHref = buildSourceSessionHref({
    workspaceId: selectedWorkspaceId,
    subjectId: selectedSubjectId,
    sessionId: selectedReport?.latest_version?.source_session_id,
    iterationId: selectedReport?.latest_version?.source_iteration_id,
  });

  const workbenchHref = (() => {
    if (!selectedWorkspaceId) {
      return null;
    }
    const params = new URLSearchParams();
    params.set('workspace_id', selectedWorkspaceId);
    if (selectedSubjectId) {
      params.set('subject_id', selectedSubjectId);
    }
    if (selectedWorkspace?.name || selectedWorkspaceSummary?.name) {
      params.set('workspace_name', selectedWorkspace?.name ?? selectedWorkspaceSummary?.name ?? '');
    }
    if (selectedSubject?.display_name) {
      params.set('subject_name', selectedSubject.display_name);
    }
    if (defaultRunPresetId) {
      params.set('preset', defaultRunPresetId);
    }
    return `/prompt-agent?${params.toString()}`;
  })();

  const sessionsHref = (() => {
    if (!selectedWorkspaceId) {
      return null;
    }
    const params = new URLSearchParams();
    params.set('run_kind', 'workspace_run');
    params.set('domain_workspace_id', selectedWorkspaceId);
    if (selectedSubjectId) {
      params.set('subject_id', selectedSubjectId);
    }
    return `/sessions?${params.toString()}`;
  })();

  const createWorkspaceMutation = useMutation({
    mutationFn: async () => {
      setWorkspaceError(null);
      if (!workspaceDraft.workspaceType.trim() || !workspaceDraft.name.trim()) {
        throw new Error('workspace type 和 name 都不能为空。');
      }
      const { data } = await api.post<DomainWorkspaceDetail>('/domain-workspaces', {
        workspace_type: workspaceDraft.workspaceType.trim(),
        name: workspaceDraft.name.trim(),
        description: workspaceDraft.description.trim() || null,
        config: parseObjectJson(workspaceDraft.configText, 'Workspace Config JSON'),
      });
      return data;
    },
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['domain-workspaces'] });
      setSelectedWorkspaceId(data.id);
      setWorkspaceDraft(DEFAULT_WORKSPACE_DRAFT);
      setSelectedSubjectId(null);
      setSelectedReportId(null);
    },
    onError: (error) => {
      setWorkspaceError(error instanceof Error ? error.message : '创建 workspace 失败。');
    },
  });

  const createSubjectMutation = useMutation({
    mutationFn: async () => {
      setSubjectError(null);
      if (!selectedWorkspaceId) {
        throw new Error('先选择一个 workspace。');
      }
      if (!subjectDraft.subjectType.trim() || !subjectDraft.displayName.trim()) {
        throw new Error('subject type 和 display name 不能为空。');
      }
      const { data } = await api.post<WorkspaceSubjectDetail>(
        `/domain-workspaces/${selectedWorkspaceId}/subjects`,
        {
          subject_type: subjectDraft.subjectType.trim(),
          external_key: subjectDraft.externalKey.trim() || null,
          display_name: subjectDraft.displayName.trim(),
          metadata: parseObjectJson(subjectDraft.metadataText, 'Subject Metadata JSON'),
        },
      );
      return data;
    },
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['domain-workspace-detail', selectedWorkspaceId] });
      await queryClient.invalidateQueries({ queryKey: ['workspace-subjects', selectedWorkspaceId] });
      setSelectedSubjectId(data.id);
      setSubjectDraft(DEFAULT_SUBJECT_DRAFT);
    },
    onError: (error) => {
      setSubjectError(error instanceof Error ? error.message : '创建 subject 失败。');
    },
  });

  const createSourceMutation = useMutation({
    mutationFn: async () => {
      setSourceError(null);
      if (!selectedWorkspaceId) {
        throw new Error('先选择一个 workspace。');
      }
      if (!sourceDraft.sourceType.trim()) {
        throw new Error('source type 不能为空。');
      }
      const { data } = await api.post<ResearchSourceDetail>(
        `/domain-workspaces/${selectedWorkspaceId}/sources`,
        {
          subject_id: selectedSubjectId,
          source_type: sourceDraft.sourceType.trim(),
          title: sourceDraft.title.trim() || null,
          canonical_uri: sourceDraft.canonicalUri.trim() || null,
          source_timestamp: sourceDraft.sourceTimestamp.trim() || null,
          content: parseObjectJson(sourceDraft.contentText, 'Source Content JSON'),
        },
      );
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['domain-workspace-detail', selectedWorkspaceId] });
      await queryClient.invalidateQueries({ queryKey: ['research-sources', selectedWorkspaceId] });
      setSourceDraft(DEFAULT_SOURCE_DRAFT);
    },
    onError: (error) => {
      setSourceError(error instanceof Error ? error.message : '创建 source 失败。');
    },
  });

  const createReportMutation = useMutation({
    mutationFn: async () => {
      setReportError(null);
      if (!selectedWorkspaceId) {
        throw new Error('先选择一个 workspace。');
      }
      if (!reportDraft.reportType.trim() || !reportDraft.title.trim()) {
        throw new Error('report type 和 title 不能为空。');
      }
      const { data } = await api.post<ResearchReportDetail>(
        `/domain-workspaces/${selectedWorkspaceId}/reports`,
        {
          subject_id: selectedSubjectId,
          report_type: reportDraft.reportType.trim(),
          title: reportDraft.title.trim(),
          content: parseObjectJson(reportDraft.contentText, 'Report Content JSON'),
          source_session_id: reportDraft.sourceSessionId.trim() || null,
          source_iteration_id: reportDraft.sourceIterationId.trim() || null,
          summary_text: reportDraft.summaryText.trim() || null,
          confidence_score: parseOptionalNumber(reportDraft.confidenceScore, 'Report Confidence'),
        },
      );
      return data;
    },
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['domain-workspace-detail', selectedWorkspaceId] });
      await queryClient.invalidateQueries({ queryKey: ['research-reports', selectedWorkspaceId] });
      await queryClient.invalidateQueries({ queryKey: ['research-report-detail', data.id] });
      await queryClient.invalidateQueries({ queryKey: ['research-report-versions', data.id] });
      setSelectedReportId(data.id);
      setReportDraft(DEFAULT_REPORT_DRAFT);
    },
    onError: (error) => {
      setReportError(error instanceof Error ? error.message : '创建 report 失败。');
    },
  });

  const createVersionMutation = useMutation({
    mutationFn: async () => {
      setVersionError(null);
      if (!selectedReportId) {
        throw new Error('先选择一个 report。');
      }
      const { data } = await api.post<ResearchReportDetail>(
        `/research-reports/${selectedReportId}/versions`,
        {
          content: parseObjectJson(versionDraft.contentText, 'Report Version Content JSON'),
          source_session_id: versionDraft.sourceSessionId.trim() || null,
          source_iteration_id: versionDraft.sourceIterationId.trim() || null,
          summary_text: versionDraft.summaryText.trim() || null,
          confidence_score: parseOptionalNumber(versionDraft.confidenceScore, 'Report Version Confidence'),
        },
      );
      return data;
    },
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['research-reports', selectedWorkspaceId] });
      await queryClient.invalidateQueries({ queryKey: ['research-report-detail', data.id] });
      await queryClient.invalidateQueries({ queryKey: ['research-report-versions', data.id] });
      setVersionDraft(DEFAULT_VERSION_DRAFT);
    },
    onError: (error) => {
      setVersionError(error instanceof Error ? error.message : '创建 report version 失败。');
    },
  });

  return (
    <div className="bp-shell pb-10 pt-4 md:pt-8">
      <section className="bp-surface overflow-hidden px-5 py-6 md:px-8 md:py-8">
        <div className="grid gap-8 xl:grid-cols-[minmax(0,1.04fr)_360px]">
          <div>
            <div className="bp-overline">Domain Workspaces / V3 Shell</div>
            <h1 className="bp-display mt-4 max-w-4xl text-[var(--bp-ink)]">
              把主题、来源、研究结论，
              <br />
              收进一个可运行的工作区。
            </h1>
            <p className="bp-subtitle mt-5 max-w-3xl text-[1.02rem]">
              这里是 V3 的 workspace shell。你可以先建立 domain workspace，再向下收纳 subjects、sources 和 research reports，最后从当前上下文直接跳到 Workbench 或 Sessions。
            </p>
          </div>

          <div className="grid gap-3">
            <MetaCard label="Loaded Workspaces">{filteredWorkspaces.length}</MetaCard>
            <MetaCard label="Current Focus">
              {selectedWorkspace?.name ?? selectedWorkspaceSummary?.name ?? '尚未选择 workspace'}
            </MetaCard>
            <MetaCard label="Current Subject">
              {selectedSubject?.display_name ?? '未选择 subject'}
            </MetaCard>
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        <div className="space-y-6">
          <SectionCard
            title="Workspace Catalog"
            subtitle="先筛到你正在看的 domain workspace，再在右侧展开 subjects、sources 与 reports。"
          >
            <div className="space-y-4">
              <label className="block space-y-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                  <Boxes className="h-4 w-4 text-[var(--bp-clay)]" />
                  Workspace Type
                </div>
                <input
                  value={workspaceType}
                  onChange={(event) => setWorkspaceType(event.target.value)}
                  className="bp-input h-12"
                  placeholder="如 research_workspace / market_map"
                />
              </label>

              <label className="block space-y-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                  <Search className="h-4 w-4 text-[var(--bp-clay)]" />
                  搜索 workspace
                </div>
                <input
                  value={searchText}
                  onChange={(event) => setSearchText(event.target.value)}
                  className="bp-input h-12"
                  placeholder="按名称、说明、类型搜索"
                />
              </label>

              {workspacesQuery.isLoading && <EmptyState>正在加载 workspace 列表...</EmptyState>}
              {!workspacesQuery.isLoading && workspaces.length === 0 && (
                <EmptyState>当前还没有 domain workspace，先在下方创建第一个工作区。</EmptyState>
              )}
              {!workspacesQuery.isLoading && workspaces.length > 0 && filteredWorkspaces.length === 0 && (
                <EmptyState>没有匹配“{searchText}”的 workspace。</EmptyState>
              )}

              <div className="space-y-3">
                {filteredWorkspaces.map((item) => {
                  const isActive = item.id === selectedWorkspaceId;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setSelectedWorkspaceId(item.id)}
                      className={`w-full rounded-[1.2rem] border px-4 py-4 text-left transition ${
                        isActive
                          ? 'border-[rgba(162,74,53,0.2)] bg-[rgba(162,74,53,0.1)]'
                          : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)]'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="text-sm font-semibold text-[var(--bp-ink)]">{item.name}</div>
                        <div className="rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.74)] px-3 py-1 text-[11px] font-semibold text-[var(--bp-ink-soft)]">
                          {item.workspace_type}
                        </div>
                      </div>
                      <div className="mt-2 text-xs leading-6 text-[var(--bp-ink-soft)]">
                        {item.description || summaryLineForWorkspace(item)}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </SectionCard>

          <SectionCard
            title="Create Workspace"
            subtitle="最小字段就能启动一个 workspace；默认 preset / recipe / profile 等 ref 都可以放进 config。"
          >
            <div className="space-y-3">
              <input
                value={workspaceDraft.workspaceType}
                onChange={(event) => setWorkspaceDraft((current) => ({ ...current, workspaceType: event.target.value }))}
                className="bp-input h-12"
                placeholder="workspace type"
              />
              <input
                value={workspaceDraft.name}
                onChange={(event) => setWorkspaceDraft((current) => ({ ...current, name: event.target.value }))}
                className="bp-input h-12"
                placeholder="workspace 名称"
              />
              <textarea
                value={workspaceDraft.description}
                onChange={(event) => setWorkspaceDraft((current) => ({ ...current, description: event.target.value }))}
                className="bp-input min-h-[92px] py-3"
                placeholder="workspace 描述"
              />
              <textarea
                value={workspaceDraft.configText}
                onChange={(event) => setWorkspaceDraft((current) => ({ ...current, configText: event.target.value }))}
                className="bp-input min-h-[190px] py-3 font-mono text-xs"
                placeholder="config JSON"
              />
              {workspaceError && (
                <div className="rounded-[1.2rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700">
                  {workspaceError}
                </div>
              )}
              <button
                type="button"
                onClick={() => createWorkspaceMutation.mutate()}
                disabled={createWorkspaceMutation.isPending}
                className="inline-flex items-center gap-2 rounded-full border border-[rgba(31,36,45,0.18)] bg-[linear-gradient(135deg,rgba(30,38,52,0.98),rgba(55,65,78,0.98))] px-4 py-2.5 text-sm font-semibold text-[#f8f3eb] transition hover:shadow-[0_18px_42px_-28px_rgba(24,25,27,0.5)] disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Sparkles className="h-4 w-4" />
                {createWorkspaceMutation.isPending ? '创建中...' : '创建 Workspace'}
              </button>
            </div>
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            title="Workspace Desk"
            subtitle="当前 workspace 的配置、计数和跳转入口都会集中显示在这里。"
          >
            {!selectedWorkspaceId && <EmptyState>先从左侧选一个 workspace。</EmptyState>}
            {selectedWorkspaceId && workspaceDetailQuery.isLoading && <EmptyState>正在读取 workspace 详情...</EmptyState>}
            {selectedWorkspace && (
              <div className="space-y-5">
                <div className="grid gap-3 md:grid-cols-4">
                  <MetaCard label="Workspace">{selectedWorkspace.name}</MetaCard>
                  <MetaCard label="Subjects">{selectedWorkspace.subject_count}</MetaCard>
                  <MetaCard label="Sources">{selectedWorkspace.source_count}</MetaCard>
                  <MetaCard label="Reports">{selectedWorkspace.report_count}</MetaCard>
                </div>

                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                  <MetaCard label="Default Preset">{defaultRunPresetId || '—'}</MetaCard>
                  <MetaCard label="Default Recipe">{defaultRecipeVersionId || '—'}</MetaCard>
                  <MetaCard label="Default Profile">{defaultEvaluationProfileId || '—'}</MetaCard>
                  <MetaCard label="Context Packs">{defaultContextPackIds.length}</MetaCard>
                </div>

                <div className="flex flex-wrap gap-2">
                  {workbenchHref && (
                    <Link
                      to={workbenchHref}
                      className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                    >
                      在 Workbench 打开当前上下文
                      <ArrowUpRight className="h-4 w-4" />
                    </Link>
                  )}
                  {sessionsHref && (
                    <Link
                      to={sessionsHref}
                      className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                    >
                      查看 Workspace Sessions
                      <ArrowUpRight className="h-4 w-4" />
                    </Link>
                  )}
                  {defaultRunPresetId && (
                    <Link
                      to={`/library?kind=run_preset&id=${defaultRunPresetId}`}
                      className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                    >
                      打开 Default Preset
                      <ArrowUpRight className="h-4 w-4" />
                    </Link>
                  )}
                  {defaultRecipeVersionId && (
                    <Link
                      to={`/library?kind=workflow_recipe&recipe_version=${defaultRecipeVersionId}`}
                      className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                    >
                      打开 Default Recipe
                      <ArrowUpRight className="h-4 w-4" />
                    </Link>
                  )}
                </div>

                <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(249,243,235,0.96))] p-5">
                  <div className="bp-overline">Workspace Config JSON</div>
                  <pre className="mt-4 overflow-x-auto whitespace-pre-wrap break-all text-sm leading-7 text-[var(--bp-ink)]">
                    {formatJson(selectedWorkspace.config)}
                  </pre>
                </div>
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Subjects"
            subtitle="subject 是 workspace 内真正聚焦的研究对象，Workbench 会消费这里选中的 scope。"
          >
            {!selectedWorkspaceId && <EmptyState>先选择一个 workspace，再创建或切换 subject。</EmptyState>}
            {selectedWorkspaceId && (
              <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
                <div>
                  <label className="mb-4 block space-y-2">
                    <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                      <Search className="h-4 w-4 text-[var(--bp-clay)]" />
                      搜索 subject
                    </div>
                    <input
                      value={subjectSearchText}
                      onChange={(event) => setSubjectSearchText(event.target.value)}
                      className="bp-input h-12"
                      placeholder="按名称或 external key 过滤"
                    />
                  </label>
                  {subjectsQuery.isLoading && <EmptyState>正在加载 subjects...</EmptyState>}
                  {!subjectsQuery.isLoading && subjects.length === 0 && (
                    <EmptyState>当前 workspace 还没有 subject，先在右侧创建一个。</EmptyState>
                  )}
                  <div className="space-y-3">
                    {subjects.map((item) => {
                      const isActive = item.id === selectedSubjectId;
                      return (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() => setSelectedSubjectId(item.id)}
                          className={`w-full rounded-[1.2rem] border px-4 py-4 text-left transition ${
                            isActive
                              ? 'border-[rgba(162,74,53,0.2)] bg-[rgba(162,74,53,0.1)]'
                              : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)]'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="text-sm font-semibold text-[var(--bp-ink)]">{item.display_name}</div>
                            <div className="rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.74)] px-3 py-1 text-[11px] font-semibold text-[var(--bp-ink-soft)]">
                              {item.subject_type}
                            </div>
                          </div>
                          <div className="mt-2 text-xs leading-6 text-[var(--bp-ink-soft)]">{subjectLine(item)}</div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="rounded-[1.25rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)] p-4">
                    <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                      <Users className="h-4 w-4 text-[var(--bp-clay)]" />
                      当前 Subject
                    </div>
                    <div className="mt-2 text-sm leading-6 text-[var(--bp-ink-soft)]">
                      {selectedSubject?.display_name || '还没有选中 subject。'}
                    </div>
                  </div>
                  <input
                    value={subjectDraft.subjectType}
                    onChange={(event) => setSubjectDraft((current) => ({ ...current, subjectType: event.target.value }))}
                    className="bp-input h-12"
                    placeholder="subject type"
                  />
                  <input
                    value={subjectDraft.displayName}
                    onChange={(event) => setSubjectDraft((current) => ({ ...current, displayName: event.target.value }))}
                    className="bp-input h-12"
                    placeholder="display name"
                  />
                  <input
                    value={subjectDraft.externalKey}
                    onChange={(event) => setSubjectDraft((current) => ({ ...current, externalKey: event.target.value }))}
                    className="bp-input h-12"
                    placeholder="external key"
                  />
                  <textarea
                    value={subjectDraft.metadataText}
                    onChange={(event) => setSubjectDraft((current) => ({ ...current, metadataText: event.target.value }))}
                    className="bp-input min-h-[170px] py-3 font-mono text-xs"
                    placeholder="metadata JSON"
                  />
                  {subjectError && (
                    <div className="rounded-[1.2rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700">
                      {subjectError}
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={() => createSubjectMutation.mutate()}
                    disabled={createSubjectMutation.isPending || !selectedWorkspaceId}
                    className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2.5 text-sm font-semibold text-[var(--bp-ink)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <FilePlus2 className="h-4 w-4" />
                    {createSubjectMutation.isPending ? '创建中...' : '创建 Subject'}
                  </button>
                </div>
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Sources"
            subtitle="sources 先支持最小写入和回看，默认挂到当前选中的 subject。"
          >
            {!selectedWorkspaceId && <EmptyState>先选择 workspace。</EmptyState>}
            {selectedWorkspaceId && (
              <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
                <div className="space-y-3">
                  {sourcesQuery.isLoading && <EmptyState>正在加载 sources...</EmptyState>}
                  {!sourcesQuery.isLoading && (sourcesQuery.data ?? []).length === 0 && (
                    <EmptyState>当前 scope 下还没有 source，右侧表单可以直接补第一条。</EmptyState>
                  )}
                  {(sourcesQuery.data ?? []).map((item) => (
                    <div
                      key={item.id}
                      className="rounded-[1.2rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] px-4 py-4"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="text-sm font-semibold text-[var(--bp-ink)]">{item.title || item.canonical_uri || item.id}</div>
                        <div className="rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.74)] px-3 py-1 text-[11px] font-semibold text-[var(--bp-ink-soft)]">
                          {item.source_type}
                        </div>
                      </div>
                      <div className="mt-2 text-xs leading-6 text-[var(--bp-ink-soft)]">{sourceLine(item)}</div>
                    </div>
                  ))}
                </div>

                <div className="space-y-3">
                  <div className="rounded-[1.25rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)] p-4 text-sm leading-6 text-[var(--bp-ink-soft)]">
                    当前新 source 会写入
                    {' '}
                    <span className="font-semibold text-[var(--bp-ink)]">{selectedSubject?.display_name || 'workspace 级别'}</span>
                    {' '}
                    scope。
                  </div>
                  <input
                    value={sourceDraft.sourceType}
                    onChange={(event) => setSourceDraft((current) => ({ ...current, sourceType: event.target.value }))}
                    className="bp-input h-12"
                    placeholder="source type"
                  />
                  <input
                    value={sourceDraft.title}
                    onChange={(event) => setSourceDraft((current) => ({ ...current, title: event.target.value }))}
                    className="bp-input h-12"
                    placeholder="title"
                  />
                  <input
                    value={sourceDraft.canonicalUri}
                    onChange={(event) => setSourceDraft((current) => ({ ...current, canonicalUri: event.target.value }))}
                    className="bp-input h-12"
                    placeholder="canonical uri"
                  />
                  <input
                    value={sourceDraft.sourceTimestamp}
                    onChange={(event) => setSourceDraft((current) => ({ ...current, sourceTimestamp: event.target.value }))}
                    className="bp-input h-12"
                    placeholder="source timestamp，如 2026-03-19T09:00:00Z"
                  />
                  <textarea
                    value={sourceDraft.contentText}
                    onChange={(event) => setSourceDraft((current) => ({ ...current, contentText: event.target.value }))}
                    className="bp-input min-h-[170px] py-3 font-mono text-xs"
                    placeholder="content JSON"
                  />
                  {sourceError && (
                    <div className="rounded-[1.2rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700">
                      {sourceError}
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={() => createSourceMutation.mutate()}
                    disabled={createSourceMutation.isPending || !selectedWorkspaceId}
                    className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2.5 text-sm font-semibold text-[var(--bp-ink)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <BookOpenText className="h-4 w-4" />
                    {createSourceMutation.isPending ? '写入中...' : '创建 Source'}
                  </button>
                </div>
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Reports"
            subtitle="report 列表、最新版本和新增版本都集中在这里，方便把研究结果沉淀出来。"
          >
            {!selectedWorkspaceId && <EmptyState>先选择 workspace。</EmptyState>}
            {selectedWorkspaceId && (
              <div className="space-y-6">
                <div className="grid gap-6 xl:grid-cols-[minmax(0,0.86fr)_minmax(0,1fr)]">
                  <div className="space-y-3">
                    {reportsQuery.isLoading && <EmptyState>正在加载 reports...</EmptyState>}
                    {!reportsQuery.isLoading && reports.length === 0 && (
                      <EmptyState>当前 scope 下还没有 report，右侧表单可以直接新建第一版。</EmptyState>
                    )}
                    {reports.map((item) => {
                      const isActive = item.id === selectedReportId;
                      return (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() => setSelectedReportId(item.id)}
                          className={`w-full rounded-[1.2rem] border px-4 py-4 text-left transition ${
                            isActive
                              ? 'border-[rgba(162,74,53,0.2)] bg-[rgba(162,74,53,0.1)]'
                              : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.92)]'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="text-sm font-semibold text-[var(--bp-ink)]">{item.title}</div>
                            <div className="rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.74)] px-3 py-1 text-[11px] font-semibold text-[var(--bp-ink-soft)]">
                              {item.report_type}
                            </div>
                          </div>
                          <div className="mt-2 text-xs leading-6 text-[var(--bp-ink-soft)]">{reportLine(item)}</div>
                        </button>
                      );
                    })}
                  </div>

                  <div className="space-y-4">
                    {!selectedReportId && <EmptyState>从左侧选一个 report，或直接在下方创建新的 report。</EmptyState>}
                    {selectedReportId && reportDetailQuery.isLoading && <EmptyState>正在加载 report 详情...</EmptyState>}
                    {selectedReport && (
                      <>
                        <div className="grid gap-3 md:grid-cols-2">
                          <MetaCard label="Selected Report">{selectedReport.title}</MetaCard>
                          <MetaCard label="Latest Version">
                            {selectedReport.latest_version ? `v${selectedReport.latest_version.version_number}` : '—'}
                          </MetaCard>
                        </div>
                        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                          <MetaCard label="Summary">{selectedReport.latest_version?.summary_text || '—'}</MetaCard>
                          <MetaCard label="Confidence">
                            {selectedReport.latest_version?.confidence_score ?? '—'}
                          </MetaCard>
                          <MetaCard label="Session Ref">{selectedReport.latest_version?.source_session_id || '—'}</MetaCard>
                          <MetaCard label="Iteration Ref">{selectedReport.latest_version?.source_iteration_id || '—'}</MetaCard>
                        </div>
                        {latestVersionSessionHref && (
                          <div className="flex flex-wrap gap-2">
                            <Link
                              to={latestVersionSessionHref}
                              className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2 text-sm text-[var(--bp-ink-soft)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] hover:text-[var(--bp-ink)]"
                            >
                              查看最新版本来源 Session
                              <ArrowUpRight className="h-4 w-4" />
                            </Link>
                          </div>
                        )}
                        <div className="rounded-[1.35rem] border border-[var(--bp-line)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(249,243,235,0.96))] p-5">
                          <div className="bp-overline">Latest Report Content JSON</div>
                          <pre className="mt-4 overflow-x-auto whitespace-pre-wrap break-all text-sm leading-7 text-[var(--bp-ink)]">
                            {formatJson(selectedReport.latest_version?.content ?? {})}
                          </pre>
                        </div>
                        <div className="rounded-[1.25rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)] p-4">
                          <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                            <FileClock className="h-4 w-4 text-[var(--bp-clay)]" />
                            Version Timeline
                          </div>
                          <div className="mt-3 space-y-3">
                            {reportVersionsQuery.isLoading && <div className="text-sm text-[var(--bp-ink-soft)]">正在加载 versions...</div>}
                            {!reportVersionsQuery.isLoading && reportVersions.length === 0 && (
                              <div className="text-sm text-[var(--bp-ink-soft)]">这个 report 还没有 versions。</div>
                            )}
                            {reportVersions.map((version) => {
                              const versionSourceSessionHref = buildSourceSessionHref({
                                workspaceId: selectedWorkspaceId,
                                subjectId: selectedSubjectId,
                                sessionId: version.source_session_id,
                                iterationId: version.source_iteration_id,
                              });

                              return (
                                <div
                                  key={version.id}
                                  className="rounded-[1rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.74)] px-4 py-3"
                                >
                                  <div className="flex items-start justify-between gap-3">
                                    <div className="text-sm font-semibold text-[var(--bp-ink)]">
                                      Version {version.version_number}
                                    </div>
                                    <div className="text-xs text-[var(--bp-ink-soft)]">{formatDateTime(version.created_at)}</div>
                                  </div>
                                  <div className="mt-2 text-xs leading-6 text-[var(--bp-ink-soft)]">
                                    {version.summary_text || '无 summary'}
                                    {version.confidence_score !== null ? ` · confidence ${version.confidence_score}` : ''}
                                  </div>
                                  {versionSourceSessionHref && (
                                    <div className="mt-3">
                                      <Link
                                        to={versionSourceSessionHref}
                                        className="inline-flex items-center gap-2 text-xs font-semibold text-[var(--bp-clay)] transition hover:text-[var(--bp-ink)]"
                                      >
                                        查看 v{version.version_number} 来源 Session
                                        <ArrowUpRight className="h-3.5 w-3.5" />
                                      </Link>
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                <div className="grid gap-6 xl:grid-cols-2">
                  <div className="space-y-3 rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)] p-5">
                    <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                      <FileText className="h-4 w-4 text-[var(--bp-clay)]" />
                      新建 Report
                    </div>
                    <input
                      value={reportDraft.reportType}
                      onChange={(event) => setReportDraft((current) => ({ ...current, reportType: event.target.value }))}
                      className="bp-input h-12"
                      placeholder="report type"
                    />
                    <input
                      value={reportDraft.title}
                      onChange={(event) => setReportDraft((current) => ({ ...current, title: event.target.value }))}
                      className="bp-input h-12"
                      placeholder="title"
                    />
                    <input
                      value={reportDraft.summaryText}
                      onChange={(event) => setReportDraft((current) => ({ ...current, summaryText: event.target.value }))}
                      className="bp-input h-12"
                      placeholder="summary text"
                    />
                    <input
                      value={reportDraft.confidenceScore}
                      onChange={(event) => setReportDraft((current) => ({ ...current, confidenceScore: event.target.value }))}
                      className="bp-input h-12"
                      placeholder="confidence score"
                    />
                    <input
                      value={reportDraft.sourceSessionId}
                      onChange={(event) => setReportDraft((current) => ({ ...current, sourceSessionId: event.target.value }))}
                      className="bp-input h-12"
                      placeholder="source session id"
                    />
                    <input
                      value={reportDraft.sourceIterationId}
                      onChange={(event) => setReportDraft((current) => ({ ...current, sourceIterationId: event.target.value }))}
                      className="bp-input h-12"
                      placeholder="source iteration id"
                    />
                    <textarea
                      value={reportDraft.contentText}
                      onChange={(event) => setReportDraft((current) => ({ ...current, contentText: event.target.value }))}
                      className="bp-input min-h-[190px] py-3 font-mono text-xs"
                      placeholder="report content JSON"
                    />
                    {reportError && (
                      <div className="rounded-[1.2rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700">
                        {reportError}
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={() => createReportMutation.mutate()}
                      disabled={createReportMutation.isPending || !selectedWorkspaceId}
                      className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2.5 text-sm font-semibold text-[var(--bp-ink)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <FolderKanban className="h-4 w-4" />
                      {createReportMutation.isPending ? '创建中...' : '创建 Report'}
                    </button>
                  </div>

                  <div className="space-y-3 rounded-[1.35rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.68)] p-5">
                    <div className="flex items-center gap-2 text-sm font-semibold text-[var(--bp-ink)]">
                      <FileClock className="h-4 w-4 text-[var(--bp-clay)]" />
                      新建 Report Version
                    </div>
                    <div className="rounded-[1.15rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.7)] px-4 py-3 text-sm leading-6 text-[var(--bp-ink-soft)]">
                      当前目标：
                      {' '}
                      <span className="font-semibold text-[var(--bp-ink)]">{selectedReport?.title || '尚未选择 report'}</span>
                    </div>
                    <input
                      value={versionDraft.summaryText}
                      onChange={(event) => setVersionDraft((current) => ({ ...current, summaryText: event.target.value }))}
                      className="bp-input h-12"
                      placeholder="summary text"
                    />
                    <input
                      value={versionDraft.confidenceScore}
                      onChange={(event) => setVersionDraft((current) => ({ ...current, confidenceScore: event.target.value }))}
                      className="bp-input h-12"
                      placeholder="confidence score"
                    />
                    <input
                      value={versionDraft.sourceSessionId}
                      onChange={(event) => setVersionDraft((current) => ({ ...current, sourceSessionId: event.target.value }))}
                      className="bp-input h-12"
                      placeholder="source session id"
                    />
                    <input
                      value={versionDraft.sourceIterationId}
                      onChange={(event) => setVersionDraft((current) => ({ ...current, sourceIterationId: event.target.value }))}
                      className="bp-input h-12"
                      placeholder="source iteration id"
                    />
                    <textarea
                      value={versionDraft.contentText}
                      onChange={(event) => setVersionDraft((current) => ({ ...current, contentText: event.target.value }))}
                      className="bp-input min-h-[190px] py-3 font-mono text-xs"
                      placeholder="report version content JSON"
                    />
                    {versionError && (
                      <div className="rounded-[1.2rem] border border-red-200/80 bg-red-50/90 px-4 py-3 text-sm text-red-700">
                        {versionError}
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={() => createVersionMutation.mutate()}
                      disabled={createVersionMutation.isPending || !selectedReportId}
                      className="inline-flex items-center gap-2 rounded-full border border-[var(--bp-line)] bg-[rgba(255,255,255,0.82)] px-4 py-2.5 text-sm font-semibold text-[var(--bp-ink)] transition hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.94)] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <FilePlus2 className="h-4 w-4" />
                      {createVersionMutation.isPending ? '创建中...' : '创建 Report Version'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </SectionCard>
        </div>
      </section>
    </div>
  );
}

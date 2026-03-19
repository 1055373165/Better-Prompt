import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '@/lib/api/client';
import { renderWithProviders } from '@/test/render';
import WorkspaceShellPage from './index';

vi.mock('@/lib/api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const workspaceList = [
  {
    id: 'workspace-main',
    workspace_type: 'research_workspace',
    name: 'Semiconductor Research Desk',
    description: 'Workspace for chip research',
    status: 'active',
    updated_at: '2026-03-19T08:00:00Z',
  },
];

const workspaceDetail = {
  ...workspaceList[0],
  config: {
    default_run_preset_id: 'preset-research',
    default_recipe_version_id: 'recipe-version-1',
    default_context_pack_ids: ['cp-1', 'cp-2'],
    default_evaluation_profile_id: 'profile-1',
  },
  subject_count: 1,
  source_count: 1,
  report_count: 1,
  created_at: '2026-03-19T08:00:00Z',
  archived_at: null,
};

const subjectList = [
  {
    id: 'subject-nvda',
    workspace_id: 'workspace-main',
    subject_type: 'company',
    external_key: 'NVDA',
    display_name: 'NVIDIA',
    status: 'active',
    updated_at: '2026-03-19T08:00:00Z',
    created_at: '2026-03-19T08:00:00Z',
    metadata: {
      ticker: 'NVDA',
    },
  },
];

const sourceList = [
  {
    id: 'source-1',
    workspace_id: 'workspace-main',
    subject_id: 'subject-nvda',
    source_type: 'article',
    canonical_uri: 'https://example.com/nvda',
    title: 'NVIDIA briefing',
    source_timestamp: '2026-03-19T08:00:00Z',
    ingest_status: 'ready',
    updated_at: '2026-03-19T08:00:00Z',
    created_at: '2026-03-19T08:00:00Z',
    content: {
      summary: 'Quarterly commentary',
    },
  },
];

const reportDetail = {
  id: 'report-1',
  workspace_id: 'workspace-main',
  subject_id: 'subject-nvda',
  report_type: 'research_memo',
  title: 'NVIDIA investment memo',
  status: 'active',
  updated_at: '2026-03-19T08:00:00Z',
  created_at: '2026-03-19T08:00:00Z',
  archived_at: null,
  latest_version: {
    id: 'report-version-2',
    version_number: 2,
    summary_text: 'Raised conviction after channel checks',
    confidence_score: 0.82,
    created_at: '2026-03-19T08:30:00Z',
    source_session_id: 'session-123',
    source_iteration_id: 'iteration-123',
    content: {
      thesis: 'Demand remains strong',
    },
  },
};

const reportVersions = [
  {
    id: 'report-version-1',
    version_number: 1,
    summary_text: 'Initial memo',
    confidence_score: 0.67,
    created_at: '2026-03-19T08:10:00Z',
    source_session_id: 'session-100',
    source_iteration_id: 'iteration-100',
    content: {
      thesis: 'Initial draft',
    },
  },
  reportDetail.latest_version,
];

describe('WorkspaceShellPage', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockImplementation(async (url) => {
      if (url === '/domain-workspaces') {
        return { data: { items: workspaceList } };
      }
      if (url === '/domain-workspaces/workspace-main') {
        return { data: workspaceDetail };
      }
      if (url === '/domain-workspaces/workspace-main/subjects') {
        return { data: { items: subjectList } };
      }
      if (url === '/domain-workspaces/workspace-main/sources') {
        return { data: { items: sourceList } };
      }
      if (url === '/domain-workspaces/workspace-main/reports') {
        return { data: { items: [reportDetail] } };
      }
      if (url === '/research-reports/report-1') {
        return { data: reportDetail };
      }
      if (url === '/research-reports/report-1/versions') {
        return { data: { items: reportVersions } };
      }
      throw new Error(`Unexpected GET ${String(url)}`);
    });
  });

  it('hydrates workspace scope and exposes quick links into workbench and sessions', async () => {
    renderWithProviders(
      <WorkspaceShellPage />,
      '/workspaces?workspace_id=workspace-main&subject_id=subject-nvda',
    );

    await screen.findAllByText('Semiconductor Research Desk');
    await screen.findByText('NVIDIA investment memo');

    const workbenchLink = screen.getByRole('link', { name: /在 Workbench 打开当前上下文/i });
    expect(workbenchLink.getAttribute('href')).toBe(
      '/prompt-agent?workspace_id=workspace-main&subject_id=subject-nvda&workspace_name=Semiconductor+Research+Desk&subject_name=NVIDIA&preset=preset-research',
    );

    const sessionsLink = screen.getByRole('link', { name: /查看 Workspace Sessions/i });
    expect(sessionsLink.getAttribute('href')).toBe(
      '/sessions?run_kind=workspace_run&domain_workspace_id=workspace-main&subject_id=subject-nvda',
    );

    const recipeLink = screen.getByRole('link', { name: /打开 Default Recipe/i });
    expect(recipeLink.getAttribute('href')).toBe('/library?kind=workflow_recipe&recipe_version=recipe-version-1');

    const latestVersionSessionLink = await screen.findByRole('link', { name: /查看最新版本来源 Session/i });
    expect(latestVersionSessionLink.getAttribute('href')).toBe(
      '/sessions?domain_workspace_id=workspace-main&subject_id=subject-nvda&q=session-123',
    );

    const versionTimelineLink = await screen.findByRole('link', { name: /查看 v1 来源 Session/i });
    expect(versionTimelineLink.getAttribute('href')).toBe(
      '/sessions?domain_workspace_id=workspace-main&subject_id=subject-nvda&q=session-100',
    );
  });
});

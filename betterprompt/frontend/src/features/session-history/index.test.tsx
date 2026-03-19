import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '@/lib/api/client';
import { renderWithProviders } from '@/test/render';
import { useWorkflowAssetCatalog } from '@/features/prompt-agent/hooks/use-workflow-asset-catalog';
import SessionHistoryPage from './index';

vi.mock('@/lib/api/client', () => ({
  api: {
    get: vi.fn(),
  },
}));

vi.mock('@/features/prompt-agent/hooks/use-workflow-asset-catalog', () => ({
  useWorkflowAssetCatalog: vi.fn(),
}));

const catalogData = {
  contextPacks: [],
  evaluationProfiles: [],
  workflowRecipes: [
    {
      id: 'recipe-main',
      name: 'Research Flow',
      description: 'Main research recipe',
      domain_hint: 'research',
      current_version: {
        id: 'recipe-version-1',
        version_number: 3,
        change_summary: 'Current production version',
        created_at: '2026-03-18T10:00:00Z',
      },
      updated_at: '2026-03-18T10:00:00Z',
    },
  ],
  runPresets: [
    {
      id: 'preset-alpha',
      name: 'Alpha Preset',
      description: 'Primary preset',
      last_used_at: null,
      updated_at: '2026-03-18T10:00:00Z',
    },
  ],
};

const sessionList = [
  {
    id: 'session-alpha',
    title: 'Alpha Session',
    entry_mode: 'debug',
    status: 'active',
    run_kind: 'workspace_run',
    domain_workspace_id: 'workspace-main',
    subject_id: 'subject-nvda',
    agent_monitor_id: null,
    trigger_kind: null,
    run_preset_id: 'preset-alpha',
    run_preset_name: 'Alpha Preset',
    workflow_recipe_version_id: 'recipe-version-1',
    workflow_recipe_name: 'Research Flow',
    workflow_recipe_version_number: 3,
    latest_iteration_id: 'iteration-alpha',
    created_at: '2026-03-18T10:00:00Z',
    updated_at: '2026-03-18T10:00:00Z',
  },
  {
    id: 'session-beta',
    title: 'Beta Session',
    entry_mode: 'generate',
    status: 'active',
    run_kind: 'manual_workbench',
    domain_workspace_id: null,
    subject_id: null,
    agent_monitor_id: null,
    trigger_kind: null,
    run_preset_id: null,
    run_preset_name: null,
    workflow_recipe_version_id: null,
    workflow_recipe_name: null,
    workflow_recipe_version_number: null,
    latest_iteration_id: 'iteration-beta',
    created_at: '2026-03-18T10:00:00Z',
    updated_at: '2026-03-18T10:00:00Z',
  },
];

describe('SessionHistoryPage', () => {
  beforeEach(() => {
    vi.mocked(useWorkflowAssetCatalog).mockReturnValue({
      data: catalogData,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useWorkflowAssetCatalog>);

    vi.mocked(api.get).mockImplementation(async (url) => {
      if (url === '/prompt-sessions') {
        return { data: { items: sessionList } };
      }
      if (url === '/prompt-sessions/session-alpha') {
        return {
          data: {
            ...sessionList[0],
            metadata: {
              launched_from: 'preset',
            },
          },
        };
      }
      throw new Error(`Unexpected GET ${String(url)}`);
    });
  });

  it('hydrates filters from url params and exposes provenance quick links', async () => {
    renderWithProviders(
      <SessionHistoryPage />,
      '/sessions?run_kind=workspace_run&domain_workspace_id=workspace-main&subject_id=subject-nvda&run_preset_id=preset-alpha&workflow_recipe_version_id=recipe-version-1&q=alpha',
    );

    await screen.findByText('Alpha Session');

    await waitFor(() => {
      const input = screen.getByPlaceholderText('按 session、workspace、subject、preset、recipe 或 iteration 搜索') as HTMLInputElement;
      expect(input.value).toBe('alpha');
    });

    expect(screen.queryByText('Beta Session')).toBeNull();

    const workbenchLink = await screen.findByRole('link', { name: /在 Workbench 复现/i });
    expect(workbenchLink.getAttribute('href')).toBe('/prompt-agent?mode=debug&preset=preset-alpha&workspace_id=workspace-main&subject_id=subject-nvda');

    const workspaceLink = screen.getByRole('link', { name: /打开对应 Workspace/i });
    expect(workspaceLink.getAttribute('href')).toBe('/workspaces?workspace_id=workspace-main&subject_id=subject-nvda');

    const presetLink = screen.getByRole('link', { name: /打开对应 Preset/i });
    expect(presetLink.getAttribute('href')).toBe('/library?kind=run_preset&id=preset-alpha');

    const recipeLink = screen.getByRole('link', { name: /打开对应 Recipe/i });
    expect(recipeLink.getAttribute('href')).toBe('/library?kind=workflow_recipe&recipe_version=recipe-version-1');
  });

  it('hydrates agent_run sessions and shows agent provenance fields', async () => {
    vi.mocked(api.get).mockImplementation(async (url) => {
      if (url === '/prompt-sessions') {
        return {
          data: {
            items: [
              {
                id: 'session-agent',
                title: 'Agent Monitor Session',
                entry_mode: 'debug',
                status: 'active',
                run_kind: 'agent_run',
                domain_workspace_id: 'workspace-main',
                subject_id: 'subject-nvda',
                agent_monitor_id: 'monitor-1',
                trigger_kind: 'manual',
                run_preset_id: 'preset-alpha',
                run_preset_name: 'Alpha Preset',
                workflow_recipe_version_id: 'recipe-version-1',
                workflow_recipe_name: 'Research Flow',
                workflow_recipe_version_number: 3,
                latest_iteration_id: 'iteration-agent',
                created_at: '2026-03-18T10:00:00Z',
                updated_at: '2026-03-18T10:00:00Z',
              },
            ],
          },
        };
      }
      if (url === '/prompt-sessions/session-agent') {
        return {
          data: {
            id: 'session-agent',
            title: 'Agent Monitor Session',
            entry_mode: 'debug',
            status: 'active',
            run_kind: 'agent_run',
            domain_workspace_id: 'workspace-main',
            subject_id: 'subject-nvda',
            agent_monitor_id: 'monitor-1',
            trigger_kind: 'manual',
            run_preset_id: 'preset-alpha',
            run_preset_name: 'Alpha Preset',
            workflow_recipe_version_id: 'recipe-version-1',
            workflow_recipe_name: 'Research Flow',
            workflow_recipe_version_number: 3,
            latest_iteration_id: 'iteration-agent',
            created_at: '2026-03-18T10:00:00Z',
            updated_at: '2026-03-18T10:00:00Z',
            metadata: {
              created_by: 'agent_monitor',
            },
          },
        };
      }
      throw new Error(`Unexpected GET ${String(url)}`);
    });

    renderWithProviders(
      <SessionHistoryPage />,
      '/sessions?run_kind=agent_run&q=manual',
    );

    await screen.findByText('Agent Monitor Session');
    expect(screen.getByText('Agent Run')).toBeTruthy();
    const sessionButton = screen.getByRole('button', { name: /Agent Monitor Session/i });
    expect(sessionButton.textContent).toContain('trigger manual');
    expect(sessionButton.textContent).toContain('Alpha Preset');
    expect(sessionButton.textContent).toContain('workspace workspace-main');
    expect(sessionButton.textContent).toContain('subject subject-nvda');

    await screen.findByText('monitor-1');
    expect(screen.getAllByText('manual').length).toBeGreaterThan(0);

    const workbenchLink = screen.getByRole('link', { name: /在 Workbench 复现/i });
    expect(workbenchLink.getAttribute('href')).toBe('/prompt-agent?mode=debug&preset=preset-alpha&workspace_id=workspace-main&subject_id=subject-nvda');
  });
});

import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '@/lib/api/client';
import { renderWithProviders } from '@/test/render';
import { useWorkflowAssetCatalog } from '@/features/prompt-agent/hooks/use-workflow-asset-catalog';
import WorkflowLibraryPage from './index';

vi.mock('@/lib/api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
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
    {
      id: 'preset-beta',
      name: 'Beta Preset',
      description: 'Secondary preset',
      last_used_at: null,
      updated_at: '2026-03-18T10:00:00Z',
    },
  ],
};

describe('WorkflowLibraryPage', () => {
  beforeEach(() => {
    vi.mocked(useWorkflowAssetCatalog).mockReturnValue({
      data: catalogData,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof useWorkflowAssetCatalog>);

    vi.mocked(api.get).mockImplementation(async (url) => {
      if (url === '/run-presets/preset-alpha') {
        return {
          data: {
            id: 'preset-alpha',
            name: 'Alpha Preset',
            description: 'Primary preset',
            definition: {
              mode: 'debug',
              workflow_recipe_version_id: 'recipe-version-1',
            },
            last_used_at: null,
            created_at: '2026-03-18T10:00:00Z',
            updated_at: '2026-03-18T10:00:00Z',
            archived_at: null,
          },
        };
      }
      throw new Error(`Unexpected GET ${String(url)}`);
    });
  });

  it('hydrates preset selection and quick links from the url', async () => {
    renderWithProviders(<WorkflowLibraryPage />, '/library?kind=run_preset&id=preset-alpha&q=alpha');

    await screen.findByText('Alpha Preset');

    await waitFor(() => {
      const input = screen.getByPlaceholderText('在 Run Presets 中按名称或说明搜索') as HTMLInputElement;
      expect(input.value).toBe('alpha');
    });

    expect(screen.queryByText('Beta Preset')).toBeNull();

    const workbenchLink = await screen.findByRole('link', { name: /在 Workbench 打开/i });
    expect(workbenchLink.getAttribute('href')).toBe('/prompt-agent?preset=preset-alpha&mode=debug');

    const sessionsLink = screen.getByRole('link', { name: /查看相关 Sessions/i });
    expect(sessionsLink.getAttribute('href')).toBe('/sessions?run_preset_id=preset-alpha');
  });
});

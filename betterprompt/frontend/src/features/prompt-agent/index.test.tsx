import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '@/lib/api/client';
import { renderWithProviders } from '@/test/render';
import { usePromptAgentContinue } from './hooks/use-prompt-agent-continue';
import { usePromptAgentDebug } from './hooks/use-prompt-agent-debug';
import { usePromptAgentEvaluate } from './hooks/use-prompt-agent-evaluate';
import { usePromptAgentGenerateStream } from './hooks/use-prompt-agent-generate-stream';
import { useRunPresetDetail } from './hooks/use-run-preset-detail';
import { useRunPresetLaunch } from './hooks/use-run-preset-launch';
import { useWorkflowAssetCatalog } from './hooks/use-workflow-asset-catalog';
import PromptAgentPage from './index';

vi.mock('@/lib/api/client', () => ({
  api: {
    post: vi.fn(),
  },
}));

vi.mock('./hooks/use-workflow-asset-catalog', () => ({
  useWorkflowAssetCatalog: vi.fn(),
}));

vi.mock('./hooks/use-run-preset-detail', () => ({
  useRunPresetDetail: vi.fn(),
}));

vi.mock('./hooks/use-run-preset-launch', () => ({
  useRunPresetLaunch: vi.fn(),
}));

vi.mock('./hooks/use-prompt-agent-generate-stream', () => ({
  usePromptAgentGenerateStream: vi.fn(),
}));

vi.mock('./hooks/use-prompt-agent-debug', () => ({
  usePromptAgentDebug: vi.fn(),
}));

vi.mock('./hooks/use-prompt-agent-evaluate', () => ({
  usePromptAgentEvaluate: vi.fn(),
}));

vi.mock('./hooks/use-prompt-agent-continue', () => ({
  usePromptAgentContinue: vi.fn(),
}));

const catalogData = {
  contextPacks: [
    {
      id: 'context-pack-1',
      name: 'QA smoke context pack',
      description: 'Created during prompt agent test',
      tags: ['qa'],
      current_version: {
        id: 'context-pack-version-1',
        version_number: 1,
        change_summary: null,
        created_at: '2026-03-18T10:00:00Z',
      },
      updated_at: '2026-03-18T10:00:00Z',
    },
  ],
  evaluationProfiles: [
    {
      id: 'evaluation-profile-1',
      name: 'QA smoke evaluation profile',
      description: 'Created during prompt agent test',
      current_version: {
        id: 'evaluation-profile-version-1',
        version_number: 1,
        change_summary: null,
        created_at: '2026-03-18T10:00:00Z',
      },
      updated_at: '2026-03-18T10:00:00Z',
    },
  ],
  workflowRecipes: [
    {
      id: 'workflow-recipe-1',
      name: 'QA smoke workflow recipe',
      description: 'Created during prompt agent test',
      domain_hint: 'qa',
      current_version: {
        id: 'workflow-recipe-version-1',
        version_number: 1,
        change_summary: null,
        created_at: '2026-03-18T10:00:00Z',
      },
      updated_at: '2026-03-18T10:00:00Z',
    },
  ],
  runPresets: [
    {
      id: 'run-preset-1',
      name: 'QA smoke debug preset',
      description: 'Created during prompt agent test',
      last_used_at: null,
      updated_at: '2026-03-18T10:00:00Z',
    },
  ],
};

const runPresetDetail = {
  id: 'run-preset-1',
  name: 'QA smoke debug preset',
  description: 'Created during prompt agent test',
  definition: {
    mode: 'debug',
    context_pack_version_ids: ['context-pack-version-1'],
    evaluation_profile_version_id: 'evaluation-profile-version-1',
    workflow_recipe_version_id: 'workflow-recipe-version-1',
    run_settings: {
      original_task: 'Review runtime behavior',
      current_prompt: 'Please review it.',
      current_output: 'Looks fine.',
      output_preference: 'balanced',
    },
  },
  last_used_at: null,
  created_at: '2026-03-18T10:00:00Z',
  updated_at: '2026-03-18T10:00:00Z',
  archived_at: null,
};

function mockIdleMutation(overrides: Record<string, unknown> = {}) {
  return {
    data: null,
    error: null,
    mutate: vi.fn(),
    reset: vi.fn(),
    variables: null,
    meta: null,
    streamingText: '',
    isStreaming: false,
    isPending: false,
    ...overrides,
  };
}

describe('PromptAgentPage', () => {
  let launchPresetMutate: ReturnType<typeof vi.fn>;
  let debugMutate: ReturnType<typeof vi.fn>;
  let continueMutate: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    launchPresetMutate = vi.fn();
    debugMutate = vi.fn();
    continueMutate = vi.fn();
    vi.mocked(api.post).mockReset();

    vi.mocked(useWorkflowAssetCatalog).mockReturnValue({
      data: catalogData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useWorkflowAssetCatalog>);

    vi.mocked(useRunPresetDetail).mockReturnValue({
      data: runPresetDetail,
      isLoading: false,
    } as unknown as ReturnType<typeof useRunPresetDetail>);

    vi.mocked(useRunPresetLaunch).mockReturnValue({
      isPending: false,
      error: null,
      mutate: launchPresetMutate,
    } as unknown as ReturnType<typeof useRunPresetLaunch>);

    vi.mocked(usePromptAgentGenerateStream).mockReturnValue(mockIdleMutation() as unknown as ReturnType<typeof usePromptAgentGenerateStream>);
    vi.mocked(usePromptAgentDebug).mockReturnValue(
      mockIdleMutation({ mutate: debugMutate }) as unknown as ReturnType<typeof usePromptAgentDebug>,
    );
    vi.mocked(usePromptAgentEvaluate).mockReturnValue(mockIdleMutation() as unknown as ReturnType<typeof usePromptAgentEvaluate>);
    vi.mocked(usePromptAgentContinue).mockReturnValue(
      mockIdleMutation({ mutate: continueMutate }) as unknown as ReturnType<typeof usePromptAgentContinue>,
    );
  });

  it('hydrates workflow refs and workspace scope from deeplink params', async () => {
    renderWithProviders(
      <PromptAgentPage />,
      '/prompt-agent?preset=run-preset-1&mode=debug&workspace_id=workspace-1&subject_id=subject-1&workspace_name=Research%20Desk&subject_name=NVIDIA',
    );

    await waitFor(() => {
      expect(screen.getByText('1 Recipe · 1 Profile · 1 Context Packs')).toBeTruthy();
    });

    expect(screen.getByDisplayValue('QA smoke workflow recipe · v1')).toBeTruthy();
    expect(screen.getByDisplayValue('QA smoke evaluation profile · v1')).toBeTruthy();
    expect(screen.getByDisplayValue('QA smoke debug preset')).toBeTruthy();
    expect(screen.getByText('当前运行绑定了 V3 workspace scope')).toBeTruthy();
    expect(screen.getByText('Research Desk')).toBeTruthy();
    expect(screen.getByText('NVIDIA')).toBeTruthy();
  });

  it('submits debug payloads with inherited workspace scope and workflow refs', async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <PromptAgentPage />,
      '/prompt-agent?preset=run-preset-1&mode=debug&workspace_id=workspace-1&subject_id=subject-1&workspace_name=Research%20Desk&subject_name=NVIDIA',
    );

    await screen.findByDisplayValue('QA smoke workflow recipe · v1');

    await user.type(
      screen.getByPlaceholderText('原始任务，例如：帮我分析一个 SaaS 产品的商业模式。'),
      'Review workspace scoped runtime behavior',
    );
    await user.type(screen.getByPlaceholderText('粘贴当前 Prompt'), 'Please review the runtime setup.');
    await user.type(screen.getByPlaceholderText('粘贴当前输出'), 'Looks acceptable at first glance.');
    await user.click(screen.getByRole('button', { name: '开始调试' }));

    expect(debugMutate).toHaveBeenCalledWith(expect.objectContaining({
      original_task: 'Review workspace scoped runtime behavior',
      current_prompt: 'Please review the runtime setup.',
      current_output: 'Looks acceptable at first glance.',
      domain_workspace_id: 'workspace-1',
      subject_id: 'subject-1',
      context_pack_version_ids: ['context-pack-version-1'],
      evaluation_profile_version_id: 'evaluation-profile-version-1',
      workflow_recipe_version_id: 'workflow-recipe-version-1',
    }));
  });

  it('continues launched preset results with inherited session and provenance refs', async () => {
    const user = userEvent.setup();

    launchPresetMutate.mockImplementation((input, options) => {
      options?.onSuccess?.({
        mode: 'debug',
        iteration: {
          session_id: 'session-launched',
          iteration_id: 'iteration-launched',
        },
        strengths: ['good structure'],
        weaknesses: ['missing prioritization'],
        top_failure_mode: 'no_priority_judgment',
        missing_control_layers: ['key_point_priority'],
        minimal_fix: ['增加关键点优先与判断强度'],
        fixed_prompt: 'Fixed prompt from preset launch',
      });
    });

    renderWithProviders(
      <PromptAgentPage />,
      '/prompt-agent?preset=run-preset-1&mode=debug&workspace_id=workspace-1&subject_id=subject-1&workspace_name=Research%20Desk&subject_name=NVIDIA',
    );

    await screen.findByDisplayValue('QA smoke workflow recipe · v1');
    await user.click(screen.getByRole('button', { name: '按当前工作流启动' }));

    await screen.findByRole('button', { name: '继续修复结构缺口' });
    await user.click(screen.getByRole('button', { name: '继续修复结构缺口' }));

    expect(launchPresetMutate).toHaveBeenCalledWith(expect.objectContaining({
      runPresetId: 'run-preset-1',
      payload: expect.objectContaining({
        domain_workspace_id: 'workspace-1',
        subject_id: 'subject-1',
        mode_override: 'debug',
      }),
    }), expect.any(Object));

    expect(continueMutate).toHaveBeenCalledWith(expect.objectContaining({
      previous_result: 'Fixed prompt from preset launch',
      optimization_goal: '继续修复结构缺口',
      mode: 'debug',
      session_id: 'session-launched',
      parent_iteration_id: 'iteration-launched',
      domain_workspace_id: 'workspace-1',
      subject_id: 'subject-1',
      context_pack_version_ids: ['context-pack-version-1'],
      evaluation_profile_version_id: 'evaluation-profile-version-1',
      workflow_recipe_version_id: 'workflow-recipe-version-1',
      run_preset_id: 'run-preset-1',
    }));
  });
});

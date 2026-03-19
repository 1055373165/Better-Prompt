import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { renderWithProviders } from '@/test/render';
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
import PromptAgentPage from './index';

vi.mock('./hooks/use-prompt-library', () => ({
  usePromptLibrary: vi.fn(),
  usePromptAssetDetail: vi.fn(),
  useCreatePromptCategory: vi.fn(),
  useDeletePromptCategory: vi.fn(),
  useCreatePromptAsset: vi.fn(),
  useUpdatePromptAsset: vi.fn(),
  useDeletePromptAsset: vi.fn(),
  useCreatePromptAssetVersion: vi.fn(),
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

function mockMutation(overrides: Record<string, unknown> = {}) {
  return {
    mutate: vi.fn(),
    mutateAsync: vi.fn(),
    isPending: false,
    error: null,
    data: null,
    reset: vi.fn(),
    ...overrides,
  };
}

const promptLibraryData = {
  categories: [
    {
      id: 'category-market',
      name: '市场研究',
      path: '市场研究',
      depth: 0,
      sort_order: 0,
      children: [],
    },
  ],
  assets: [
    {
      id: 'asset-research',
      category_id: 'category-market',
      name: '行业研究深挖',
      description: '适合从模糊行业问题扩成研究型 Prompt。',
      is_favorite: true,
      tags: ['研究', '商业'],
      current_version: {
        id: 'asset-research-version-3',
        version_number: 3,
        change_summary: null,
        created_at: '2026-03-19T08:00:00Z',
      },
      updated_at: '2026-03-19T08:00:00Z',
    },
  ],
};

const promptAssetDetail = {
  id: 'asset-research',
  category_id: 'category-market',
  name: '行业研究深挖',
  description: '适合从模糊行业问题扩成研究型 Prompt。',
  is_favorite: true,
  tags: ['研究', '商业'],
  current_version: {
    id: 'asset-research-version-3',
    version_number: 3,
    change_summary: null,
    created_at: '2026-03-19T08:00:00Z',
    content: '你是行业研究专家。先判断研究边界，再输出结构化研究 Prompt。',
    source_iteration_id: null,
    source_asset_version_id: null,
  },
  updated_at: '2026-03-19T08:00:00Z',
  created_at: '2026-03-18T08:00:00Z',
  archived_at: null,
};

describe('PromptAgentPage', () => {
  let generateMutate: ReturnType<typeof vi.fn>;
  let debugMutate: ReturnType<typeof vi.fn>;
  let createVersionMutateAsync: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    generateMutate = vi.fn();
    debugMutate = vi.fn();
    createVersionMutateAsync = vi.fn().mockResolvedValue({
      ...promptAssetDetail,
      current_version: {
        ...promptAssetDetail.current_version,
        id: 'asset-research-version-4',
        version_number: 4,
        content: '你是升级后的行业研究专家提示词。',
      },
    });
    window.localStorage.clear();

    vi.mocked(usePromptLibrary).mockReturnValue({
      data: promptLibraryData,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof usePromptLibrary>);

    vi.mocked(usePromptAssetDetail).mockReturnValue({
      data: promptAssetDetail,
      isLoading: false,
      error: null,
    } as unknown as ReturnType<typeof usePromptAssetDetail>);

    vi.mocked(useCreatePromptCategory).mockReturnValue(mockMutation() as unknown as ReturnType<typeof useCreatePromptCategory>);
    vi.mocked(useDeletePromptCategory).mockReturnValue(mockMutation() as unknown as ReturnType<typeof useDeletePromptCategory>);
    vi.mocked(useCreatePromptAsset).mockReturnValue(mockMutation() as unknown as ReturnType<typeof useCreatePromptAsset>);
    vi.mocked(useUpdatePromptAsset).mockReturnValue(mockMutation() as unknown as ReturnType<typeof useUpdatePromptAsset>);
    vi.mocked(useDeletePromptAsset).mockReturnValue(mockMutation() as unknown as ReturnType<typeof useDeletePromptAsset>);
    vi.mocked(useCreatePromptAssetVersion).mockReturnValue(
      mockMutation({ mutateAsync: createVersionMutateAsync }) as unknown as ReturnType<typeof useCreatePromptAssetVersion>,
    );

    vi.mocked(usePromptAgentGenerateStream).mockReturnValue(
      {
        mutate: generateMutate,
        reset: vi.fn(),
        isPending: false,
        isStreaming: false,
        streamingText: '',
        meta: null,
        data: null,
        error: null,
      } as unknown as ReturnType<typeof usePromptAgentGenerateStream>,
    );

    vi.mocked(usePromptAgentDebug).mockReturnValue(
      {
        mutate: debugMutate,
        isPending: false,
        data: null,
        error: null,
      } as unknown as ReturnType<typeof usePromptAgentDebug>,
    );

    vi.mocked(usePromptAgentEvaluate).mockReturnValue(
      {
        mutate: vi.fn(),
        isPending: false,
        data: null,
        error: null,
      } as unknown as ReturnType<typeof usePromptAgentEvaluate>,
    );
  });

  it('uses the selected prompt asset version when submitting generate', async () => {
    const user = userEvent.setup();

    renderWithProviders(<PromptAgentPage />, '/prompt-agent');

    await user.click(screen.getByText('行业研究深挖'));
    await user.type(
      screen.getByPlaceholderText('例如：帮我写一个用于分析竞品官网信息架构的 Prompt。'),
      '帮我研究一家新公司的竞争格局。',
    );
    await user.click(screen.getByRole('button', { name: '开始生成' }));

    expect(generateMutate).toHaveBeenCalledWith(expect.objectContaining({
      user_input: '帮我研究一家新公司的竞争格局。',
      source_asset_version_id: 'asset-research-version-3',
    }));

    expect(generateMutate.mock.calls[0][0].context_notes).toContain('提示词优化模式');
    expect(generateMutate.mock.calls[0][0].context_notes).toContain('行业研究深挖');
  });

  it('switches to research strategy and injects research context notes', async () => {
    const user = userEvent.setup();

    renderWithProviders(<PromptAgentPage />, '/prompt-agent');

    await user.click(screen.getByText('行业研究深挖'));
    await user.click(screen.getByText('研究模式'));
    await user.type(
      screen.getByPlaceholderText('例如：我想研究一个新行业，但目前还不知道应该从哪些角度切入。'),
      '我想研究机器人赛道，但还不知道从哪里开始。',
    );
    await user.click(screen.getByRole('button', { name: '开始生成' }));

    expect(generateMutate).toHaveBeenCalledWith(expect.objectContaining({
      artifact_type: 'conversation_prompt',
      user_input: '我想研究机器人赛道，但还不知道从哪里开始。',
    }));
    expect(generateMutate.mock.calls[0][0].context_notes).toContain('研究模式');
    expect(generateMutate.mock.calls[0][0].context_notes).toContain('研究领域');
  });

  it('can fill the selected prompt into debug mode before submitting', async () => {
    const user = userEvent.setup();

    renderWithProviders(<PromptAgentPage />, '/prompt-agent');

    await user.click(screen.getByText('行业研究深挖'));
    await user.click(screen.getByText('拆开失败现场，给出一版更可靠的修复 Prompt'));
    await user.click(screen.getByRole('button', { name: '填入当前 Prompt' }));

    expect(
      (screen.getByPlaceholderText('把你当前在用的 Prompt 粘贴到这里。') as HTMLTextAreaElement).value,
    ).toBe('你是行业研究专家。先判断研究边界，再输出结构化研究 Prompt。');

    await user.type(
      screen.getByPlaceholderText('例如：帮我写一个多因素框架来分析某个 SaaS 产品的商业模式。'),
      '帮我分析一家 SaaS 公司的商业模式',
    );
    await user.type(
      screen.getByPlaceholderText('把模型当前输出粘贴到这里。'),
      '输出太空泛，没有真正分析关键变量。',
    );
    await user.click(screen.getByRole('button', { name: '开始调试' }));

    expect(debugMutate).toHaveBeenCalledWith(expect.objectContaining({
      original_task: '帮我分析一家 SaaS 公司的商业模式',
      current_prompt: '你是行业研究专家。先判断研究边界，再输出结构化研究 Prompt。',
      current_output: '输出太空泛，没有真正分析关键变量。',
    }));
  });

  it('shows the selected prompt content and persists edited content as a new version', async () => {
    const user = userEvent.setup();

    renderWithProviders(<PromptAgentPage />, '/prompt-agent');

    await user.click(screen.getByText('行业研究深挖'));

    expect(screen.getByText('当前持久化版本预览')).toBeTruthy();
    expect(screen.getByText('你是行业研究专家。先判断研究边界，再输出结构化研究 Prompt。')).toBeTruthy();

    await user.click(screen.getByRole('button', { name: '编辑当前提示词' }));
    expect(screen.getByRole('dialog', { name: '编辑当前提示词' })).toBeTruthy();
    await user.clear(screen.getByPlaceholderText('把这条子提示词的核心结构写在这里。'));
    await user.type(
      screen.getByPlaceholderText('把这条子提示词的核心结构写在这里。'),
      '你是升级后的行业研究专家提示词。',
    );
    await user.click(screen.getByRole('button', { name: '保存修改' }));

    expect(createVersionMutateAsync).toHaveBeenCalledWith(expect.objectContaining({
      assetId: 'asset-research',
      source_asset_version_id: 'asset-research-version-3',
      content: '你是升级后的行业研究专家提示词。',
    }));
  });
});

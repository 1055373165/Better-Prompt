import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type {
  PromptAssetDetail,
  PromptAssetSummary,
  PromptCategoryTreeItem,
} from '../types';

interface PromptLibraryResponse {
  categories: PromptCategoryTreeItem[];
  assets: PromptAssetSummary[];
}

export function usePromptLibrary() {
  return useQuery({
    queryKey: ['prompt-library'],
    queryFn: async () => {
      const [categoriesResponse, assetsResponse] = await Promise.all([
        api.get<{ items: PromptCategoryTreeItem[] }>('/prompt-categories/tree'),
        api.get<{ items: PromptAssetSummary[] }>('/prompt-assets', {
          params: { page: 1, page_size: 200 },
        }),
      ]);

      return {
        categories: categoriesResponse.data.items,
        assets: assetsResponse.data.items,
      } satisfies PromptLibraryResponse;
    },
  });
}

export function usePromptAssetDetail(assetId: string | null) {
  return useQuery({
    queryKey: ['prompt-asset-detail', assetId],
    enabled: Boolean(assetId),
    queryFn: async () => {
      const { data } = await api.get<PromptAssetDetail>(`/prompt-assets/${assetId}`);
      return data;
    },
  });
}

export function useCreatePromptCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { name: string; parent_id?: string | null; sort_order?: number }) => {
      const { data } = await api.post<PromptCategoryTreeItem>('/prompt-categories', payload);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['prompt-library'] });
    },
  });
}

export function useUpdatePromptCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { categoryId: string; name?: string; parent_id?: string | null; sort_order?: number }) => {
      const { categoryId, ...body } = payload;
      const { data } = await api.patch<PromptCategoryTreeItem>(`/prompt-categories/${categoryId}`, body);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['prompt-library'] });
    },
  });
}

export function useDeletePromptCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (categoryId: string) => {
      await api.delete(`/prompt-categories/${categoryId}`);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['prompt-library'] });
    },
  });
}

export function useCreatePromptAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      category_id?: string | null;
      name: string;
      description?: string | null;
      content: string;
      tags?: string[];
      source_iteration_id?: string | null;
      change_summary?: string | null;
    }) => {
      const { data } = await api.post<PromptAssetDetail>('/prompt-assets', payload);
      return data;
    },
    onSuccess: async (data) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['prompt-library'] }),
        queryClient.invalidateQueries({ queryKey: ['prompt-asset-detail', data.id] }),
      ]);
    },
  });
}

export function useUpdatePromptAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      assetId: string;
      category_id?: string | null;
      name?: string;
      description?: string | null;
      is_favorite?: boolean;
      tags?: string[];
      archived_at?: string | null;
    }) => {
      const { assetId, ...body } = payload;
      const { data } = await api.patch<PromptAssetDetail>(`/prompt-assets/${assetId}`, body);
      return data;
    },
    onSuccess: async (data) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['prompt-library'] }),
        queryClient.invalidateQueries({ queryKey: ['prompt-asset-detail', data.id] }),
      ]);
    },
  });
}

export function useDeletePromptAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (assetId: string) => {
      await api.delete(`/prompt-assets/${assetId}`);
    },
    onSuccess: async (_, assetId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['prompt-library'] }),
        queryClient.removeQueries({ queryKey: ['prompt-asset-detail', assetId] }),
      ]);
    },
  });
}

export function useCreatePromptAssetVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      assetId: string;
      content: string;
      source_iteration_id?: string | null;
      source_asset_version_id?: string | null;
      change_summary?: string | null;
    }) => {
      const { assetId, ...body } = payload;
      const { data } = await api.post<PromptAssetDetail>(`/prompt-assets/${assetId}/versions`, body);
      return data;
    },
    onSuccess: async (data) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['prompt-library'] }),
        queryClient.invalidateQueries({ queryKey: ['prompt-asset-detail', data.id] }),
      ]);
    },
  });
}

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type {
  ContextPackSummary,
  EvaluationProfileSummary,
  RunPresetSummary,
  WorkflowRecipeSummary,
} from '../types';

interface ListResponse<TItem> {
  items: TItem[];
}

export function useWorkflowAssetCatalog() {
  return useQuery({
    queryKey: ['workflow-asset-catalog'],
    queryFn: async () => {
      const [contextPacksResponse, evaluationProfilesResponse, workflowRecipesResponse, runPresetsResponse] = await Promise.all([
        api.get<ListResponse<ContextPackSummary>>('/context-packs', { params: { page: 1, page_size: 100 } }),
        api.get<ListResponse<EvaluationProfileSummary>>('/evaluation-profiles', { params: { page: 1, page_size: 100 } }),
        api.get<ListResponse<WorkflowRecipeSummary>>('/workflow-recipes', { params: { page: 1, page_size: 100 } }),
        api.get<ListResponse<RunPresetSummary>>('/run-presets', { params: { page: 1, page_size: 100 } }),
      ]);

      return {
        contextPacks: contextPacksResponse.data.items,
        evaluationProfiles: evaluationProfilesResponse.data.items,
        workflowRecipes: workflowRecipesResponse.data.items,
        runPresets: runPresetsResponse.data.items,
      };
    },
    staleTime: 30_000,
  });
}

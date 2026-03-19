import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { EvaluatePromptResponse } from '../types';

export function usePromptAgentEvaluate() {
  return useMutation({
    mutationFn: async (payload: {
      target_text: string;
      target_type: 'prompt' | 'output';
      session_id?: string;
      domain_workspace_id?: string;
      subject_id?: string;
      context_pack_version_ids?: string[];
      evaluation_profile_version_id?: string | null;
      workflow_recipe_version_id?: string | null;
      run_preset_id?: string | null;
    }) => {
      const { data } = await api.post<EvaluatePromptResponse>('/prompt-agent/evaluate', payload);
      return data;
    },
  });
}

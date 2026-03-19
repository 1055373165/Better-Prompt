import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { DebugPromptResponse } from '../types';

export function usePromptAgentDebug() {
  return useMutation({
    mutationFn: async (payload: {
      original_task: string;
      current_prompt: string;
      current_output: string;
      output_preference?: 'balanced' | 'depth' | 'execution' | 'natural';
      session_id?: string;
      domain_workspace_id?: string;
      subject_id?: string;
      context_pack_version_ids?: string[];
      evaluation_profile_version_id?: string | null;
      workflow_recipe_version_id?: string | null;
      run_preset_id?: string | null;
    }) => {
      const { data } = await api.post<DebugPromptResponse>('/prompt-agent/debug', payload);
      return data;
    },
  });
}

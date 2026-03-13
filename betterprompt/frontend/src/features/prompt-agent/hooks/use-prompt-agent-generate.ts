import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { GeneratePromptResponse, PromptArtifactType } from '../types';

export function usePromptAgentGenerate() {
  return useMutation({
    mutationFn: async (payload: {
      user_input: string;
      show_diagnosis?: boolean;
      output_preference?: 'balanced' | 'depth' | 'execution' | 'natural';
      artifact_type?: PromptArtifactType;
      prompt_only?: boolean;
      context_notes?: string;
    }) => {
      const { data } = await api.post<GeneratePromptResponse>('/prompt-agent/generate', payload);
      return data;
    },
  });
}

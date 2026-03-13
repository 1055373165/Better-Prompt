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
    }) => {
      const { data } = await api.post<DebugPromptResponse>('/prompt-agent/debug', payload);
      return data;
    },
  });
}

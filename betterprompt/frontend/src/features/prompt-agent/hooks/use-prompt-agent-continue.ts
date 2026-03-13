import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { ContinuePromptResponse } from '../types';

export function usePromptAgentContinue() {
  return useMutation({
    mutationFn: async (payload: {
      previous_result: string;
      optimization_goal: string;
      mode: 'generate' | 'debug' | 'evaluate';
    }) => {
      const { data } = await api.post<ContinuePromptResponse>('/prompt-agent/continue', payload);
      return data;
    },
  });
}

import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { EvaluatePromptResponse } from '../types';

export function usePromptAgentEvaluate() {
  return useMutation({
    mutationFn: async (payload: {
      target_text: string;
      target_type: 'prompt' | 'output';
    }) => {
      const { data } = await api.post<EvaluatePromptResponse>('/prompt-agent/evaluate', payload);
      return data;
    },
  });
}

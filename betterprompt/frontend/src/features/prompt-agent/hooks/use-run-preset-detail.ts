import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { RunPresetDetail } from '../types';

export function useRunPresetDetail(runPresetId: string | null) {
  return useQuery({
    queryKey: ['run-preset-detail', runPresetId],
    queryFn: async () => {
      const { data } = await api.get<RunPresetDetail>(`/run-presets/${runPresetId}`);
      return data;
    },
    enabled: Boolean(runPresetId),
    staleTime: 30_000,
  });
}

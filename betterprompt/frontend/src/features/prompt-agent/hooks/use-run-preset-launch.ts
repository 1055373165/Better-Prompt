import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { RunPresetLaunchResponse } from '../types';

interface RunPresetLaunchPayload {
  runPresetId: string;
  payload: {
    session_id?: string;
    parent_iteration_id?: string;
    domain_workspace_id?: string;
    subject_id?: string;
    mode_override?: 'generate' | 'debug' | 'evaluate' | 'continue';
    user_input_override?: string;
    run_settings_override?: Record<string, unknown>;
  };
}

export function useRunPresetLaunch() {
  return useMutation({
    mutationFn: async ({ runPresetId, payload }: RunPresetLaunchPayload) => {
      const { data } = await api.post<RunPresetLaunchResponse>(`/run-presets/${runPresetId}/launch`, payload);
      return data;
    },
  });
}

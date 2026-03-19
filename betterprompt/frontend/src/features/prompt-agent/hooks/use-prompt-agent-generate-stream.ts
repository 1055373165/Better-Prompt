import { useCallback, useRef, useState } from 'react';
import type { GeneratePromptResponse, PromptArtifactType, PromptDiagnosis, PromptIterationRef } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

interface StreamMeta {
  diagnosis: PromptDiagnosis | null;
  artifact_type: PromptArtifactType;
  applied_modules: string[];
  optimization_strategy: string;
  optimized_input: string;
  prompt_only: boolean;
  diagnosis_visible: boolean;
}

interface UseStreamGenerateReturn {
  /** Accumulated text so far */
  streamingText: string;
  /** Whether streaming is in progress */
  isStreaming: boolean;
  /** Metadata received at stream start */
  meta: StreamMeta | null;
  /** Final assembled result (set when stream completes) */
  data: GeneratePromptResponse | null;
  /** Error if any */
  error: Error | null;
  /** Start streaming */
  mutate: (payload: {
    user_input: string;
    show_diagnosis?: boolean;
    output_preference?: 'balanced' | 'depth' | 'execution' | 'natural';
    artifact_type?: PromptArtifactType;
    prompt_only?: boolean;
    context_notes?: string;
    session_id?: string;
    domain_workspace_id?: string;
    subject_id?: string;
    source_asset_version_id?: string;
    context_pack_version_ids?: string[];
    evaluation_profile_version_id?: string | null;
    workflow_recipe_version_id?: string | null;
    run_preset_id?: string | null;
  }) => void;
  /** Reset state */
  reset: () => void;
  isPending: boolean;
}

export function usePromptAgentGenerateStream(): UseStreamGenerateReturn {
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [meta, setMeta] = useState<StreamMeta | null>(null);
  const [data, setData] = useState<GeneratePromptResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setStreamingText('');
    setIsStreaming(false);
    setMeta(null);
    setData(null);
    setError(null);
  }, []);

  const mutate = useCallback((payload: Parameters<UseStreamGenerateReturn['mutate']>[0]) => {
    // Abort any previous stream
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setStreamingText('');
    setIsStreaming(true);
    setData(null);
    setError(null);
    setMeta(null);

    let accumulated = '';
    let receivedMeta: StreamMeta | null = null;
    let generationBackend: 'llm' | 'template' = 'template';
    let generationModel: string | null = null;
    let iteration: PromptIterationRef = { session_id: null, iteration_id: null };

    (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/prompt-agent/generate/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Request failed (${response.status}): ${errorText}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error('No response body');

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith('data: ')) continue;
            const jsonStr = trimmed.slice(6);

            let event: { event: string; [key: string]: unknown };
            try {
              event = JSON.parse(jsonStr);
            } catch {
              continue;
            }

            if (event.event === 'meta') {
              receivedMeta = {
                diagnosis: (event.diagnosis as PromptDiagnosis) || null,
                artifact_type: (event.artifact_type as PromptArtifactType) || 'task_prompt',
                applied_modules: (event.applied_modules as string[]) || [],
                optimization_strategy: (event.optimization_strategy as string) || '',
                optimized_input: (event.optimized_input as string) || '',
                prompt_only: (event.prompt_only as boolean) || false,
                diagnosis_visible: (event.diagnosis_visible as boolean) ?? true,
              };
              setMeta(receivedMeta);
            } else if (event.event === 'chunk') {
              accumulated += event.content as string;
              setStreamingText(accumulated);
            } else if (event.event === 'done') {
              generationBackend = (event.generation_backend as 'llm' | 'template') || 'template';
              generationModel = (event.generation_model as string) || null;
              iteration = {
                session_id: (event.session_id as string) || null,
                iteration_id: (event.iteration_id as string) || null,
              };
            } else if (event.event === 'error') {
              throw new Error((event.detail as string) || 'Stream error');
            }
          }
        }

        // Assemble final result
        const finalResult: GeneratePromptResponse = {
          mode: 'generate',
          iteration,
          diagnosis: receivedMeta?.diagnosis ?? null,
          final_prompt: accumulated,
          artifact_type: receivedMeta?.artifact_type ?? 'task_prompt',
          applied_modules: receivedMeta?.applied_modules ?? [],
          optimization_strategy: receivedMeta?.optimization_strategy ?? '',
          optimized_input: receivedMeta?.optimized_input ?? '',
          prompt_only: receivedMeta?.prompt_only ?? false,
          diagnosis_visible: receivedMeta?.diagnosis_visible ?? true,
          generation_backend: generationBackend,
          generation_model: generationModel,
        };
        setData(finalResult);
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        setError(err instanceof Error ? err : new Error(String(err)));
      } finally {
        setIsStreaming(false);
      }
    })();
  }, []);

  return {
    streamingText,
    isStreaming,
    meta,
    data,
    error,
    mutate,
    reset,
    isPending: isStreaming,
  };
}

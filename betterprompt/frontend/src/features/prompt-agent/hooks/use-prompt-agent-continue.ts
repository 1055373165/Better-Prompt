import { useCallback, useRef, useState } from 'react';
import type { ContinuePromptResponse, PromptAgentMode } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

interface ContinuePayload {
  previous_result: string;
  optimization_goal: string;
  mode: PromptAgentMode;
  context_notes?: string;
}

interface ContinueStreamMeta {
  source_mode: PromptAgentMode;
  optimization_goal: string;
  result_label: string;
  suggested_next_actions: string[];
}

interface UsePromptAgentContinueReturn {
  streamingText: string;
  isStreaming: boolean;
  meta: ContinueStreamMeta | null;
  data: ContinuePromptResponse | null;
  error: Error | null;
  variables: ContinuePayload | null;
  mutate: (payload: ContinuePayload) => void;
  reset: () => void;
  isPending: boolean;
}

export function usePromptAgentContinue(): UsePromptAgentContinueReturn {
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [meta, setMeta] = useState<ContinueStreamMeta | null>(null);
  const [data, setData] = useState<ContinuePromptResponse | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [variables, setVariables] = useState<ContinuePayload | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setStreamingText('');
    setIsStreaming(false);
    setMeta(null);
    setData(null);
    setError(null);
    setVariables(null);
  }, []);

  const mutate = useCallback((payload: ContinuePayload) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setStreamingText('');
    setIsStreaming(true);
    setMeta(null);
    setData(null);
    setError(null);
    setVariables(payload);

    let accumulated = '';
    let receivedMeta: ContinueStreamMeta | null = null;
    let generationBackend: 'llm' | 'template' = 'llm';
    let generationModel: string | null = null;

    (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/prompt-agent/continue/stream`, {
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
                source_mode: (event.source_mode as PromptAgentMode) || payload.mode,
                optimization_goal: (event.optimization_goal as string) || payload.optimization_goal,
                result_label: (event.result_label as string) || '优化后版本',
                suggested_next_actions: (event.suggested_next_actions as string[]) || [],
              };
              setMeta(receivedMeta);
            } else if (event.event === 'chunk') {
              accumulated += event.content as string;
              setStreamingText(accumulated);
            } else if (event.event === 'done') {
              generationBackend = (event.generation_backend as 'llm' | 'template') || 'llm';
              generationModel = (event.generation_model as string) || null;
            } else if (event.event === 'error') {
              throw new Error((event.detail as string) || 'Stream error');
            }
          }
        }

        setData({
          mode: 'continue',
          source_mode: receivedMeta?.source_mode ?? payload.mode,
          optimization_goal: receivedMeta?.optimization_goal ?? payload.optimization_goal,
          refined_result: accumulated,
          result_label: receivedMeta?.result_label ?? '优化后版本',
          suggested_next_actions: receivedMeta?.suggested_next_actions ?? [],
          generation_backend: generationBackend,
          generation_model: generationModel,
        });
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
    variables,
    mutate,
    reset,
    isPending: isStreaming,
  };
}

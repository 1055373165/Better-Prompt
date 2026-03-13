import axios, { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Custom params serializer for FastAPI compatibility
// FastAPI expects: indicators=MA&indicators=RSI (not indicators[]=MA&indicators[]=RSI)
function serializeParams(params: Record<string, unknown>): string {
  const parts: string[] = [];
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      value.forEach((v) => parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(v)}`));
    } else {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
    }
  }
  return parts.join('&');
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120s for LLM analysis requests
  headers: {
    'Content-Type': 'application/json',
  },
  paramsSerializer: serializeParams,
});

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

export default api;

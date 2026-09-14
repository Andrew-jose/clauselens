const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface GeminiHealthResponse {
  status: string;
  latency_ms?: number;
  model?: string;
  message?: string;
  flash_model?: string;
  embedding_model?: string;
  error?: string;
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  return response.json();
}

export async function checkGeminiHealth(): Promise<GeminiHealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health/gemini`);
  if (!response.ok) {
    throw new Error(`Gemini health check failed: ${response.statusText}`);
  }
  return response.json();
}

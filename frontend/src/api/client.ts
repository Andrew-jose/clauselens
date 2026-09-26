import type {
  DocumentItem,
  DocumentChunk,
  ClauseItem,
  FindingItem,
  QAResponse,
  ComparisonResponse,
  SituationClassification,
  ActionPlanData,
  LawyerQuestionsData,
} from '../types';

const envApiUrl =
  typeof import.meta !== 'undefined' && (import.meta as any).env
    ? (import.meta as any).env.VITE_API_URL
    : typeof globalThis !== 'undefined'
      ? (globalThis as any).process?.env?.VITE_API_URL
      : undefined;
const rawBaseUrl = envApiUrl || 'http://localhost:8008/api';
export const API_BASE_URL = rawBaseUrl.trim().replace(/\/+$/, '');

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

export function getAuthToken(): string | null {
  if (typeof localStorage !== 'undefined') {
    return localStorage.getItem('clauselens_auth_token');
  }
  return null;
}

export function setAuthToken(token: string | null): void {
  if (typeof localStorage !== 'undefined') {
    if (token) {
      localStorage.setItem('clauselens_auth_token', token);
    } else {
      localStorage.removeItem('clauselens_auth_token');
    }
  }
}

function buildHeaders(extraHeaders?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = { ...extraHeaders };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(response: Response, defaultErrorMsg: string): Promise<T> {
  if (!response.ok) {
    let detail = '';
    try {
      const errData = await response.json();
      detail = errData.detail || (Array.isArray(errData) ? errData[0]?.msg : '');
    } catch {
      // not JSON
    }
    throw new Error(detail || `${defaultErrorMsg}: ${response.statusText} (${response.status})`);
  }
  return response.json();
}

export async function checkHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    headers: buildHeaders(),
    signal,
  });
  return handleResponse<HealthResponse>(response, 'Health check failed');
}

export async function checkGeminiHealth(signal?: AbortSignal): Promise<GeminiHealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health/gemini`, {
    headers: buildHeaders(),
    signal,
  });
  return handleResponse<GeminiHealthResponse>(response, 'Gemini health check failed');
}

export async function uploadDocument(file: File, signal?: AbortSignal): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: 'POST',
    headers: buildHeaders(),
    body: formData,
    signal,
  });

  return handleResponse<DocumentItem>(response, 'Upload failed');
}

export async function getDocuments(signal?: AbortSignal): Promise<DocumentItem[]> {
  const response = await fetch(`${API_BASE_URL}/documents`, {
    headers: buildHeaders(),
    signal,
  });
  return handleResponse<DocumentItem[]>(response, 'Failed to fetch documents');
}

export async function getDocument(id: string, signal?: AbortSignal): Promise<DocumentItem> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}`, {
    headers: buildHeaders(),
    signal,
  });
  return handleResponse<DocumentItem>(response, `Failed to fetch document ${id}`);
}

export async function getDocumentChunks(id: string, signal?: AbortSignal): Promise<DocumentChunk[]> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}/chunks`, {
    headers: buildHeaders(),
    signal,
  });
  return handleResponse<DocumentChunk[]>(response, `Failed to fetch chunks for document ${id}`);
}

export async function getClauses(id: string, category?: string, signal?: AbortSignal): Promise<ClauseItem[]> {
  const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5173';
  const url = new URL(`${API_BASE_URL}/documents/${id}/clauses`, baseUrl);
  if (category) {
    url.searchParams.append('category', category);
  }
  const response = await fetch(url.toString(), {
    headers: buildHeaders(),
    signal,
  });
  return handleResponse<ClauseItem[]>(response, `Failed to fetch clauses for document ${id}`);
}

export async function getFindings(
  id: string,
  severity?: string,
  category?: string,
  signal?: AbortSignal
): Promise<FindingItem[]> {
  const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5173';
  const url = new URL(`${API_BASE_URL}/documents/${id}/findings`, baseUrl);
  if (severity) url.searchParams.append('severity', severity);
  if (category) url.searchParams.append('category', category);

  const response = await fetch(url.toString(), {
    headers: buildHeaders(),
    signal,
  });
  return handleResponse<FindingItem[]>(response, `Failed to fetch findings for document ${id}`);
}

export async function askQuestion(
  id: string,
  question: string,
  conversationId?: string,
  signal?: AbortSignal
): Promise<QAResponse> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}/ask`, {
    method: 'POST',
    headers: buildHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      question,
      conversation_id: conversationId,
    }),
    signal,
  });

  return handleResponse<QAResponse>(response, 'Question answering failed');
}

export async function compareLeases(
  documentAId: string,
  documentBId: string,
  signal?: AbortSignal
): Promise<ComparisonResponse> {
  const response = await fetch(`${API_BASE_URL}/compare`, {
    method: 'POST',
    headers: buildHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      document_a_id: documentAId,
      document_b_id: documentBId,
    }),
    signal,
  });

  return handleResponse<ComparisonResponse>(response, 'Comparison failed');
}

export async function getComparison(id: string, signal?: AbortSignal): Promise<ComparisonResponse> {
  const response = await fetch(`${API_BASE_URL}/compare/${id}`, {
    headers: buildHeaders(),
    signal,
  });
  return handleResponse<ComparisonResponse>(response, `Failed to fetch comparison ${id}`);
}

export async function submitSituation(
  id: string,
  contextText: string,
  signal?: AbortSignal
): Promise<SituationClassification> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}/situation`, {
    method: 'POST',
    headers: buildHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ context_text: contextText }),
    signal,
  });

  return handleResponse<SituationClassification>(response, 'Situation submission failed');
}

export async function getActionPlan(id: string, signal?: AbortSignal): Promise<ActionPlanData> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}/action-plan`, {
    headers: buildHeaders(),
    signal,
  });
  return handleResponse<ActionPlanData>(response, `Failed to fetch action plan for document ${id}`);
}

export async function getLawyerQuestions(id: string, signal?: AbortSignal): Promise<LawyerQuestionsData> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}/lawyer-questions`, {
    headers: buildHeaders(),
    signal,
  });
  return handleResponse<LawyerQuestionsData>(response, `Failed to fetch lawyer questions for document ${id}`);
}

export function getExportPdfUrl(id: string): string {
  return `${API_BASE_URL}/documents/${id}/export`;
}

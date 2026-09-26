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

const rawBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8008/api';
const API_BASE_URL = rawBaseUrl.trim().replace(/\/+$/, '');

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

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `Upload failed: ${response.statusText}`);
  }
  return response.json();
}

export async function getDocuments(): Promise<DocumentItem[]> {
  const response = await fetch(`${API_BASE_URL}/documents`);
  if (!response.ok) {
    throw new Error(`Failed to fetch documents: ${response.statusText}`);
  }
  return response.json();
}

export async function getDocument(id: string): Promise<DocumentItem> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch document ${id}: ${response.statusText}`);
  }
  return response.json();
}

export async function getDocumentChunks(id: string): Promise<DocumentChunk[]> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}/chunks`);
  if (!response.ok) {
    throw new Error(`Failed to fetch chunks for document ${id}: ${response.statusText}`);
  }
  return response.json();
}

export async function getClauses(id: string, category?: string): Promise<ClauseItem[]> {
  const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5173';
  const url = new URL(`${API_BASE_URL}/documents/${id}/clauses`, baseUrl);
  if (category) {
    url.searchParams.append('category', category);
  }
  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(`Failed to fetch clauses for document ${id}: ${response.statusText}`);
  }
  return response.json();
}

export async function getFindings(
  id: string,
  severity?: string,
  category?: string
): Promise<FindingItem[]> {
  const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5173';
  const url = new URL(`${API_BASE_URL}/documents/${id}/findings`, baseUrl);
  if (severity) url.searchParams.append('severity', severity);
  if (category) url.searchParams.append('category', category);

  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(`Failed to fetch findings for document ${id}: ${response.statusText}`);
  }
  return response.json();
}

export async function askQuestion(
  id: string,
  question: string,
  conversationId?: string
): Promise<QAResponse> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      conversation_id: conversationId,
    }),
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `Question answering failed: ${response.statusText}`);
  }
  return response.json();
}

export async function compareLeases(
  documentAId: string,
  documentBId: string
): Promise<ComparisonResponse> {
  const response = await fetch(`${API_BASE_URL}/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_a_id: documentAId,
      document_b_id: documentBId,
    }),
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `Comparison failed: ${response.statusText}`);
  }
  return response.json();
}

export async function getComparison(id: string): Promise<ComparisonResponse> {
  const response = await fetch(`${API_BASE_URL}/compare/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch comparison ${id}: ${response.statusText}`);
  }
  return response.json();
}

export async function submitSituation(
  id: string,
  contextText: string
): Promise<SituationClassification> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}/situation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ context_text: contextText }),
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `Situation submission failed: ${response.statusText}`);
  }
  return response.json();
}

export async function getActionPlan(id: string): Promise<ActionPlanData> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}/action-plan`);
  if (!response.ok) {
    throw new Error(`Failed to fetch action plan for document ${id}: ${response.statusText}`);
  }
  return response.json();
}

export async function getLawyerQuestions(id: string): Promise<LawyerQuestionsData> {
  const response = await fetch(`${API_BASE_URL}/documents/${id}/lawyer-questions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch lawyer questions for document ${id}: ${response.statusText}`);
  }
  return response.json();
}

export function getExportPdfUrl(id: string): string {
  return `${API_BASE_URL}/documents/${id}/export`;
}

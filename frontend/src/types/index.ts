export interface DocumentItem {
  id: string;
  filename: string;
  mime_type: string;
  page_count: number;
  status: 'uploading' | 'processing' | 'ready' | 'failed';
  summary?: string | null;
  key_terms?: string[] | null;
  created_at?: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  page_number: number;
  clause_id?: string | null;
  section_heading?: string | null;
  text: string;
  start_char?: number;
  end_char?: number;
  token_count?: number;
}

export interface ClauseCitation {
  page: number;
  clause_id?: string | null;
  quote: string;
  chunk_id?: string;
  verified?: boolean;
  match_score?: number;
}

export type ClauseCategory =
  | 'rent_fees'
  | 'term_renewal'
  | 'termination_penalties'
  | 'repairs_habitability'
  | 'access_privacy'
  | 'deposit'
  | 'restrictions'
  | 'other';

export interface ClauseItem {
  id: string;
  document_id: string;
  clause_number?: string | null;
  heading?: string | null;
  category: ClauseCategory;
  summary?: string | null;
  quote?: string | null;
  page_number: number;
}

export type SeverityLevel = 'low' | 'medium' | 'high';
export type FindingType = 'risk' | 'obligation' | 'inconsistency';

export interface FindingItem {
  id: string;
  document_id: string;
  clause_id?: string | null;
  type: FindingType;
  severity: SeverityLevel;
  title: string;
  plain_explanation: string;
  page_number: number;
  quote?: string | null;
  verified: boolean;
}

export type GroundedStatus =
  | 'grounded_high'
  | 'grounded_low'
  | 'not_found_in_document'
  | 'general_info';

export interface QAResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  status: GroundedStatus;
  citations: ClauseCitation[];
  confidence_note?: string;
}

export interface MessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  status?: GroundedStatus;
  citations?: ClauseCitation[];
  confidence_note?: string;
  created_at?: string;
}

export interface ComparisonFindingItem {
  id: string;
  category: string;
  delta_description: string;
  favors: 'tenant' | 'landlord' | 'neutral' | 'unclear';
  severity: SeverityLevel;
  doc_a_citation?: ClauseCitation | null;
  doc_b_citation?: ClauseCitation | null;
}

export interface ComparisonResponse {
  id: string;
  document_a_id: string;
  document_b_id: string;
  created_at?: string;
  deltas_count: number;
  findings: ComparisonFindingItem[];
}

export type SituationType =
  | 'pre_signing_review'
  | 'active_dispute'
  | 'termination'
  | 'renewal_negotiation'
  | 'general_curiosity';

export interface SituationClassification {
  situation_type: SituationType;
  urgency: SeverityLevel;
  relevant_categories: string[];
}

export interface ActionStepItem {
  order: number;
  action: string;
  rationale: string;
  citation?: ClauseCitation | null;
}

export interface ActionPlanData {
  id?: string;
  document_id: string;
  situation_context_text?: string;
  situation_type?: SituationType;
  urgency?: SeverityLevel;
  steps: ActionStepItem[];
  generated_at?: string;
}

export interface LawyerQuestionItem {
  id?: string;
  topic: string;
  question: string;
  priority: SeverityLevel;
  source_finding_id?: string | null;
}

export interface LawyerQuestionsData {
  document_id: string;
  questions: LawyerQuestionItem[];
}

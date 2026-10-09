/**
 * Type definitions for MirAI Student Policy Advisor
 */

export interface SourceCitation {
  policy_name: string;
  section: string;
  page_number: number;
  snippet: string;
  relevance_score?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: SourceCitation[];
  sub_queries?: string[];
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  chat_history?: Array<{ role: string; content: string }>;
}

export interface ChatResponse {
  answer: string;
  sources: SourceCitation[];
  sub_queries: string[];
}

export interface IngestResponse {
  status: string;
  message: string;
  total_chunks: number;
  pages_processed: number;
  collection_name: string;
}

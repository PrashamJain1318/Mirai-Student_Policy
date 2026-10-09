/**
 * TypeScript type definitions for Autonomous MirAI Student Policy Advisor.
 */

export interface SourceCitation {
  document: string;
  page: number;
  excerpt: string;
  chunk_id?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: SourceCitation[];
  sub_queries?: string[];
  abstained?: boolean;
  timestamp: string;
  isError?: boolean;
}

export interface ChatRequest {
  question: string;
  session_id?: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceCitation[];
  sub_queries: string[];
  abstained: boolean;
}

export interface HealthStatus {
  status: "healthy" | "degraded" | "offline";
  handbook_file_present: boolean;
  vector_store_initialized: boolean;
  indexed_chunks_count: number;
  api_key_configured: boolean;
  embedding_model: string;
  chat_model: string;
  details?: Record<string, unknown>;
}

export interface IngestResponse {
  status: string;
  source_file: string;
  handbook_version: string;
  total_pages: number;
  total_chunks: number;
  total_characters: number;
  average_chunk_size: number;
  doc_hash: string;
  total_collection_count: number;
  message?: string;
}

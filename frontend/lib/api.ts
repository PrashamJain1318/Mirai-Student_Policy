import { ChatResponse, HealthStatus, IngestResponse } from "./types";

const getApiBaseUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Checks backend health and dependency readiness status.
 */
export async function checkBackendHealth(): Promise<HealthStatus> {
  const baseUrl = getApiBaseUrl();
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    const res = await fetch(`${baseUrl}/health`, {
      method: "GET",
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      return {
        status: "offline",
        handbook_file_present: false,
        vector_store_initialized: false,
        indexed_chunks_count: 0,
        api_key_configured: false,
        embedding_model: "text-embedding-004",
        chat_model: "gemini-3.8-flash",
      };
    }
    return await res.json();
  } catch {
    return {
      status: "offline",
      handbook_file_present: false,
      vector_store_initialized: false,
      indexed_chunks_count: 0,
      api_key_configured: false,
      embedding_model: "text-embedding-004",
      chat_model: "gemini-3.8-flash",
    };
  }
}

/**
 * Sends student policy question to the FastAPI /chat endpoint.
 */
export async function askPolicyAdvisor(
  question: string,
  sessionId?: string
): Promise<ChatResponse> {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question: question.trim(),
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      // Use status text if not JSON
    }
    throw new ApiError(response.status, errorDetail);
  }

  return response.json();
}

/**
 * Triggers official handbook ingestion or uploads a new PDF file.
 * Uses FormData without manual Content-Type header so browser sets multipart boundary.
 */
export async function ingestPolicyHandbook(file?: File): Promise<IngestResponse> {
  const baseUrl = getApiBaseUrl();
  const formData = new FormData();
  if (file) {
    formData.append("file", file);
  }

  const response = await fetch(`${baseUrl}/ingest`, {
    method: "POST",
    body: file ? formData : undefined,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      // Fallback
    }
    throw new ApiError(response.status, errorDetail);
  }

  return response.json();
}

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const FRIENDLY_API_ERROR = '案内機能の準備中です。しばらくしてからもう一度お試しください。';

export type ChatMessage = {
  role: 'user' | 'assistant' | 'system';
  content: string;
};

export type ChatRequest = {
  message: string;
  history?: ChatMessage[];
  user_type?: 'visitor' | 'staff';
  filters?: Record<string, unknown>;
};

export type WaitTime = {
  id: number;
  exhibition_id: number;
  current_wait_minutes: number;
  updated_at?: string;
  exhibition_name?: string;
  category?: string;
  location_name?: string;
  duration_minutes?: number;
  recommended_for?: string;
  cautions?: string;
  stage_start_time?: string;
  ticket_status?: string;
  capacity_status?: string;
};

export type CrowdReportSummary = {
  exhibition_id: number;
  status: 'empty' | 'short' | 'busy' | 'closed' | string;
  label: string;
  report_count: number;
  last_reported_at?: string | null;
  source?: string;
};

export type SourceChunk = {
  content: string;
  metadata: Record<string, unknown>;
  distance?: number;
};

export type ChatResponse = {
  answer: string;
  sources: SourceChunk[];
  used_context: boolean;
};

export type RagStatus = {
  data_dir: string;
  file_count: number;
  chunk_count: number;
  collection_count: number;
  sources: Array<{ path: string; type: string; chunk_count: number }>;
  warning?: string;
};

export type RagIngestResult = {
  loaded: number;
  upserted: number;
};

export type RagSearchResponse = {
  results: SourceChunk[];
};

export type ItineraryStop = {
  exhibition_id: number;
  exhibition_name: string;
  wait_minutes: number;
  visit_minutes: number;
  travel_minutes_from_previous: number;
  elapsed_minutes: number;
};

export type ItineraryResponse = {
  stops: ItineraryStop[];
  total_minutes: number;
  total_travel_minutes?: number;
  total_wait_minutes?: number;
  total_visit_minutes?: number;
  return_travel_minutes?: number;
  skipped_exhibition_ids: number[];
  note: string;
};

export type StaffSession = {
  ok: boolean;
  message: string;
  exhibition_id: number;
  exhibition_name?: string;
};

export type AdminLog = {
  time: string;
  level: string;
  logger: string;
  message: string;
};

export type ModelStatus = {
  ollama_base_url: string;
  answer_model: {
    name: string;
    ok: boolean;
    matched_name?: string;
    available_models: string[];
    latency_ms: number;
    error?: string;
  };
  embedding_model: {
    name: string;
    ok: boolean;
    matched_name?: string;
    available_models: string[];
    latency_ms: number;
    error?: string;
  };
  vector_store: {
    ok: boolean;
    collection_count: number;
    error?: string;
  };
};

export type AdminPin = {
  exhibition_id: number;
  name: string;
  pin: string;
};

async function parseError(response: Response) {
  try {
    const body = await response.json();
    return body.detail || body.message || FRIENDLY_API_ERROR;
  } catch {
    return FRIENDLY_API_ERROR;
  }
}

export const apiClient = {
  async get(endpoint: string) {
    const response = await fetch(`${BASE_URL}${endpoint}`);
    if (!response.ok) {
      throw new Error(await parseError(response));
    }
    return response.json();
  },

  async post(endpoint: string, data: any) {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(await parseError(response));
    }
    return response.json();
  },

  async chat(data: ChatRequest): Promise<ChatResponse> {
    return this.post('/api/v1/chat', { history: [], user_type: 'visitor', ...data });
  },

  async getRagStatus(): Promise<RagStatus> {
    return this.get('/api/v1/rag/status');
  },

  async ingestRagDocuments(): Promise<RagIngestResult> {
    return this.post('/api/v1/rag/ingest', {});
  },

  async rebuildRagDocuments(): Promise<RagIngestResult> {
    return this.post('/api/v1/rag/rebuild', {});
  },

  async searchRagDocuments(query: string, topK = 5): Promise<RagSearchResponse> {
    return this.post('/api/v1/rag/search', { query, top_k: topK });
  },

  async getAdminLogs(): Promise<{ logs: AdminLog[] }> {
    return this.get('/api/v1/admin/logs');
  },

  async getModelStatus(): Promise<ModelStatus> {
    return this.get('/api/v1/admin/model-status');
  },

  async getAdminPins(adminPin: string): Promise<{ pins: AdminPin[] }> {
    const response = await fetch(`${BASE_URL}/api/v1/admin/staff-pins`, {
      headers: { 'x-admin-pin': adminPin },
    });
    if (!response.ok) throw new Error(await parseError(response));
    return response.json();
  },

  async updateAdminPin(adminPin: string, exhibitionId: number, pin: string) {
    const response = await fetch(`${BASE_URL}/api/v1/admin/staff-pins/${exhibitionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'x-admin-pin': adminPin },
      body: JSON.stringify({ pin }),
    });
    if (!response.ok) throw new Error(await parseError(response));
    return response.json();
  },

  async updateAdminWaitTime(adminPin: string, exhibitionId: number, waitMinutes: number) {
    const response = await fetch(`${BASE_URL}/api/v1/admin/wait-times/${exhibitionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-admin-pin': adminPin },
      body: JSON.stringify({ current_wait_minutes: waitMinutes }),
    });
    if (!response.ok) throw new Error(await parseError(response));
    return response.json();
  },

  async publishPublicWaitTimes(adminPin: string): Promise<{ enabled: boolean; published: number }> {
    const response = await fetch(`${BASE_URL}/api/v1/admin/public-wait-times/publish`, {
      method: 'POST',
      headers: { 'x-admin-pin': adminPin },
    });
    if (!response.ok) throw new Error(await parseError(response));
    return response.json();
  },

  async syncAdminCrowdReports(adminPin?: string): Promise<{ enabled: boolean; synced: boolean; report_count: number; summary_count: number; last_synced_at?: string | null; error?: string | null }> {
    const response = await fetch(`${BASE_URL}/api/v1/admin/crowd-reports/sync`, {
      method: 'POST',
      headers: adminPin ? { 'x-admin-pin': adminPin } : undefined,
    });
    if (!response.ok) throw new Error(await parseError(response));
    return response.json();
  },

  async getWaitTimes(): Promise<WaitTime[]> {
    return this.get('/api/v1/wait-times');
  },

  async getCrowdReportSummary(): Promise<CrowdReportSummary[]> {
    return this.get('/api/v1/crowd-reports/summary');
  },

  async updateWaitTime(exhibitionId: number, waitMinutes: number, staffPin: string) {
    const response = await fetch(`${BASE_URL}/api/v1/exhibitions/${exhibitionId}/wait-time`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-staff-pin': staffPin },
      body: JSON.stringify({ current_wait_minutes: waitMinutes }),
    });
    if (!response.ok) throw new Error('待ち時間を更新できませんでした。企画IDとPINを確認してください。');
    return response.json();
  },

  async staffLogin(exhibitionId: number, pin: string): Promise<StaffSession> {
    return this.post('/api/v1/staff/login', { exhibition_id: exhibitionId, pin });
  },

  async planItinerary(
    exhibitionIds: number[],
    availableMinutes: number,
    startExhibitionId?: number,
    endExhibitionId?: number,
  ): Promise<ItineraryResponse> {
    return this.post('/api/v1/itinerary/plan', {
      exhibition_ids: exhibitionIds,
      available_minutes: availableMinutes,
      start_exhibition_id: startExhibitionId || null,
      end_exhibition_id: endExhibitionId || null,
      include_wait_times: true,
    });
  },

  async streamChat(
    data: ChatRequest,
    onChunk: (chunk: string) => void,
    onSources?: (sources: SourceChunk[]) => void,
    signal?: AbortSignal,
  ) {
    const response = await fetch(`${BASE_URL}/api/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ history: [], user_type: 'visitor', ...data }),
      signal,
    });

    if (!response.ok || !response.body) throw new Error(FRIENDLY_API_ERROR);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() || '';

      for (const event of events) {
        const line = event.split('\n').find((item) => item.startsWith('data: '));
        if (!line) continue;

        const payload = line.replace(/^data: /, '');
        if (payload === '[DONE]') return;

        const parsed = JSON.parse(payload);
        if (parsed.sources && onSources) onSources(parsed.sources);
        if (parsed.content) onChunk(parsed.content);
      }
    }
  },
};

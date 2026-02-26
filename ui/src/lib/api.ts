import type {
  AdminConfig,
  ConvoTurnRequest,
  ConvoTurnResponse,
  MetaResponse,
  STTResponse,
  TTSResponse,
  VoicePreviewResponse,
  VoiceRecord,
  VoiceSyncResponse
} from "./schema";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    let message = "Request failed";
    try {
      const body = await response.json();
      message = body?.message ?? message;
    } catch {
      // ignore
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export const api = {
  async getMeta(): Promise<MetaResponse> {
    return request<MetaResponse>("/v1/meta");
  },

  async postTts(body: {
    text: string;
    voice_id?: string;
    format: "wav" | "mp3";
    latency_mode: "balanced" | "low" | "ultra_low";
    nuance: number;
  }): Promise<TTSResponse> {
    return request<TTSResponse>("/v1/tts", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body)
    });
  },

  async postStt(file: File, language?: string, diarization = false): Promise<STTResponse> {
    const formData = new FormData();
    formData.append("audio", file);
    if (language) {
      formData.append("language", language);
    }
    formData.append("diarization", String(diarization));

    return request<STTResponse>("/v1/stt", {
      method: "POST",
      body: formData
    });
  },

  async cloneVoice(name: string, samples: File[]): Promise<{ voice_id: string; status: string }> {
    const formData = new FormData();
    formData.append("name", name);
    for (const sample of samples) {
      formData.append("samples", sample);
    }
    return request<{ voice_id: string; status: string }>("/v1/voice/clone", {
      method: "POST",
      body: formData
    });
  },

  async listVoices(): Promise<VoiceRecord[]> {
    const payload = await request<{ voices: VoiceRecord[] }>("/v1/voice/list");
    return payload.voices;
  },

  async syncVoices(): Promise<VoiceSyncResponse> {
    return request<VoiceSyncResponse>("/v1/voice/sync", {
      method: "POST"
    });
  },

  async previewVoice(voiceId: string): Promise<VoicePreviewResponse> {
    return request<VoicePreviewResponse>(`/v1/voice/preview/${voiceId}`, {
      method: "POST"
    });
  },

  async getVoice(voiceId: string): Promise<VoiceRecord> {
    return request<VoiceRecord>(`/v1/voice/${voiceId}`);
  },

  async deleteVoice(voiceId: string): Promise<{ status: string; voice_id: string }> {
    return request<{ status: string; voice_id: string }>(`/v1/voice/${voiceId}`, {
      method: "DELETE"
    });
  },

  async getAdminConfig(token: string): Promise<AdminConfig> {
    return request<AdminConfig>("/v1/admin/config", {
      headers: { authorization: `Bearer ${token}` }
    });
  },

  async updateAdminConfig(token: string, payload: Partial<AdminConfig>): Promise<AdminConfig> {
    return request<AdminConfig>("/v1/admin/config", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
  },

  async postConvoTurn(payload: ConvoTurnRequest): Promise<ConvoTurnResponse> {
    return request<ConvoTurnResponse>("/v1/convo/turn", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload)
    });
  },

  getFileUrl(path: string): string {
    if (/^https?:\/\//.test(path)) {
      return path;
    }
    return `${API_BASE}${path}`;
  },

  async pingMs(): Promise<number> {
    const started = performance.now();
    await fetch(`${API_BASE}/health`);
    return Math.round(performance.now() - started);
  }
};

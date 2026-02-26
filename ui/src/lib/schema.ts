export type MetaResponse = {
  brand: string;
  models: string[];
  features: {
    voice_cloning: boolean;
    streaming: boolean;
    realtime: boolean;
  };
};

export type TTSResponse = {
  audio_url: string;
  duration_ms: number;
  meta: { model_alias: string };
};

export type STTResponse = {
  transcript: string;
  words: Array<Record<string, unknown>>;
  meta: { model_alias: string };
};

export type VoiceRecord = {
  voice_id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
  sample_files: string[];
};

export type VoicePreviewResponse = {
  voice_id: string;
  preview_text: string;
  audio_url: string;
  duration_ms: number;
};

export type VoiceSyncResponse = {
  synced: number;
  voices: VoiceRecord[];
};

export type AdminConfig = {
  Sugar: string;
  Salt: string;
  Lime: string;
  Pepper: boolean;
  Mint: string;
  Cocoa: string;
  Vanilla: string;
  Ice: string;
};

export type WSMessage = {
  type: string;
  [key: string]: unknown;
};

export type ConvoTurnRequest = {
  session_id?: string;
  voice_id?: string;
  text: string;
  latency_mode: "balanced" | "low" | "ultra_low";
  nuance: number;
  agent_prompt?: string;
};

export type ConvoTurnResponse = {
  session_id: string;
  user_text: string;
  agent_text: string;
  audio_url: string;
  duration_ms: number;
  meta: { model_alias: string };
};

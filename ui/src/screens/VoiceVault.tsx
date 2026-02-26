import { useEffect, useState } from "react";

import { GlassButton } from "../components/GlassButton";
import { GlassCard } from "../components/GlassCard";
import { GlassInput } from "../components/GlassInput";
import { api } from "../lib/api";
import type { VoiceRecord } from "../lib/schema";

type Props = {
  onVoicesChanged: (voices: VoiceRecord[]) => void;
};

export function VoiceVault({ onVoicesChanged }: Props) {
  const [voices, setVoices] = useState<VoiceRecord[]>([]);
  const [name, setName] = useState("New Echo Voice");
  const [samples, setSamples] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [previewUrl, setPreviewUrl] = useState("");
  const [previewText, setPreviewText] = useState("");

  async function loadVoices() {
    const all = await api.listVoices();
    setVoices(all);
    onVoicesChanged(all);
  }

  async function syncVoices() {
    setSyncing(true);
    try {
      const synced = await api.syncVoices();
      setVoices(synced.voices);
      onVoicesChanged(synced.voices);
    } finally {
      setSyncing(false);
    }
  }

  useEffect(() => {
    syncVoices().catch(() => loadVoices().catch(() => undefined));
  }, []);

  async function createVoice() {
    if (!name.trim() || samples.length === 0) {
      return;
    }

    setBusy(true);
    try {
      await api.cloneVoice(name.trim(), samples);
      await syncVoices();
      setSamples([]);
    } finally {
      setBusy(false);
    }
  }

  async function previewVoice(voiceId: string) {
    const response = await api.previewVoice(voiceId);
    setPreviewText(response.preview_text);
    setPreviewUrl(api.getFileUrl(response.audio_url));
  }

  async function removeVoice(voiceId: string) {
    await api.deleteVoice(voiceId);
    await syncVoices();
  }

  return (
    <div className="screen-grid">
      <GlassCard
        title="Voice Vault"
        actions={
          <GlassButton onClick={syncVoices} disabled={syncing}>
            {syncing ? "Syncing..." : "Sync Echo Voices"}
          </GlassButton>
        }
      >
        <div className="inline-grid two">
          <GlassInput label="Voice Name" value={name} onChange={(event) => setName(event.target.value)} />
          <label className="field">
            <span>Sample Audio (multiple)</span>
            <input
              className="glass-input"
              type="file"
              accept="audio/*"
              multiple
              onChange={(event) => setSamples(Array.from(event.target.files ?? []))}
            />
          </label>
        </div>
        <GlassButton onClick={createVoice} disabled={busy || samples.length === 0}>
          {busy ? "Creating..." : "Create Echo Voice Profile"}
        </GlassButton>
      </GlassCard>

      <GlassCard title="Voice Profiles">
        <ul className="list-reset">
          {voices.map((voice) => (
            <li key={voice.voice_id} className="list-item">
              <div>
                <strong>{voice.name}</strong>
                <small>{voice.status}</small>
              </div>
              <div className="inline-actions">
                <GlassButton onClick={() => previewVoice(voice.voice_id)}>Preview</GlassButton>
                <GlassButton onClick={() => removeVoice(voice.voice_id)}>Remove</GlassButton>
              </div>
            </li>
          ))}
          {voices.length === 0 && <li className="list-item">No voice profiles created yet.</li>}
        </ul>
        {previewText && <p className="muted">Preview Text: {previewText}</p>}
        {previewUrl && <audio controls src={previewUrl} className="full-width" />}
      </GlassCard>
    </div>
  );
}

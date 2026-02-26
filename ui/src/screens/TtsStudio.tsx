import { useMemo, useState } from "react";

import { api } from "../lib/api";
import type { VoiceRecord } from "../lib/schema";
import { DropdownSelect } from "../components/DropdownSelect";
import { GlassButton } from "../components/GlassButton";
import { GlassCard } from "../components/GlassCard";
import { GlassTextarea } from "../components/GlassInput";
import { WaveformCanvas } from "../components/WaveformCanvas";

type GenerationItem = {
  id: string;
  text: string;
  audioUrl: string;
  durationMs: number;
};

type Props = {
  voices: VoiceRecord[];
};

export function TtsStudio({ voices }: Props) {
  const [text, setText] = useState("Welcome to EchoLabs by Eburon AI.");
  const [voiceId, setVoiceId] = useState<string>(voices[0]?.voice_id ?? "");
  const [latencyMode, setLatencyMode] = useState<"balanced" | "low" | "ultra_low">("balanced");
  const [nuance, setNuance] = useState(0.9);
  const [format, setFormat] = useState<"wav" | "mp3">("wav");
  const [generating, setGenerating] = useState(false);
  const [currentAudioUrl, setCurrentAudioUrl] = useState<string>("");
  const [history, setHistory] = useState<GenerationItem[]>([]);

  const voiceOptions = useMemo(
    () => voices.map((voice) => ({ label: voice.name, value: voice.voice_id })),
    [voices]
  );

  async function generate() {
    if (!text.trim()) {
      return;
    }

    setGenerating(true);
    try {
      const response = await api.postTts({
        text,
        voice_id: voiceId || undefined,
        format,
        latency_mode: latencyMode,
        nuance
      });
      const absoluteUrl = api.getFileUrl(response.audio_url);
      setCurrentAudioUrl(absoluteUrl);
      setHistory((previous) => [
        {
          id: crypto.randomUUID(),
          text,
          audioUrl: absoluteUrl,
          durationMs: response.duration_ms
        },
        ...previous
      ]);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="screen-grid">
      <GlassCard title="Echo TTS Studio">
        <GlassTextarea
          label="Prompt"
          value={text}
          onChange={(event) => setText(event.target.value)}
          rows={7}
          placeholder="Enter text for synthesis"
        />
        <div className="inline-grid two">
          <DropdownSelect
            label="Echo Voice Profile"
            options={voiceOptions.length ? voiceOptions : [{ label: "Default Voice", value: "" }]}
            value={voiceId}
            onChange={(event) => setVoiceId(event.target.value)}
          />
          <DropdownSelect
            label="Latency Mode"
            options={[
              { label: "Balanced", value: "balanced" },
              { label: "Low", value: "low" },
              { label: "Ultra Low", value: "ultra_low" }
            ]}
            value={latencyMode}
            onChange={(event) => setLatencyMode(event.target.value as "balanced" | "low" | "ultra_low")}
          />
        </div>
        <div className="inline-grid two">
          <label className="field">
            <span>Nuance</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={nuance}
              onChange={(event) => setNuance(Number(event.target.value))}
            />
          </label>
          <DropdownSelect
            label="Format"
            options={[
              { label: "WAV", value: "wav" },
              { label: "MP3", value: "mp3" }
            ]}
            value={format}
            onChange={(event) => setFormat(event.target.value as "wav" | "mp3")}
          />
        </div>
        <GlassButton onClick={generate} disabled={generating}>
          {generating ? "Generating..." : "Generate Audio"}
        </GlassButton>
      </GlassCard>

      <GlassCard title="Playback">
        <WaveformCanvas values={[0.25, 0.38, 0.16, 0.42, 0.29, 0.22, 0.4]} />
        {currentAudioUrl ? <audio controls src={currentAudioUrl} className="full-width" /> : <p>No output yet.</p>}
      </GlassCard>

      <GlassCard title="Generation History">
        <ul className="list-reset">
          {history.map((item) => (
            <li key={item.id} className="list-item">
              <div>
                <strong>{item.text.slice(0, 52)}</strong>
                <small>{item.durationMs} ms</small>
              </div>
              <a href={item.audioUrl} target="_blank" rel="noreferrer">
                Open Audio
              </a>
            </li>
          ))}
          {history.length === 0 && <li className="list-item">No generations yet.</li>}
        </ul>
      </GlassCard>
    </div>
  );
}

import { useState } from "react";

import { DropdownSelect } from "../components/DropdownSelect";
import { GlassButton } from "../components/GlassButton";
import { GlassCard } from "../components/GlassCard";
import { ToggleSwitch } from "../components/ToggleSwitch";
import { api } from "../lib/api";

export function SttStudio() {
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("en");
  const [diarization, setDiarization] = useState(false);
  const [loading, setLoading] = useState(false);
  const [transcript, setTranscript] = useState("");

  async function runStt() {
    if (!audioFile) {
      return;
    }

    setLoading(true);
    try {
      const response = await api.postStt(audioFile, language, diarization);
      setTranscript(response.transcript);
    } finally {
      setLoading(false);
    }
  }

  function exportTranscript(kind: "txt" | "json") {
    const payload = kind === "txt" ? transcript : JSON.stringify({ transcript }, null, 2);
    const blob = new Blob([payload], { type: kind === "txt" ? "text/plain" : "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = kind === "txt" ? "echo-transcript.txt" : "echo-transcript.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="screen-grid">
      <GlassCard title="Echo STT Studio">
        <label className="field">
          <span>Upload Audio</span>
          <input
            className="glass-input"
            type="file"
            accept="audio/*"
            onChange={(event) => setAudioFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <DropdownSelect
          label="Language"
          value={language}
          onChange={(event) => setLanguage(event.target.value)}
          options={[
            { label: "English", value: "en" },
            { label: "French", value: "fr" },
            { label: "Dutch", value: "nl" },
            { label: "German", value: "de" }
          ]}
        />
        <ToggleSwitch checked={diarization} onChange={setDiarization} label="Diarization" />
        <GlassButton onClick={runStt} disabled={loading || !audioFile}>
          {loading ? "Transcribing..." : "Run Transcription"}
        </GlassButton>
      </GlassCard>

      <GlassCard title="Transcript">
        <pre className="transcript-block">{transcript || "Transcript appears here."}</pre>
        <div className="inline-actions">
          <GlassButton onClick={() => exportTranscript("txt")} disabled={!transcript}>
            Export TXT
          </GlassButton>
          <GlassButton onClick={() => exportTranscript("json")} disabled={!transcript}>
            Export JSON
          </GlassButton>
        </div>
      </GlassCard>
    </div>
  );
}

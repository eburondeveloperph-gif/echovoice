import { useEffect, useMemo, useRef, useState } from "react";

import { DropdownSelect } from "../components/DropdownSelect";
import { GlassButton } from "../components/GlassButton";
import { GlassCard } from "../components/GlassCard";
import { GlassInput } from "../components/GlassInput";
import { ToggleSwitch } from "../components/ToggleSwitch";
import { VuMeter } from "../components/VuMeter";
import { WaveformCanvas } from "../components/WaveformCanvas";
import { api } from "../lib/api";
import { base64ToUint8Array, listAudioInputDevices, MicCapture } from "../lib/audio";
import type { VoiceRecord, WSMessage } from "../lib/schema";
import { EchoWebSocket } from "../lib/ws";

type Props = {
  voices: VoiceRecord[];
};

export function RealtimePlayground({ voices }: Props) {
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState("");
  const [voiceId, setVoiceId] = useState(voices[0]?.voice_id ?? "");
  const [latencyMode, setLatencyMode] = useState<"balanced" | "low" | "ultra_low">("balanced");
  const [nuance, setNuance] = useState(0.9);
  const [liveMode, setLiveMode] = useState(true);
  const [agentPrompt, setAgentPrompt] = useState("Keep replies concise and actionable.");
  const [turnInput, setTurnInput] = useState("Hello, start my agent session.");

  const [state, setState] = useState<"listening" | "thinking" | "speaking" | "idle">("idle");
  const [partialText, setPartialText] = useState("");
  const [finalTexts, setFinalTexts] = useState<string[]>([]);
  const [agentStream, setAgentStream] = useState("");
  const [agentFinals, setAgentFinals] = useState<string[]>([]);
  const [vuLevel, setVuLevel] = useState(0);
  const [waveform, setWaveform] = useState<number[]>([0.1, 0.2, 0.3, 0.2, 0.1]);
  const [connected, setConnected] = useState(false);
  const [pingMs, setPingMs] = useState<number>(0);
  const [busyTurn, setBusyTurn] = useState(false);

  const socketRef = useRef<EchoWebSocket | null>(null);
  const micRef = useRef<MicCapture | null>(null);
  const audioChunksRef = useRef<ArrayBuffer[]>([]);
  const sessionIdRef = useRef(`session_${crypto.randomUUID().slice(0, 8)}`);

  const wsUrl = useMemo(() => {
    const apiBase = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
    const wsBase = apiBase.replace("http://", "ws://").replace("https://", "wss://");
    return `${wsBase}/v1/convo/ws?session_id=${sessionIdRef.current}`;
  }, []);

  useEffect(() => {
    listAudioInputDevices().then(setDevices).catch(() => setDevices([]));
    micRef.current = new MicCapture();

    return () => {
      micRef.current?.stop();
      socketRef.current?.disconnect();
    };
  }, []);

  useEffect(() => {
    if (voices.length > 0 && !voiceId) {
      setVoiceId(voices[0].voice_id);
    }
  }, [voices, voiceId]);

  useEffect(() => {
    const timer = window.setInterval(async () => {
      const ms = await api.pingMs();
      setPingMs(ms);
    }, 8000);

    return () => window.clearInterval(timer);
  }, []);

  function onMessage(message: WSMessage) {
    const type = String(message.type ?? "");

    if (type === "state") {
      const incoming = String(message.state ?? "idle") as "listening" | "thinking" | "speaking" | "idle";
      setState(incoming);
      if (incoming === "listening" && audioChunksRef.current.length > 0) {
        const blob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.play().catch(() => undefined);
        audioChunksRef.current = [];
      }
      return;
    }

    if (type === "stt_partial") {
      setPartialText(String(message.text ?? ""));
      return;
    }

    if (type === "stt_final") {
      const text = String(message.text ?? "");
      setFinalTexts((prev) => [...prev, text]);
      setPartialText("");
      return;
    }

    if (type === "agent_delta") {
      setAgentStream((prev) => prev + String(message.text_delta ?? ""));
      return;
    }

    if (type === "agent_final") {
      const text = String(message.text ?? "");
      setAgentFinals((prev) => [...prev, text]);
      setAgentStream("");
      return;
    }

    if (type === "tts_audio") {
      const chunk = String(message.chunk_b64 ?? "");
      const bytes = base64ToUint8Array(chunk);
      const copy = new Uint8Array(bytes.byteLength);
      copy.set(bytes);
      audioChunksRef.current.push(copy.buffer);
    }
  }

  function connect() {
    if (socketRef.current) {
      socketRef.current.disconnect();
    }
    const socket = new EchoWebSocket(wsUrl, {
      onOpen: () => {
        setConnected(true);
        socket.send({
          type: "start",
          session_id: sessionIdRef.current,
          voice_id: voiceId,
          prefs: { latency_mode: latencyMode, nuance, agent_prompt: agentPrompt }
        });
      },
      onClose: () => setConnected(false),
      onMessage
    });
    socket.connect();
    socketRef.current = socket;
  }

  async function startCapture() {
    const mic = micRef.current;
    const socket = socketRef.current;
    if (!mic || !socket) {
      return;
    }

    await mic.start({
      deviceId: selectedDeviceId || undefined,
      onChunk: (chunk) => {
        socket.send({ type: "audio", chunk_b64: chunk, codec: "audio/webm", sample_rate: 48000, seq: Date.now() });
      },
      onLevel: (level) => {
        setVuLevel(level);
        setWaveform((prev) => [...prev.slice(-30), Math.max(0.05, level)]);
      }
    });
  }

  function stopCapture() {
    micRef.current?.stop();
    socketRef.current?.send({ type: "stop" });
  }

  async function runTurn() {
    if (!turnInput.trim()) {
      return;
    }

    setBusyTurn(true);
    setState("thinking");
    try {
      const response = await api.postConvoTurn({
        session_id: sessionIdRef.current,
        voice_id: voiceId || undefined,
        text: turnInput,
        latency_mode: latencyMode,
        nuance,
        agent_prompt: agentPrompt
      });

      setFinalTexts((prev) => [...prev, response.user_text]);
      setAgentFinals((prev) => [...prev, response.agent_text]);
      const audio = new Audio(api.getFileUrl(response.audio_url));
      await audio.play().catch(() => undefined);
      setState("listening");
    } finally {
      setBusyTurn(false);
    }
  }

  function newSession() {
    sessionIdRef.current = `session_${crypto.randomUUID().slice(0, 8)}`;
    setFinalTexts([]);
    setAgentFinals([]);
    setAgentStream("");
    setPartialText("");
    setState("idle");
    setConnected(false);
    socketRef.current?.disconnect();
  }

  function exportTranscript() {
    const payload = {
      user: finalTexts,
      assistant: agentFinals,
      session_id: sessionIdRef.current
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `echolabs-transcript-${sessionIdRef.current}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="screen-grid">
      <GlassCard title="Echo Agents Playground">
        <div className="inline-grid two">
          <DropdownSelect
            label="Mic Device"
            value={selectedDeviceId}
            onChange={(event) => setSelectedDeviceId(event.target.value)}
            options={[
              { label: "Default Device", value: "" },
              ...devices.map((device) => ({ label: device.label || "Microphone", value: device.deviceId }))
            ]}
          />
          <DropdownSelect
            label="Echo Voice Profile"
            value={voiceId}
            onChange={(event) => setVoiceId(event.target.value)}
            options={
              voices.length > 0
                ? voices.map((voice) => ({ label: voice.name, value: voice.voice_id }))
                : [{ label: "Default Voice", value: "" }]
            }
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
            label="Latency Mode"
            value={latencyMode}
            onChange={(event) => setLatencyMode(event.target.value as "balanced" | "low" | "ultra_low")}
            options={[
              { label: "Balanced", value: "balanced" },
              { label: "Low", value: "low" },
              { label: "Ultra Low", value: "ultra_low" }
            ]}
          />
        </div>

        <GlassInput
          label="Agent Prompt"
          value={agentPrompt}
          onChange={(event) => setAgentPrompt(event.target.value)}
          placeholder="Set behavior for your Echo agent"
        />

        <GlassInput
          label="Text Turn"
          value={turnInput}
          onChange={(event) => setTurnInput(event.target.value)}
          placeholder="Send a text turn to the agent"
        />

        <ToggleSwitch label="Live Mic Mode" checked={liveMode} onChange={setLiveMode} />

        <div className="inline-actions">
          <GlassButton onClick={connect}>{connected ? "Reconnect" : "Connect"}</GlassButton>
          <GlassButton onClick={runTurn} disabled={busyTurn}>
            {busyTurn ? "Thinking..." : "Send Turn"}
          </GlassButton>
          <GlassButton onClick={startCapture} disabled={!connected || !liveMode}>
            Push To Talk
          </GlassButton>
          <GlassButton onClick={stopCapture} disabled={!connected || !liveMode}>
            Stop
          </GlassButton>
          <GlassButton onClick={newSession}>New Session</GlassButton>
          <GlassButton onClick={exportTranscript}>Export Transcript</GlassButton>
        </div>

        <div className="inline-grid two">
          <VuMeter level={vuLevel} />
          <p>Latency: {pingMs} ms</p>
        </div>
        <WaveformCanvas values={waveform} />
      </GlassCard>

      <GlassCard title="Transcript Stream">
        <p className="muted">State: {state}</p>
        <p>
          <strong>Partial:</strong> {partialText || "..."}
        </p>
        <div className="transcript-block">
          {finalTexts.map((line, index) => (
            <p key={`user-${index}`} className="text-final">
              {line}
            </p>
          ))}
          {agentStream && <p className="text-stream">{agentStream}</p>}
          {agentFinals.map((line, index) => (
            <p key={`agent-${index}`} className="text-assistant">
              {line}
            </p>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}

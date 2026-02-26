import { useEffect, useMemo, useState } from "react";

import logoUrl from "./assets/echolabs-logo.svg";
import { StatusPill } from "./components/StatusPill";
import { WaveBackground } from "./components/WaveBackground";
import { api } from "./lib/api";
import type { MetaResponse, VoiceRecord } from "./lib/schema";
import { RealtimePlayground } from "./screens/RealtimePlayground";
import { SettingsScreen } from "./screens/Settings";
import { SttStudio } from "./screens/SttStudio";
import { TtsStudio } from "./screens/TtsStudio";
import { VoiceVault } from "./screens/VoiceVault";

type ScreenKey = "realtime" | "tts" | "stt" | "vault" | "settings";
type ThemeMode = "dark" | "light";

const TABS: Array<{ key: ScreenKey; label: string }> = [
  { key: "realtime", label: "Agents" },
  { key: "tts", label: "TTS" },
  { key: "stt", label: "STT" },
  { key: "vault", label: "Voices" },
  { key: "settings", label: "Settings" }
];

function App() {
  const [activeScreen, setActiveScreen] = useState<ScreenKey>("realtime");
  const [meta, setMeta] = useState<MetaResponse | null>(null);
  const [status, setStatus] = useState<"CONNECTED" | "DEGRADED" | "OFFLINE">("OFFLINE");
  const [voices, setVoices] = useState<VoiceRecord[]>([]);
  const [theme, setTheme] = useState<ThemeMode>("dark");

  useEffect(() => {
    const saved = localStorage.getItem("echolabs-theme");
    if (saved === "dark" || saved === "light") {
      setTheme(saved);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("echolabs-theme", theme);
  }, [theme]);

  useEffect(() => {
    api
      .getMeta()
      .then((payload) => {
        setMeta(payload);
        setStatus("CONNECTED");
      })
      .catch(() => {
        setStatus("OFFLINE");
      });

    api
      .listVoices()
      .then(setVoices)
      .catch(() => setVoices([]));
  }, []);

  const screenNode = useMemo(() => {
    if (activeScreen === "realtime") {
      return <RealtimePlayground voices={voices} />;
    }
    if (activeScreen === "tts") {
      return <TtsStudio voices={voices} />;
    }
    if (activeScreen === "stt") {
      return <SttStudio />;
    }
    if (activeScreen === "vault") {
      return <VoiceVault onVoicesChanged={setVoices} />;
    }
    return <SettingsScreen />;
  }, [activeScreen, voices]);

  return (
    <div className="app-shell" data-theme={theme}>
      <WaveBackground />
      <header className="topbar glass-panel">
        <div className="brand-wrap">
          <img src={logoUrl} alt="EchoLabs logo" className="brand-logo" />
          <div>
            <h1>EchoLabs</h1>
            <p>Eburon AI</p>
          </div>
        </div>

        <div className="topbar-right">
          <button
            type="button"
            className="theme-toggle"
            onClick={() => setTheme((prev) => (prev === "dark" ? "light" : "dark"))}
          >
            {theme === "dark" ? "Light" : "Dark"}
          </button>
          <StatusPill state={status} />
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar glass-panel">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              className={`sidebar-tab ${activeScreen === tab.key ? "active" : ""}`}
              onClick={() => setActiveScreen(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </aside>

        <main className="main-content">{screenNode}</main>
      </div>
    </div>
  );
}

export default App;

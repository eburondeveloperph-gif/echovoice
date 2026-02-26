import { useMemo, useState } from "react";

import { GlassButton } from "../components/GlassButton";
import { GlassCard } from "../components/GlassCard";
import { GlassInput } from "../components/GlassInput";
import { ToggleSwitch } from "../components/ToggleSwitch";
import { api } from "../lib/api";
import type { AdminConfig } from "../lib/schema";

const EMPTY_CONFIG: AdminConfig = {
  Sugar: "",
  Salt: "",
  Lime: "echo-tts@v2.5",
  Pepper: true,
  Mint: "echo-stt@v2",
  Cocoa: "clone_mode_default",
  Vanilla: "realtime_mode_default",
  Ice: "120rpm"
};

export function SettingsScreen() {
  const [token, setToken] = useState(localStorage.getItem("echolabs-admin-token") ?? "");
  const [config, setConfig] = useState<AdminConfig>(EMPTY_CONFIG);
  const [status, setStatus] = useState("Admin settings idle.");

  const saveEnabled = useMemo(() => token.trim().length > 0, [token]);

  async function loadConfig() {
    if (!token.trim()) {
      return;
    }
    const next = await api.getAdminConfig(token.trim());
    setConfig(next);
    setStatus("Loaded obfuscated admin settings.");
  }

  async function saveConfig() {
    if (!token.trim()) {
      return;
    }
    const next = await api.updateAdminConfig(token.trim(), config);
    setConfig(next);
    localStorage.setItem("echolabs-admin-token", token.trim());
    setStatus("Saved admin settings.");
  }

  async function testConnection() {
    const ms = await api.pingMs();
    setStatus(`Connection OK (${ms} ms)`);
  }

  return (
    <div className="screen-grid">
      <GlassCard title="Admin Settings">
        <GlassInput
          label="Admin Token"
          type="password"
          value={token}
          onChange={(event) => setToken(event.target.value)}
        />
        <div className="inline-grid two">
          <GlassInput
            label="Sugar"
            value={config.Sugar}
            onChange={(event) => setConfig((prev) => ({ ...prev, Sugar: event.target.value }))}
          />
          <GlassInput
            label="Salt"
            value={config.Salt}
            onChange={(event) => setConfig((prev) => ({ ...prev, Salt: event.target.value }))}
          />
          <GlassInput
            label="Lime"
            value={config.Lime}
            onChange={(event) => setConfig((prev) => ({ ...prev, Lime: event.target.value }))}
          />
          <GlassInput
            label="Mint"
            value={config.Mint}
            onChange={(event) => setConfig((prev) => ({ ...prev, Mint: event.target.value }))}
          />
          <GlassInput
            label="Cocoa"
            value={config.Cocoa}
            onChange={(event) => setConfig((prev) => ({ ...prev, Cocoa: event.target.value }))}
          />
          <GlassInput
            label="Vanilla"
            value={config.Vanilla}
            onChange={(event) => setConfig((prev) => ({ ...prev, Vanilla: event.target.value }))}
          />
          <GlassInput
            label="Ice"
            value={config.Ice}
            onChange={(event) => setConfig((prev) => ({ ...prev, Ice: event.target.value }))}
          />
        </div>
        <ToggleSwitch
          label="Pepper"
          checked={config.Pepper}
          onChange={(value) => setConfig((prev) => ({ ...prev, Pepper: value }))}
        />
        <div className="inline-actions">
          <GlassButton onClick={loadConfig} disabled={!saveEnabled}>
            Load
          </GlassButton>
          <GlassButton onClick={saveConfig} disabled={!saveEnabled}>
            Save
          </GlassButton>
          <GlassButton onClick={testConnection}>Test Connection</GlassButton>
        </div>
        <p>{status}</p>
      </GlassCard>
    </div>
  );
}

# EchoLabs by Eburon AI - FULL To-Do (Backend + Frontend)

Constraint: Provider = ElevenLabs API (server-side only)
Branding: UI/Client must never reveal provider/vendor/model names. Everything is aliased as EchoLabs by Eburon AI.

## 0) Non-Negotiables (Global Rules)
- [ ] UI strings blacklist: "Eleven", "ElevenLabs", "11labs", provider model names, provider endpoints, provider docs links
- [ ] Keys never exposed to browser. All provider calls originate from FastAPI only.
- [ ] All model/provider identifiers are internal-only. UI sees only Eburon alias names:
  - [ ] `echo-tts@v2.5`
  - [ ] `echo-stt@v2`
  - [ ] `echo-realtime@v1`
- [ ] High nuance required: enforce server config for high nuance flag + "2.5 turbo" selection.
- [ ] Docker-first: one `docker compose up` boots API + optional deps.
- [ ] Realtime conversational playground supports streaming mic in + partial transcript + streamed audio out.

## 1) Repo Structure (Monorepo Recommended)
- [ ] Create repo layout:

```text
/backend
  /app
    main.py
    /core
      config.py
      logging.py
      security.py
      cors.py
    /models
      schemas.py
    /routers
      health.py
      meta.py
      tts.py
      stt.py
      voice.py
      convo.py
      admin.py
    /services
      provider_client.py
      alias_models.py
      audio_utils.py
      storage.py
      sessions.py
      guardrails.py
      rate_limit.py
    /workers
      jobs.py
  requirements.txt
  Dockerfile

/ui
  src/
    app/ or pages/
    components/
      GlassCard.tsx
      GlassButton.tsx
      GlassInput.tsx
      StatusPill.tsx
      WaveBackground.tsx
      WaveformCanvas.tsx
      VuMeter.tsx
    screens/
      RealtimePlayground.tsx
      TtsStudio.tsx
      SttStudio.tsx
      VoiceVault.tsx
      Settings.tsx
    lib/
      api.ts
      schema.ts
      audio.ts
      ws.ts
    styles/
      tokens.css
      globals.css
  Dockerfile
  nginx/caddy

docker-compose.yml
README.md
```

- [ ] Ensure `/data` volume mounts for:
  - [ ] `/data/uploads`
  - [ ] `/data/outputs`
  - [ ] `/data/voices`
  - [ ] `/data/config`

## 2) Backend - FastAPI + Docker

### 2.1 Docker & Env
- [ ] Build backend Dockerfile:
  - [ ] Python slim
  - [ ] install deps
  - [ ] uvicorn startup
- [ ] Create `docker-compose.yml` services:
  - [ ] api (FastAPI)
  - [ ] redis (optional)
  - [ ] worker (optional)
  - [ ] reverse proxy (optional)
- [ ] Create `.env` template (server-side only):
  - [ ] `ECHOLABS_SUGAR=<provider_api_key>`
  - [ ] `ECHOLABS_SALT=<provider_base_url_or_region>`
  - [ ] `ECHOLABS_LIME=echo-tts@v2.5` alias mapping -> provider 2.5 turbo
  - [ ] `ECHOLABS_PEPPER=true` high nuance enabled
  - [ ] `ECHOLABS_MINT=echo-stt@v2`
  - [ ] `ECHOLABS_COCOA=clone_mode_default`
  - [ ] `ECHOLABS_VANILLA=realtime_mode_default`
  - [ ] `ECHOLABS_ICE=rate_limit_settings`
- [ ] Implement config loader in `core/config.py` (pydantic settings, do not log secrets)

### 2.2 API Baseline
- [ ] Create `/health` route: `GET /health -> { status: "ok", ts, version }`
- [ ] Create `/v1/meta` route returning only alias models + UI-safe flags

### 2.3 Guardrails (No Vendor Disclosure)
- [ ] Implement `services/guardrails.py`:
  - [ ] sanitize outbound responses
  - [ ] denylist provider strings in returned fields
  - [ ] brand-safe answer for provider identity queries
- [ ] Add middleware to strip provider headers and sanitize error bodies

### 2.4 Storage
- [ ] Implement `services/storage.py` for uploads/outputs/voice assets under `/data`
- [ ] Implement secure static file serving: `/files/{path}`

### 2.5 Audio Utilities
- [ ] Implement `services/audio_utils.py`:
  - [ ] normalize audio
  - [ ] resample to backend standard
  - [ ] realtime PCM chunking
  - [ ] safe limits (duration/size/sample-rate/channels)

### 2.6 Provider Client (Internal Wrapper)
- [ ] Implement `services/provider_client.py` to call ElevenLabs internally:
  - [ ] TTS
  - [ ] STT
  - [ ] Voice clone
  - [ ] Realtime proxy
- [ ] Implement `services/alias_models.py`:
  - [ ] alias -> provider config
  - [ ] enforce high nuance + 2.5 turbo server-side
- [ ] Map provider errors to EchoLabs-safe error codes/messages

### 2.7 TTS Endpoints
- [ ] `POST /v1/tts` (text, voice_id, format, latency_mode, nuance)
- [ ] Return `audio_url`, `duration_ms`, `meta.model_alias=echo-tts@v2.5`
- [ ] Optional `POST /v1/tts/stream`

### 2.8 STT Endpoints
- [ ] `POST /v1/stt` (audio upload, language, diarization)
- [ ] Return transcript, optional words, `meta.model_alias=echo-stt@v2`

### 2.9 Voice Cloning Endpoints
- [ ] `POST /v1/voice/clone`
- [ ] `GET /v1/voice/list`
- [ ] `GET /v1/voice/{voice_id}`
- [ ] `DELETE /v1/voice/{voice_id}` (soft delete recommended)

### 2.10 Realtime Conversational Agent (WS)
- [ ] WS endpoint: `/v1/convo/ws?session_id=...`
- [ ] Client -> Server messages:
  - [ ] `start`
  - [ ] `audio`
  - [ ] `stop`
- [ ] Server -> Client messages:
  - [ ] `stt_partial`
  - [ ] `stt_final`
  - [ ] `agent_delta`
  - [ ] `agent_final`
  - [ ] `tts_audio`
  - [ ] `state`
  - [ ] `error`
- [ ] Implement `services/sessions.py` with rolling memory and prefs
- [ ] Implement orchestration loop (STT partials -> EOU -> agent -> streamed TTS)
- [ ] Add backpressure and queue limits

### 2.11 Admin Settings (Obfuscated Labels)
- [ ] Implement protected `/v1/admin/config`
  - [ ] GET returns obfuscated keys only
  - [ ] POST updates config in `/data/config/config.json` or DB
- [ ] Add private server-only legend file: `/backend/ADMIN_LEGEND.md`

### 2.12 Security & Ops
- [ ] CORS for UI origin only
- [ ] Basic IP rate limiting
- [ ] Upload validation (mime, size, duration)
- [ ] Structured logs with request_id + session_id
- [ ] Never log secrets or raw provider payloads
- [ ] Optional `/metrics`

### 2.13 Tests
- [ ] Unit tests:
  - [ ] alias mapping
  - [ ] guardrails sanitization
  - [ ] audio normalize/chunk
- [ ] Integration tests:
  - [ ] `/v1/tts` -> playable audio
  - [ ] `/v1/stt` -> transcript
  - [ ] `/v1/voice/clone` -> appears in list
  - [ ] WS convo partial transcript + reply audio

## 3) Frontend - Modern Wavy Dark Gradient UI

### 3.1 Framework Setup
- [ ] Choose React stack:
  - [ ] Next.js (recommended)
  - [ ] Vite + React
- [ ] Add TypeScript + ESLint + Prettier
- [ ] Single API base URL config (FastAPI only, no provider keys/endpoints)

### 3.2 Theme Tokens (Dark Gradient + Glass)
- [ ] `styles/tokens.css`:
  - [ ] charcoal -> indigo -> violet background
  - [ ] near-white text + muted secondary text
  - [ ] glass alpha, border, shadow tokens
- [ ] Global layout: TopBar + Sidebar + Main panel

### 3.3 Wavy Background (Must-Have)
- [ ] `WaveBackground` component:
  - [ ] base gradient layer
  - [ ] animated SVG wave overlay
  - [ ] low opacity 0.10-0.20
  - [ ] blend mode soft-light/screen
- [ ] Performance + reduced-motion support

### 3.4 Shared Components (Glassmorphism)
- [ ] Build:
  - [ ] `GlassCard`
  - [ ] `GlassButton`
  - [ ] `GlassInput/Textarea`
  - [ ] `StatusPill`
  - [ ] `WaveformCanvas`
  - [ ] `VuMeter`
  - [ ] `ToggleSwitch`
  - [ ] `DropdownSelect`

### 3.5 API Client
- [ ] Implement `lib/api.ts` for meta/tts/stt/voice endpoints
- [ ] Implement `lib/ws.ts` with reconnect + queue + heartbeat
- [ ] Implement `lib/audio.ts` for mic capture + PCM base64 chunks + optional downsample

### 3.6 Screens
- [ ] `RealtimePlayground`:
  - [ ] mic selector
  - [ ] push-to-talk + live mode
  - [ ] VU + waveform
  - [ ] partial/final transcript panels
  - [ ] agent stream
  - [ ] right-side controls (voice/nuance/latency)
  - [ ] session controls (new/reset/export)
- [ ] `TtsStudio`:
  - [ ] prompt
  - [ ] voice selector
  - [ ] generate
  - [ ] waveform/player
  - [ ] history
  - [ ] export audio
- [ ] `SttStudio`:
  - [ ] drag-drop upload
  - [ ] language
  - [ ] diarization
  - [ ] transcript + timestamps
  - [ ] export JSON/TXT
- [ ] `VoiceVault`:
  - [ ] voice cards
  - [ ] create voice modal (name + multi-sample upload + progress + preview)
- [ ] `Settings` (protected admin):
  - [ ] obfuscated fields only (Sugar/Salt/Lime/Pepper/Mint/Cocoa/Vanilla/Ice)
  - [ ] save + test connection
  - [ ] never show real mapping

### 3.7 UI Copy (Strict)
- [ ] Only use:
  - [ ] EchoLabs
  - [ ] Eburon AI
  - [ ] Echo Voice Profiles
  - [ ] Echo TTS / Echo STT / Echo Realtime
- [ ] Add CI string scan to fail on banned vendor keywords in UI code

### 3.8 UX Polish
- [ ] Subtle hover glow
- [ ] Card lift on hover
- [ ] Smooth transcript updates
- [ ] Latency indicator (backend ping ms)
- [ ] Brand-safe error UX with remediation hints

### 3.9 Frontend Tests
- [ ] Component tests:
  - [ ] WaveBackground renders
  - [ ] WS reconnect
  - [ ] mic capture start/stop
- [ ] E2E smoke:
  - [ ] load app -> meta -> connected
  - [ ] tts generate -> playback
  - [ ] stt upload -> transcript
  - [ ] realtime -> partial transcript -> reply audio

## 4) Delivery Artifacts
- [ ] Working FastAPI backend + Docker compose
- [ ] Working modern frontend with wavy dark gradient + glass UI
- [ ] Functional realtime websocket playground
- [ ] Functional voice cloning workflow
- [ ] Strict vendor masking + CI string blacklist
- [ ] `ADMIN_LEGEND.md` server-side only mapping:
  - [ ] Sugar -> Provider API Key (ElevenLabs)
  - [ ] Salt -> Provider Base Endpoint/Region
  - [ ] Lime -> TTS Model Selector (maps to 2.5 turbo)
  - [ ] Pepper -> High Nuance Flag (required)
  - [ ] Mint -> STT Model Selector
  - [ ] Cocoa -> Voice Clone Mode
  - [ ] Vanilla -> Realtime Mode
  - [ ] Ice -> Limits/Rate settings

## 5) Definition of Done
- [ ] `docker compose up` boots successfully
- [ ] UI loads with wavy dark gradient background and glass panels
- [ ] TTS: text -> audio plays in UI
- [ ] STT: upload audio -> transcript appears
- [ ] Voice cloning: samples -> new voice selectable -> usable in TTS
- [ ] Realtime: mic stream -> partial transcript -> assistant text + streamed audio
- [ ] No vendor strings in UI or API responses
- [ ] Secrets never exposed client-side and logs are sanitized

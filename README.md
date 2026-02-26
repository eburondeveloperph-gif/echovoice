# EchoLabs by Eburon AI

EchoLabs is a Docker-first monorepo with:
- FastAPI backend (`/backend`) for TTS, STT, Voice Vault, realtime websocket conversation, admin config, and file serving.
- React + Vite frontend (`/ui`) with black/lime slow-wave UI and optional light mode.
- Provider calls isolated server-side with brand-safe aliasing in UI/API output.
- Provider voice sync into Echo Voice Profiles with preview phrase generation.
- Agents Playground with live mic websocket mode and text-turn mode.
- Invisible TTS text editor pipeline (lazy-loaded) using remote Ollama with fallback punctuation refinement.

## Monorepo Layout

```text
/backend
/api
/ui
/data
/scripts
/.env.example
/docker-compose.yml
/vercel.json
/SKILL.md
/TODO.md
```

## Quick Start

1. Copy env template:

```bash
cd /Users/master/skills/echovoice
cp .env.example .env
```

2. Start stack:

```bash
docker compose up --build
```

If ports are occupied, adjust `.env`:
- `API_PORT=8010` (host -> container `8000`)
- `UI_PORT=4173` (host -> container `4173`)

3. Open:
- UI: `http://localhost:4173`
- API: `http://localhost:8010`
- Health: `http://localhost:8010/health`

## Backend Local Run (without Docker)

```bash
cd /Users/master/skills/echovoice/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend Local Run (without Docker)

```bash
cd /Users/master/skills/echovoice/ui
npm install
npm run dev -- --host 0.0.0.0 --port 4173
```

## Vercel Deployment

This repo is configured for Vercel with:
- static frontend output from `ui/dist`
- python serverless function at `api/index.py` serving `/v1/*`, `/health`, `/files/*`, and `/metrics`

Set these Vercel environment variables:
- `ECHOLABS_SUGAR`
- `ECHOLABS_SALT`
- `ECHOLABS_DEMO_MODE=false`
- `ECHOLABS_PEPPER=true`
- `ADMIN_TOKEN`
- `UI_ORIGIN` (your deployed app URL)
- `DATA_ROOT=/tmp/echolabs_data`
- `TTS_EDITOR_ENABLED=true`
- `OLLAMA_BASE_URL=http://168.231.78.113:11434`
- `OLLAMA_MODEL=gpt-oss-20b`
- `OLLAMA_EDITOR_SSML=true`

Deploy from repo root:

```bash
vercel --prod
```

Or use the included helper:

```bash
bash scripts/deploy_vercel.sh
```

## Verification

Backend tests:

```bash
cd /Users/master/skills/echovoice/backend
PYTHONPATH=. python3 -m pytest -q
```

Frontend checks:

```bash
cd /Users/master/skills/echovoice/ui
npm run qa:alias
npm run test:run
npm run build
```

## Notes
- UI and public API expose only these aliases:
  - `echo-tts@v2.5`
  - `echo-stt@v2`
  - `echo-realtime@v1`
- Admin panel uses obfuscated labels only: `Sugar/Salt/Lime/Pepper/Mint/Cocoa/Vanilla/Ice`.
- Voice Vault sync endpoint: `POST /v1/voice/sync`
- Voice preview endpoint: `POST /v1/voice/preview/{voice_id}`
- Voice preview phrase: `HI THIS IS ECHO VOICE FROM EBURON AI`
- TTS input is edited server-side only (not shown to user) before synthesis.
- Use `scripts/setup_ollama_vps.sh` for manual VPS setup from your own terminal.
- For offline dev, set `ECHOLABS_DEMO_MODE=true`.

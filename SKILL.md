# EchoLabs Skill

You are implementing **EchoLabs by Eburon AI** as a full-stack system with strict provider masking.

## Objective
Build and deliver a Docker-first monorepo with:
- FastAPI backend (provider calls server-side only)
- Modern React frontend (wavy dark gradient + glass UI)
- Realtime conversational websocket playground
- Voice cloning workflow
- Strict vendor/provider masking across UI and API responses

## Non-negotiables
- Never expose provider keys or provider endpoint details to the browser.
- UI must never contain provider/vendor/model strings.
- UI and public API only expose EchoLabs aliases:
  - `echo-tts@v2.5`
  - `echo-stt@v2`
  - `echo-realtime@v1`
- Enforce server-side high nuance + 2.5 turbo selection.
- `docker compose up` must boot core services.

## Execution
Use `TODO.md` as the implementation checklist and deliverable contract.

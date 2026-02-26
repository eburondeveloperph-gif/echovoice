#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required. Install Node.js first."
  exit 1
fi

echo "Deploying EchoLabs to Vercel (production)..."

echo "Required env vars in Vercel project settings:"
echo "  ECHOLABS_SUGAR, ECHOLABS_SALT, ECHOLABS_DEMO_MODE=false"
echo "  ECHOLABS_PEPPER=true, ADMIN_TOKEN, UI_ORIGIN"
echo "  DATA_ROOT=/tmp/echolabs_data"
echo "  TTS_EDITOR_ENABLED=true, OLLAMA_BASE_URL, OLLAMA_MODEL=gpt-oss-20b"

echo
echo "Running: npx vercel@latest --prod"
exec npx vercel@latest --prod

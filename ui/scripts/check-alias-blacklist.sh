#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_DIR="$ROOT_DIR/src"

BANNED=(
  "Eleven"
  "ElevenLabs"
  "11labs"
  "api.elevenlabs"
  "docs.elevenlabs"
  "eleven_turbo"
  "scribe_v1"
)

FOUND=0
for pattern in "${BANNED[@]}"; do
  if rg -n -i "$pattern" "$TARGET_DIR" >/dev/null 2>&1; then
    echo "Blocked keyword found in UI code: $pattern"
    rg -n -i "$pattern" "$TARGET_DIR"
    FOUND=1
  fi
done

if [[ "$FOUND" -eq 1 ]]; then
  exit 1
fi

echo "Alias blacklist scan passed."

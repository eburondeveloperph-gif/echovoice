#!/usr/bin/env bash
set -euo pipefail

VPS_HOST="${1:-168.231.78.113}"
VPS_USER="${2:-root}"
MODEL="${3:-gpt-oss-20b}"

cat <<MSG
Run the following on your local machine (interactive SSH):

ssh ${VPS_USER}@${VPS_HOST}

# then on VPS:
curl -fsSL https://ollama.com/install.sh | sh
mkdir -p /etc/systemd/system/ollama.service.d
cat >/etc/systemd/system/ollama.service.d/override.conf <<'EOC'
[Service]
Environment=OLLAMA_HOST=0.0.0.0:11434
EOC
systemctl daemon-reload
systemctl enable --now ollama
ollama pull ${MODEL}

# verify:
curl http://127.0.0.1:11434/api/tags
MSG

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Serverless-safe defaults for Vercel runtime
os.environ.setdefault("DATA_ROOT", "/tmp/echolabs_data")
os.environ.setdefault("CORS_ORIGINS", os.environ.get("UI_ORIGIN", "*"))

from app.main import app  # noqa: E402

from __future__ import annotations


def run_background_job(name: str) -> str:
    return f"job:{name}:queued"

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class Turn:
    user: str
    assistant: str
    ts: str


@dataclass(slots=True)
class SessionState:
    session_id: str
    voice_id: str | None = None
    latency_mode: str = "balanced"
    nuance: float = 0.8
    agent_prompt: str | None = None
    turns: deque[Turn] = field(default_factory=deque)


class SessionManager:
    def __init__(self, max_turns: int = 10) -> None:
        self._sessions: dict[str, SessionState] = {}
        self.max_turns = max_turns

    def get_or_create(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]

    def reset(self, session_id: str) -> SessionState:
        state = SessionState(session_id=session_id)
        self._sessions[session_id] = state
        return state

    def append_turn(self, session_id: str, user: str, assistant: str) -> None:
        state = self.get_or_create(session_id)
        state.turns.append(
            Turn(user=user, assistant=assistant, ts=datetime.now(tz=timezone.utc).isoformat())
        )
        while len(state.turns) > self.max_turns:
            state.turns.popleft()

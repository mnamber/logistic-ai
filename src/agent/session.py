"""In-process session memory. Replace with Redis or a DB for multi-instance deployments."""

from collections import defaultdict
from datetime import datetime, timezone

_store: dict[str, list[dict]] = defaultdict(list)

MAX_HISTORY = 20


class SessionMemory:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    def add_message(self, role: str, content: str) -> None:
        _store[self.session_id].append(
            {"role": role, "content": content, "ts": datetime.now(timezone.utc).isoformat()}
        )

    def get_history(self) -> list[dict]:
        """Return last MAX_HISTORY messages in OpenAI message format (no timestamp)."""
        msgs = _store[self.session_id][-MAX_HISTORY:]
        return [{"role": m["role"], "content": m["content"]} for m in msgs]

    def clear(self) -> None:
        _store[self.session_id] = []

# velvet/core/schemas/events.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


def _now_ts() -> float:
    # Keep time import local (tiny + avoids import cycles)
    import time
    return float(time.time())


@dataclass(frozen=True)
class Event:
    """
    Standard event envelope for Velvet's event bus.
    """
    ts: float
    topic: str
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"ts": self.ts, "topic": self.topic, "data": self.data}


def make_event(topic: str, data: Optional[Dict[str, Any]] = None) -> Event:
    return Event(ts=_now_ts(), topic=str(topic), data=dict(data or {}))


# ---- Minimal validators (best-effort; keep core dependency-free) ----

def require_fields(obj: Dict[str, Any], *fields: str) -> None:
    for f in fields:
        if f not in obj:
            raise ValueError(f"Missing field: {f}")

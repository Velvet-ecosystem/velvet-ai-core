"""Translate incoming event records into factual observations."""

from __future__ import annotations

from typing import Any, Mapping

from .models import Observation


class Observer:
    """Record event facts without interpretation."""

    def observe(self, event: Mapping[str, Any]) -> Observation:
        return Observation(
            event_type=str(event.get("type", "unknown")),
            source=str(event.get("source", "unknown")),
            payload=dict(event.get("payload", {})),
        )

"""Context construction for Native Brain decisions."""

from __future__ import annotations

from typing import Any, Mapping

from .models import BrainContext


class ContextBuilder:
    """Build a bounded working context from trusted runtime state."""

    def build(self, state: Mapping[str, Any] | None = None) -> BrainContext:
        state = state or {}
        return BrainContext(
            runtime_mode=str(state.get("runtime_mode", "unknown")),
            court_permissions=tuple(state.get("court_permissions", ())),
            presence=str(state.get("presence", "unknown")),
            active_scene=state.get("active_scene"),
            recent_events=tuple(state.get("recent_events", ())),
            active_organs=tuple(state.get("active_organs", ())),
            world_state=dict(state.get("world_state", {})),
        )

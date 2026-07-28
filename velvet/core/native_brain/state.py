# SPDX-License-Identifier: GPL-3.0-only
"""Native Brain v0 shared state.

State is descriptive. It records what Velvet currently knows. It does not grant
authority, select executors, or touch hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional


@dataclass
class NativeBrainState:
    """Small shared state snapshot for the first Native Brain loop."""

    owner_present: bool = False
    guest_present: bool = False
    system_mode: str = "offline_demo"
    active_scene: Optional[str] = None
    vehicle_state: Dict[str, Any] = field(default_factory=dict)
    cabin_state: Dict[str, Any] = field(default_factory=dict)
    recent_events: List[str] = field(default_factory=list)
    known_faults: Dict[str, Any] = field(default_factory=dict)
    attention_state: str = "background"

    def update_from_ghost_observation(self, payload: Mapping[str, Any]) -> None:
        """Update descriptive state from a validated ghost CAN observation."""

        event_type = str(payload.get("event_type", "unknown"))
        self.recent_events.append(event_type)
        self.recent_events = self.recent_events[-10:]

        signals = payload.get("signals", {})
        if isinstance(signals, Mapping):
            for name, signal in signals.items():
                if isinstance(signal, Mapping):
                    value = signal.get("value")
                else:
                    value = signal
                self.vehicle_state[str(name)] = value

            o2_value = self.vehicle_state.get("o2_fault")
            if o2_value not in (None, "", "none", "clear", "ok"):
                self.known_faults["o2_fault"] = o2_value

        profile = payload.get("vehicle_profile") or payload.get("profile")
        if profile:
            self.vehicle_state["vehicle_profile"] = str(profile)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner_present": self.owner_present,
            "guest_present": self.guest_present,
            "system_mode": self.system_mode,
            "active_scene": self.active_scene,
            "vehicle_state": dict(self.vehicle_state),
            "cabin_state": dict(self.cabin_state),
            "recent_events": list(self.recent_events),
            "known_faults": dict(self.known_faults),
            "attention_state": self.attention_state,
        }

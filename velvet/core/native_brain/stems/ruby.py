# SPDX-License-Identifier: GPL-3.0-only
"""Ruby stem: engine and diagnostics observation only."""

from __future__ import annotations

from typing import Any, Mapping

from velvet.core.ghost_can import GHOST_CAN_EVENT_TYPE
from ..handmaiden_stem import HandmaidenStem, StemResult


class RubyStem(HandmaidenStem):
    def __init__(self) -> None:
        super().__init__(
            name="ruby",
            title="Engine and Diagnostics",
            domain=("vehicle", "can", "diagnostics", "engine"),
            can_observe=("vehicle_speed", "engine_rpm", "ignition_state", "o2_fault"),
            can_suggest=("diagnostic_note", "inspection_note", "log_event"),
            must_not=("write_can", "start_engine", "clear_fault", "command_actuator"),
            memory_scope="diagnostic_observation",
            handoff={"continuity": "velour"},
        )

    def interpret(self, payload: Mapping[str, Any]) -> StemResult:
        signals = payload.get("signals", {})
        if payload.get("event_type") != GHOST_CAN_EVENT_TYPE or not isinstance(signals, Mapping):
            return StemResult(self.name, False, "Ruby found no diagnostic ghost observation.")

        speed = _signal_value(signals, "vehicle_speed", "unknown")
        rpm = _signal_value(signals, "engine_rpm", "unknown")
        ignition = _signal_value(signals, "ignition_state", "unknown")
        o2_fault = _signal_value(signals, "o2_fault", "none")
        summary = (
            "Ruby reads vehicle_speed=%s, engine_rpm=%s, ignition_state=%s, "
            "o2_fault=%s. Observation only." % (speed, rpm, ignition, o2_fault)
        )
        return StemResult(
            stem=self.name,
            domain_match=True,
            summary=summary,
            suggested_memory={
                "kind": self.memory_scope,
                "fault": "o2_fault",
                "fault_value": o2_fault,
                "public_safe": True,
            },
            authority_requested=False,
            blocked=False,
            handoff=["velour"],
        )


def _signal_value(signals: Mapping[str, Any], name: str, default: Any) -> Any:
    signal = signals.get(name)
    if isinstance(signal, Mapping):
        return signal.get("value", default)
    return default if signal is None else signal

# SPDX-License-Identifier: GPL-3.0-only
"""No-LLM response rendering for Velvet Native Brain v0."""

from __future__ import annotations

from typing import Any, Mapping


def render_no_llm_ghost_response(payload: Mapping[str, Any]) -> str:
    profile = payload.get("vehicle_profile") or payload.get("profile") or "Ghost vehicle"
    signals = payload.get("signals", {})

    speed = _signal_value(signals, "vehicle_speed", "unknown")
    rpm = _signal_value(signals, "engine_rpm", "unknown")
    ignition = _signal_value(signals, "ignition_state", "unknown")
    o2_fault = _signal_value(signals, "o2_fault", "none")

    return (
        "%s observed. Ignition %s, speed %s, RPM %s, simulated O2 fault %s. "
        "No authority requested."
        % (profile, ignition, speed, rpm, o2_fault)
    )


def _signal_value(signals: Any, name: str, default: Any) -> Any:
    if isinstance(signals, Mapping):
        signal = signals.get(name)
        if isinstance(signal, Mapping):
            return signal.get("value", default)
        if signal is not None:
            return signal
    return default

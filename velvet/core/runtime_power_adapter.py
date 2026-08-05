"""Adapter from Runtime power-state payloads to the AI Core power governor."""

from __future__ import annotations

from typing import Any, Mapping

from velvet.core.power_governor import (
    PowerDecision,
    PowerGovernor,
    PowerState,
    WorkloadRequest,
)

_REQUIRED = (
    "ignition_on",
    "battery_voltage",
    "charging",
    "temperature_c",
    "node_healthy",
    "owner_present",
    "runtime_mode",
)


def decide_runtime_power(
    governor: PowerGovernor,
    request: WorkloadRequest,
    payload: Mapping[str, Any],
) -> PowerDecision:
    if not isinstance(payload, Mapping):
        raise TypeError("runtime power payload must be a mapping")
    missing = [name for name in _REQUIRED if name not in payload]
    if missing:
        raise ValueError(
            "runtime power payload is missing: %s" % ",".join(missing)
        )

    state = PowerState(
        ignition_on=bool(payload["ignition_on"]),
        battery_voltage=float(payload["battery_voltage"]),
        charging=bool(payload["charging"]),
        temperature_c=float(payload["temperature_c"]),
        node_healthy=bool(payload["node_healthy"]),
        owner_present=bool(payload["owner_present"]),
        runtime_mode=str(payload["runtime_mode"]),
    )
    return governor.decide(request, state)


def power_decision_payload(decision: PowerDecision) -> Mapping[str, Any]:
    return {
        "workload_id": decision.workload_id,
        "disposition": decision.disposition.value,
        "reasons": decision.reasons,
        "authority_granted": decision.authority_granted,
        "execution_performed": decision.execution_performed,
    }

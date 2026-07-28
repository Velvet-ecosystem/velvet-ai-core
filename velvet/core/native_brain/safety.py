# SPDX-License-Identifier: GPL-3.0-only
"""No-authority safety checks for Velvet Native Brain v0.

Native Brain v0 may observe, classify, remember, and explain. It must not become
an execution lane around Runtime. These checks are deliberately strict because
the preserved first loop is synthetic and read-only.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping


class NativeBrainSafetyError(ValueError):
    """Raised when a Native Brain payload crosses the public v0 boundary."""


REQUIRED_TRUE_FLAGS = ("read_only", "synthetic_fixture", "synthetic")

REQUIRED_FALSE_FLAGS = (
    "physical_bus_opened",
    "hardware_bus_opened",
    "can_transmission_attempted",
    "can_transmission_performed",
    "actuation_granted",
    "actuation_performed",
    "authority_granted",
)

FORBIDDEN_AUTHORITY_KEYS = frozenset(
    {
        "command", "cmd", "executor", "executor_name", "route_id", "target",
        "hardware_target", "capability", "capabilities", "capability_token",
        "token", "secret", "shell", "subprocess", "callable", "module_path",
        "python_callable", "write", "transmit", "inject", "send", "actuate",
        "actuator", "relay", "can_id_to_write", "frame_to_send",
        "can_payload_to_send", "steering", "throttle", "brake", "clutch",
        "shifter", "unlock", "start_vehicle", "medical_takeover", "driver_assist",
    }
)


def validate_no_authority_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a preserved Native Brain v0 Ghost observation payload."""

    if not isinstance(payload, Mapping):
        raise TypeError("native brain payload must be a mapping")

    normalized = dict(payload)
    _reject_forbidden_keys(normalized)

    for flag in REQUIRED_TRUE_FLAGS:
        if normalized.get(flag) is not True:
            raise NativeBrainSafetyError(
                "%s must be true for Native Brain v0 Ghost observations" % flag
            )

    for flag in REQUIRED_FALSE_FLAGS:
        if normalized.get(flag) is not False:
            raise NativeBrainSafetyError(
                "%s must be false for Native Brain v0 Ghost observations" % flag
            )

    return normalized


def authority_report() -> Dict[str, bool]:
    """Return the fixed authority truth for the preserved v0 Ghost loop."""

    return {
        "requested": False,
        "granted": False,
        "runtime_required": False,
        "hardware_touched": False,
    }


def _reject_forbidden_keys(obj: Any, path: str = "payload") -> None:
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            if isinstance(key, str) and key.strip().lower() in FORBIDDEN_AUTHORITY_KEYS:
                raise NativeBrainSafetyError(
                    "forbidden authority key in Native Brain v0 payload: %s.%s"
                    % (path, key)
                )
            _reject_forbidden_keys(value, "%s.%s" % (path, key))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            _reject_forbidden_keys(value, "%s[%d]" % (path, index))

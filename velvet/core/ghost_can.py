# SPDX-License-Identifier: GPL-3.0-only
"""Public-safe Core models for Ghost CAN observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from velvet.core.authority import AuthorityContext, Court, Intent, Receipt
from velvet.core.schemas.memory import MemoryKind, MemoryRecord

GHOST_CAN_EVENT_TYPE = "vehicle.can.ghost_observation"
GHOST_CAN_ACTION = "describe_ghost_can_observation"
GHOST_CAN_TARGET = "vehicle-can-ghost"
GHOST_CAN_SOURCE = "velvet-ai-core.ghost_can"
_REQUIRED_TRUE_FLAGS = ("read_only", "synthetic_fixture", "synthetic")
_REQUIRED_FALSE_FLAGS = ("physical_bus_opened", "hardware_bus_opened", "can_transmission_attempted", "can_transmission_performed", "actuation_granted", "actuation_performed", "authority_granted")
_FORBIDDEN_KEYS = frozenset({"command","cmd","executor","executor_name","route_id","target","hardware_target","capability","capabilities","capability_token","token","secret","shell","subprocess","callable","module_path","python_callable","write","transmit","inject","send","actuate","actuator","relay","can_id_to_write","frame_to_send"})


def _clamp_confidence(value: Any) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError("confidence must be numeric")
    numeric = float(value)
    if not 0.0 <= numeric <= 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")
    return numeric


@dataclass(frozen=True)
class GhostCanProposal:
    observation: Dict[str, Any]
    actor: str = "velvet-core"
    action: str = GHOST_CAN_ACTION
    target: str = GHOST_CAN_TARGET
    reason: str = "summarize synthetic read-only vehicle telemetry"
    tags: Tuple[str, ...] = field(default=("ghost-can", "observation-only", "public-demo"))

    def __post_init__(self) -> None:
        object.__setattr__(self, "observation", validate_ghost_can_observation(self.observation))
        if not isinstance(self.actor, str) or not self.actor.strip():
            raise ValueError("actor must be a non-empty string")

    def to_intent(self) -> Intent:
        return Intent(
            action=self.action,
            actor=self.actor.strip(),
            target=self.target,
            parameters={"event_type": GHOST_CAN_EVENT_TYPE, "observation": dict(self.observation), "reason": self.reason, "tags": list(self.tags)},
            requires_physical_presence=False,
            privilege_elevation=False,
        )

    def to_memory_record(self, receipt_id: Optional[str] = None) -> MemoryRecord:
        return ghost_can_memory_record(self.observation, receipt_id=receipt_id)


def validate_ghost_can_observation(payload: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise TypeError("ghost CAN observation must be a mapping")
    normalized = dict(payload)
    if normalized.get("event_type", GHOST_CAN_EVENT_TYPE) != GHOST_CAN_EVENT_TYPE:
        raise ValueError("event_type must be %s" % GHOST_CAN_EVENT_TYPE)
    normalized["event_type"] = GHOST_CAN_EVENT_TYPE
    _reject_forbidden_keys(normalized)
    for flag in _REQUIRED_TRUE_FLAGS:
        if normalized.get(flag) is not True:
            raise ValueError("%s must be true for ghost CAN observations" % flag)
    for flag in _REQUIRED_FALSE_FLAGS:
        if normalized.get(flag) is not False:
            raise ValueError("%s must be false for ghost CAN observations" % flag)
    signals = normalized.get("signals")
    if not isinstance(signals, Mapping) or not signals:
        raise ValueError("signals must be a non-empty mapping")
    normalized_signals: Dict[str, Dict[str, Any]] = {}
    for name, signal in signals.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("signal names must be non-empty strings")
        if not isinstance(signal, Mapping):
            raise ValueError("signal %s must be a mapping" % name)
        signal_copy = dict(signal)
        _reject_forbidden_keys(signal_copy)
        unit = signal_copy.get("unit", "")
        if not isinstance(unit, str):
            raise ValueError("signal %s unit must be a string" % name)
        signal_copy["unit"] = unit
        signal_copy["confidence"] = _clamp_confidence(signal_copy.get("confidence", 1.0))
        normalized_signals[name.strip()] = signal_copy
    normalized["signals"] = normalized_signals
    return normalized


def build_ghost_can_proposal(payload: Mapping[str, Any], actor: str = "velvet-core") -> GhostCanProposal:
    return GhostCanProposal(observation=validate_ghost_can_observation(payload), actor=actor)


def ghost_can_authority_context() -> AuthorityContext:
    return AuthorityContext(presence_verified=False, allowed_actions=frozenset({GHOST_CAN_ACTION}), allowed_targets=frozenset({GHOST_CAN_TARGET}))


def evaluate_ghost_can_proposal(proposal: GhostCanProposal) -> Receipt:
    return Court().evaluate(proposal.to_intent(), ghost_can_authority_context())


def summarize_ghost_can_observation(payload: Mapping[str, Any]) -> str:
    observation = validate_ghost_can_observation(payload)
    title = str(observation.get("vehicle_profile") or observation.get("profile") or "Ghost vehicle")
    source = str(observation.get("source", "synthetic fixture"))
    parts: List[str] = []
    for name in sorted(observation["signals"]):
        signal = observation["signals"][name]
        value, unit = signal.get("value"), signal.get("unit", "")
        parts.append("%s=%s %s" % (name, value, unit) if unit else "%s=%s" % (name, value))
    return "%s ghost observation from %s: %s. Read-only synthetic fixture; no physical bus opened, no authority granted." % (title, source, ", ".join(parts))


def ghost_can_memory_record(payload: Mapping[str, Any], receipt_id: Optional[str] = None) -> MemoryRecord:
    observation = validate_ghost_can_observation(payload)
    return MemoryRecord(
        kind=MemoryKind.OBSERVATION.value,
        payload={"event_type": GHOST_CAN_EVENT_TYPE, "summary": summarize_ghost_can_observation(observation), "observation": observation, "authority_boundary": "observation_only_no_physical_authority"},
        source=GHOST_CAN_SOURCE,
        confidence=_minimum_signal_confidence(observation["signals"].values()),
        authority_status="observation_only",
        receipt_id=receipt_id,
        tags=["ghost-can", "synthetic-fixture", "read-only", "public-demo"],
    )


def _minimum_signal_confidence(signals: Iterable[Mapping[str, Any]]) -> float:
    values = [_clamp_confidence(signal.get("confidence", 1.0)) for signal in signals]
    return min(values) if values else 1.0


def _reject_forbidden_keys(obj: Any, path: str = "payload") -> None:
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            if isinstance(key, str) and key.strip().lower() in _FORBIDDEN_KEYS:
                raise ValueError("forbidden authority key in ghost CAN observation: %s.%s" % (path, key))
            _reject_forbidden_keys(value, "%s.%s" % (path, key))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            _reject_forbidden_keys(value, "%s[%d]" % (path, index))

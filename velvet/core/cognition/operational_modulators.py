# SPDX-License-Identifier: GPL-3.0-only
"""Bounded operational modulators for attention and presentation.

Modulators are descriptive shared variables. They cannot alter Court,
authentication, capabilities, executors, safety gates, or receipt policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple
from uuid import uuid4

from .workspace_context import CognitiveWorkspaceContext

CONTRACT = "velvet.cognitive-events.v1"
SCHEMA_VERSION = "1.0"
MODULATORS_SNAPSHOTTED = "cognitive.modulators.snapshotted"

MODULATOR_NAMES = (
    "arousal",
    "novelty",
    "uncertainty",
    "urgency",
    "social_engagement",
    "resource_pressure",
    "prediction_stability",
)

_BASELINES = {
    "arousal": 0.0,
    "novelty": 0.0,
    "uncertainty": 0.0,
    "urgency": 0.0,
    "social_engagement": 0.0,
    "resource_pressure": 0.0,
    "prediction_stability": 1.0,
}
_MAX_RATE = {
    "arousal": 0.8,
    "novelty": 1.0,
    "uncertainty": 0.6,
    "urgency": 1.0,
    "social_engagement": 0.5,
    "resource_pressure": 0.5,
    "prediction_stability": 0.25,
}
_DECAY_RATE = {
    "arousal": 0.12,
    "novelty": 0.25,
    "uncertainty": 0.08,
    "urgency": 0.20,
    "social_engagement": 0.05,
    "resource_pressure": 0.04,
    "prediction_stability": 0.02,
}
_SOURCE_ALLOWLIST = {
    "arousal": {"salience", "presence", "driving-demand"},
    "novelty": {"salience", "world-model"},
    "uncertainty": {"prediction", "world-model", "sensor-health"},
    "urgency": {"salience", "runtime-health"},
    "social_engagement": {"presence", "turn-taking"},
    "resource_pressure": {"runtime-resource"},
    "prediction_stability": {"prediction"},
}
_CONSUMER_ALLOWLIST = {
    "turn-taking": {
        "arousal",
        "novelty",
        "uncertainty",
        "urgency",
        "social_engagement",
        "prediction_stability",
    },
    "interface": set(MODULATOR_NAMES),
    "logging": {"uncertainty", "urgency", "resource_pressure"},
    "learning-observer": {"novelty", "uncertainty", "prediction_stability"},
}
_FORBIDDEN_CONSUMERS = {
    "court",
    "authentication",
    "capability",
    "executor",
    "safety-gate",
    "receipt-writer",
}
_TRUST_CONTEXTS = {
    "owner_verified",
    "guest_verified",
    "maintenance",
    "unknown",
    "disputed",
}
_FLAGS = {
    "interpretation_only": True,
    "transport_only": True,
    "canonical_evidence": False,
    "authority": "none",
    "grants_authority": False,
    "grants_execution": False,
    "grants_actuation": False,
    "replay_safe": True,
}
_FORBIDDEN_KEYS = {
    "actuate",
    "actuation",
    "authorization",
    "authorized",
    "authorized_by",
    "capability",
    "capability_token",
    "command",
    "court_decision",
    "court_token",
    "execution_token",
    "executor",
    "executor_handle",
    "executor_name",
    "hardware_handle",
    "hardware_target",
    "permit",
    "policy_override",
    "retry_authorized",
    "safety_override",
    "shell",
    "token",
}


@dataclass(frozen=True)
class ModulatorUpdate:
    update_id: str
    source: str
    body_id: str
    node_id: str
    cognitive_event_id: str
    values: Mapping[str, float]
    source_refs: Tuple[str, ...]
    correlation_ids: Tuple[str, ...] = ()
    monotonic_time: float = 0.0
    replay_state: str = "live"

    def __post_init__(self) -> None:
        for name, value in (
            ("update_id", self.update_id),
            ("source", self.source),
            ("body_id", self.body_id),
            ("node_id", self.node_id),
            ("cognitive_event_id", self.cognitive_event_id),
        ):
            _text(name, value)
        if not isinstance(self.values, Mapping) or not self.values:
            raise ValueError("values must be a non-empty mapping")
        unknown = set(self.values) - set(MODULATOR_NAMES)
        if unknown:
            raise ValueError("unknown modulators: %s" % sorted(unknown))
        for name, value in self.values.items():
            _ratio(name, value)
            if self.source not in _SOURCE_ALLOWLIST[name]:
                raise ValueError("source %s cannot update %s" % (self.source, name))
        _sequence("source_refs", self.source_refs, True)
        _sequence("correlation_ids", self.correlation_ids)
        _non_negative("monotonic_time", self.monotonic_time)
        if self.replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid replay_state")
        _reject(self.values, "modulator update")


@dataclass(frozen=True)
class ModulatorSnapshot:
    snapshot_id: str
    cognitive_event_id: str
    body_id: str
    node_id: str
    consumer: str
    trust_context: str
    values: Mapping[str, float]
    source_refs: Tuple[str, ...]
    correlation_ids: Tuple[str, ...]
    monotonic_time: float
    replay_state: str

    @property
    def authority_granted(self) -> bool:
        return False

    def read_only_view(self) -> Mapping[str, Any]:
        return _freeze(
            {
                "snapshot_id": self.snapshot_id,
                "cognitive_event_id": self.cognitive_event_id,
                "body_id": self.body_id,
                "node_id": self.node_id,
                "consumer": self.consumer,
                "trust_context": self.trust_context,
                "values": dict(self.values),
                "source_refs": list(self.source_refs),
                "correlation_ids": list(self.correlation_ids),
                "monotonic_time": self.monotonic_time,
                "replay_state": self.replay_state,
                "cannot_change_authority": True,
                "authority_granted": False,
            }
        )

    def to_event_document(self, *, source: str, timestamp: float) -> Dict[str, Any]:
        _text("source", source)
        _non_negative("timestamp", timestamp)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "cognitive_event_id": self.cognitive_event_id,
            "node_id": self.node_id,
            "body_id": self.body_id,
            "source_refs": list(self.source_refs),
            "correlation_ids": list(self.correlation_ids),
            "monotonic_time": self.monotonic_time,
            "replay_state": self.replay_state,
            "health_state": "healthy",
            "degraded_reasons": [],
            **_FLAGS,
            "snapshot_id": self.snapshot_id,
            "trust_context": self.trust_context,
            "values": dict(self.values),
            "consumer": self.consumer,
            "cannot_change_authority": True,
        }
        return {
            "event_id": self.snapshot_id,
            "timestamp": float(timestamp),
            "source": source.strip(),
            "event_type": MODULATORS_SNAPSHOTTED,
            "intent": None,
            "payload": payload,
            "metadata": {
                "contract": CONTRACT,
                "schema_version": SCHEMA_VERSION,
                "family": "cognitive-event",
                "authority": "none",
                "interpretation_only": True,
            },
            "parent_event_id": None,
            "receipt_id": None,
        }


class OperationalModulatorRegistry:
    def __init__(
        self,
        *,
        body_id: str,
        node_id: str,
        replay_state: str = "live",
        id_factory: Optional[Callable[[str], str]] = None,
    ) -> None:
        _text("body_id", body_id)
        _text("node_id", node_id)
        if replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid replay_state")
        self.body_id = body_id.strip()
        self.node_id = node_id.strip()
        self.replay_state = replay_state
        self._id = id_factory or (lambda prefix: "%s_%s" % (prefix, uuid4().hex))
        self._values = dict(_BASELINES)
        self._updated_at = {name: None for name in MODULATOR_NAMES}
        self._source_refs = []
        self._seen_updates = set()
        self._trust_context = "unknown"
        self._trust_context_ref = None

    def apply(
        self,
        update: ModulatorUpdate,
        *,
        workspace_view: Mapping[str, Any],
    ) -> bool:
        context = CognitiveWorkspaceContext.from_view(workspace_view)
        context.assert_matches(body_id=self.body_id, node_id=self.node_id)
        if update.update_id in self._seen_updates:
            return False
        if update.body_id != self.body_id:
            raise ValueError("modulator update belongs to another body")
        if update.node_id != self.node_id:
            raise ValueError("modulator update belongs to another node")
        if update.cognitive_event_id != context.cognitive_event_id:
            raise ValueError("modulator update belongs to another cognitive event")
        if update.replay_state != self.replay_state or context.replay_state != self.replay_state:
            raise ValueError("workspace, update, and registry replay_state differ")
        if context.correlation_ids and update.correlation_ids:
            if not set(context.correlation_ids).intersection(update.correlation_ids):
                raise ValueError("modulator update lacks workspace correlation")
        self._seen_updates.add(update.update_id)
        for name, target in update.values.items():
            previous_at = self._updated_at[name]
            current = self._values[name]
            if previous_at is None:
                next_value = float(target)
            else:
                elapsed = max(0.0, float(update.monotonic_time) - float(previous_at))
                current = _decay_toward_baseline(name, current, elapsed)
                allowed = _MAX_RATE[name] * elapsed
                delta = max(-allowed, min(allowed, float(target) - current))
                next_value = current + delta
            self._values[name] = round(max(0.0, min(1.0, next_value)), 6)
            self._updated_at[name] = float(update.monotonic_time)
        _extend_unique(self._source_refs, update.source_refs)
        _extend_unique(self._source_refs, (update.update_id,))
        return True

    def advance(self, monotonic_time: float) -> None:
        _non_negative("monotonic_time", monotonic_time)
        for name in MODULATOR_NAMES:
            previous_at = self._updated_at[name]
            if previous_at is None:
                continue
            elapsed = max(0.0, float(monotonic_time) - float(previous_at))
            self._values[name] = round(
                _decay_toward_baseline(name, self._values[name], elapsed), 6
            )
            self._updated_at[name] = float(monotonic_time)

    def set_trust_context(
        self,
        trust_context: str,
        *,
        source: str,
        source_ref: str,
    ) -> None:
        if source != "velvet-runtime":
            raise ValueError("trust_context must come from velvet-runtime")
        if trust_context not in _TRUST_CONTEXTS:
            raise ValueError("invalid trust_context")
        _text("source_ref", source_ref)
        self._trust_context = trust_context
        self._trust_context_ref = source_ref.strip()
        _extend_unique(self._source_refs, (source_ref.strip(),))

    def snapshot_for_consumer(
        self,
        consumer: str,
        *,
        workspace_view: Mapping[str, Any],
        monotonic_time: float,
    ) -> ModulatorSnapshot:
        _text("consumer", consumer)
        if consumer in _FORBIDDEN_CONSUMERS:
            raise ValueError("consumer is forbidden from operational modulators")
        if consumer not in _CONSUMER_ALLOWLIST:
            raise ValueError("unknown modulator consumer")
        context = CognitiveWorkspaceContext.from_view(workspace_view)
        context.assert_matches(body_id=self.body_id, node_id=self.node_id)
        if context.replay_state != self.replay_state:
            raise ValueError("workspace and registry replay_state differ")
        self.advance(monotonic_time)
        allowed = _CONSUMER_ALLOWLIST[consumer]
        values = {
            name: self._values[name]
            for name in MODULATOR_NAMES
            if name in allowed
        }
        source_refs = _merge(context.source_refs, tuple(self._source_refs))
        if self._trust_context_ref is not None:
            source_refs = _merge(source_refs, (self._trust_context_ref,))
        return ModulatorSnapshot(
            snapshot_id=self._id("modulator-snapshot"),
            cognitive_event_id=context.cognitive_event_id,
            body_id=self.body_id,
            node_id=self.node_id,
            consumer=consumer,
            trust_context=self._trust_context,
            values=_freeze(values),
            source_refs=source_refs,
            correlation_ids=context.correlation_ids,
            monotonic_time=float(monotonic_time),
            replay_state=self.replay_state,
        )

    def value(self, name: str) -> float:
        if name not in MODULATOR_NAMES:
            raise KeyError("unknown modulator")
        return self._values[name]


def _decay_toward_baseline(name: str, current: float, elapsed: float) -> float:
    baseline = _BASELINES[name]
    fraction = min(1.0, _DECAY_RATE[name] * max(0.0, elapsed))
    return current + (baseline - current) * fraction


def _reject(value: Any, name: str) -> None:
    found = _find_forbidden(value)
    if found:
        raise ValueError(
            "%s contains forbidden authority fields: %s"
            % (name, sorted(found))
        )


def _find_forbidden(value: Any) -> set:
    found = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if isinstance(key, str) and key.lower() in _FORBIDDEN_KEYS:
                found.add(key.lower())
            found.update(_find_forbidden(nested))
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            found.update(_find_forbidden(nested))
    return found


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze(nested) for key, nested in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(nested) for nested in value)
    return value


def _sequence(name: str, values: Any, required: bool = False) -> Tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise ValueError("%s must be a list or tuple" % name)
    result = []
    for value in values:
        _text(name, value)
        if value.strip() not in result:
            result.append(value.strip())
    if required and not result:
        raise ValueError("%s must not be empty" % name)
    return tuple(result)


def _merge(*groups: Iterable[str]) -> Tuple[str, ...]:
    result = []
    for group in groups:
        _extend_unique(result, group)
    return tuple(result)


def _extend_unique(values: list, additions: Iterable[str]) -> None:
    for value in additions:
        if value not in values:
            values.append(value)


def _text(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


def _ratio(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % name)
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError("%s must be between 0 and 1" % name)


def _non_negative(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % name)
    if float(value) < 0.0:
        raise ValueError("%s must be non-negative" % name)


__all__ = [
    "CONTRACT",
    "SCHEMA_VERSION",
    "MODULATORS_SNAPSHOTTED",
    "MODULATOR_NAMES",
    "ModulatorUpdate",
    "ModulatorSnapshot",
    "OperationalModulatorRegistry",
]

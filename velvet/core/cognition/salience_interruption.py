# SPDX-License-Identifier: GPL-3.0-only
"""Continuous, non-authoritative salience and interruption assessment.

The accumulator may notice that a higher-priority event deserves cognitive
attention. It never authorizes safeing, invokes an executor, retries an action,
or replaces source evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple
from uuid import uuid4

from .workspace_context import CognitiveWorkspaceContext

CONTRACT = "velvet.cognitive-events.v1"
SCHEMA_VERSION = "1.0"
INTERRUPT_CANDIDATE = "cognitive.interrupt.candidate"
INTERRUPT_ACCEPTED = "cognitive.interrupt.accepted"

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
_FORBIDDEN = {
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
    "automatic_retry_requested",
    "safety_override",
    "shell",
    "token",
}
_CLAIMS = {
    "authority",
    "authority_granted",
    "grants_authority",
    "grants_execution",
    "grants_actuation",
    "execution_performed",
    "actuation_performed",
    "safeing_authorized",
    "safeing_performed",
}


class SalienceDisposition(str, Enum):
    ACCUMULATING = "accumulating"
    ACCEPTED = "accepted"
    ALREADY_ACCEPTED = "already_accepted"
    DUPLICATE = "duplicate"
    STALE = "stale"
    UNRELATED = "unrelated"
    WRONG_BODY = "wrong_body"
    WRONG_NODE = "wrong_node"
    RATE_LIMITED = "rate_limited"
    CAPACITY_REACHED = "capacity_reached"


@dataclass(frozen=True)
class SalienceSignal:
    signal_id: str
    interrupt_key: str
    cognitive_event_id: str
    event_type: str
    source: str
    body_id: str
    node_id: str
    reason: str
    observed_at: float
    monotonic_time: float
    severity: float
    rate_of_change: float
    novelty: float
    confidence: float
    source_trust: float
    persistence: float
    cross_sensor_agreement: float
    source_refs: Tuple[str, ...]
    correlation_ids: Tuple[str, ...] = ()
    outstanding_effect_refs: Tuple[str, ...] = ()
    payload: Mapping[str, Any] = field(default_factory=dict)
    stale_after_ms: int = 1000
    replay_state: str = "live"
    authority_context_change: bool = False
    resource_failure: bool = False
    safety_critical: bool = False
    requires_immediate_safeing: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("signal_id", self.signal_id),
            ("interrupt_key", self.interrupt_key),
            ("cognitive_event_id", self.cognitive_event_id),
            ("event_type", self.event_type),
            ("source", self.source),
            ("body_id", self.body_id),
            ("node_id", self.node_id),
            ("reason", self.reason),
        ):
            _text(name, value)
        _non_negative("observed_at", self.observed_at)
        _non_negative("monotonic_time", self.monotonic_time)
        for name, value in (
            ("severity", self.severity),
            ("rate_of_change", self.rate_of_change),
            ("novelty", self.novelty),
            ("confidence", self.confidence),
            ("source_trust", self.source_trust),
            ("persistence", self.persistence),
            ("cross_sensor_agreement", self.cross_sensor_agreement),
        ):
            _ratio(name, value)
        if isinstance(self.stale_after_ms, bool) or not isinstance(
            self.stale_after_ms, int
        ):
            raise ValueError("stale_after_ms must be an integer")
        if self.stale_after_ms <= 0:
            raise ValueError("stale_after_ms must be positive")
        if self.replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid replay_state")
        for name, value in (
            ("authority_context_change", self.authority_context_change),
            ("resource_failure", self.resource_failure),
            ("safety_critical", self.safety_critical),
            ("requires_immediate_safeing", self.requires_immediate_safeing),
        ):
            if not isinstance(value, bool):
                raise ValueError("%s must be boolean" % name)
        _texts("source_refs", self.source_refs, required=True)
        _texts("correlation_ids", self.correlation_ids)
        _texts("outstanding_effect_refs", self.outstanding_effect_refs)
        if not isinstance(self.payload, Mapping):
            raise ValueError("payload must be a mapping")
        _reject(self.payload, "salience signal payload")

    def is_stale(self, now: float) -> bool:
        _non_negative("now", now)
        return max(0.0, float(now) - float(self.observed_at)) * 1000.0 > float(
            self.stale_after_ms
        )


@dataclass(frozen=True)
class InterruptEmission:
    emission_id: str
    event_type: str
    payload: Mapping[str, Any]
    parent_emission_id: Optional[str] = None

    def __post_init__(self) -> None:
        _text("emission_id", self.emission_id)
        if self.event_type not in {INTERRUPT_CANDIDATE, INTERRUPT_ACCEPTED}:
            raise ValueError("unexpected interruption event type")
        _validate_interrupt_payload(self.event_type, self.payload)

    @property
    def authority_granted(self) -> bool:
        return False

    @property
    def safeing_performed(self) -> bool:
        return False

    def to_event_document(self, *, source: str, timestamp: float) -> Dict[str, Any]:
        _text("source", source)
        _non_negative("timestamp", timestamp)
        return {
            "event_id": self.emission_id,
            "timestamp": float(timestamp),
            "source": source.strip(),
            "event_type": self.event_type,
            "intent": None,
            "payload": _thaw(self.payload),
            "metadata": {
                "contract": CONTRACT,
                "schema_version": SCHEMA_VERSION,
                "family": "cognitive-event",
                "authority": "none",
                "interpretation_only": True,
            },
            "parent_event_id": self.parent_emission_id,
            "receipt_id": None,
        }


@dataclass
class InterruptRecord:
    interrupt_id: str
    interrupt_key: str
    cognitive_event_id: str
    body_id: str
    node_id: str
    reason: str
    threshold: float
    accumulated_score: float
    priority: float
    source_refs: Tuple[str, ...]
    correlation_ids: Tuple[str, ...]
    signal_refs: Tuple[str, ...]
    source_ids: Tuple[str, ...]
    outstanding_effect_refs: Tuple[str, ...]
    replay_state: str
    last_update_at: float
    requires_immediate_safeing: bool = False
    accepted: bool = False
    accepted_at: Optional[float] = None
    safe_state_reached: str = "unknown"
    last_emission_id: Optional[str] = None

    @property
    def authority_granted(self) -> bool:
        return False

    @property
    def safeing_authorized(self) -> bool:
        return False

    @property
    def safeing_performed(self) -> bool:
        return False

    def read_only_view(self) -> Mapping[str, Any]:
        return _freeze(
            {
                "interrupt_id": self.interrupt_id,
                "interrupt_key": self.interrupt_key,
                "cognitive_event_id": self.cognitive_event_id,
                "body_id": self.body_id,
                "node_id": self.node_id,
                "reason": self.reason,
                "threshold": self.threshold,
                "accumulated_score": self.accumulated_score,
                "priority": self.priority,
                "source_refs": list(self.source_refs),
                "correlation_ids": list(self.correlation_ids),
                "signal_refs": list(self.signal_refs),
                "source_ids": list(self.source_ids),
                "outstanding_effect_refs": list(self.outstanding_effect_refs),
                "replay_state": self.replay_state,
                "requires_immediate_safeing": self.requires_immediate_safeing,
                "accepted": self.accepted,
                "accepted_at": self.accepted_at,
                "safe_state_reached": self.safe_state_reached,
                "authority_granted": False,
                "safeing_authorized": False,
                "safeing_performed": False,
            }
        )


@dataclass(frozen=True)
class SalienceEvaluation:
    disposition: SalienceDisposition
    record: Optional[InterruptRecord]
    candidate: Optional[InterruptEmission] = None
    accepted: Optional[InterruptEmission] = None
    reason: str = ""


@dataclass(frozen=True)
class WorkspaceInterruptApplication:
    association: Any
    boundary: Any


class SalienceAccumulator:
    """Deterministic, bounded accumulation of interruption evidence."""

    def __init__(
        self,
        *,
        body_id: str,
        node_id: str,
        default_threshold: float = 0.85,
        critical_threshold: float = 0.65,
        decay_per_second: float = 0.05,
        max_candidates: int = 64,
        max_signals_per_candidate: int = 32,
        max_signals_per_source: int = 8,
        id_factory: Optional[Callable[[str], str]] = None,
        replay_state: str = "live",
    ) -> None:
        _text("body_id", body_id)
        _text("node_id", node_id)
        _ratio("default_threshold", default_threshold)
        _ratio("critical_threshold", critical_threshold)
        _ratio("decay_per_second", decay_per_second)
        for name, value in (
            ("max_candidates", max_candidates),
            ("max_signals_per_candidate", max_signals_per_candidate),
            ("max_signals_per_source", max_signals_per_source),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError("%s must be a positive integer" % name)
        if replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid replay_state")
        self.body_id = body_id.strip()
        self.node_id = node_id.strip()
        self.default_threshold = float(default_threshold)
        self.critical_threshold = float(critical_threshold)
        self.decay_per_second = float(decay_per_second)
        self.max_candidates = max_candidates
        self.max_signals_per_candidate = max_signals_per_candidate
        self.max_signals_per_source = max_signals_per_source
        self.replay_state = replay_state
        self._id = id_factory or (lambda p: "%s_%s" % (p, uuid4().hex))
        self._records: Dict[str, InterruptRecord] = {}
        self._seen_signals = set()
        self._source_counts: Dict[Tuple[str, str], int] = {}

    def evaluate(
        self,
        signal: SalienceSignal,
        *,
        workspace_view: Mapping[str, Any],
        now: float,
    ) -> SalienceEvaluation:
        context = CognitiveWorkspaceContext.from_view(workspace_view)
        if signal.signal_id in self._seen_signals:
            return SalienceEvaluation(
                SalienceDisposition.DUPLICATE,
                self._records.get(signal.interrupt_key),
                reason="signal already evaluated",
            )
        if signal.body_id != self.body_id or context.body_id != self.body_id:
            return SalienceEvaluation(
                SalienceDisposition.WRONG_BODY,
                self._records.get(signal.interrupt_key),
                reason="signal or workspace belongs to another body",
            )
        if signal.node_id != self.node_id or context.node_id != self.node_id:
            return SalienceEvaluation(
                SalienceDisposition.WRONG_NODE,
                self._records.get(signal.interrupt_key),
                reason="signal or workspace belongs to another node",
            )
        if signal.replay_state != self.replay_state or context.replay_state != self.replay_state:
            raise ValueError("workspace, signal, and accumulator replay_state differ")
        if signal.cognitive_event_id != context.cognitive_event_id:
            return SalienceEvaluation(
                SalienceDisposition.UNRELATED,
                self._records.get(signal.interrupt_key),
                reason="signal names another cognitive event",
            )
        if context.correlation_ids and signal.correlation_ids:
            if not set(context.correlation_ids).intersection(signal.correlation_ids):
                return SalienceEvaluation(
                    SalienceDisposition.UNRELATED,
                    self._records.get(signal.interrupt_key),
                    reason="signal does not share workspace correlation",
                )
        if signal.is_stale(now):
            return SalienceEvaluation(
                SalienceDisposition.STALE,
                self._records.get(signal.interrupt_key),
                reason="signal exceeded freshness window",
            )

        record = self._records.get(signal.interrupt_key)
        if record is not None and record.cognitive_event_id != signal.cognitive_event_id:
            return SalienceEvaluation(
                SalienceDisposition.UNRELATED,
                record,
                reason="interrupt key already belongs to another cognitive event",
            )
        if record is not None and record.accepted:
            self._seen_signals.add(signal.signal_id)
            return SalienceEvaluation(
                SalienceDisposition.ALREADY_ACCEPTED,
                record,
                reason="interrupt was already accepted",
            )
        if record is None:
            if len(self._records) >= self.max_candidates:
                return SalienceEvaluation(
                    SalienceDisposition.CAPACITY_REACHED,
                    None,
                    reason="interrupt candidate capacity reached",
                )
            threshold = (
                self.critical_threshold if signal.safety_critical else self.default_threshold
            )
            record = InterruptRecord(
                interrupt_id=self._id("interrupt"),
                interrupt_key=signal.interrupt_key,
                cognitive_event_id=signal.cognitive_event_id,
                body_id=self.body_id,
                node_id=self.node_id,
                reason=signal.reason,
                threshold=threshold,
                accumulated_score=0.0,
                priority=0.0,
                source_refs=(),
                correlation_ids=(),
                signal_refs=(),
                source_ids=(),
                outstanding_effect_refs=(),
                replay_state=self.replay_state,
                last_update_at=float(signal.monotonic_time),
            )
            self._records[signal.interrupt_key] = record

        if len(record.signal_refs) >= self.max_signals_per_candidate:
            return SalienceEvaluation(
                SalienceDisposition.CAPACITY_REACHED,
                record,
                reason="candidate signal capacity reached",
            )
        source_count_key = (record.interrupt_key, signal.source)
        if self._source_counts.get(source_count_key, 0) >= self.max_signals_per_source:
            return SalienceEvaluation(
                SalienceDisposition.RATE_LIMITED,
                record,
                reason="source signal limit reached for candidate",
            )

        self._seen_signals.add(signal.signal_id)
        self._source_counts[source_count_key] = self._source_counts.get(source_count_key, 0) + 1
        elapsed = max(0.0, float(signal.monotonic_time) - record.last_update_at)
        decay = max(0.0, 1.0 - elapsed * self.decay_per_second)
        instant = _instantaneous_score(signal)
        record.accumulated_score = round(
            min(2.0, record.accumulated_score * decay + instant), 6
        )
        record.priority = round(min(1.0, instant), 6)
        record.reason = signal.reason
        record.last_update_at = max(record.last_update_at, float(signal.monotonic_time))
        record.requires_immediate_safeing = (
            record.requires_immediate_safeing or signal.requires_immediate_safeing
        )
        if signal.safety_critical:
            record.threshold = min(record.threshold, self.critical_threshold)
        record.source_refs = _merge(record.source_refs, signal.source_refs, (signal.signal_id,))
        record.correlation_ids = _merge(record.correlation_ids, signal.correlation_ids)
        record.signal_refs = _merge(record.signal_refs, (signal.signal_id,))
        record.source_ids = _merge(record.source_ids, (signal.source,))
        record.outstanding_effect_refs = _merge(
            record.outstanding_effect_refs, signal.outstanding_effect_refs
        )

        candidate = self._emit(record, INTERRUPT_CANDIDATE)
        if record.accumulated_score < record.threshold:
            return SalienceEvaluation(
                SalienceDisposition.ACCUMULATING,
                record,
                candidate=candidate,
            )

        record.accepted = True
        record.accepted_at = float(signal.monotonic_time)
        accepted = self._emit(record, INTERRUPT_ACCEPTED)
        return SalienceEvaluation(
            SalienceDisposition.ACCEPTED,
            record,
            candidate=candidate,
            accepted=accepted,
        )

    def read_only_view(self, interrupt_key: str) -> Mapping[str, Any]:
        _text("interrupt_key", interrupt_key)
        if interrupt_key not in self._records:
            raise KeyError("unknown interrupt_key")
        return self._records[interrupt_key].read_only_view()

    def active_keys(self) -> Tuple[str, ...]:
        return tuple(key for key, record in self._records.items() if not record.accepted)

    def accepted_keys(self) -> Tuple[str, ...]:
        return tuple(key for key, record in self._records.items() if record.accepted)

    def _emit(self, record: InterruptRecord, event_type: str) -> InterruptEmission:
        payload = _common_payload(record)
        emission = InterruptEmission(
            emission_id=self._id("cognitive-event"),
            event_type=event_type,
            payload=_freeze(payload),
            parent_emission_id=record.last_emission_id,
        )
        record.last_emission_id = emission.emission_id
        return emission


def apply_accepted_interrupt(
    workspace: Any,
    evaluation: SalienceEvaluation,
    *,
    now: float,
) -> WorkspaceInterruptApplication:
    """Attach accepted interruption evidence and propose a cognitive boundary.

    This function changes only the Cognitive Event workspace. It does not
    perform safeing and does not open a physical execution path.
    """

    if evaluation.disposition is not SalienceDisposition.ACCEPTED:
        raise ValueError("evaluation must contain an accepted interrupt")
    if evaluation.record is None or evaluation.accepted is None:
        raise ValueError("accepted evaluation is incomplete")

    from .event_workspace import (
        BoundaryType,
        LifecycleState,
        ObservationRole,
        WorkspaceObservation,
    )

    record = evaluation.record
    context = CognitiveWorkspaceContext.from_view(workspace.read_only_view())
    context.assert_matches(body_id=record.body_id, node_id=record.node_id)
    if context.cognitive_event_id != record.cognitive_event_id:
        raise ValueError("accepted interrupt belongs to another cognitive event")
    observation = WorkspaceObservation(
        event_id=evaluation.accepted.emission_id,
        event_type=INTERRUPT_ACCEPTED,
        source="velvet-ai-core.salience",
        body_id=record.body_id,
        observed_at=float(now),
        monotonic_time=record.accepted_at or record.last_update_at,
        confidence=record.priority,
        payload={
            "interrupt_id": record.interrupt_id,
            "reason": record.reason,
            "requires_immediate_safeing": record.requires_immediate_safeing,
            "safeing_authorized": False,
            "safeing_performed": False,
        },
        correlation_ids=record.correlation_ids,
        source_refs=record.source_refs,
        stale_after_ms=1000,
        simulated=record.replay_state != "live",
        related_cognitive_event_id=record.cognitive_event_id,
    )
    association = workspace.observe(
        observation,
        now=float(now),
        role=ObservationRole.INTERRUPTING,
    )
    if getattr(association.disposition, "value", None) != "accepted":
        raise RuntimeError("workspace rejected accepted interrupt evidence")
    boundary = workspace.propose_boundary(
        boundary_type=BoundaryType.INTERRUPTION,
        recommended_terminal_state=LifecycleState.INTERRUPTED,
        evidence_refs=(observation.event_id,),
        confidence=record.priority,
        monotonic_time=record.accepted_at or record.last_update_at,
    )
    return WorkspaceInterruptApplication(association=association, boundary=boundary)


def _instantaneous_score(signal: SalienceSignal) -> float:
    score = (
        signal.severity * 0.28
        + signal.rate_of_change * 0.12
        + signal.novelty * 0.08
        + signal.confidence * 0.15
        + signal.source_trust * 0.12
        + signal.persistence * 0.10
        + signal.cross_sensor_agreement * 0.10
    )
    if signal.authority_context_change:
        score += 0.03
    if signal.resource_failure:
        score += 0.04
    if signal.safety_critical:
        score += 0.16
    if signal.requires_immediate_safeing:
        score += 0.08
    return round(min(1.0, score), 6)


def _common_payload(record: InterruptRecord) -> Dict[str, Any]:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "cognitive_event_id": record.cognitive_event_id,
        "node_id": record.node_id,
        "body_id": record.body_id,
        "source_refs": list(record.source_refs),
        "correlation_ids": list(record.correlation_ids),
        "monotonic_time": record.last_update_at,
        "replay_state": record.replay_state,
        "health_state": "healthy",
        "degraded_reasons": [],
        **_FLAGS,
        "interrupt_id": record.interrupt_id,
        "priority": record.priority,
        "reason": record.reason,
        "accumulated_score": record.accumulated_score,
        "threshold": record.threshold,
        "requires_immediate_safeing": record.requires_immediate_safeing,
        "safe_state_reached": record.safe_state_reached,
        "safeing_authorized": False,
        "safeing_performed": False,
        "outstanding_effect_refs": list(record.outstanding_effect_refs),
    }
    if record.accepted:
        payload["interrupted_event_id"] = record.cognitive_event_id
    return payload


def _validate_interrupt_payload(event_type: str, payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("interrupt payload must be a mapping")
    for key, expected in _FLAGS.items():
        if payload.get(key) != expected:
            raise ValueError("interrupt payload %s must be %r" % (key, expected))
    for name in ("cognitive_event_id", "node_id", "body_id", "interrupt_id", "reason"):
        _text(name, payload.get(name))
    _texts("source_refs", payload.get("source_refs", ()), required=True)
    _texts("correlation_ids", payload.get("correlation_ids", ()))
    _texts("outstanding_effect_refs", payload.get("outstanding_effect_refs", ()))
    _ratio("priority", payload.get("priority"))
    _non_negative("accumulated_score", payload.get("accumulated_score"))
    _non_negative("threshold", payload.get("threshold"))
    if not isinstance(payload.get("requires_immediate_safeing"), bool):
        raise ValueError("requires_immediate_safeing must be boolean")
    if payload.get("safe_state_reached") not in {"true", "false", "unknown"}:
        raise ValueError("invalid safe_state_reached")
    if payload.get("safeing_authorized") is not False:
        raise ValueError("interrupt cannot authorize safeing")
    if payload.get("safeing_performed") is not False:
        raise ValueError("interrupt cannot claim safeing")
    permitted = set(_FLAGS) | {"safeing_authorized", "safeing_performed"}
    nested = {key: value for key, value in payload.items() if key not in permitted}
    _reject(nested, "interrupt payload")
    if event_type == INTERRUPT_ACCEPTED:
        _text("interrupted_event_id", payload.get("interrupted_event_id"))
        if float(payload["accumulated_score"]) < float(payload["threshold"]):
            raise ValueError("accepted interrupt must meet threshold")
    elif "interrupted_event_id" in payload:
        raise ValueError("candidate interrupt cannot claim interrupted event")


def _reject(value: Any, name: str) -> None:
    found = _find(value, _FORBIDDEN) | _find(value, _CLAIMS)
    if found:
        raise ValueError("%s contains forbidden authority fields: %s" % (name, sorted(found)))


def _find(value: Any, names: set) -> set:
    found = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if isinstance(key, str) and key.lower() in names:
                found.add(key.lower())
            found.update(_find(nested, names))
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            found.update(_find(nested, names))
    return found


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(nested) for key, nested in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(nested) for nested in value)
    if isinstance(value, set):
        return tuple(sorted(_freeze(nested) for nested in value))
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_thaw(nested) for nested in value]
    return value


def _texts(name: str, values: Iterable[str], required: bool = False) -> Tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise ValueError("%s must be a list or tuple" % name)
    normalized = []
    for value in values:
        _text(name, value)
        stripped = value.strip()
        if stripped not in normalized:
            normalized.append(stripped)
    if required and not normalized:
        raise ValueError("%s must not be empty" % name)
    return tuple(normalized)


def _merge(*groups: Iterable[str]) -> Tuple[str, ...]:
    result = []
    for group in groups:
        for value in group:
            if value not in result:
                result.append(value)
    return tuple(result)


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
    "INTERRUPT_CANDIDATE",
    "INTERRUPT_ACCEPTED",
    "SalienceDisposition",
    "SalienceSignal",
    "InterruptEmission",
    "InterruptRecord",
    "SalienceEvaluation",
    "WorkspaceInterruptApplication",
    "SalienceAccumulator",
    "apply_accepted_interrupt",
]

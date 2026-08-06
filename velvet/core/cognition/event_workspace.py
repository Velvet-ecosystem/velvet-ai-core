# SPDX-License-Identifier: GPL-3.0-only
"""Bounded, read-only current-event workspace for Velvet AI Core.

The workspace associates evidence into a temporary interpretation of what appears
happening now. It never authorizes, executes, retries, persists receipts, or
claims identity continuity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple
from uuid import uuid4

COGNITIVE_EVENT_CONTRACT = "velvet.cognitive-events.v1"
COGNITIVE_SCHEMA_VERSION = "1.0"

EVENT_OPENED = "cognitive.event.opened"
EVENT_UPDATED = "cognitive.event.updated"
BOUNDARY_PROPOSED = "cognitive.event.boundary_proposed"
EVENT_CLOSED = "cognitive.event.closed"

_TERMINAL_STATES = {
    "COMPLETED",
    "INTERRUPTED",
    "STALE",
    "CONTRADICTED",
    "ABANDONED",
    "UNKNOWN_OUTCOME",
    "DEGRADED_COMPLETION",
}
_FORBIDDEN_AUTHORITY_KEYS = {
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
_AUTHORITY_CLAIM_KEYS = {
    "authority",
    "authority_granted",
    "grants_authority",
    "grants_execution",
    "grants_actuation",
    "execution_performed",
    "actuation_performed",
}


class CognitiveMode(str, Enum):
    OBSERVE = "OBSERVE"
    PROPOSE_ACTION = "PROPOSE_ACTION"
    TRACK_ACTION = "TRACK_ACTION"


class LifecycleState(str, Enum):
    OPEN = "OPEN"
    DEVELOPING = "DEVELOPING"
    PROPOSAL_PENDING = "PROPOSAL_PENDING"
    ACTION_TRACKING = "ACTION_TRACKING"
    COMPLETED = "COMPLETED"
    INTERRUPTED = "INTERRUPTED"
    STALE = "STALE"
    CONTRADICTED = "CONTRADICTED"
    ABANDONED = "ABANDONED"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    DEGRADED_COMPLETION = "DEGRADED_COMPLETION"


class BoundaryType(str, Enum):
    COMPLETION = "completion"
    INTERRUPTION = "interruption"
    CONTEXT_SHIFT = "context_shift"
    TIMEOUT = "timeout"
    CONTRADICTION = "contradiction"


class ObservationRole(str, Enum):
    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    INTERRUPTING = "interrupting"


class AssociationDisposition(str, Enum):
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"
    STALE = "stale"
    UNRELATED = "unrelated"
    WRONG_BODY = "wrong_body"
    CAPACITY_REACHED = "capacity_reached"
    CLOSED = "closed"


@dataclass(frozen=True)
class WorkspaceObservation:
    """One immutable observation reference accepted by the workspace."""

    event_id: str
    event_type: str
    source: str
    body_id: str
    observed_at: float
    monotonic_time: float
    confidence: float
    payload: Mapping[str, Any] = field(default_factory=dict)
    correlation_ids: Tuple[str, ...] = ()
    source_refs: Tuple[str, ...] = ()
    receipt_id: Optional[str] = None
    stale_after_ms: int = 1000
    simulated: bool = False
    related_cognitive_event_id: Optional[str] = None

    def __post_init__(self) -> None:
        for name, value in (
            ("event_id", self.event_id),
            ("event_type", self.event_type),
            ("source", self.source),
            ("body_id", self.body_id),
        ):
            _require_text(name, value)
        _require_non_negative("observed_at", self.observed_at)
        _require_non_negative("monotonic_time", self.monotonic_time)
        _require_ratio("confidence", self.confidence)
        if isinstance(self.stale_after_ms, bool) or not isinstance(self.stale_after_ms, int):
            raise ValueError("stale_after_ms must be an integer")
        if self.stale_after_ms <= 0:
            raise ValueError("stale_after_ms must be positive")
        if not isinstance(self.payload, Mapping):
            raise ValueError("payload must be a mapping")
        _require_text_tuple("correlation_ids", self.correlation_ids)
        _require_text_tuple("source_refs", self.source_refs)
        if self.receipt_id is not None:
            _require_text("receipt_id", self.receipt_id)
        if self.related_cognitive_event_id is not None:
            _require_text("related_cognitive_event_id", self.related_cognitive_event_id)
        if not isinstance(self.simulated, bool):
            raise ValueError("simulated must be boolean")
        forbidden = _find_forbidden_keys(self.payload)
        claims = _find_named_keys(self.payload, _AUTHORITY_CLAIM_KEYS)
        if forbidden or claims:
            raise ValueError(
                "observation contains forbidden authority fields: %s"
                % sorted(forbidden | claims)
            )

    def is_stale(self, now: float) -> bool:
        _require_non_negative("now", now)
        return max(0.0, float(now) - float(self.observed_at)) * 1000.0 > self.stale_after_ms


@dataclass(frozen=True)
class WorkspaceSnapshot:
    cognitive_event_id: str
    event_kind: str
    body_id: str
    node_id: str
    mode: CognitiveMode
    lifecycle_state: LifecycleState
    started_at: float
    last_update_at: float
    confidence: float
    observation_refs: Tuple[str, ...]
    source_refs: Tuple[str, ...]
    correlation_ids: Tuple[str, ...]
    receipt_refs: Tuple[str, ...]
    contradiction_refs: Tuple[str, ...]
    interruption_refs: Tuple[str, ...]
    proposal_refs: Tuple[str, ...]
    authorization_refs: Tuple[str, ...]
    execution_refs: Tuple[str, ...]
    degraded_reasons: Tuple[str, ...]
    boundary_ids: Tuple[str, ...]
    replay_state: str

    @property
    def canonical(self) -> bool:
        return False

    @property
    def authority_granted(self) -> bool:
        return False

    @property
    def execution_performed(self) -> bool:
        return False

    def to_payload(self) -> Dict[str, Any]:
        freshness = "stale" if self.lifecycle_state is LifecycleState.STALE else "fresh"
        health = "degraded" if self.degraded_reasons else "healthy"
        return {
            "schema_version": COGNITIVE_SCHEMA_VERSION,
            "cognitive_event_id": self.cognitive_event_id,
            "node_id": self.node_id,
            "body_id": self.body_id,
            "source_refs": list(self.source_refs),
            "correlation_ids": list(self.correlation_ids),
            "monotonic_time": self.last_update_at,
            "replay_state": self.replay_state,
            "health_state": health,
            "degraded_reasons": list(self.degraded_reasons),
            "interpretation_only": True,
            "transport_only": True,
            "canonical_evidence": False,
            "authority": "none",
            "grants_authority": False,
            "grants_execution": False,
            "grants_actuation": False,
            "replay_safe": True,
            "mode": self.mode.value,
            "lifecycle_state": self.lifecycle_state.value,
            "event_kind": self.event_kind,
            "confidence": self.confidence,
            "freshness_state": freshness,
            "observation_refs": list(self.observation_refs),
            "organ_contribution_refs": [],
            "proposal_refs": list(self.proposal_refs),
            "authorization_refs": list(self.authorization_refs),
            "execution_refs": list(self.execution_refs),
            "receipt_refs": list(self.receipt_refs),
            "prediction_refs": [],
            "interruption_refs": list(self.interruption_refs),
            "nested_event_ids": [],
            "contradiction_refs": list(self.contradiction_refs),
            "boundary_ids": list(self.boundary_ids),
        }


@dataclass(frozen=True)
class WorkspaceEmission:
    emission_id: str
    event_type: str
    payload: Mapping[str, Any]
    parent_emission_id: Optional[str]

    def __post_init__(self) -> None:
        _require_text("emission_id", self.emission_id)
        _require_text("event_type", self.event_type)
        if not isinstance(self.payload, Mapping):
            raise ValueError("payload must be a mapping")
        forbidden = _find_forbidden_keys(self.payload)
        if forbidden:
            raise ValueError(
                "emission contains forbidden authority fields: %s"
                % sorted(forbidden)
            )
        required = {
            "interpretation_only": True,
            "transport_only": True,
            "canonical_evidence": False,
            "authority": "none",
            "grants_authority": False,
            "grants_execution": False,
            "grants_actuation": False,
            "replay_safe": True,
        }
        for key, expected in required.items():
            if self.payload.get(key) != expected:
                raise ValueError(
                    "emission payload %s must be %r" % (key, expected)
                )

    @property
    def authority_granted(self) -> bool:
        return False

    def to_event_document(
        self,
        *,
        source: str,
        timestamp: float,
    ) -> Dict[str, Any]:
        _require_text("source", source)
        _require_non_negative("timestamp", timestamp)
        return {
            "event_id": self.emission_id,
            "timestamp": float(timestamp),
            "source": source.strip(),
            "event_type": self.event_type,
            "intent": None,
            "payload": _thaw(self.payload),
            "metadata": {
                "contract": COGNITIVE_EVENT_CONTRACT,
                "schema_version": COGNITIVE_SCHEMA_VERSION,
                "family": "cognitive-event",
                "authority": "none",
                "interpretation_only": True,
            },
            "parent_event_id": self.parent_emission_id,
            "receipt_id": None,
        }


@dataclass(frozen=True)
class AssociationResult:
    disposition: AssociationDisposition
    snapshot: WorkspaceSnapshot
    emission: Optional[WorkspaceEmission] = None
    reason: str = ""


@dataclass(frozen=True)
class BoundaryProposal:
    boundary_id: str
    boundary_type: BoundaryType
    recommended_terminal_state: LifecycleState
    evidence_refs: Tuple[str, ...]
    confidence: float
    emission: WorkspaceEmission


class CurrentEventWorkspace:
    """One bounded current event with explicit, deterministic associations."""

    def __init__(
        self,
        *,
        body_id: str,
        node_id: str,
        max_observations: int = 64,
        id_factory: Optional[Callable[[str], str]] = None,
        replay_state: str = "live",
    ) -> None:
        _require_text("body_id", body_id)
        _require_text("node_id", node_id)
        if isinstance(max_observations, bool) or not isinstance(max_observations, int):
            raise ValueError("max_observations must be an integer")
        if max_observations < 1:
            raise ValueError("max_observations must be positive")
        if replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid replay_state")
        self._body_id = body_id.strip()
        self._node_id = node_id.strip()
        self._max_observations = max_observations
        self._id_factory = id_factory or (lambda prefix: "%s_%s" % (prefix, uuid4().hex))
        self._replay_state = replay_state
        self._reset()

    @property
    def is_open(self) -> bool:
        return self._cognitive_event_id is not None and self._state not in _terminal_enums()

    def open(
        self,
        *,
        event_kind: str,
        observation: WorkspaceObservation,
        now: float,
        cognitive_event_id: Optional[str] = None,
    ) -> WorkspaceEmission:
        if self._cognitive_event_id is not None:
            raise RuntimeError("workspace already contains an event")
        _require_text("event_kind", event_kind)
        self._validate_observation_body(observation)
        if observation.is_stale(now):
            raise ValueError("initial observation is stale")
        self._cognitive_event_id = cognitive_event_id or self._id_factory("cog")
        _require_text("cognitive_event_id", self._cognitive_event_id)
        self._event_kind = event_kind.strip()
        self._mode = CognitiveMode.OBSERVE
        self._state = LifecycleState.OPEN
        self._started_at = float(observation.monotonic_time)
        self._last_update_at = float(observation.monotonic_time)
        self._confidence = float(observation.confidence)
        self._accept_observation(observation, ObservationRole.SUPPORTING)
        return self._emit(EVENT_OPENED, self.snapshot().to_payload())

    def observe(
        self,
        observation: WorkspaceObservation,
        *,
        now: float,
        role: ObservationRole = ObservationRole.SUPPORTING,
        allow_uncorrelated: bool = False,
    ) -> AssociationResult:
        self._require_event()
        if self._state in _terminal_enums():
            return AssociationResult(
                AssociationDisposition.CLOSED,
                self.snapshot(),
                reason="workspace event is closed",
            )
        if observation.event_id in self._observations:
            return AssociationResult(
                AssociationDisposition.DUPLICATE,
                self.snapshot(),
                reason="observation already associated",
            )
        if observation.body_id != self._body_id:
            return AssociationResult(
                AssociationDisposition.WRONG_BODY,
                self.snapshot(),
                reason="observation belongs to another body",
            )
        if observation.is_stale(now):
            return AssociationResult(
                AssociationDisposition.STALE,
                self.snapshot(),
                reason="observation exceeded its freshness window",
            )
        if len(self._observations) >= self._max_observations:
            self._add_unique(self._degraded_reasons, "observation-capacity-reached")
            emission = self._emit(EVENT_UPDATED, self.snapshot().to_payload())
            return AssociationResult(
                AssociationDisposition.CAPACITY_REACHED,
                self.snapshot(),
                emission=emission,
                reason="workspace observation capacity reached",
            )
        if not self._is_related(observation, allow_uncorrelated=allow_uncorrelated):
            return AssociationResult(
                AssociationDisposition.UNRELATED,
                self.snapshot(),
                reason="observation has no explicit event relationship",
            )
        self._accept_observation(observation, role)
        if self._state is LifecycleState.OPEN:
            self._state = LifecycleState.DEVELOPING
        emission = self._emit(EVENT_UPDATED, self.snapshot().to_payload())
        return AssociationResult(
            AssociationDisposition.ACCEPTED,
            self.snapshot(),
            emission=emission,
        )

    def set_mode(
        self,
        mode: CognitiveMode,
        *,
        proposal_ref: Optional[str] = None,
        authorization_ref: Optional[str] = None,
        execution_ref: Optional[str] = None,
        monotonic_time: Optional[float] = None,
    ) -> WorkspaceEmission:
        self._require_open_event()
        if not isinstance(mode, CognitiveMode):
            raise ValueError("mode must be CognitiveMode")
        if mode is CognitiveMode.PROPOSE_ACTION:
            _require_text("proposal_ref", proposal_ref)
            self._add_unique(self._proposal_refs, proposal_ref.strip())
            self._state = LifecycleState.PROPOSAL_PENDING
        elif mode is CognitiveMode.TRACK_ACTION:
            _require_text("authorization_ref", authorization_ref)
            _require_text("execution_ref", execution_ref)
            self._add_unique(self._authorization_refs, authorization_ref.strip())
            self._add_unique(self._execution_refs, execution_ref.strip())
            self._state = LifecycleState.ACTION_TRACKING
        else:
            self._state = LifecycleState.DEVELOPING
        self._mode = mode
        if monotonic_time is not None:
            _require_non_negative("monotonic_time", monotonic_time)
            self._last_update_at = max(self._last_update_at, float(monotonic_time))
        return self._emit(EVENT_UPDATED, self.snapshot().to_payload())

    def propose_boundary(
        self,
        *,
        boundary_type: BoundaryType,
        recommended_terminal_state: LifecycleState,
        evidence_refs: Iterable[str],
        confidence: float,
        monotonic_time: float,
    ) -> BoundaryProposal:
        self._require_open_event()
        if not isinstance(boundary_type, BoundaryType):
            raise ValueError("boundary_type must be BoundaryType")
        if recommended_terminal_state not in _terminal_enums():
            raise ValueError("boundary must recommend a terminal state")
        evidence = _normalize_texts("evidence_refs", evidence_refs, required=True)
        known = set(self._source_refs) | set(self._observations) | set(self._receipt_refs)
        if not set(evidence).issubset(known):
            raise ValueError("boundary evidence must already belong to the workspace")
        _require_ratio("confidence", confidence)
        _require_non_negative("monotonic_time", monotonic_time)
        self._last_update_at = max(self._last_update_at, float(monotonic_time))
        boundary_id = self._id_factory("boundary")
        self._boundaries[boundary_id] = (
            boundary_type,
            recommended_terminal_state,
            evidence,
            float(confidence),
        )
        payload = self._base_payload()
        payload.update(
            {
                "boundary_id": boundary_id,
                "boundary_type": boundary_type.value,
                "recommended_terminal_state": recommended_terminal_state.value,
                "evidence_refs": list(evidence),
                "confidence": float(confidence),
            }
        )
        emission = self._emit(BOUNDARY_PROPOSED, payload)
        return BoundaryProposal(
            boundary_id,
            boundary_type,
            recommended_terminal_state,
            evidence,
            float(confidence),
            emission,
        )

    def close(
        self,
        *,
        boundary_id: str,
        completion_reason: str,
        monotonic_time: float,
    ) -> WorkspaceEmission:
        self._require_open_event()
        _require_text("boundary_id", boundary_id)
        _require_text("completion_reason", completion_reason)
        _require_non_negative("monotonic_time", monotonic_time)
        if boundary_id not in self._boundaries:
            raise ValueError("unknown boundary_id")
        _, terminal_state, _, _ = self._boundaries[boundary_id]
        self._state = terminal_state
        self._last_update_at = max(self._last_update_at, float(monotonic_time))
        payload = self.snapshot().to_payload()
        payload["completion_reason"] = completion_reason.strip()
        payload["closing_boundary_id"] = boundary_id
        return self._emit(EVENT_CLOSED, payload)

    def snapshot(self) -> WorkspaceSnapshot:
        self._require_event()
        return WorkspaceSnapshot(
            cognitive_event_id=self._cognitive_event_id,
            event_kind=self._event_kind,
            body_id=self._body_id,
            node_id=self._node_id,
            mode=self._mode,
            lifecycle_state=self._state,
            started_at=self._started_at,
            last_update_at=self._last_update_at,
            confidence=round(self._confidence, 6),
            observation_refs=tuple(self._observations),
            source_refs=tuple(self._source_refs),
            correlation_ids=tuple(self._correlation_ids),
            receipt_refs=tuple(self._receipt_refs),
            contradiction_refs=tuple(self._contradiction_refs),
            interruption_refs=tuple(self._interruption_refs),
            proposal_refs=tuple(self._proposal_refs),
            authorization_refs=tuple(self._authorization_refs),
            execution_refs=tuple(self._execution_refs),
            degraded_reasons=tuple(self._degraded_reasons),
            boundary_ids=tuple(self._boundaries),
            replay_state=self._replay_state,
        )

    def read_only_view(self) -> Mapping[str, Any]:
        """Return an immutable view for language and interface queries."""
        return _freeze(self.snapshot().to_payload())

    def reset_closed(self) -> None:
        self._require_event()
        if self._state not in _terminal_enums():
            raise RuntimeError("cannot reset an open event")
        self._reset()

    def _is_related(
        self,
        observation: WorkspaceObservation,
        *,
        allow_uncorrelated: bool,
    ) -> bool:
        if observation.related_cognitive_event_id is not None:
            return observation.related_cognitive_event_id == self._cognitive_event_id
        current = set(self._correlation_ids)
        incoming = set(observation.correlation_ids)
        if current and incoming:
            return bool(current.intersection(incoming))
        return bool(allow_uncorrelated)

    def _accept_observation(
        self,
        observation: WorkspaceObservation,
        role: ObservationRole,
    ) -> None:
        if not isinstance(role, ObservationRole):
            raise ValueError("role must be ObservationRole")
        self._observations[observation.event_id] = observation
        self._last_update_at = max(self._last_update_at, observation.monotonic_time)
        self._add_unique(self._source_refs, observation.event_id)
        for ref in observation.source_refs:
            self._add_unique(self._source_refs, ref)
        for correlation_id in observation.correlation_ids:
            self._add_unique(self._correlation_ids, correlation_id)
        if observation.receipt_id is not None:
            self._add_unique(self._receipt_refs, observation.receipt_id)
        count = len(self._observations)
        if role is ObservationRole.SUPPORTING:
            self._confidence = (
                (self._confidence * max(0, count - 1)) + observation.confidence
            ) / count
        elif role is ObservationRole.CONTRADICTING:
            self._add_unique(self._contradiction_refs, observation.event_id)
            self._confidence = max(0.0, self._confidence - observation.confidence / 2.0)
        else:
            self._add_unique(self._interruption_refs, observation.event_id)
            self._confidence = min(self._confidence, observation.confidence)

    def _base_payload(self) -> Dict[str, Any]:
        snap = self.snapshot()
        return {
            "schema_version": COGNITIVE_SCHEMA_VERSION,
            "cognitive_event_id": snap.cognitive_event_id,
            "node_id": snap.node_id,
            "body_id": snap.body_id,
            "source_refs": list(snap.source_refs),
            "correlation_ids": list(snap.correlation_ids),
            "monotonic_time": snap.last_update_at,
            "replay_state": snap.replay_state,
            "health_state": "degraded" if snap.degraded_reasons else "healthy",
            "degraded_reasons": list(snap.degraded_reasons),
            "interpretation_only": True,
            "transport_only": True,
            "canonical_evidence": False,
            "authority": "none",
            "grants_authority": False,
            "grants_execution": False,
            "grants_actuation": False,
            "replay_safe": True,
        }

    def _emit(self, event_type: str, payload: Mapping[str, Any]) -> WorkspaceEmission:
        emission_id = self._id_factory("cognitive-event")
        emission = WorkspaceEmission(
            emission_id=emission_id,
            event_type=event_type,
            payload=_freeze(payload),
            parent_emission_id=self._last_emission_id,
        )
        self._last_emission_id = emission_id
        return emission

    def _validate_observation_body(self, observation: WorkspaceObservation) -> None:
        if observation.body_id != self._body_id:
            raise ValueError("observation belongs to another body")

    def _require_event(self) -> None:
        if self._cognitive_event_id is None:
            raise RuntimeError("workspace has no current event")

    def _require_open_event(self) -> None:
        self._require_event()
        if self._state in _terminal_enums():
            raise RuntimeError("workspace event is closed")

    @staticmethod
    def _add_unique(values: list, value: str) -> None:
        if value not in values:
            values.append(value)

    def _reset(self) -> None:
        self._cognitive_event_id = None
        self._event_kind = ""
        self._mode = CognitiveMode.OBSERVE
        self._state = LifecycleState.OPEN
        self._started_at = 0.0
        self._last_update_at = 0.0
        self._confidence = 0.0
        self._observations = {}
        self._source_refs = []
        self._correlation_ids = []
        self._receipt_refs = []
        self._contradiction_refs = []
        self._interruption_refs = []
        self._proposal_refs = []
        self._authorization_refs = []
        self._execution_refs = []
        self._degraded_reasons = []
        self._boundaries = {}
        self._last_emission_id = None


def _terminal_enums() -> set:
    return {LifecycleState(value) for value in _TERMINAL_STATES}


def _find_forbidden_keys(value: Any) -> set:
    found = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if isinstance(key, str) and key.lower() in _FORBIDDEN_AUTHORITY_KEYS:
                found.add(key.lower())
            found.update(_find_forbidden_keys(nested))
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            found.update(_find_forbidden_keys(nested))
    return found


def _find_named_keys(value: Any, names: set) -> set:
    found = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if isinstance(key, str) and key.lower() in names:
                found.add(key.lower())
            found.update(_find_named_keys(nested, names))
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            found.update(_find_named_keys(nested, names))
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


def _normalize_texts(name: str, values: Iterable[str], required: bool = False) -> Tuple[str, ...]:
    normalized = []
    for value in values:
        _require_text(name, value)
        stripped = value.strip()
        if stripped not in normalized:
            normalized.append(stripped)
    if required and not normalized:
        raise ValueError("%s must not be empty" % name)
    return tuple(normalized)


def _require_text(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


def _require_text_tuple(name: str, values: Any) -> None:
    if not isinstance(values, tuple):
        raise ValueError("%s must be a tuple" % name)
    for value in values:
        _require_text(name, value)


def _require_ratio(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % name)
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError("%s must be between 0 and 1" % name)


def _require_non_negative(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % name)
    if float(value) < 0.0:
        raise ValueError("%s must be non-negative" % name)

# SPDX-License-Identifier: GPL-3.0-only
"""Evidence-linked episode proposals for closed cognitive events.

Episodes are navigational memory objects. They never replace observations,
receipts, Court decisions, execution records, or Riven identity continuity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple
from uuid import uuid4

CONTRACT = "velvet.cognitive-events.v1"
SCHEMA_VERSION = "1.0"
EVENT_OPENED = "cognitive.event.opened"
EVENT_CLOSED = "cognitive.event.closed"
EPISODE_PROPOSED = "cognitive.episode.proposed"

_TERMINAL_STATES = {
    "COMPLETED",
    "INTERRUPTED",
    "STALE",
    "CONTRADICTED",
    "ABANDONED",
    "UNKNOWN_OUTCOME",
    "DEGRADED_COMPLETION",
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
    "identity_proof",
    "canonical_memory",
}


class RetentionClass(str, Enum):
    TRANSIENT = "transient"
    OPERATIONAL = "operational"
    SIGNIFICANT = "significant"
    PROTECTED = "protected"


@dataclass(frozen=True)
class ClosedEventContext:
    cognitive_event_id: str
    body_id: str
    node_id: str
    event_kind: str
    lifecycle_state: str
    mode: str
    started_at: float
    ended_at: float
    confidence: float
    completion_reason: str
    closing_boundary_id: str
    opened_event_id: str
    closed_event_id: str
    source_refs: Tuple[str, ...]
    correlation_ids: Tuple[str, ...]
    observation_refs: Tuple[str, ...]
    proposal_refs: Tuple[str, ...]
    authorization_refs: Tuple[str, ...]
    execution_refs: Tuple[str, ...]
    receipt_refs: Tuple[str, ...]
    prediction_refs: Tuple[str, ...]
    interruption_refs: Tuple[str, ...]
    contradiction_refs: Tuple[str, ...]
    boundary_refs: Tuple[str, ...]
    replay_state: str

    @classmethod
    def from_event_documents(
        cls,
        opened: Mapping[str, Any],
        closed: Mapping[str, Any],
    ) -> "ClosedEventContext":
        opened_payload = _event_payload(opened, EVENT_OPENED)
        closed_payload = _event_payload(closed, EVENT_CLOSED)
        for name in ("cognitive_event_id", "body_id", "node_id", "replay_state"):
            if opened_payload.get(name) != closed_payload.get(name):
                raise ValueError("opened and closed events disagree on %s" % name)
        opened_state = opened_payload.get("lifecycle_state")
        if opened_state in _TERMINAL_STATES:
            raise ValueError("opened event cannot already be terminal")
        closed_state = closed_payload.get("lifecycle_state")
        if closed_state not in _TERMINAL_STATES:
            raise ValueError("closed event requires terminal lifecycle_state")
        start = opened_payload.get("monotonic_time")
        end = closed_payload.get("monotonic_time")
        _non_negative("started_at", start)
        _non_negative("ended_at", end)
        if float(end) < float(start):
            raise ValueError("closed event cannot end before it opened")
        _text("event_kind", closed_payload.get("event_kind"))
        _text("completion_reason", closed_payload.get("completion_reason"))
        _text("closing_boundary_id", closed_payload.get("closing_boundary_id"))
        _ratio("confidence", closed_payload.get("confidence"))
        opened_event_id = opened.get("event_id")
        closed_event_id = closed.get("event_id")
        _text("opened_event_id", opened_event_id)
        _text("closed_event_id", closed_event_id)
        source_refs = _merge(
            _sequence("source_refs", opened_payload.get("source_refs", ()), True),
            _sequence("source_refs", closed_payload.get("source_refs", ()), True),
            (opened_event_id, closed_event_id),
        )
        return cls(
            cognitive_event_id=closed_payload["cognitive_event_id"],
            body_id=closed_payload["body_id"],
            node_id=closed_payload["node_id"],
            event_kind=closed_payload["event_kind"],
            lifecycle_state=closed_state,
            mode=closed_payload.get("mode", "OBSERVE"),
            started_at=float(start),
            ended_at=float(end),
            confidence=float(closed_payload["confidence"]),
            completion_reason=closed_payload["completion_reason"],
            closing_boundary_id=closed_payload["closing_boundary_id"],
            opened_event_id=opened_event_id,
            closed_event_id=closed_event_id,
            source_refs=source_refs,
            correlation_ids=_merge(
                _sequence("correlation_ids", opened_payload.get("correlation_ids", ())),
                _sequence("correlation_ids", closed_payload.get("correlation_ids", ())),
            ),
            observation_refs=_sequence(
                "observation_refs", closed_payload.get("observation_refs", ())
            ),
            proposal_refs=_sequence(
                "proposal_refs", closed_payload.get("proposal_refs", ())
            ),
            authorization_refs=_sequence(
                "authorization_refs", closed_payload.get("authorization_refs", ())
            ),
            execution_refs=_sequence(
                "execution_refs", closed_payload.get("execution_refs", ())
            ),
            receipt_refs=_sequence(
                "receipt_refs", closed_payload.get("receipt_refs", ())
            ),
            prediction_refs=_sequence(
                "prediction_refs", closed_payload.get("prediction_refs", ())
            ),
            interruption_refs=_sequence(
                "interruption_refs", closed_payload.get("interruption_refs", ())
            ),
            contradiction_refs=_sequence(
                "contradiction_refs", closed_payload.get("contradiction_refs", ())
            ),
            boundary_refs=_merge(
                _sequence("boundary_ids", closed_payload.get("boundary_ids", ())),
                (closed_payload["closing_boundary_id"],),
            ),
            replay_state=closed_payload["replay_state"],
        )

    @property
    def canonical(self) -> bool:
        return False

    @property
    def identity_proof(self) -> bool:
        return False


@dataclass(frozen=True)
class RetentionPolicy:
    retention_class: RetentionClass = RetentionClass.OPERATIONAL
    policy_ref: Optional[str] = None
    continuity_anchor_ref: Optional[str] = None
    protected_reason: Optional[str] = None

    def validate(self, receipt_refs: Tuple[str, ...]) -> None:
        if not isinstance(self.retention_class, RetentionClass):
            raise ValueError("retention_class must be RetentionClass")
        if self.policy_ref is not None:
            _text("policy_ref", self.policy_ref)
        if self.continuity_anchor_ref is not None:
            _text("continuity_anchor_ref", self.continuity_anchor_ref)
        if self.protected_reason is not None:
            _text("protected_reason", self.protected_reason)
        if self.retention_class in {
            RetentionClass.SIGNIFICANT,
            RetentionClass.PROTECTED,
        }:
            if self.policy_ref is None:
                raise ValueError("significant or protected retention requires policy_ref")
            if not receipt_refs:
                raise ValueError("significant or protected retention requires receipts")
        if self.retention_class is RetentionClass.PROTECTED:
            if self.protected_reason is None:
                raise ValueError("protected retention requires protected_reason")
        elif self.protected_reason is not None:
            raise ValueError("protected_reason requires protected retention")
        if self.continuity_anchor_ref is not None and self.retention_class not in {
            RetentionClass.SIGNIFICANT,
            RetentionClass.PROTECTED,
        }:
            raise ValueError("continuity anchor requires significant or protected retention")


@dataclass(frozen=True)
class EpisodeEmission:
    emission_id: str
    payload: Mapping[str, Any]
    parent_event_id: str

    def __post_init__(self) -> None:
        _text("emission_id", self.emission_id)
        _text("parent_event_id", self.parent_event_id)
        _validate_episode_payload(self.payload)

    @property
    def authority_granted(self) -> bool:
        return False

    @property
    def identity_proof(self) -> bool:
        return False

    def to_event_document(self, *, source: str, timestamp: float) -> Dict[str, Any]:
        _text("source", source)
        _non_negative("timestamp", timestamp)
        return {
            "event_id": self.emission_id,
            "timestamp": float(timestamp),
            "source": source.strip(),
            "event_type": EPISODE_PROPOSED,
            "intent": None,
            "payload": _thaw(self.payload),
            "metadata": {
                "contract": CONTRACT,
                "schema_version": SCHEMA_VERSION,
                "family": "cognitive-event",
                "authority": "none",
                "interpretation_only": True,
            },
            "parent_event_id": self.parent_event_id,
            "receipt_id": None,
        }


@dataclass(frozen=True)
class EpisodeProposal:
    episode_id: str
    cognitive_event_id: str
    body_id: str
    node_id: str
    summary: str
    retention_class: RetentionClass
    confidence: float
    source_refs: Tuple[str, ...]
    receipt_refs: Tuple[str, ...]
    prediction_refs: Tuple[str, ...]
    prediction_error_refs: Tuple[str, ...]
    action_tracking_refs: Tuple[str, ...]
    interruption_refs: Tuple[str, ...]
    outstanding_effect_refs: Tuple[str, ...]
    emission: EpisodeEmission

    @property
    def canonical(self) -> bool:
        return False

    @property
    def memory_navigation_only(self) -> bool:
        return True

    @property
    def identity_proof(self) -> bool:
        return False

    def read_only_view(self) -> Mapping[str, Any]:
        return _freeze(
            {
                "episode_id": self.episode_id,
                "cognitive_event_id": self.cognitive_event_id,
                "body_id": self.body_id,
                "node_id": self.node_id,
                "summary": self.summary,
                "retention_class": self.retention_class.value,
                "confidence": self.confidence,
                "source_refs": list(self.source_refs),
                "receipt_refs": list(self.receipt_refs),
                "prediction_refs": list(self.prediction_refs),
                "prediction_error_refs": list(self.prediction_error_refs),
                "action_tracking_refs": list(self.action_tracking_refs),
                "interruption_refs": list(self.interruption_refs),
                "outstanding_effect_refs": list(self.outstanding_effect_refs),
                "canonical": False,
                "memory_navigation_only": True,
                "identity_proof": False,
                "authority_granted": False,
            }
        )


class EpisodeConsolidator:
    def __init__(
        self,
        *,
        body_id: str,
        node_id: str,
        max_episodes: int = 128,
        id_factory: Optional[Callable[[str], str]] = None,
        replay_state: str = "live",
    ) -> None:
        _text("body_id", body_id)
        _text("node_id", node_id)
        if isinstance(max_episodes, bool) or not isinstance(max_episodes, int):
            raise ValueError("max_episodes must be an integer")
        if max_episodes < 1:
            raise ValueError("max_episodes must be positive")
        if replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid replay_state")
        self.body_id = body_id.strip()
        self.node_id = node_id.strip()
        self.max_episodes = max_episodes
        self.replay_state = replay_state
        self._id = id_factory or (lambda prefix: "%s_%s" % (prefix, uuid4().hex))
        self._episode_ids = set()

    def consolidate(
        self,
        *,
        opened_event: Mapping[str, Any],
        closed_event: Mapping[str, Any],
        summary: str,
        confidence: float,
        retention: RetentionPolicy = RetentionPolicy(),
        actors: Iterable[str] = (),
        locations: Iterable[str] = (),
        what_changed: Iterable[str] = (),
        prediction_views: Iterable[Mapping[str, Any]] = (),
        action_views: Iterable[Mapping[str, Any]] = (),
        interrupt_views: Iterable[Mapping[str, Any]] = (),
        outcome_refs: Iterable[str] = (),
        receipt_refs: Iterable[str] = (),
        episode_id: Optional[str] = None,
    ) -> EpisodeProposal:
        if len(self._episode_ids) >= self.max_episodes:
            raise RuntimeError("episode proposal capacity reached")
        context = ClosedEventContext.from_event_documents(opened_event, closed_event)
        if context.body_id != self.body_id:
            raise ValueError("closed event belongs to another body")
        if context.node_id != self.node_id:
            raise ValueError("closed event belongs to another node")
        if context.replay_state != self.replay_state:
            raise ValueError("closed event and consolidator replay_state differ")
        _text("summary", summary)
        _ratio("confidence", confidence)
        actor_refs = _sequence("actors", actors)
        location_refs = _sequence("locations", locations)
        changes = _sequence("what_changed", what_changed)
        explicit_outcomes = _sequence("outcome_refs", outcome_refs)
        explicit_receipts = _sequence("receipt_refs", receipt_refs)

        prediction_ids = []
        prediction_error_ids = []
        action_ids = []
        interrupt_ids = []
        outstanding_effects = []
        source_refs = list(context.source_refs)
        receipts = list(_merge(context.receipt_refs, explicit_receipts))
        proposal_refs = list(context.proposal_refs)
        authorization_refs = list(context.authorization_refs)
        execution_refs = list(context.execution_refs)
        outcomes = list(explicit_outcomes)

        for view in prediction_views:
            _validate_related_view(view, context, "prediction")
            status = view.get("status")
            if status == "pending":
                raise ValueError("pending prediction cannot enter a completed episode")
            if status not in {"confirmed", "contradicted", "expired", "unknown"}:
                raise ValueError("invalid prediction status")
            prediction_id_value = view.get("prediction_id")
            _text("prediction_id", prediction_id_value)
            _append_unique(prediction_ids, prediction_id_value)
            error_id = view.get("prediction_error_id")
            if error_id is not None:
                _text("prediction_error_id", error_id)
                _append_unique(prediction_error_ids, error_id)
            _extend_unique(source_refs, _sequence("source_refs", view.get("source_refs", ())))
            _extend_unique(receipts, _sequence("receipt_refs", view.get("receipt_refs", ())))

        for view in action_views:
            _validate_related_view(view, context, "action tracking")
            state = view.get("state")
            if state == "started":
                raise ValueError("active action tracking cannot enter a completed episode")
            if state not in {"completed", "failed", "unknown", "interrupted"}:
                raise ValueError("invalid action tracking state")
            tracking_id = view.get("tracking_id")
            _text("tracking_id", tracking_id)
            _append_unique(action_ids, tracking_id)
            _append_unique(outcomes, tracking_id)
            _extend_unique(source_refs, _sequence("source_refs", view.get("source_refs", ())))
            _extend_unique(receipts, _sequence("receipt_refs", view.get("receipt_refs", ())))
            _extend_unique(
                outstanding_effects,
                _sequence(
                    "outstanding_effect_refs",
                    view.get("outstanding_effect_refs", ()),
                ),
            )
            auth_ref = view.get("authorization_ref")
            exec_ref = view.get("execution_ref")
            _text("authorization_ref", auth_ref)
            _text("execution_ref", exec_ref)
            _append_unique(authorization_refs, auth_ref)
            _append_unique(execution_refs, exec_ref)

        for view in interrupt_views:
            _validate_related_view(view, context, "interrupt")
            if view.get("accepted") is not True:
                raise ValueError("only accepted interrupts may enter an episode")
            interrupt_id_value = view.get("interrupt_id")
            _text("interrupt_id", interrupt_id_value)
            _append_unique(interrupt_ids, interrupt_id_value)
            _extend_unique(source_refs, _sequence("source_refs", view.get("source_refs", ())))
            _extend_unique(
                outstanding_effects,
                _sequence(
                    "outstanding_effect_refs",
                    view.get("outstanding_effect_refs", ()),
                ),
            )

        receipt_tuple = tuple(receipts)
        retention.validate(receipt_tuple)
        chosen_id = episode_id or self._id("episode")
        _text("episode_id", chosen_id)
        if chosen_id in self._episode_ids:
            raise ValueError("episode_id already exists")

        all_prediction_refs = _merge(context.prediction_refs, tuple(prediction_ids))
        all_interrupt_refs = _merge(context.interruption_refs, tuple(interrupt_ids))
        all_outcome_refs = _merge(tuple(outcomes), tuple(action_ids))
        payload = {
            "schema_version": SCHEMA_VERSION,
            "cognitive_event_id": context.cognitive_event_id,
            "node_id": context.node_id,
            "body_id": context.body_id,
            "source_refs": list(tuple(source_refs)),
            "correlation_ids": list(context.correlation_ids),
            "monotonic_time": context.ended_at,
            "replay_state": context.replay_state,
            "health_state": "healthy",
            "degraded_reasons": [],
            **_FLAGS,
            "episode_id": chosen_id,
            "source_event_id": context.cognitive_event_id,
            "opened_event_ref": context.opened_event_id,
            "closed_event_ref": context.closed_event_id,
            "summary": summary.strip(),
            "start_time": context.started_at,
            "end_time": context.ended_at,
            "event_kind": context.event_kind,
            "completion_state": context.lifecycle_state,
            "completion_reason": context.completion_reason,
            "closing_boundary_ref": context.closing_boundary_id,
            "actors": list(actor_refs),
            "locations": list(location_refs),
            "what_changed": list(changes),
            "observation_refs": list(context.observation_refs),
            "proposal_refs": list(tuple(proposal_refs)),
            "authorization_refs": list(tuple(authorization_refs)),
            "execution_refs": list(tuple(execution_refs)),
            "outcome_refs": list(all_outcome_refs),
            "prediction_refs": list(all_prediction_refs),
            "prediction_error_refs": list(tuple(prediction_error_ids)),
            "interruption_refs": list(all_interrupt_refs),
            "contradiction_refs": list(context.contradiction_refs),
            "boundary_refs": list(context.boundary_refs),
            "action_tracking_refs": list(tuple(action_ids)),
            "outstanding_effect_refs": list(tuple(outstanding_effects)),
            "receipt_refs": list(receipt_tuple),
            "confidence": float(confidence),
            "retention_class": retention.retention_class.value,
            "retention_policy_ref": retention.policy_ref,
            "continuity_anchor_ref": retention.continuity_anchor_ref,
            "protected_reason": retention.protected_reason,
            "memory_navigation_only": True,
            "canonical_memory": False,
            "identity_proof": False,
        }
        _validate_episode_payload(payload)
        emission = EpisodeEmission(
            emission_id=self._id("cognitive-event"),
            payload=_freeze(payload),
            parent_event_id=context.closed_event_id,
        )
        self._episode_ids.add(chosen_id)
        return EpisodeProposal(
            episode_id=chosen_id,
            cognitive_event_id=context.cognitive_event_id,
            body_id=context.body_id,
            node_id=context.node_id,
            summary=summary.strip(),
            retention_class=retention.retention_class,
            confidence=float(confidence),
            source_refs=tuple(source_refs),
            receipt_refs=receipt_tuple,
            prediction_refs=all_prediction_refs,
            prediction_error_refs=tuple(prediction_error_ids),
            action_tracking_refs=tuple(action_ids),
            interruption_refs=all_interrupt_refs,
            outstanding_effect_refs=tuple(outstanding_effects),
            emission=emission,
        )


def _event_payload(document: Mapping[str, Any], event_type: str) -> Mapping[str, Any]:
    if not isinstance(document, Mapping):
        raise ValueError("cognitive event document must be a mapping")
    if document.get("event_type") != event_type:
        raise ValueError("unexpected cognitive event type")
    metadata = document.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("cognitive event metadata must be a mapping")
    if metadata.get("contract") != CONTRACT:
        raise ValueError("unexpected cognitive event contract")
    if metadata.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected cognitive schema version")
    if metadata.get("authority") != "none":
        raise ValueError("cognitive event metadata cannot carry authority")
    if metadata.get("interpretation_only") is not True:
        raise ValueError("cognitive event must remain interpretation-only")
    payload = document.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("cognitive event payload must be a mapping")
    for key, expected in _FLAGS.items():
        if payload.get(key) != expected:
            raise ValueError("cognitive event payload %s must be %r" % (key, expected))
    for name in ("cognitive_event_id", "body_id", "node_id", "event_kind"):
        _text(name, payload.get(name))
    if payload.get("replay_state") not in {"live", "fixture", "replay"}:
        raise ValueError("invalid replay_state")
    _reject_except_false_flags(payload, "cognitive event payload")
    return payload


def _validate_related_view(
    view: Mapping[str, Any],
    context: ClosedEventContext,
    name: str,
) -> None:
    if not isinstance(view, Mapping):
        raise ValueError("%s view must be a mapping" % name)
    if view.get("cognitive_event_id") != context.cognitive_event_id:
        raise ValueError("%s belongs to another cognitive event" % name)
    if view.get("body_id") != context.body_id:
        raise ValueError("%s belongs to another body" % name)
    if view.get("node_id") != context.node_id:
        raise ValueError("%s belongs to another node" % name)
    if view.get("replay_state") != context.replay_state:
        raise ValueError("%s replay_state differs from event" % name)
    _reject_except_false_flags(view, "%s view" % name)


def _validate_episode_payload(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("episode payload must be a mapping")
    for key, expected in _FLAGS.items():
        if payload.get(key) != expected:
            raise ValueError("episode payload %s must be %r" % (key, expected))
    for name in (
        "cognitive_event_id",
        "body_id",
        "node_id",
        "episode_id",
        "source_event_id",
        "opened_event_ref",
        "closed_event_ref",
        "summary",
        "event_kind",
        "completion_state",
        "completion_reason",
        "closing_boundary_ref",
    ):
        _text(name, payload.get(name))
    if payload.get("completion_state") not in _TERMINAL_STATES:
        raise ValueError("episode requires terminal completion_state")
    if payload.get("retention_class") not in {
        "transient",
        "operational",
        "significant",
        "protected",
    }:
        raise ValueError("invalid retention_class")
    _ratio("confidence", payload.get("confidence"))
    _non_negative("start_time", payload.get("start_time"))
    _non_negative("end_time", payload.get("end_time"))
    if float(payload["end_time"]) < float(payload["start_time"]):
        raise ValueError("episode cannot end before it starts")
    for name in (
        "source_refs",
        "correlation_ids",
        "actors",
        "locations",
        "what_changed",
        "observation_refs",
        "proposal_refs",
        "authorization_refs",
        "execution_refs",
        "outcome_refs",
        "prediction_refs",
        "prediction_error_refs",
        "interruption_refs",
        "contradiction_refs",
        "boundary_refs",
        "action_tracking_refs",
        "outstanding_effect_refs",
        "receipt_refs",
    ):
        _sequence(name, payload.get(name, ()), required=name == "source_refs")
    if payload.get("memory_navigation_only") is not True:
        raise ValueError("episode must remain memory-navigation-only")
    if payload.get("canonical_memory") is not False:
        raise ValueError("episode cannot claim canonical memory")
    if payload.get("identity_proof") is not False:
        raise ValueError("episode cannot become identity proof")
    _reject_except_false_flags(payload, "episode payload")


def _reject_except_false_flags(value: Mapping[str, Any], name: str) -> None:
    permitted_false = {
        "authority",
        "grants_authority",
        "grants_execution",
        "grants_actuation",
        "canonical_evidence",
        "canonical_memory",
        "identity_proof",
        "authority_granted",
        "execution_performed",
        "actuation_performed",
        "safeing_authorized",
        "safeing_performed",
        "automatic_retry_requested",
    }
    nested = {}
    for key, item in value.items():
        if key in permitted_false:
            if key == "authority":
                if item != "none":
                    raise ValueError("%s authority must be none" % name)
            elif item is not False:
                raise ValueError("%s %s must be False" % (name, key))
            continue
        nested[key] = item
    found = _find(nested, _FORBIDDEN) | _find(nested, _CLAIMS)
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


def _sequence(name: str, values: Any, required: bool = False) -> Tuple[str, ...]:
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


def _append_unique(values: list, value: str) -> None:
    if value not in values:
        values.append(value)


def _extend_unique(values: list, additions: Iterable[str]) -> None:
    for value in additions:
        _append_unique(values, value)


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
    "EPISODE_PROPOSED",
    "RetentionClass",
    "ClosedEventContext",
    "RetentionPolicy",
    "EpisodeEmission",
    "EpisodeProposal",
    "EpisodeConsolidator",
]

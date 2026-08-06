# SPDX-License-Identifier: GPL-3.0-only
"""Prediction and externally owned action-outcome tracking for cognitive events.

This module is interpretation-only. It never authorizes, executes, retries,
performs safeing, creates receipts, or replaces source evidence.
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
PREDICTION_CREATED = "cognitive.prediction.created"
PREDICTION_RESOLVED = "cognitive.prediction.resolved"
PREDICTION_ERROR = "cognitive.prediction.error"
ACTION_TRACKING_STARTED = "cognitive.action.tracking_started"
ACTION_TRACKING_FINISHED = "cognitive.action.tracking_finished"

_FORBIDDEN = {
    "actuate", "actuation", "authorization", "authorized", "authorized_by",
    "capability", "capability_token", "command", "court_decision",
    "court_token", "execution_token", "executor", "executor_handle",
    "executor_name", "hardware_handle", "hardware_target", "permit",
    "policy_override", "retry_authorized", "safety_override", "shell", "token",
}
_CLAIMS = {
    "authority", "authority_granted", "grants_authority", "grants_execution",
    "grants_actuation", "execution_performed", "actuation_performed",
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


class PredictionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CONTRADICTED = "contradicted"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class PredictionErrorClass(str, Enum):
    MISMATCH = "mismatch"
    TIMEOUT = "timeout"
    PARTIAL = "partial"
    IMPOSSIBLE = "impossible"
    UNOBSERVABLE = "unobservable"


class ActionTrackingState(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True)
class CognitiveEmission:
    emission_id: str
    event_type: str
    payload: Mapping[str, Any]
    parent_emission_id: Optional[str] = None

    def __post_init__(self) -> None:
        _text("emission_id", self.emission_id)
        if self.event_type not in {
            PREDICTION_CREATED, PREDICTION_RESOLVED, PREDICTION_ERROR,
            ACTION_TRACKING_STARTED, ACTION_TRACKING_FINISHED,
        }:
            raise ValueError("unexpected cognitive event type")
        _transport_payload(self.payload)

    @property
    def authority_granted(self) -> bool:
        return False

    @property
    def execution_performed(self) -> bool:
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
class PredictionRecord:
    prediction_id: str
    cognitive_event_id: str
    body_id: str
    node_id: str
    subject: str
    expected_state: Mapping[str, Any]
    tolerance: Mapping[str, Any]
    expected_by: float
    confidence: float
    source_model: str
    source_version: str
    source_refs: Tuple[str, ...]
    observation_refs: Tuple[str, ...]
    correlation_ids: Tuple[str, ...]
    replay_state: str
    created_at: float
    status: PredictionStatus = PredictionStatus.PENDING
    receipt_refs: Tuple[str, ...] = ()
    resolved_at: Optional[float] = None
    observed_state: Mapping[str, Any] = field(default_factory=dict)
    error_class: Optional[PredictionErrorClass] = None
    prediction_error_id: Optional[str] = None
    last_emission_id: Optional[str] = None

    @property
    def canonical(self) -> bool:
        return False

    @property
    def authority_granted(self) -> bool:
        return False

    @property
    def automatic_retry_requested(self) -> bool:
        return False

    def read_only_view(self) -> Mapping[str, Any]:
        return _freeze({
            "prediction_id": self.prediction_id,
            "cognitive_event_id": self.cognitive_event_id,
            "body_id": self.body_id,
            "node_id": self.node_id,
            "subject": self.subject,
            "expected_state": _thaw(self.expected_state),
            "tolerance": _thaw(self.tolerance),
            "expected_by": self.expected_by,
            "confidence": self.confidence,
            "source_model": self.source_model,
            "source_version": self.source_version,
            "source_refs": list(self.source_refs),
            "observation_refs": list(self.observation_refs),
            "correlation_ids": list(self.correlation_ids),
            "receipt_refs": list(self.receipt_refs),
            "status": self.status.value,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "observed_state": _thaw(self.observed_state),
            "error_class": self.error_class.value if self.error_class else None,
            "prediction_error_id": self.prediction_error_id,
            "replay_state": self.replay_state,
            "canonical": False,
            "authority_granted": False,
            "automatic_retry_requested": False,
        })


@dataclass(frozen=True)
class PredictionOutcome:
    record: PredictionRecord
    resolution: CognitiveEmission
    error: Optional[CognitiveEmission] = None


class PredictionTracker:
    def __init__(
        self, *, body_id: str, node_id: str, max_predictions: int = 64,
        id_factory: Optional[Callable[[str], str]] = None,
        replay_state: str = "live",
    ) -> None:
        _text("body_id", body_id)
        _text("node_id", node_id)
        if isinstance(max_predictions, bool) or not isinstance(max_predictions, int) or max_predictions < 1:
            raise ValueError("max_predictions must be a positive integer")
        if replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid replay_state")
        self.body_id, self.node_id = body_id.strip(), node_id.strip()
        self.max_predictions, self.replay_state = max_predictions, replay_state
        self._id = id_factory or (lambda p: "%s_%s" % (p, uuid4().hex))
        self._records: Dict[str, PredictionRecord] = {}

    def create_from_workspace(
        self, *, workspace_view: Mapping[str, Any], subject: str,
        expected_state: Mapping[str, Any], expected_by: float, confidence: float,
        source_model: str, source_version: str, monotonic_time: float,
        tolerance: Optional[Mapping[str, Any]] = None,
        observation_refs: Iterable[str] = (), source_refs: Iterable[str] = (),
        prediction_id: Optional[str] = None,
    ) -> Tuple[PredictionRecord, CognitiveEmission]:
        context = CognitiveWorkspaceContext.from_view(workspace_view)
        context.assert_matches(body_id=self.body_id, node_id=self.node_id)
        if context.replay_state != self.replay_state:
            raise ValueError("workspace and prediction replay_state differ")
        return self.create(
            cognitive_event_id=context.cognitive_event_id, subject=subject,
            expected_state=expected_state, expected_by=expected_by,
            confidence=confidence, source_model=source_model,
            source_version=source_version, monotonic_time=monotonic_time,
            tolerance=tolerance, observation_refs=observation_refs,
            source_refs=_merge(context.source_refs, source_refs),
            correlation_ids=context.correlation_ids, prediction_id=prediction_id,
        )

    def create(
        self, *, cognitive_event_id: str, subject: str,
        expected_state: Mapping[str, Any], expected_by: float, confidence: float,
        source_model: str, source_version: str, source_refs: Iterable[str],
        monotonic_time: float, tolerance: Optional[Mapping[str, Any]] = None,
        observation_refs: Iterable[str] = (), correlation_ids: Iterable[str] = (),
        prediction_id: Optional[str] = None,
    ) -> Tuple[PredictionRecord, CognitiveEmission]:
        if len(self._records) >= self.max_predictions:
            raise RuntimeError("prediction capacity reached")
        for name, value in (
            ("cognitive_event_id", cognitive_event_id), ("subject", subject),
            ("source_model", source_model), ("source_version", source_version),
        ):
            _text(name, value)
        _non_negative("monotonic_time", monotonic_time)
        _non_negative("expected_by", expected_by)
        if float(expected_by) < float(monotonic_time):
            raise ValueError("expected_by cannot precede prediction creation")
        _ratio("confidence", confidence)
        if not isinstance(expected_state, Mapping) or not expected_state:
            raise ValueError("expected_state must be a non-empty mapping")
        tolerance = {} if tolerance is None else tolerance
        if not isinstance(tolerance, Mapping):
            raise ValueError("tolerance must be a mapping")
        _reject(expected_state, "expected_state")
        _reject(tolerance, "tolerance")
        _tolerance(expected_state, tolerance)
        chosen = prediction_id or self._id("prediction")
        _text("prediction_id", chosen)
        if chosen in self._records:
            raise ValueError("prediction_id already exists")
        record = PredictionRecord(
            prediction_id=chosen.strip(),
            cognitive_event_id=cognitive_event_id.strip(),
            body_id=self.body_id, node_id=self.node_id, subject=subject.strip(),
            expected_state=_freeze(expected_state), tolerance=_freeze(tolerance),
            expected_by=float(expected_by), confidence=float(confidence),
            source_model=source_model.strip(), source_version=source_version.strip(),
            source_refs=_texts("source_refs", source_refs, True),
            observation_refs=_texts("observation_refs", observation_refs),
            correlation_ids=_texts("correlation_ids", correlation_ids),
            replay_state=self.replay_state, created_at=float(monotonic_time),
        )
        self._records[record.prediction_id] = record
        emission = self._emit(record, PREDICTION_CREATED, self._created(record))
        return record, emission

    def resolve(
        self, prediction_id: str, *, observed_state: Mapping[str, Any],
        observation_refs: Iterable[str], receipt_refs: Iterable[str] = (),
        confidence: float, monotonic_time: float,
    ) -> PredictionOutcome:
        record = self._pending(prediction_id)
        if not isinstance(observed_state, Mapping):
            raise ValueError("observed_state must be a mapping")
        _reject(observed_state, "observed_state")
        observations, receipts = (
            _texts("observation_refs", observation_refs),
            _texts("receipt_refs", receipt_refs),
        )
        if not observations and not receipts:
            raise ValueError("prediction resolution requires evidence references")
        _ratio("confidence", confidence)
        _non_negative("monotonic_time", monotonic_time)
        if float(monotonic_time) < record.created_at:
            raise ValueError("resolution cannot precede prediction creation")
        record.status, record.error_class = _compare(
            record.expected_state, observed_state, record.tolerance
        )
        record.resolved_at, record.confidence = float(monotonic_time), float(confidence)
        record.observed_state = _freeze(observed_state)
        record.observation_refs = _merge(record.observation_refs, observations)
        record.receipt_refs = _merge(record.receipt_refs, receipts)
        resolution = self._emit(record, PREDICTION_RESOLVED, self._resolved(record))
        error = self._error(record) if record.error_class else None
        return PredictionOutcome(record, resolution, error)

    def expire(
        self, prediction_id: str, *, monotonic_time: float,
        observation_refs: Iterable[str] = (), receipt_refs: Iterable[str] = (),
        confidence: float = 1.0,
    ) -> PredictionOutcome:
        record = self._pending(prediction_id)
        _non_negative("monotonic_time", monotonic_time)
        if float(monotonic_time) < record.expected_by:
            raise ValueError("prediction cannot expire before expected_by")
        _ratio("confidence", confidence)
        record.status, record.error_class = PredictionStatus.EXPIRED, PredictionErrorClass.TIMEOUT
        record.resolved_at, record.confidence = float(monotonic_time), float(confidence)
        record.observation_refs = _merge(record.observation_refs, _texts("observation_refs", observation_refs))
        record.receipt_refs = _merge(record.receipt_refs, _texts("receipt_refs", receipt_refs))
        resolution = self._emit(record, PREDICTION_RESOLVED, self._resolved(record))
        return PredictionOutcome(record, resolution, self._error(record))

    def mark_unknown(
        self, prediction_id: str, *, monotonic_time: float,
        reason_class: PredictionErrorClass = PredictionErrorClass.UNOBSERVABLE,
        observed_state: Optional[Mapping[str, Any]] = None,
        observation_refs: Iterable[str] = (), receipt_refs: Iterable[str] = (),
        confidence: float = 1.0,
    ) -> PredictionOutcome:
        if reason_class not in {PredictionErrorClass.UNOBSERVABLE, PredictionErrorClass.IMPOSSIBLE}:
            raise ValueError("unknown outcome requires unobservable or impossible")
        record = self._pending(prediction_id)
        _non_negative("monotonic_time", monotonic_time)
        _ratio("confidence", confidence)
        observed = {} if observed_state is None else observed_state
        if not isinstance(observed, Mapping):
            raise ValueError("observed_state must be a mapping")
        _reject(observed, "observed_state")
        record.status, record.error_class = PredictionStatus.UNKNOWN, reason_class
        record.resolved_at, record.confidence = float(monotonic_time), float(confidence)
        record.observed_state = _freeze(observed)
        record.observation_refs = _merge(record.observation_refs, _texts("observation_refs", observation_refs))
        record.receipt_refs = _merge(record.receipt_refs, _texts("receipt_refs", receipt_refs))
        resolution = self._emit(record, PREDICTION_RESOLVED, self._resolved(record))
        return PredictionOutcome(record, resolution, self._error(record))

    def read_only_view(self, prediction_id: str) -> Mapping[str, Any]:
        return self._record(prediction_id).read_only_view()

    def pending_ids(self) -> Tuple[str, ...]:
        return tuple(k for k, v in self._records.items() if v.status is PredictionStatus.PENDING)

    def prediction_stability(self) -> float:
        resolved = [v for v in self._records.values() if v.status is not PredictionStatus.PENDING]
        if not resolved:
            return 1.0
        return round(sum(v.status is PredictionStatus.CONFIRMED for v in resolved) / float(len(resolved)), 6)

    def _record(self, prediction_id: str) -> PredictionRecord:
        _text("prediction_id", prediction_id)
        if prediction_id not in self._records:
            raise KeyError("unknown prediction_id")
        return self._records[prediction_id]

    def _pending(self, prediction_id: str) -> PredictionRecord:
        record = self._record(prediction_id)
        if record.status is not PredictionStatus.PENDING:
            raise RuntimeError("prediction is already resolved")
        return record

    def _base(self, r: PredictionRecord, when: float) -> Dict[str, Any]:
        return _common(
            r.cognitive_event_id, r.node_id, r.body_id,
            _merge(r.source_refs, r.observation_refs, r.receipt_refs),
            r.correlation_ids, when, r.replay_state,
        )

    def _created(self, r: PredictionRecord) -> Dict[str, Any]:
        p = self._base(r, r.created_at)
        p.update({
            "prediction_id": r.prediction_id, "subject": r.subject,
            "expected_state": _thaw(r.expected_state), "tolerance": _thaw(r.tolerance),
            "expected_by": r.expected_by, "confidence": r.confidence,
            "source_model": r.source_model, "source_version": r.source_version,
            "observation_refs": list(r.observation_refs), "status": "pending",
        })
        return p

    def _resolved(self, r: PredictionRecord) -> Dict[str, Any]:
        p = self._base(r, r.resolved_at or r.created_at)
        p.update({
            "prediction_id": r.prediction_id, "status": r.status.value,
            "observed_state": _thaw(r.observed_state), "confidence": r.confidence,
            "observation_refs": list(r.observation_refs),
            "receipt_refs": list(r.receipt_refs),
        })
        return p

    def _error(self, r: PredictionRecord) -> CognitiveEmission:
        r.prediction_error_id = self._id("prediction-error")
        p = self._base(r, r.resolved_at or r.created_at)
        p.update({
            "prediction_error_id": r.prediction_error_id,
            "prediction_id": r.prediction_id, "error_class": r.error_class.value,
            "observed_state": _thaw(r.observed_state), "confidence": r.confidence,
            "receipt_refs": list(r.receipt_refs), "automatic_retry_requested": False,
        })
        return self._emit(r, PREDICTION_ERROR, p)

    def _emit(self, r: PredictionRecord, event_type: str, payload: Mapping[str, Any]) -> CognitiveEmission:
        emission = CognitiveEmission(self._id("cognitive-event"), event_type, _freeze(payload), r.last_emission_id)
        r.last_emission_id = emission.emission_id
        return emission


@dataclass
class ActionTrackingRecord:
    tracking_id: str
    cognitive_event_id: str
    body_id: str
    node_id: str
    authorization_ref: str
    execution_ref: str
    source_refs: Tuple[str, ...]
    correlation_ids: Tuple[str, ...]
    prediction_refs: Tuple[str, ...]
    observation_refs: Tuple[str, ...]
    replay_state: str
    started_at: float
    state: ActionTrackingState = ActionTrackingState.STARTED
    receipt_refs: Tuple[str, ...] = ()
    outstanding_effect_refs: Tuple[str, ...] = ()
    finished_at: Optional[float] = None
    observed_state: Mapping[str, Any] = field(default_factory=dict)
    outcome_confidence: float = 1.0
    last_emission_id: Optional[str] = None

    @property
    def authority_granted(self) -> bool:
        return False

    @property
    def execution_performed(self) -> bool:
        return False

    @property
    def automatic_retry_requested(self) -> bool:
        return False

    def read_only_view(self) -> Mapping[str, Any]:
        return _freeze({
            "tracking_id": self.tracking_id,
            "cognitive_event_id": self.cognitive_event_id,
            "body_id": self.body_id, "node_id": self.node_id,
            "authorization_ref": self.authorization_ref,
            "execution_ref": self.execution_ref,
            "source_refs": list(self.source_refs),
            "correlation_ids": list(self.correlation_ids),
            "prediction_refs": list(self.prediction_refs),
            "observation_refs": list(self.observation_refs),
            "receipt_refs": list(self.receipt_refs),
            "outstanding_effect_refs": list(self.outstanding_effect_refs),
            "state": self.state.value, "started_at": self.started_at,
            "finished_at": self.finished_at,
            "observed_state": _thaw(self.observed_state),
            "outcome_confidence": self.outcome_confidence,
            "replay_state": self.replay_state,
            "authority_granted": False, "execution_performed": False,
            "automatic_retry_requested": False,
        })


class ActionOutcomeTracker:
    def __init__(
        self, *, body_id: str, node_id: str, max_actions: int = 32,
        id_factory: Optional[Callable[[str], str]] = None,
        replay_state: str = "live",
    ) -> None:
        _text("body_id", body_id)
        _text("node_id", node_id)
        if isinstance(max_actions, bool) or not isinstance(max_actions, int) or max_actions < 1:
            raise ValueError("max_actions must be a positive integer")
        if replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid replay_state")
        self.body_id, self.node_id = body_id.strip(), node_id.strip()
        self.max_actions, self.replay_state = max_actions, replay_state
        self._id = id_factory or (lambda p: "%s_%s" % (p, uuid4().hex))
        self._records: Dict[str, ActionTrackingRecord] = {}

    def start_from_workspace(
        self, *, workspace_view: Mapping[str, Any], authorization_ref: str,
        execution_ref: str, monotonic_time: float,
        source_refs: Iterable[str] = (), prediction_refs: Iterable[str] = (),
        observation_refs: Iterable[str] = (), tracking_id: Optional[str] = None,
    ) -> Tuple[ActionTrackingRecord, CognitiveEmission]:
        context = CognitiveWorkspaceContext.from_view(workspace_view)
        context.assert_matches(body_id=self.body_id, node_id=self.node_id)
        if context.replay_state != self.replay_state:
            raise ValueError("workspace and tracking replay_state differ")
        if context.mode != "TRACK_ACTION":
            raise ValueError("workspace must be in TRACK_ACTION mode")
        if authorization_ref not in context.authorization_refs:
            raise ValueError("authorization_ref is not present in workspace")
        if execution_ref not in context.execution_refs:
            raise ValueError("execution_ref is not present in workspace")
        return self.start(
            cognitive_event_id=context.cognitive_event_id,
            authorization_ref=authorization_ref, execution_ref=execution_ref,
            source_refs=_merge(context.source_refs, source_refs),
            correlation_ids=context.correlation_ids,
            prediction_refs=_merge(context.prediction_refs, prediction_refs),
            observation_refs=observation_refs, monotonic_time=monotonic_time,
            tracking_id=tracking_id,
        )

    def start(
        self, *, cognitive_event_id: str, authorization_ref: str,
        execution_ref: str, source_refs: Iterable[str], monotonic_time: float,
        correlation_ids: Iterable[str] = (), prediction_refs: Iterable[str] = (),
        observation_refs: Iterable[str] = (), tracking_id: Optional[str] = None,
    ) -> Tuple[ActionTrackingRecord, CognitiveEmission]:
        if len(self._records) >= self.max_actions:
            raise RuntimeError("action-tracking capacity reached")
        for name, value in (
            ("cognitive_event_id", cognitive_event_id),
            ("authorization_ref", authorization_ref),
            ("execution_ref", execution_ref),
        ):
            _text(name, value)
        _non_negative("monotonic_time", monotonic_time)
        chosen = tracking_id or self._id("tracking")
        _text("tracking_id", chosen)
        if chosen in self._records:
            raise ValueError("tracking_id already exists")
        record = ActionTrackingRecord(
            tracking_id=chosen.strip(),
            cognitive_event_id=cognitive_event_id.strip(),
            body_id=self.body_id, node_id=self.node_id,
            authorization_ref=authorization_ref.strip(),
            execution_ref=execution_ref.strip(),
            source_refs=_merge(_texts("source_refs", source_refs, True), (authorization_ref.strip(), execution_ref.strip())),
            correlation_ids=_texts("correlation_ids", correlation_ids),
            prediction_refs=_texts("prediction_refs", prediction_refs),
            observation_refs=_texts("observation_refs", observation_refs),
            replay_state=self.replay_state, started_at=float(monotonic_time),
        )
        self._records[record.tracking_id] = record
        emission = self._emit(record, ACTION_TRACKING_STARTED, self._payload(record, monotonic_time))
        return record, emission

    def finish(
        self, tracking_id: str, *, state: ActionTrackingState,
        monotonic_time: float, observation_refs: Iterable[str] = (),
        receipt_refs: Iterable[str] = (), outstanding_effect_refs: Iterable[str] = (),
        observed_state: Optional[Mapping[str, Any]] = None,
        outcome_confidence: float = 1.0,
    ) -> Tuple[ActionTrackingRecord, CognitiveEmission]:
        record = self._record(tracking_id)
        if record.state is not ActionTrackingState.STARTED:
            raise RuntimeError("action tracking is already finished")
        if state not in {
            ActionTrackingState.COMPLETED, ActionTrackingState.FAILED,
            ActionTrackingState.UNKNOWN, ActionTrackingState.INTERRUPTED,
        }:
            raise ValueError("finish requires a terminal tracking state")
        _non_negative("monotonic_time", monotonic_time)
        if float(monotonic_time) < record.started_at:
            raise ValueError("finish cannot precede tracking start")
        _ratio("outcome_confidence", outcome_confidence)
        observations = _texts("observation_refs", observation_refs)
        receipts = _texts("receipt_refs", receipt_refs)
        outstanding = _texts("outstanding_effect_refs", outstanding_effect_refs)
        observed = {} if observed_state is None else observed_state
        if not isinstance(observed, Mapping):
            raise ValueError("observed_state must be a mapping")
        _reject(observed, "observed_state")
        if state in {ActionTrackingState.COMPLETED, ActionTrackingState.FAILED} and not observations and not receipts:
            raise ValueError("completed or failed tracking requires outcome evidence")
        if state is ActionTrackingState.INTERRUPTED and not outstanding:
            raise ValueError("interrupted tracking requires outstanding effect refs")
        record.state, record.finished_at = state, float(monotonic_time)
        record.observation_refs = _merge(record.observation_refs, observations)
        record.receipt_refs = _merge(record.receipt_refs, receipts)
        record.outstanding_effect_refs = _merge(record.outstanding_effect_refs, outstanding)
        record.observed_state, record.outcome_confidence = _freeze(observed), float(outcome_confidence)
        emission = self._emit(record, ACTION_TRACKING_FINISHED, self._payload(record, monotonic_time))
        return record, emission

    def read_only_view(self, tracking_id: str) -> Mapping[str, Any]:
        return self._record(tracking_id).read_only_view()

    def active_ids(self) -> Tuple[str, ...]:
        return tuple(k for k, v in self._records.items() if v.state is ActionTrackingState.STARTED)

    def _record(self, tracking_id: str) -> ActionTrackingRecord:
        _text("tracking_id", tracking_id)
        if tracking_id not in self._records:
            raise KeyError("unknown tracking_id")
        return self._records[tracking_id]

    def _payload(self, r: ActionTrackingRecord, when: float) -> Dict[str, Any]:
        p = _common(
            r.cognitive_event_id, r.node_id, r.body_id,
            _merge(r.source_refs, r.observation_refs, r.receipt_refs, r.outstanding_effect_refs),
            r.correlation_ids, when, r.replay_state,
        )
        p.update({
            "tracking_id": r.tracking_id, "state": r.state.value,
            "authorization_ref": r.authorization_ref, "execution_ref": r.execution_ref,
            "observation_refs": list(r.observation_refs),
            "receipt_refs": list(r.receipt_refs),
            "outstanding_effect_refs": list(r.outstanding_effect_refs),
            "prediction_refs": list(r.prediction_refs), "tracking_only": True,
            "observed_state": _thaw(r.observed_state),
            "outcome_confidence": r.outcome_confidence,
            "automatic_retry_requested": False,
            "execution_performed": False, "actuation_performed": False,
        })
        return p

    def _emit(self, r: ActionTrackingRecord, event_type: str, payload: Mapping[str, Any]) -> CognitiveEmission:
        emission = CognitiveEmission(self._id("cognitive-event"), event_type, _freeze(payload), r.last_emission_id)
        r.last_emission_id = emission.emission_id
        return emission


def _common(
    cognitive_event_id: str, node_id: str, body_id: str,
    source_refs: Iterable[str], correlation_ids: Iterable[str],
    monotonic_time: float, replay_state: str,
) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "cognitive_event_id": cognitive_event_id,
        "node_id": node_id, "body_id": body_id,
        "source_refs": list(_texts("source_refs", source_refs, True)),
        "correlation_ids": list(_texts("correlation_ids", correlation_ids)),
        "monotonic_time": float(monotonic_time), "replay_state": replay_state,
        "health_state": "healthy", "degraded_reasons": [], **_FLAGS,
    }


def _compare(
    expected: Mapping[str, Any], observed: Mapping[str, Any],
    tolerance: Mapping[str, Any],
) -> Tuple[PredictionStatus, Optional[PredictionErrorClass]]:
    if not observed:
        return PredictionStatus.UNKNOWN, PredictionErrorClass.UNOBSERVABLE
    missing, mismatch = set(expected) - set(observed), []
    for key in set(expected).intersection(observed):
        if not _matches(expected[key], observed[key], tolerance.get(key)):
            mismatch.append(key)
    if not missing and not mismatch:
        return PredictionStatus.CONFIRMED, None
    if missing and len(missing) < len(expected):
        return PredictionStatus.CONTRADICTED, PredictionErrorClass.PARTIAL
    if missing and not mismatch:
        return PredictionStatus.UNKNOWN, PredictionErrorClass.UNOBSERVABLE
    return PredictionStatus.CONTRADICTED, PredictionErrorClass.MISMATCH


def _matches(expected: Any, observed: Any, tolerance: Any) -> bool:
    if tolerance is not None and _number(expected) and _number(observed) and _number(tolerance):
        return abs(float(observed) - float(expected)) <= float(tolerance)
    if isinstance(expected, Mapping) and isinstance(observed, Mapping):
        nested = tolerance if isinstance(tolerance, Mapping) else {}
        return all(
            key in observed and _matches(value, observed[key], nested.get(key))
            for key, value in expected.items()
        )
    return observed == expected


def _tolerance(expected: Mapping[str, Any], tolerance: Mapping[str, Any]) -> None:
    unknown = set(tolerance) - set(expected)
    if unknown:
        raise ValueError("tolerance contains unknown expected fields: %s" % sorted(unknown))
    for key, value in tolerance.items():
        if isinstance(expected[key], Mapping):
            if not isinstance(value, Mapping):
                raise ValueError("nested expected state requires nested tolerance")
            _tolerance(expected[key], value)
        elif not _number(expected[key]) or not _number(value) or float(value) < 0:
            raise ValueError("tolerance requires numeric expected value and non-negative delta")


def _transport_payload(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    for key, expected in _FLAGS.items():
        if payload.get(key) != expected:
            raise ValueError("cognitive payload %s must be %r" % (key, expected))
    permitted = set(_FLAGS)
    nested = {k: v for k, v in payload.items() if k not in permitted}
    _reject(nested, "cognitive payload")


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
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, set):
        return tuple(sorted(_freeze(v) for v in value))
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


def _texts(name: str, values: Iterable[str], required: bool = False) -> Tuple[str, ...]:
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
        for value in group:
            if value not in result:
                result.append(value)
    return tuple(result)


def _text(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


def _ratio(name: str, value: Any) -> None:
    if not _number(value) or not 0.0 <= float(value) <= 1.0:
        raise ValueError("%s must be between 0 and 1" % name)


def _non_negative(name: str, value: Any) -> None:
    if not _number(value) or float(value) < 0:
        raise ValueError("%s must be non-negative" % name)


def _number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float))


__all__ = [
    "CONTRACT", "SCHEMA_VERSION",
    "PREDICTION_CREATED", "PREDICTION_RESOLVED", "PREDICTION_ERROR",
    "ACTION_TRACKING_STARTED", "ACTION_TRACKING_FINISHED",
    "PredictionStatus", "PredictionErrorClass", "ActionTrackingState",
    "CognitiveEmission", "PredictionRecord", "PredictionOutcome",
    "PredictionTracker", "ActionTrackingRecord", "ActionOutcomeTracker",
]

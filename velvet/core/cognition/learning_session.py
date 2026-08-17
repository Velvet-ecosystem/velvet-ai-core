# SPDX-License-Identifier: GPL-3.0-only
"""Finite, non-authoritative Learning Mode session orchestration.

A learning session coordinates already-bounded cognitive work. It does not
reason on behalf of Native Brain, persist canonical memory, place Runtime work,
access networks or hardware, modify policy, or apply learning changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable, Optional, Tuple
from uuid import uuid4

from .event_workspace import WorkspaceSnapshot


class LearningSessionState(str, Enum):
    PROPOSED = "PROPOSED"
    ELIGIBILITY_CHECK = "ELIGIBILITY_CHECK"
    OPEN = "OPEN"
    STUDYING = "STUDYING"
    REVIEW_PENDING = "REVIEW_PENDING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    ABORTED = "ABORTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    DEGRADED = "DEGRADED"


class LearningCandidateKind(str, Enum):
    EXPLANATION = "explanation"
    QUESTION = "question"
    REVALIDATION = "revalidation"
    ASSOCIATION = "association"
    CONFIDENCE_REVISION = "confidence_revision"
    MEMORY_ADMISSION = "memory_admission"
    GOVERNED_PLASTICITY = "governed_plasticity"
    NEGATIVE_LEARNING = "negative_learning"
    NO_CHANGE = "no_change"


_TERMINAL_STATES = {
    LearningSessionState.COMPLETED,
    LearningSessionState.ABORTED,
    LearningSessionState.INSUFFICIENT_EVIDENCE,
}

_STUDY_STATES = {
    LearningSessionState.STUDYING,
    LearningSessionState.DEGRADED,
}


@dataclass(frozen=True)
class LearningSessionBudget:
    """Conservative limits owned by one Learning Mode session."""

    max_steps: int = 16
    max_workspace_refs: int = 8
    max_candidates: int = 8
    max_distributed_work_refs: int = 4

    def __post_init__(self) -> None:
        for name in (
            "max_steps",
            "max_workspace_refs",
            "max_candidates",
            "max_distributed_work_refs",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("%s must be an integer" % name)
            if value < 1:
                raise ValueError("%s must be positive" % name)


@dataclass(frozen=True)
class LearningEligibility:
    """Injected eligibility result from the owning body/runtime policy path."""

    allowed: bool
    reason: str
    source_refs: Tuple[str, ...] = ()
    authority: str = "none"

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, bool):
            raise ValueError("allowed must be boolean")
        _require_text("reason", self.reason)
        _require_text_tuple("source_refs", self.source_refs)
        if self.authority != "none":
            raise ValueError("Learning Mode eligibility cannot carry authority")


@dataclass(frozen=True)
class LearningCandidate:
    """Non-canonical study result for an existing promotion/admission path."""

    candidate_id: str
    kind: LearningCandidateKind
    summary: str
    evidence_refs: Tuple[str, ...]
    confidence: float
    canonical: bool = False
    changes_applied: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        _require_text("candidate_id", self.candidate_id)
        if not isinstance(self.kind, LearningCandidateKind):
            raise ValueError("kind must be LearningCandidateKind")
        _require_text("summary", self.summary)
        _require_text_tuple("evidence_refs", self.evidence_refs, required=True)
        _require_ratio("confidence", self.confidence)
        if self.canonical:
            raise ValueError("Learning Mode candidates must remain non-canonical")
        if self.changes_applied:
            raise ValueError("Learning Mode candidates cannot apply changes")
        if self.authority != "none":
            raise ValueError("Learning Mode candidates cannot carry authority")


@dataclass(frozen=True)
class LearningSessionTransition:
    session_id: str
    previous_state: LearningSessionState
    state: LearningSessionState
    reason: str
    step: int
    authority: str = "none"

    def __post_init__(self) -> None:
        _require_text("session_id", self.session_id)
        if not isinstance(self.previous_state, LearningSessionState):
            raise ValueError("previous_state must be LearningSessionState")
        if not isinstance(self.state, LearningSessionState):
            raise ValueError("state must be LearningSessionState")
        _require_text("reason", self.reason)
        if isinstance(self.step, bool) or not isinstance(self.step, int) or self.step < 0:
            raise ValueError("step must be a non-negative integer")
        if self.authority != "none":
            raise ValueError("Learning Mode transitions cannot carry authority")


@dataclass(frozen=True)
class LearningSessionSnapshot:
    session_id: str
    body_id: str
    node_id: str
    objective: str
    state: LearningSessionState
    evidence_refs: Tuple[str, ...]
    simulated_evidence_refs: Tuple[str, ...]
    eligibility_refs: Tuple[str, ...]
    workspace_refs: Tuple[str, ...]
    distributed_work_refs: Tuple[str, ...]
    candidate_ids: Tuple[str, ...]
    degraded_reasons: Tuple[str, ...]
    pause_reason: str
    completion_reason: str
    steps_used: int
    canonical: bool = False
    memory_write_authorized: bool = False
    runtime_placement_authorized: bool = False
    court_authorized: bool = False
    execution_authorized: bool = False
    actuation_authorized: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        for name, value in (
            ("session_id", self.session_id),
            ("body_id", self.body_id),
            ("node_id", self.node_id),
            ("objective", self.objective),
        ):
            _require_text(name, value)
        if not isinstance(self.state, LearningSessionState):
            raise ValueError("state must be LearningSessionState")
        _require_text_tuple("evidence_refs", self.evidence_refs, required=True)
        _require_text_tuple("simulated_evidence_refs", self.simulated_evidence_refs)
        if not set(self.simulated_evidence_refs).issubset(set(self.evidence_refs)):
            raise ValueError("simulated evidence must also belong to session evidence")
        _require_text_tuple("eligibility_refs", self.eligibility_refs)
        _require_text_tuple("workspace_refs", self.workspace_refs)
        _require_text_tuple("distributed_work_refs", self.distributed_work_refs)
        _require_text_tuple("candidate_ids", self.candidate_ids)
        _require_text_tuple("degraded_reasons", self.degraded_reasons)
        if isinstance(self.steps_used, bool) or not isinstance(self.steps_used, int):
            raise ValueError("steps_used must be an integer")
        if self.steps_used < 0:
            raise ValueError("steps_used cannot be negative")
        if self.canonical:
            raise ValueError("Learning Mode session snapshots are not canonical memory")
        if (
            self.memory_write_authorized
            or self.runtime_placement_authorized
            or self.court_authorized
            or self.execution_authorized
            or self.actuation_authorized
        ):
            raise ValueError("Learning Mode cannot authorize downstream effects")
        if self.authority != "none":
            raise ValueError("Learning Mode snapshots cannot carry authority")


class LearningSessionSupervisor:
    """Coordinate one finite Learning Mode study without performing the study."""

    def __init__(
        self,
        *,
        body_id: str,
        node_id: str,
        budget: Optional[LearningSessionBudget] = None,
        id_factory: Optional[Callable[[str], str]] = None,
    ) -> None:
        _require_text("body_id", body_id)
        _require_text("node_id", node_id)
        self._body_id = body_id.strip()
        self._node_id = node_id.strip()
        self._budget = budget or LearningSessionBudget()
        self._id_factory = id_factory or (lambda prefix: "%s_%s" % (prefix, uuid4().hex))
        self._reset()

    @property
    def state(self) -> LearningSessionState:
        return self._state

    @property
    def is_terminal(self) -> bool:
        return self._state in _TERMINAL_STATES

    def propose(
        self,
        *,
        objective: str,
        evidence_refs: Iterable[str],
        session_id: Optional[str] = None,
    ) -> LearningSessionTransition:
        if self._session_id is not None:
            raise RuntimeError("supervisor already contains a Learning Mode session")
        _require_text("objective", objective)
        evidence = _normalize_texts("evidence_refs", evidence_refs, required=True)
        self._session_id = session_id or self._id_factory("learning-session")
        _require_text("session_id", self._session_id)
        self._objective = objective.strip()
        self._evidence_refs = list(evidence)
        return self._transition(
            LearningSessionState.PROPOSED,
            "bounded Learning Mode session proposed",
            count_step=False,
            previous_override=LearningSessionState.PROPOSED,
        )

    def evaluate_eligibility(
        self,
        decision: LearningEligibility,
    ) -> LearningSessionTransition:
        self._require_session()
        if not isinstance(decision, LearningEligibility):
            raise ValueError("decision must be LearningEligibility")
        if self._state not in {
            LearningSessionState.PROPOSED,
            LearningSessionState.PAUSED,
        }:
            raise RuntimeError("eligibility may only be evaluated before opening or resuming")
        self._transition(
            LearningSessionState.ELIGIBILITY_CHECK,
            "Learning Mode eligibility checked",
            count_step=True,
        )
        for ref in decision.source_refs:
            _add_unique(self._eligibility_refs, ref)
        if decision.allowed:
            self._pause_reason = ""
            return self._transition(
                LearningSessionState.OPEN,
                decision.reason,
                count_step=False,
            )
        self._pause_reason = decision.reason.strip()
        return self._transition(
            LearningSessionState.PAUSED,
            decision.reason,
            count_step=False,
        )

    def attach_workspace(
        self,
        workspace: WorkspaceSnapshot,
        *,
        simulated_observation_refs: Iterable[str],
    ) -> LearningSessionTransition:
        """Associate one workspace while preserving explicit simulation provenance."""
        self._require_session()
        if self._state not in {
            LearningSessionState.OPEN,
            LearningSessionState.STUDYING,
            LearningSessionState.DEGRADED,
        }:
            raise RuntimeError("workspace may only be attached to an open study session")
        if not isinstance(workspace, WorkspaceSnapshot):
            raise ValueError("workspace must be WorkspaceSnapshot")
        if workspace.body_id != self._body_id:
            raise ValueError("workspace belongs to another body")
        if workspace.canonical:
            raise ValueError("workspace must remain non-canonical")
        if workspace.authority_granted or workspace.execution_performed:
            raise ValueError("workspace cannot provide authority to Learning Mode")
        simulated = _normalize_texts(
            "simulated_observation_refs",
            simulated_observation_refs,
        )
        if not set(simulated).issubset(set(workspace.observation_refs)):
            raise ValueError("simulated observation refs must belong to the workspace")
        new_workspace = workspace.cognitive_event_id not in self._workspace_refs
        if new_workspace and len(self._workspace_refs) >= self._budget.max_workspace_refs:
            raise RuntimeError("Learning Mode workspace budget exhausted")
        self._ensure_step_available()
        if new_workspace:
            self._workspace_refs.append(workspace.cognitive_event_id)
        for ref in (
            workspace.observation_refs
            + workspace.source_refs
            + workspace.receipt_refs
            + workspace.contradiction_refs
            + workspace.interruption_refs
        ):
            _add_unique(self._evidence_refs, ref)
        for ref in simulated:
            _add_unique(self._simulated_evidence_refs, ref)
        return self._transition(
            LearningSessionState.STUDYING,
            "bounded cognitive workspace associated",
            count_step=True,
        )

    def note_distributed_work(self, work_ref: str) -> LearningSessionTransition:
        """Track a Runtime work reference without placing or authorizing it."""
        self._require_study_state()
        _require_text("work_ref", work_ref)
        normalized = work_ref.strip()
        new_ref = normalized not in self._distributed_work_refs
        if new_ref and len(self._distributed_work_refs) >= self._budget.max_distributed_work_refs:
            raise RuntimeError("Learning Mode distributed-work budget exhausted")
        self._ensure_step_available()
        if new_ref:
            self._distributed_work_refs.append(normalized)
        return self._transition(
            self._state,
            "proposal-only distributed work referenced",
            count_step=True,
        )

    def add_candidate(
        self,
        *,
        kind: LearningCandidateKind,
        summary: str,
        evidence_refs: Iterable[str],
        confidence: float,
        candidate_id: Optional[str] = None,
    ) -> LearningCandidate:
        self._require_study_state()
        if len(self._candidates) >= self._budget.max_candidates:
            raise RuntimeError("Learning Mode candidate budget exhausted")
        if not isinstance(kind, LearningCandidateKind):
            raise ValueError("kind must be LearningCandidateKind")
        _require_text("summary", summary)
        evidence = _normalize_texts("evidence_refs", evidence_refs, required=True)
        unknown = set(evidence) - set(self._evidence_refs)
        if unknown:
            raise ValueError("candidate evidence must already belong to the session")
        _require_ratio("confidence", confidence)
        self._ensure_step_available()
        candidate = LearningCandidate(
            candidate_id=candidate_id or self._id_factory("learning-candidate"),
            kind=kind,
            summary=summary.strip(),
            evidence_refs=evidence,
            confidence=confidence,
        )
        self._candidates.append(candidate)
        self._consume_step()
        return candidate

    def request_review(self, reason: str) -> LearningSessionTransition:
        self._require_study_state()
        _require_text("reason", reason)
        return self._transition(
            LearningSessionState.REVIEW_PENDING,
            reason,
            count_step=True,
        )

    def complete(self, reason: str) -> LearningSessionTransition:
        self._require_session()
        if self._state is not LearningSessionState.REVIEW_PENDING:
            raise RuntimeError("Learning Mode may complete only after review is pending")
        _require_text("reason", reason)
        self._completion_reason = reason.strip()
        return self._transition(
            LearningSessionState.COMPLETED,
            reason,
            count_step=False,
        )

    def pause(self, reason: str) -> LearningSessionTransition:
        self._require_active_session()
        _require_text("reason", reason)
        self._pause_reason = reason.strip()
        return self._transition(
            LearningSessionState.PAUSED,
            reason,
            count_step=False,
        )

    def abort(self, reason: str) -> LearningSessionTransition:
        self._require_active_session()
        _require_text("reason", reason)
        self._completion_reason = reason.strip()
        return self._transition(
            LearningSessionState.ABORTED,
            reason,
            count_step=False,
        )

    def mark_insufficient_evidence(self, reason: str) -> LearningSessionTransition:
        self._require_active_session()
        _require_text("reason", reason)
        self._completion_reason = reason.strip()
        return self._transition(
            LearningSessionState.INSUFFICIENT_EVIDENCE,
            reason,
            count_step=False,
        )

    def mark_degraded(self, reason: str) -> LearningSessionTransition:
        self._require_study_state()
        _require_text("reason", reason)
        _add_unique(self._degraded_reasons, reason.strip())
        return self._transition(
            LearningSessionState.DEGRADED,
            reason,
            count_step=False,
        )

    def candidates(self) -> Tuple[LearningCandidate, ...]:
        return tuple(self._candidates)

    def transitions(self) -> Tuple[LearningSessionTransition, ...]:
        return tuple(self._transitions)

    def snapshot(self) -> LearningSessionSnapshot:
        self._require_session()
        return LearningSessionSnapshot(
            session_id=self._session_id,
            body_id=self._body_id,
            node_id=self._node_id,
            objective=self._objective,
            state=self._state,
            evidence_refs=tuple(self._evidence_refs),
            simulated_evidence_refs=tuple(self._simulated_evidence_refs),
            eligibility_refs=tuple(self._eligibility_refs),
            workspace_refs=tuple(self._workspace_refs),
            distributed_work_refs=tuple(self._distributed_work_refs),
            candidate_ids=tuple(candidate.candidate_id for candidate in self._candidates),
            degraded_reasons=tuple(self._degraded_reasons),
            pause_reason=self._pause_reason,
            completion_reason=self._completion_reason,
            steps_used=self._steps_used,
        )

    def reset_terminal(self) -> None:
        self._require_session()
        if not self.is_terminal:
            raise RuntimeError("cannot reset an active Learning Mode session")
        self._reset()

    def _require_session(self) -> None:
        if self._session_id is None:
            raise RuntimeError("no Learning Mode session has been proposed")

    def _require_active_session(self) -> None:
        self._require_session()
        if self.is_terminal:
            raise RuntimeError("Learning Mode session is already terminal")

    def _require_study_state(self) -> None:
        self._require_session()
        if self._state not in _STUDY_STATES:
            raise RuntimeError("operation requires an active Learning Mode study state")

    def _ensure_step_available(self) -> None:
        if self._steps_used >= self._budget.max_steps:
            raise RuntimeError("Learning Mode step budget exhausted")

    def _consume_step(self) -> None:
        self._ensure_step_available()
        self._steps_used += 1

    def _transition(
        self,
        state: LearningSessionState,
        reason: str,
        *,
        count_step: bool,
        previous_override: Optional[LearningSessionState] = None,
    ) -> LearningSessionTransition:
        _require_text("reason", reason)
        if count_step:
            self._consume_step()
        previous = previous_override or self._state
        self._state = state
        transition = LearningSessionTransition(
            session_id=self._session_id,
            previous_state=previous,
            state=state,
            reason=reason.strip(),
            step=self._steps_used,
        )
        self._transitions.append(transition)
        return transition

    def _reset(self) -> None:
        self._session_id = None
        self._objective = ""
        self._state = LearningSessionState.PROPOSED
        self._evidence_refs = []
        self._simulated_evidence_refs = []
        self._eligibility_refs = []
        self._workspace_refs = []
        self._distributed_work_refs = []
        self._candidates = []
        self._degraded_reasons = []
        self._pause_reason = ""
        self._completion_reason = ""
        self._steps_used = 0
        self._transitions = []


def _add_unique(values: list, value: str) -> None:
    if value not in values:
        values.append(value)


def _normalize_texts(
    name: str,
    values: Iterable[str],
    *,
    required: bool = False,
) -> Tuple[str, ...]:
    normalized = []
    for value in values:
        _require_text(name, value)
        stripped = value.strip()
        if stripped not in normalized:
            normalized.append(stripped)
    if required and not normalized:
        raise ValueError("%s must not be empty" % name)
    return tuple(normalized)


def _require_text_tuple(
    name: str,
    values: Tuple[str, ...],
    *,
    required: bool = False,
) -> None:
    if not isinstance(values, tuple):
        raise ValueError("%s must be a tuple" % name)
    _normalize_texts(name, values, required=required)


def _require_text(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


def _require_ratio(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % name)
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError("%s must be between 0 and 1" % name)

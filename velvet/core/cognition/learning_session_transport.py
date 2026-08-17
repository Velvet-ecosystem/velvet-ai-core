# SPDX-License-Identifier: GPL-3.0-only
"""Transport-safe projection of Learning Mode lifecycle state.

This module deliberately separates local cognitive detail from nervous-system
lifecycle evidence. Human-readable study objectives and transition prose stay
inside AI Core. Only stable references and bounded lifecycle facts are exposed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .learning_session import (
    LearningSessionSnapshot,
    LearningSessionState,
    LearningSessionTransition,
)

_STATE_EVENT = {
    LearningSessionState.PROPOSED: "learning.session.proposed",
    LearningSessionState.ELIGIBILITY_CHECK: "learning.session.eligibility_checked",
    LearningSessionState.OPEN: "learning.session.opened",
    LearningSessionState.STUDYING: "learning.session.studying",
    LearningSessionState.REVIEW_PENDING: "learning.session.review_pending",
    LearningSessionState.PAUSED: "learning.session.paused",
    LearningSessionState.DEGRADED: "learning.session.degraded",
    LearningSessionState.INSUFFICIENT_EVIDENCE: "learning.session.insufficient_evidence",
    LearningSessionState.COMPLETED: "learning.session.completed",
    LearningSessionState.ABORTED: "learning.session.aborted",
}

_STATE_REASON_CODE = {
    LearningSessionState.PROPOSED: "session_proposed",
    LearningSessionState.ELIGIBILITY_CHECK: "eligibility_checked",
    LearningSessionState.OPEN: "session_opened",
    LearningSessionState.STUDYING: "study_progress",
    LearningSessionState.REVIEW_PENDING: "review_pending",
    LearningSessionState.PAUSED: "session_paused",
    LearningSessionState.DEGRADED: "session_degraded",
    LearningSessionState.INSUFFICIENT_EVIDENCE: "insufficient_evidence",
    LearningSessionState.COMPLETED: "session_completed",
    LearningSessionState.ABORTED: "session_aborted",
}


@dataclass(frozen=True)
class LearningSessionTransportProjection:
    """Event-Protocol-shaped fields without importing Event Protocol itself."""

    event_type: str
    session_id: str
    body_id: str
    node_id: str
    subject_ref: str
    state: str
    evidence_refs: Tuple[str, ...]
    simulated_evidence_refs: Tuple[str, ...]
    eligibility_refs: Tuple[str, ...]
    workspace_refs: Tuple[str, ...]
    distributed_work_refs: Tuple[str, ...]
    candidate_refs: Tuple[str, ...]
    degraded_reasons: Tuple[str, ...]
    steps_used: int
    reason_code: str

    def to_record_kwargs(self) -> Dict[str, object]:
        """Return kwargs compatible with Event Protocol's session record."""
        return {
            "session_id": self.session_id,
            "body_id": self.body_id,
            "node_id": self.node_id,
            "subject_ref": self.subject_ref,
            "state": self.state,
            "evidence_refs": self.evidence_refs,
            "simulated_evidence_refs": self.simulated_evidence_refs,
            "eligibility_refs": self.eligibility_refs,
            "workspace_refs": self.workspace_refs,
            "distributed_work_refs": self.distributed_work_refs,
            "candidate_refs": self.candidate_refs,
            "degraded_reasons": self.degraded_reasons,
            "steps_used": self.steps_used,
            "reason_code": self.reason_code,
        }


def project_learning_session_transition(
    snapshot: LearningSessionSnapshot,
    transition: LearningSessionTransition,
    *,
    subject_ref: str,
) -> LearningSessionTransportProjection:
    """Project one recorded transition into bounded lifecycle evidence.

    The caller supplies a stable subject reference. The free-text objective and
    free-text transition reason are intentionally not copied. A current session
    snapshot may project an earlier recorded transition from that same session;
    the transition's own state and step counter remain authoritative for the
    lifecycle record.
    """
    if not isinstance(snapshot, LearningSessionSnapshot):
        raise ValueError("snapshot must be LearningSessionSnapshot")
    if not isinstance(transition, LearningSessionTransition):
        raise ValueError("transition must be LearningSessionTransition")
    if not isinstance(subject_ref, str) or not subject_ref.strip():
        raise ValueError("subject_ref must be a non-empty string")
    if snapshot.session_id != transition.session_id:
        raise ValueError("snapshot and transition belong to different sessions")
    if transition.state not in _STATE_EVENT:
        raise ValueError("unsupported Learning Mode transport state")
    if transition.step > snapshot.steps_used:
        raise ValueError("transition step cannot exceed the current session step count")
    if not set(snapshot.simulated_evidence_refs).issubset(set(snapshot.evidence_refs)):
        raise ValueError("simulated evidence must remain session evidence")

    return LearningSessionTransportProjection(
        event_type=_STATE_EVENT[transition.state],
        session_id=snapshot.session_id,
        body_id=snapshot.body_id,
        node_id=snapshot.node_id,
        subject_ref=subject_ref.strip(),
        state=transition.state.value,
        evidence_refs=snapshot.evidence_refs,
        simulated_evidence_refs=snapshot.simulated_evidence_refs,
        eligibility_refs=snapshot.eligibility_refs,
        workspace_refs=snapshot.workspace_refs,
        distributed_work_refs=snapshot.distributed_work_refs,
        candidate_refs=snapshot.candidate_ids,
        degraded_reasons=snapshot.degraded_reasons,
        steps_used=transition.step,
        reason_code=_STATE_REASON_CODE[transition.state],
    )

"""Shared data models for the Native Brain decision spine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Tuple
from uuid import uuid4


class Importance(str, Enum):
    ROUTINE = "routine"
    INTERESTING = "interesting"
    IMPORTANT = "important"
    CRITICAL = "critical"


class Recommendation(str, Enum):
    IGNORE = "ignore"
    OBSERVE = "observe"
    NOTIFY = "notify"
    ESCALATE = "escalate"


class ReviewDisposition(str, Enum):
    ACCEPTED = "accepted"
    FLAGGED = "flagged"


class LearningDisposition(str, Enum):
    PROPOSED = "proposed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class HandoffDisposition(str, Enum):
    """Non-authoritative states for distributed reasoning offers."""

    OFFERED = "offered"
    REFUSED = "refused"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class Observation:
    event_type: str
    source: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class BrainContext:
    runtime_mode: str = "unknown"
    court_permissions: Tuple[str, ...] = ()
    presence: str = "unknown"
    active_scene: str | None = None
    recent_events: Tuple[str, ...] = ()
    active_organs: Tuple[str, ...] = ()
    world_state: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Understanding:
    observation: Observation
    context: BrainContext
    summary: str


@dataclass(frozen=True)
class Evaluation:
    understanding: Understanding
    importance: Importance
    confidence: float
    reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Judgment:
    evaluation: Evaluation
    recommendation: Recommendation
    rationale: str


@dataclass(frozen=True)
class DecisionReceipt:
    judgment: Judgment
    receipt_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def recommendation(self) -> Recommendation:
        return self.judgment.recommendation


@dataclass(frozen=True)
class ReflectionReview:
    receipt_id: str
    disposition: ReviewDisposition
    notes: Tuple[str, ...] = ()
    review_id: str = field(default_factory=lambda: str(uuid4()))
    reviewed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class LearningProposal:
    proposal_id: str
    subject: str
    source_review_ids: Tuple[str, ...]
    source_receipt_ids: Tuple[str, ...]
    disposition: LearningDisposition
    rationale: str
    changes_applied: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class CapabilityAdvertisement:
    """One organ's bounded capability, load, health, and availability snapshot."""

    organ_name: str
    capabilities: Tuple[str, ...]
    load: float
    healthy: bool = True
    available: bool = True
    limits: Tuple[str, ...] = ()
    fallback: str | None = None


@dataclass(frozen=True)
class ReasoningTask:
    """A bounded reasoning offer, never an execution command."""

    task_id: str
    capability: str
    summary: str
    source_receipt_id: str | None = None


@dataclass(frozen=True)
class ReasoningHandoff:
    """Append-only coordination record with no authority or execution claim."""

    handoff_id: str
    task_id: str
    disposition: HandoffDisposition
    target_organ: str | None
    rationale: str
    authority_granted: bool = False
    execution_performed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

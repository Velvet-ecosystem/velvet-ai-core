"""Shared data models for the Native Brain decision spine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Tuple
from uuid import uuid4


class Importance(str, Enum):
    """Initial deterministic importance levels."""

    ROUTINE = "routine"
    INTERESTING = "interesting"
    IMPORTANT = "important"
    CRITICAL = "critical"


class Recommendation(str, Enum):
    """Recommendations the brain may return without executing them."""

    IGNORE = "ignore"
    OBSERVE = "observe"
    NOTIFY = "notify"
    ESCALATE = "escalate"


class ReviewDisposition(str, Enum):
    """Non-authoritative outcomes from receipt reflection."""

    ACCEPTED = "accepted"
    FLAGGED = "flagged"


class LearningDisposition(str, Enum):
    """Non-authoritative states for bounded learning proposals."""

    PROPOSED = "proposed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True)
class Observation:
    event_type: str
    source: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    observed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


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
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def recommendation(self) -> Recommendation:
        return self.judgment.recommendation


@dataclass(frozen=True)
class ReflectionReview:
    """Append-only review linked to an immutable decision receipt."""

    receipt_id: str
    disposition: ReviewDisposition
    notes: Tuple[str, ...] = ()
    review_id: str = field(default_factory=lambda: str(uuid4()))
    reviewed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass(frozen=True)
class LearningProposal:
    """Immutable candidate for later governed promotion review."""

    proposal_id: str
    subject: str
    source_review_ids: Tuple[str, ...]
    source_receipt_ids: Tuple[str, ...]
    disposition: LearningDisposition
    rationale: str
    changes_applied: bool = False
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

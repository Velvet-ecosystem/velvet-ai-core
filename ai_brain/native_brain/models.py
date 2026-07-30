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


class Urgency(str, Enum):
    """How quickly a recommendation may deserve governed attention."""

    ROUTINE = "routine"
    ELEVATED = "elevated"
    URGENT = "urgent"
    IMMEDIATE = "immediate"


class Consequence(str, Enum):
    """Bounded estimate of the harm possible if an understanding is correct."""

    NEGLIGIBLE = "negligible"
    LIMITED = "limited"
    SERIOUS = "serious"
    SEVERE = "severe"


class ErrorCost(str, Enum):
    """Relative cost of a false dismissal or unnecessary escalation."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class Recommendation(str, Enum):
    IGNORE = "ignore"
    OBSERVE = "observe"
    NOTIFY = "notify"
    ESCALATE = "escalate"


class AttentionDisposition(str, Enum):
    """Non-authoritative outcomes from the Doctrine of Silence."""

    SILENT = "silent"
    DEFER = "defer"
    PRESENT = "present"
    INTERRUPT = "interrupt"


class ReviewDisposition(str, Enum):
    ACCEPTED = "accepted"
    FLAGGED = "flagged"


class LearningDisposition(str, Enum):
    PROPOSED = "proposed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class HandoffDisposition(str, Enum):
    OFFERED = "offered"
    REFUSED = "refused"
    ESCALATE = "escalate"


class FusionDisposition(str, Enum):
    """Non-authoritative outcomes from cross-organ evidence fusion."""

    COHERENT = "coherent"
    CONFLICTED = "conflicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class FreshnessDisposition(str, Enum):
    """Time-quality states for append-only evidence contributions."""

    FRESH = "fresh"
    AGING = "aging"
    STALE = "stale"
    INVALID = "invalid"


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
class EvaluationProfile:
    """Explicit bounded inputs for consequence-aware evaluation.

    The profile is supplied separately from an event payload so transport data
    cannot silently declare its own urgency or authority posture.
    """

    urgency: Urgency = Urgency.ROUTINE
    potential_consequence: Consequence = Consequence.NEGLIGIBLE
    cost_of_dismissal: ErrorCost = ErrorCost.LOW
    cost_of_escalation: ErrorCost = ErrorCost.LOW
    confidence: float = 1.0
    reasons: Tuple[str, ...] = ("Conservative explicit default profile",)


@dataclass(frozen=True)
class Evaluation:
    understanding: Understanding
    importance: Importance
    confidence: float
    reasons: Tuple[str, ...] = ()
    urgency: Urgency = Urgency.ROUTINE
    potential_consequence: Consequence = Consequence.NEGLIGIBLE
    cost_of_dismissal: ErrorCost = ErrorCost.LOW
    cost_of_escalation: ErrorCost = ErrorCost.LOW


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
class AttentionProfile:
    """Explicit, non-authoritative conditions for attention arbitration."""

    quiet_mode: bool = False
    focus_protected: bool = False
    repeated_notice: bool = False
    audience_available: bool = True


@dataclass(frozen=True)
class AttentionDecision:
    """Append-only attention recommendation linked to one decision receipt."""

    attention_id: str
    receipt_id: str
    disposition: AttentionDisposition
    rationale: str
    authority_granted: bool = False
    delivery_performed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


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
    organ_name: str
    capabilities: Tuple[str, ...]
    load: float
    healthy: bool = True
    available: bool = True
    limits: Tuple[str, ...] = ()
    fallback: str | None = None


@dataclass(frozen=True)
class ReasoningTask:
    task_id: str
    capability: str
    summary: str
    source_receipt_id: str | None = None


@dataclass(frozen=True)
class ReasoningHandoff:
    handoff_id: str
    task_id: str
    disposition: HandoffDisposition
    target_organ: str | None
    rationale: str
    authority_granted: bool = False
    execution_performed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class EvidenceContribution:
    """One organ's append-only finding about a shared subject."""

    organ_name: str
    claim: str
    confidence: float
    source_receipt_id: str | None = None
    contribution_id: str = field(default_factory=lambda: str(uuid4()))
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class EvidenceFreshness:
    """Append-only time-quality review of one evidence contribution."""

    freshness_id: str
    contribution_id: str
    disposition: FreshnessDisposition
    age_seconds: float
    base_confidence: float
    effective_confidence: float
    rationale: str
    authority_granted: bool = False
    execution_performed: bool = False
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class EvidenceFusion:
    """Combined evidence record that never grants authority or execution."""

    fusion_id: str
    subject: str
    contribution_ids: Tuple[str, ...]
    disposition: FusionDisposition
    confidence: float
    rationale: str
    freshness_ids: Tuple[str, ...] = ()
    active_contribution_ids: Tuple[str, ...] = ()
    stale_contribution_ids: Tuple[str, ...] = ()
    invalid_contribution_ids: Tuple[str, ...] = ()
    authority_granted: bool = False
    execution_performed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

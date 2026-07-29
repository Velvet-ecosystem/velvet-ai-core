# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic proposal-only intent formation for Native Brain.

Intent formation describes a bounded next-step proposal from supported judgment
or an active expectation. An intent candidate is not a command, plan approval,
Runtime placement, Court authorization, executor selection, speech grant,
memory write, hardware access, or authority object.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .expectations import (
    ExpectationAssessment,
    ExpectationDisposition,
    ExpectationState,
)
from .judgment import (
    ConfidenceBand,
    JudgmentAssessment,
    JudgmentDisposition,
)


class IntentState(str, Enum):
    NONE = "none"
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    DEFERRED = "deferred"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    BLOCKED = "blocked"


class IntentDisposition(str, Enum):
    BLOCKED = "blocked"
    DEFER_TO_SAFETY = "defer_to_safety"
    OBSERVE = "observe"
    FORM_CANDIDATE = "form_candidate"
    RETAIN_CANDIDATE = "retain_candidate"
    DEFER_CANDIDATE = "defer_candidate"
    WITHDRAW_CANDIDATE = "withdraw_candidate"
    EXPIRE_CANDIDATE = "expire_candidate"


class IntentKind(str, Enum):
    WATCH = "watch"
    INFORM = "inform"
    ASK = "ask"
    SUGGEST = "suggest"
    PROPOSE_WORK = "propose_work"


@dataclass(frozen=True)
class IntentContext:
    """Verified framing for one bounded intent review."""

    proposed_statement: Optional[str] = None
    intent_kind: IntentKind = IntentKind.WATCH
    objective: Optional[str] = None
    evidence_references: Tuple[str, ...] = ()
    constraints: Tuple[str, ...] = ()
    evaluated_at: float = 0.0
    expires_after_seconds: float = 300.0
    consequential: bool = False
    reversible: bool = True
    owner_attention_available: bool = False
    presence_allows_speech: bool = False
    existing_candidate: bool = False
    existing_formed_at: Optional[float] = None
    existing_expires_at: Optional[float] = None
    contradiction_count: int = 0
    integrity_aligned: bool = True
    continuity_verified: bool = True
    runtime_context_verified: bool = True
    safety_priority: bool = False

    def __post_init__(self) -> None:
        if self.proposed_statement is not None and not self.proposed_statement.strip():
            raise ValueError("proposed_statement cannot be blank")
        if self.objective is not None and not self.objective.strip():
            raise ValueError("objective cannot be blank")
        _validate_text_tuple(self.evidence_references, "evidence_references")
        _validate_text_tuple(self.constraints, "constraints")
        if self.evaluated_at < 0:
            raise ValueError("evaluated_at cannot be negative")
        if self.expires_after_seconds <= 0:
            raise ValueError("expires_after_seconds must be positive")
        if self.contradiction_count < 0:
            raise ValueError("contradiction_count cannot be negative")
        if self.existing_candidate:
            if self.existing_formed_at is None or self.existing_expires_at is None:
                raise ValueError("existing intent candidates require formation and expiry")
            if self.existing_formed_at < 0:
                raise ValueError("existing_formed_at cannot be negative")
            if self.existing_expires_at <= self.existing_formed_at:
                raise ValueError("existing intent expiry must follow formation")
        elif self.existing_formed_at is not None or self.existing_expires_at is not None:
            raise ValueError("existing intent times require existing_candidate")


@dataclass(frozen=True)
class IntentCandidate:
    statement: str
    intent_kind: IntentKind
    objective: str
    evidence_references: Tuple[str, ...]
    constraints: Tuple[str, ...]
    state: IntentState
    confidence: float
    formed_at: float
    expires_at: float
    consequential: bool
    reversible: bool
    requires_runtime_placement: bool
    requires_court_review: bool
    requires_presence_review: bool
    candidate: bool = True
    proposal_only: bool = True
    command: bool = False
    canonical: bool = False
    speaking_authorized: bool = False
    memory_write_authorized: bool = False
    runtime_placement_authorized: bool = False
    court_authorized: bool = False
    execution_authorized: bool = False
    actuation_authorized: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if not self.statement.strip() or not self.objective.strip():
            raise ValueError("intent statement and objective are required")
        _validate_text_tuple(self.evidence_references, "evidence_references")
        _validate_text_tuple(self.constraints, "constraints")
        if not self.evidence_references:
            raise ValueError("intent candidates require evidence references")
        if self.state not in {
            IntentState.DRAFT,
            IntentState.READY_FOR_REVIEW,
            IntentState.DEFERRED,
            IntentState.WITHDRAWN,
            IntentState.EXPIRED,
        }:
            raise ValueError("intent candidates require a candidate state")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("intent confidence must be between 0 and 1")
        if self.formed_at < 0 or self.expires_at <= self.formed_at:
            raise ValueError("intent candidates require a finite lifetime")
        if not self.candidate or not self.proposal_only:
            raise ValueError("intent objects must remain proposal-only candidates")
        if self.command or self.canonical:
            raise ValueError("intent candidates are not commands or canonical memory")
        if (
            self.speaking_authorized
            or self.memory_write_authorized
            or self.runtime_placement_authorized
            or self.court_authorized
            or self.execution_authorized
            or self.actuation_authorized
        ):
            raise ValueError("intent candidates cannot authorize downstream effects")
        if self.authority != "none":
            raise ValueError("intent candidates cannot carry authority")
        if self.consequential and not self.requires_court_review:
            raise ValueError("consequential intent candidates require Court review")
        if self.intent_kind is IntentKind.PROPOSE_WORK and not self.requires_runtime_placement:
            raise ValueError("work proposals require Runtime placement review")


@dataclass(frozen=True)
class IntentAssessment:
    state: IntentState
    disposition: IntentDisposition
    reasons: Tuple[str, ...]
    candidate: Optional[IntentCandidate] = None
    eligible_for_downstream_review: bool = False
    canonical: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if not self.reasons:
            raise ValueError("intent assessment reasons are required")
        candidate_dispositions = {
            IntentDisposition.FORM_CANDIDATE,
            IntentDisposition.RETAIN_CANDIDATE,
            IntentDisposition.DEFER_CANDIDATE,
            IntentDisposition.WITHDRAW_CANDIDATE,
            IntentDisposition.EXPIRE_CANDIDATE,
        }
        if self.disposition in candidate_dispositions and self.candidate is None:
            raise ValueError("candidate dispositions require an intent candidate")
        if self.candidate is not None and self.candidate.state is not self.state:
            raise ValueError("assessment and candidate intent states must match")
        if self.eligible_for_downstream_review:
            if self.state is not IntentState.READY_FOR_REVIEW or self.candidate is None:
                raise ValueError("only ready intent candidates may enter downstream review")
        if self.canonical:
            raise ValueError("intent assessments must remain non-canonical")
        if self.authority != "none":
            raise ValueError("intent assessments cannot carry authority")


class IntentEngine:
    """Form expiring proposals without turning cognition into permission."""

    def assess(
        self,
        judgment: JudgmentAssessment,
        expectation: ExpectationAssessment,
        context: IntentContext,
    ) -> IntentAssessment:
        blocked_reasons = []
        if not context.integrity_aligned:
            blocked_reasons.append("integrity-not-aligned")
        if not context.continuity_verified:
            blocked_reasons.append("continuity-not-verified")
        if not context.runtime_context_verified:
            blocked_reasons.append("runtime-context-not-verified")
        if blocked_reasons:
            return IntentAssessment(
                state=IntentState.BLOCKED,
                disposition=IntentDisposition.BLOCKED,
                reasons=tuple(blocked_reasons),
            )

        if (
            context.safety_priority
            or judgment.disposition is JudgmentDisposition.DEFER_TO_SAFETY
            or expectation.disposition is ExpectationDisposition.DEFER_TO_SAFETY
        ):
            return IntentAssessment(
                state=IntentState.BLOCKED,
                disposition=IntentDisposition.DEFER_TO_SAFETY,
                reasons=("safety-path-owns-next-decision",),
            )

        if context.proposed_statement is None or context.objective is None:
            return IntentAssessment(
                state=IntentState.NONE,
                disposition=IntentDisposition.OBSERVE,
                reasons=("no-domain-intent-proposal",),
            )
        if not context.evidence_references:
            return IntentAssessment(
                state=IntentState.NONE,
                disposition=IntentDisposition.OBSERVE,
                reasons=("no-evidence-references",),
            )

        judgment_ready = (
            judgment.disposition is JudgmentDisposition.READY
            and judgment.band in {ConfidenceBand.SUPPORTED, ConfidenceBand.STRONG}
        )
        expectation_ready = (
            expectation.state is ExpectationState.ACTIVE
            and expectation.eligible_for_intent_review
            and expectation.candidate is not None
        )
        if not judgment_ready and not expectation_ready:
            return IntentAssessment(
                state=IntentState.NONE,
                disposition=IntentDisposition.OBSERVE,
                reasons=("supported-judgment-or-active-expectation-required",),
            )

        formed_at = (
            context.existing_formed_at
            if context.existing_candidate
            else context.evaluated_at
        )
        expires_at = (
            context.existing_expires_at
            if context.existing_candidate
            else context.evaluated_at + context.expires_after_seconds
        )
        assert formed_at is not None
        assert expires_at is not None

        upstream_confidence = judgment.confidence
        if expectation_ready and expectation.candidate is not None:
            upstream_confidence = max(
                upstream_confidence,
                expectation.candidate.confidence,
            )
        confidence = round(
            max(0.0, min(upstream_confidence - min(context.contradiction_count, 3) * 0.2, 1.0)),
            4,
        )

        if context.existing_candidate and context.evaluated_at >= expires_at:
            state = IntentState.EXPIRED
            disposition = IntentDisposition.EXPIRE_CANDIDATE
        elif context.contradiction_count >= 2:
            state = IntentState.WITHDRAWN
            disposition = IntentDisposition.WITHDRAW_CANDIDATE
        elif context.contradiction_count == 1:
            state = IntentState.DEFERRED
            disposition = IntentDisposition.DEFER_CANDIDATE
        elif confidence >= 0.75:
            state = IntentState.READY_FOR_REVIEW
            disposition = (
                IntentDisposition.RETAIN_CANDIDATE
                if context.existing_candidate
                else IntentDisposition.FORM_CANDIDATE
            )
        else:
            state = IntentState.DRAFT
            disposition = (
                IntentDisposition.RETAIN_CANDIDATE
                if context.existing_candidate
                else IntentDisposition.FORM_CANDIDATE
            )

        requires_presence_review = context.intent_kind in {
            IntentKind.INFORM,
            IntentKind.ASK,
            IntentKind.SUGGEST,
        }
        candidate = IntentCandidate(
            statement=context.proposed_statement,
            intent_kind=context.intent_kind,
            objective=context.objective,
            evidence_references=context.evidence_references,
            constraints=context.constraints,
            state=state,
            confidence=confidence,
            formed_at=formed_at,
            expires_at=expires_at,
            consequential=context.consequential,
            reversible=context.reversible,
            requires_runtime_placement=context.intent_kind is IntentKind.PROPOSE_WORK,
            requires_court_review=context.consequential,
            requires_presence_review=requires_presence_review,
        )

        reasons = [
            f"state:{state.value}",
            f"kind:{context.intent_kind.value}",
            f"confidence:{confidence:.4f}",
            f"consequential:{str(context.consequential).lower()}",
        ]
        if judgment_ready:
            reasons.append("supported-judgment")
        if expectation_ready:
            reasons.append("active-expectation")
        if context.contradiction_count:
            reasons.append(f"contradictions:{context.contradiction_count}")
        if requires_presence_review and not context.presence_allows_speech:
            reasons.append("presence-review-still-required")
        if context.intent_kind is IntentKind.PROPOSE_WORK:
            reasons.append("runtime-placement-still-required")
        if context.consequential:
            reasons.append("court-review-still-required")

        return IntentAssessment(
            state=state,
            disposition=disposition,
            reasons=tuple(reasons),
            candidate=candidate,
            eligible_for_downstream_review=state is IntentState.READY_FOR_REVIEW,
        )


def _validate_text_tuple(values: Tuple[str, ...], name: str) -> None:
    if not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"{name} must contain non-empty strings")

# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic, expiring expectation candidates for Native Brain.

Expectation formation evaluates whether one stable pattern justifies a bounded
statement about what may happen under named conditions and within a finite time
horizon. An expectation candidate is not a fact, prediction guarantee, memory
write, spoken response, operational proposal, execution grant, or authority
object.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .patterns import (
    PatternAssessment,
    PatternDisposition,
    PatternState,
)


class ExpectationState(str, Enum):
    NONE = "none"
    PROVISIONAL = "provisional"
    ACTIVE = "active"
    WEAKENED = "weakened"
    EXPIRED = "expired"
    RETIRED = "retired"
    BLOCKED = "blocked"


class ExpectationDisposition(str, Enum):
    BLOCKED = "blocked"
    DEFER_TO_SAFETY = "defer_to_safety"
    OBSERVE = "observe"
    FORM_CANDIDATE = "form_candidate"
    RETAIN_CANDIDATE = "retain_candidate"
    WEAKEN_CANDIDATE = "weaken_candidate"
    EXPIRE_CANDIDATE = "expire_candidate"
    RETIRE_CANDIDATE = "retire_candidate"


@dataclass(frozen=True)
class ExpectationContext:
    """Verified domain framing for one bounded expectation review."""

    expected_statement: Optional[str] = None
    triggering_conditions: Tuple[str, ...] = ()
    evidence_references: Tuple[str, ...] = ()
    evaluated_at: float = 0.0
    horizon_seconds: float = 300.0
    review_after_seconds: float = 120.0
    contradiction_count: int = 0
    missed_occurrences: int = 0
    existing_candidate: bool = False
    existing_formed_at: Optional[float] = None
    existing_expires_at: Optional[float] = None
    integrity_aligned: bool = True
    continuity_verified: bool = True
    runtime_context_verified: bool = True
    safety_priority: bool = False

    def __post_init__(self) -> None:
        if self.expected_statement is not None and not self.expected_statement.strip():
            raise ValueError("expected_statement cannot be blank")
        _validate_text_tuple(self.triggering_conditions, "triggering_conditions")
        _validate_text_tuple(self.evidence_references, "evidence_references")
        if self.evaluated_at < 0:
            raise ValueError("evaluated_at cannot be negative")
        if self.horizon_seconds <= 0:
            raise ValueError("horizon_seconds must be positive")
        if self.review_after_seconds <= 0:
            raise ValueError("review_after_seconds must be positive")
        if self.review_after_seconds > self.horizon_seconds:
            raise ValueError("review_after_seconds cannot exceed the horizon")
        if self.contradiction_count < 0 or self.missed_occurrences < 0:
            raise ValueError("contradiction and miss counts cannot be negative")
        if self.existing_candidate:
            if self.existing_formed_at is None or self.existing_expires_at is None:
                raise ValueError(
                    "existing expectation candidates require formed and expiry times"
                )
            if self.existing_formed_at < 0:
                raise ValueError("existing_formed_at cannot be negative")
            if self.existing_expires_at <= self.existing_formed_at:
                raise ValueError("existing expectation expiry must follow formation")
        elif self.existing_formed_at is not None or self.existing_expires_at is not None:
            raise ValueError(
                "existing expectation times require existing_candidate to be true"
            )


@dataclass(frozen=True)
class ExpectationCandidate:
    statement: str
    pattern_statement: str
    observation_key: str
    scope: str
    triggering_conditions: Tuple[str, ...]
    evidence_references: Tuple[str, ...]
    state: ExpectationState
    confidence: float
    formed_at: float
    review_at: float
    expires_at: float
    horizon_seconds: float
    support_count: int
    independent_contexts: int
    corroborating_sources: int
    contradiction_count: int
    missed_occurrences: int
    candidate: bool = True
    expectation: bool = True
    fact: bool = False
    prediction: bool = False
    canonical: bool = False
    speaking_authorized: bool = False
    memory_write_authorized: bool = False
    execution_authorized: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        for name, value in (
            ("statement", self.statement),
            ("pattern_statement", self.pattern_statement),
            ("observation_key", self.observation_key),
            ("scope", self.scope),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        _validate_text_tuple(self.triggering_conditions, "triggering_conditions")
        _validate_text_tuple(self.evidence_references, "evidence_references")
        if not self.triggering_conditions:
            raise ValueError("expectation candidates require triggering conditions")
        if not self.evidence_references:
            raise ValueError("expectation candidates require evidence references")
        if self.state not in {
            ExpectationState.PROVISIONAL,
            ExpectationState.ACTIVE,
            ExpectationState.WEAKENED,
            ExpectationState.EXPIRED,
            ExpectationState.RETIRED,
        }:
            raise ValueError("expectation candidates require a candidate state")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("expectation confidence must be between 0 and 1")
        if self.formed_at < 0 or self.review_at <= self.formed_at:
            raise ValueError("expectation review must follow formation")
        if self.expires_at <= self.formed_at or self.review_at > self.expires_at:
            raise ValueError("expectation timing must fit its finite lifetime")
        if self.horizon_seconds <= 0:
            raise ValueError("expectation horizon must be positive")
        if self.support_count < 1 or self.independent_contexts < 1:
            raise ValueError("expectation support and contexts must be positive")
        if (
            self.corroborating_sources < 0
            or self.contradiction_count < 0
            or self.missed_occurrences < 0
        ):
            raise ValueError("expectation evidence counts cannot be negative")
        if not self.candidate or not self.expectation:
            raise ValueError("expectation objects must remain explicit candidates")
        if self.fact or self.prediction or self.canonical:
            raise ValueError(
                "expectation candidates are not facts, guaranteed predictions, or canonical memory"
            )
        if (
            self.speaking_authorized
            or self.memory_write_authorized
            or self.execution_authorized
        ):
            raise ValueError("expectation candidates cannot authorize downstream effects")
        if self.authority != "none":
            raise ValueError("expectation candidates cannot carry authority")


@dataclass(frozen=True)
class ExpectationAssessment:
    state: ExpectationState
    disposition: ExpectationDisposition
    reasons: Tuple[str, ...]
    candidate: Optional[ExpectationCandidate] = None
    eligible_for_intent_review: bool = False
    canonical: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if not self.reasons:
            raise ValueError("expectation assessment reasons are required")
        candidate_dispositions = {
            ExpectationDisposition.FORM_CANDIDATE,
            ExpectationDisposition.RETAIN_CANDIDATE,
            ExpectationDisposition.WEAKEN_CANDIDATE,
            ExpectationDisposition.EXPIRE_CANDIDATE,
            ExpectationDisposition.RETIRE_CANDIDATE,
        }
        if self.disposition in candidate_dispositions and self.candidate is None:
            raise ValueError("candidate dispositions require an expectation candidate")
        if self.candidate is not None and self.candidate.state is not self.state:
            raise ValueError("assessment and candidate expectation states must match")
        if self.eligible_for_intent_review:
            if self.state is not ExpectationState.ACTIVE or self.candidate is None:
                raise ValueError("only active expectations may enter intent review")
        if self.canonical:
            raise ValueError("expectation assessments must remain non-canonical")
        if self.authority != "none":
            raise ValueError("expectation assessments cannot carry authority")


class ExpectationEngine:
    """Form finite expectation candidates without turning patterns into destiny."""

    def assess(
        self,
        pattern: PatternAssessment,
        context: ExpectationContext,
    ) -> ExpectationAssessment:
        blocked_reasons = []
        if not context.integrity_aligned:
            blocked_reasons.append("integrity-not-aligned")
        if not context.continuity_verified:
            blocked_reasons.append("continuity-not-verified")
        if not context.runtime_context_verified:
            blocked_reasons.append("runtime-context-not-verified")

        if blocked_reasons:
            return ExpectationAssessment(
                state=ExpectationState.BLOCKED,
                disposition=ExpectationDisposition.BLOCKED,
                reasons=tuple(blocked_reasons),
            )

        if (
            context.safety_priority
            or pattern.disposition is PatternDisposition.DEFER_TO_SAFETY
        ):
            return ExpectationAssessment(
                state=ExpectationState.BLOCKED,
                disposition=ExpectationDisposition.DEFER_TO_SAFETY,
                reasons=("safety-path-owns-next-judgment",),
            )

        if context.expected_statement is None:
            return ExpectationAssessment(
                state=ExpectationState.NONE,
                disposition=ExpectationDisposition.OBSERVE,
                reasons=("no-domain-expectation-statement",),
            )

        if not context.triggering_conditions:
            return ExpectationAssessment(
                state=ExpectationState.NONE,
                disposition=ExpectationDisposition.OBSERVE,
                reasons=("no-bounded-triggering-conditions",),
            )

        if not context.evidence_references:
            return ExpectationAssessment(
                state=ExpectationState.NONE,
                disposition=ExpectationDisposition.OBSERVE,
                reasons=("no-evidence-references",),
            )

        if (
            pattern.state is not PatternState.STABLE
            or not pattern.eligible_for_expectation_review
            or pattern.candidate is None
        ):
            return ExpectationAssessment(
                state=ExpectationState.NONE,
                disposition=ExpectationDisposition.OBSERVE,
                reasons=("stable-pattern-required",),
            )

        pattern_candidate = pattern.candidate
        formed_at = (
            context.existing_formed_at
            if context.existing_candidate
            else context.evaluated_at
        )
        expires_at = (
            context.existing_expires_at
            if context.existing_candidate
            else context.evaluated_at + context.horizon_seconds
        )
        assert formed_at is not None
        assert expires_at is not None
        review_at = min(
            formed_at + context.review_after_seconds,
            expires_at,
        )

        base_confidence = (
            pattern_candidate.confidence * 0.65
            + min(pattern_candidate.support_count, 6) / 6.0 * 0.15
            + min(pattern_candidate.independent_contexts, 4) / 4.0 * 0.10
            + min(pattern_candidate.corroborating_sources, 3) / 3.0 * 0.10
        )
        penalty = (
            min(context.contradiction_count, 3) * 0.18
            + min(context.missed_occurrences, 3) * 0.16
        )
        confidence = round(max(0.0, min(base_confidence - penalty, 1.0)), 4)

        if context.existing_candidate and context.evaluated_at >= expires_at:
            state = ExpectationState.EXPIRED
            disposition = ExpectationDisposition.EXPIRE_CANDIDATE
        elif context.contradiction_count >= 2 or context.missed_occurrences >= 2:
            state = ExpectationState.RETIRED
            disposition = ExpectationDisposition.RETIRE_CANDIDATE
        elif context.contradiction_count or context.missed_occurrences:
            state = ExpectationState.WEAKENED
            disposition = ExpectationDisposition.WEAKEN_CANDIDATE
        elif confidence >= 0.8:
            state = ExpectationState.ACTIVE
            disposition = (
                ExpectationDisposition.RETAIN_CANDIDATE
                if context.existing_candidate
                else ExpectationDisposition.FORM_CANDIDATE
            )
        else:
            state = ExpectationState.PROVISIONAL
            disposition = (
                ExpectationDisposition.RETAIN_CANDIDATE
                if context.existing_candidate
                else ExpectationDisposition.FORM_CANDIDATE
            )

        reasons = [
            f"state:{state.value}",
            f"pattern-confidence:{pattern_candidate.confidence:.4f}",
            f"support:{pattern_candidate.support_count}",
            f"contexts:{pattern_candidate.independent_contexts}",
            f"sources:{pattern_candidate.corroborating_sources}",
            f"horizon-seconds:{context.horizon_seconds:g}",
        ]
        if context.contradiction_count:
            reasons.append(f"contradictions:{context.contradiction_count}")
        if context.missed_occurrences:
            reasons.append(f"missed-occurrences:{context.missed_occurrences}")
        if context.existing_candidate and context.evaluated_at >= review_at:
            reasons.append("review-due-no-auto-renewal")
        if state is ExpectationState.EXPIRED:
            reasons.append("finite-expectation-expired")
        if state is ExpectationState.RETIRED:
            reasons.append("evidence-no-longer-supports-expectation")

        candidate = ExpectationCandidate(
            statement=context.expected_statement,
            pattern_statement=pattern_candidate.statement,
            observation_key=pattern_candidate.observation_key,
            scope=pattern_candidate.scope,
            triggering_conditions=context.triggering_conditions,
            evidence_references=context.evidence_references,
            state=state,
            confidence=confidence,
            formed_at=formed_at,
            review_at=review_at,
            expires_at=expires_at,
            horizon_seconds=context.horizon_seconds,
            support_count=pattern_candidate.support_count,
            independent_contexts=pattern_candidate.independent_contexts,
            corroborating_sources=pattern_candidate.corroborating_sources,
            contradiction_count=context.contradiction_count,
            missed_occurrences=context.missed_occurrences,
        )

        return ExpectationAssessment(
            state=state,
            disposition=disposition,
            reasons=tuple(reasons),
            candidate=candidate,
            eligible_for_intent_review=state is ExpectationState.ACTIVE,
        )


def _validate_text_tuple(value: Tuple[str, ...], field_name: str) -> None:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field_name} must contain non-empty strings")

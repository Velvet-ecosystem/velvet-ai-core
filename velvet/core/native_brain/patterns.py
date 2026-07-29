# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic, non-canonical pattern formation for Native Brain.

Pattern formation evaluates whether repeated supported observations justify a
bounded pattern candidate. A candidate is not a fact, expectation, memory
write, operational proposal, or authority object.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .attention import AttentionAssessment, ObservationMaturity
from .cognition import ObservationEnvelope
from .judgment import (
    ConfidenceBand,
    JudgmentAssessment,
    JudgmentDisposition,
)


class PatternState(str, Enum):
    NONE = "none"
    EMERGING = "emerging"
    TESTABLE = "testable"
    STABLE = "stable"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class PatternDisposition(str, Enum):
    BLOCKED = "blocked"
    DEFER_TO_SAFETY = "defer_to_safety"
    OBSERVE = "observe"
    FORM_CANDIDATE = "form_candidate"
    RETAIN_CANDIDATE = "retain_candidate"
    REJECT_CANDIDATE = "reject_candidate"


@dataclass(frozen=True)
class PatternContext:
    """Verified recurrence factors for one candidate pattern statement."""

    candidate_statement: Optional[str] = None
    observation_key: str = ""
    scope: str = "current-body"
    support_count: int = 1
    independent_contexts: int = 1
    corroborating_sources: int = 0
    contradiction_count: int = 0
    existing_candidate: bool = False
    integrity_aligned: bool = True
    continuity_verified: bool = True
    runtime_context_verified: bool = True

    def __post_init__(self) -> None:
        if self.candidate_statement is not None and not self.candidate_statement.strip():
            raise ValueError("candidate_statement cannot be blank")
        if self.candidate_statement is not None and not self.observation_key.strip():
            raise ValueError("observation_key is required for a pattern candidate")
        if not self.scope.strip():
            raise ValueError("pattern scope is required")
        if self.support_count < 1 or self.independent_contexts < 1:
            raise ValueError("support_count and independent_contexts must be positive")
        if self.corroborating_sources < 0 or self.contradiction_count < 0:
            raise ValueError("source and contradiction counts cannot be negative")


@dataclass(frozen=True)
class PatternCandidate:
    statement: str
    observation_key: str
    scope: str
    state: PatternState
    confidence: float
    support_count: int
    independent_contexts: int
    corroborating_sources: int
    contradiction_count: int
    fact: bool = False
    expectation: bool = False
    canonical: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if not self.statement.strip() or not self.observation_key.strip() or not self.scope.strip():
            raise ValueError("pattern statement, key, and scope are required")
        if self.state not in {
            PatternState.EMERGING,
            PatternState.TESTABLE,
            PatternState.STABLE,
            PatternState.REJECTED,
        }:
            raise ValueError("pattern candidates require a candidate state")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("pattern confidence must be between 0 and 1")
        if self.fact or self.expectation or self.canonical:
            raise ValueError("pattern candidates are not facts, expectations, or canonical memory")
        if self.authority != "none":
            raise ValueError("pattern candidates cannot carry authority")


@dataclass(frozen=True)
class PatternAssessment:
    state: PatternState
    disposition: PatternDisposition
    reasons: Tuple[str, ...]
    candidate: Optional[PatternCandidate] = None
    eligible_for_expectation_review: bool = False
    canonical: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if not self.reasons:
            raise ValueError("pattern assessment reasons are required")
        candidate_dispositions = {
            PatternDisposition.FORM_CANDIDATE,
            PatternDisposition.RETAIN_CANDIDATE,
            PatternDisposition.REJECT_CANDIDATE,
        }
        if self.disposition in candidate_dispositions and self.candidate is None:
            raise ValueError("candidate dispositions require a pattern candidate")
        if self.candidate is not None and self.candidate.state is not self.state:
            raise ValueError("assessment and candidate states must match")
        if self.eligible_for_expectation_review:
            if self.state is not PatternState.STABLE or self.candidate is None:
                raise ValueError("only stable candidates may enter expectation review")
        if self.canonical:
            raise ValueError("pattern assessments must remain non-canonical")
        if self.authority != "none":
            raise ValueError("pattern assessments cannot carry authority")


class PatternEngine:
    """Form testable pattern candidates without turning repetition into truth."""

    _MATURE_ENOUGH = {
        ObservationMaturity.REPEATED,
        ObservationMaturity.CONFIRMED,
        ObservationMaturity.PATTERN,
        ObservationMaturity.EXPECTATION,
    }

    def assess(
        self,
        observation: ObservationEnvelope,
        attention: AttentionAssessment,
        judgment: JudgmentAssessment,
        context: PatternContext,
    ) -> PatternAssessment:
        blocked_reasons = []
        if not context.integrity_aligned:
            blocked_reasons.append("integrity-not-aligned")
        if not context.continuity_verified:
            blocked_reasons.append("continuity-not-verified")
        if not context.runtime_context_verified:
            blocked_reasons.append("runtime-context-not-verified")

        if blocked_reasons:
            return PatternAssessment(
                state=PatternState.BLOCKED,
                disposition=PatternDisposition.BLOCKED,
                reasons=tuple(blocked_reasons),
            )

        if (
            attention.priority == "critical"
            or "safety-relevant" in attention.reasons
            or judgment.disposition is JudgmentDisposition.DEFER_TO_SAFETY
        ):
            return PatternAssessment(
                state=PatternState.BLOCKED,
                disposition=PatternDisposition.DEFER_TO_SAFETY,
                reasons=("safety-path-owns-next-judgment",),
            )

        if context.candidate_statement is None:
            return PatternAssessment(
                state=PatternState.NONE,
                disposition=PatternDisposition.OBSERVE,
                reasons=("no-domain-pattern-statement",),
            )

        if observation.simulated:
            return PatternAssessment(
                state=PatternState.NONE,
                disposition=PatternDisposition.OBSERVE,
                reasons=("simulated-evidence-cannot-form-real-pattern",),
            )

        if (
            judgment.disposition is not JudgmentDisposition.READY
            or judgment.band not in {ConfidenceBand.SUPPORTED, ConfidenceBand.STRONG}
        ):
            return PatternAssessment(
                state=PatternState.NONE,
                disposition=PatternDisposition.OBSERVE,
                reasons=("judgment-not-ready-for-pattern-formation",),
            )

        if context.support_count < 2 or attention.maturity not in self._MATURE_ENOUGH:
            return PatternAssessment(
                state=PatternState.NONE,
                disposition=PatternDisposition.OBSERVE,
                reasons=("recurrence-not-yet-demonstrated",),
            )

        total_evidence = context.support_count + context.contradiction_count
        contradiction_ratio = context.contradiction_count / max(total_evidence, 1)
        score = (
            judgment.confidence * 0.45
            + attention.score * 0.15
            + min(context.support_count, 6) / 6.0 * 0.15
            + min(context.independent_contexts, 4) / 4.0 * 0.10
            + min(context.corroborating_sources, 3) / 3.0 * 0.15
            - contradiction_ratio * 0.45
        )
        confidence = round(max(0.0, min(score, 1.0)), 4)

        if context.contradiction_count >= 2 and contradiction_ratio >= 0.5:
            state = PatternState.REJECTED
        elif (
            context.support_count >= 5
            and context.independent_contexts >= 3
            and context.corroborating_sources >= 2
            and context.contradiction_count == 0
            and judgment.band is ConfidenceBand.STRONG
        ):
            state = PatternState.STABLE
        elif (
            context.support_count >= 3
            and context.independent_contexts >= 2
            and context.corroborating_sources >= 1
            and contradiction_ratio < 0.25
        ):
            state = PatternState.TESTABLE
        else:
            state = PatternState.EMERGING

        reasons = [
            f"state:{state.value}",
            f"support:{context.support_count}",
            f"contexts:{context.independent_contexts}",
            f"sources:{context.corroborating_sources}",
        ]
        if context.contradiction_count:
            reasons.append(f"contradictions:{context.contradiction_count}")
        if judgment.band is ConfidenceBand.STRONG:
            reasons.append("strong-upstream-judgment")

        candidate = PatternCandidate(
            statement=context.candidate_statement,
            observation_key=context.observation_key,
            scope=context.scope,
            state=state,
            confidence=confidence,
            support_count=context.support_count,
            independent_contexts=context.independent_contexts,
            corroborating_sources=context.corroborating_sources,
            contradiction_count=context.contradiction_count,
        )

        if state is PatternState.REJECTED:
            disposition = PatternDisposition.REJECT_CANDIDATE
        elif context.existing_candidate:
            disposition = PatternDisposition.RETAIN_CANDIDATE
        else:
            disposition = PatternDisposition.FORM_CANDIDATE

        return PatternAssessment(
            state=state,
            disposition=disposition,
            reasons=tuple(reasons),
            candidate=candidate,
            eligible_for_expectation_review=state is PatternState.STABLE,
        )

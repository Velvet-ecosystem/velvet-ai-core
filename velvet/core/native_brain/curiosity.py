# SPDX-License-Identifier: GPL-3.0-only
"""Bounded curiosity for quiet observation and uncertainty reduction.

Curiosity does not speak, interrupt, poll hardware, access networks, write
memory, or grant authority. It produces deterministic working-state
candidates that Presence and the owning Runtime path may evaluate later.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .attention import AttentionAssessment, ObservationMaturity
from .cognition import ObservationEnvelope


class CuriosityDisposition(str, Enum):
    NONE = "none"
    WATCH = "watch"
    CORRELATE = "correlate"
    QUESTION_CANDIDATE = "question_candidate"
    RESOLVED = "resolved"
    DEFER_TO_SAFETY = "defer_to_safety"


@dataclass(frozen=True)
class CuriosityContext:
    """Missing-context signals supplied by verified cognition inputs."""

    unexplained_change: float = 0.0
    contradiction: float = 0.0
    missing_evidence: int = 0
    owner_available: bool = False
    addressed: bool = False
    existing_thread: bool = False
    explanation_available: bool = False

    def __post_init__(self) -> None:
        for value in (self.unexplained_change, self.contradiction):
            if not 0.0 <= value <= 1.0:
                raise ValueError("curiosity factors must be between 0 and 1")
        if self.missing_evidence < 0:
            raise ValueError("missing_evidence cannot be negative")


@dataclass(frozen=True)
class CuriosityThreadCandidate:
    """Non-canonical suggestion for an Open Thread, not a memory write."""

    subject: str
    reason: str
    expires_after_seconds: int = 3600
    canonical: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if not self.subject.strip() or not self.reason.strip():
            raise ValueError("thread subject and reason are required")
        if self.expires_after_seconds <= 0:
            raise ValueError("thread expiry must be positive")
        if self.canonical:
            raise ValueError("curiosity thread candidates must remain non-canonical")
        if self.authority != "none":
            raise ValueError("curiosity cannot carry authority")


@dataclass(frozen=True)
class CuriosityAssessment:
    disposition: CuriosityDisposition
    reason: str
    thread_candidate: Optional[CuriosityThreadCandidate] = None
    question_candidate: Optional[str] = None
    speak_now: bool = False
    interrupt: bool = False
    canonical: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("curiosity reason is required")
        if self.disposition is CuriosityDisposition.QUESTION_CANDIDATE:
            if not self.question_candidate:
                raise ValueError("question candidates require question text")
        elif self.question_candidate is not None:
            raise ValueError("question text is only valid for question candidates")
        if self.speak_now or self.interrupt:
            raise ValueError("curiosity cannot speak or interrupt directly")
        if self.canonical:
            raise ValueError("curiosity assessments must remain non-canonical")
        if self.authority != "none":
            raise ValueError("curiosity cannot carry authority")


class CuriosityEngine:
    """Decide whether to ignore, watch, correlate, ask later, or resolve."""

    def assess(
        self,
        observation: ObservationEnvelope,
        attention: AttentionAssessment,
        context: CuriosityContext,
    ) -> CuriosityAssessment:
        if attention.priority == "critical" or "safety-relevant" in attention.reasons:
            return CuriosityAssessment(
                disposition=CuriosityDisposition.DEFER_TO_SAFETY,
                reason="safety handling outranks curiosity",
            )

        if (
            context.explanation_available
            and attention.maturity in {
                ObservationMaturity.PATTERN,
                ObservationMaturity.EXPECTATION,
            }
            and context.contradiction < 0.2
        ):
            return CuriosityAssessment(
                disposition=CuriosityDisposition.RESOLVED,
                reason="the mature observation has a sufficient explanation",
            )

        if context.contradiction >= 0.6:
            thread = self._thread_candidate(
                observation,
                "conflicting evidence needs another verified observation",
                1800,
            )
            if context.addressed and context.owner_available:
                return CuriosityAssessment(
                    disposition=CuriosityDisposition.QUESTION_CANDIDATE,
                    reason="a bounded question may reduce conflicting evidence",
                    thread_candidate=None if context.existing_thread else thread,
                    question_candidate=(
                        "I have conflicting evidence about "
                        f"{observation.event_type}. Could you clarify what changed?"
                    ),
                )
            return CuriosityAssessment(
                disposition=CuriosityDisposition.CORRELATE,
                reason="conflicting evidence should be correlated quietly",
                thread_candidate=None if context.existing_thread else thread,
            )

        should_watch = (
            context.unexplained_change >= 0.5
            or context.missing_evidence > 0
            or attention.maturity
            in {ObservationMaturity.REPEATED, ObservationMaturity.CONFIRMED}
            or (attention.priority in {"normal", "high"} and "novel" in attention.reasons)
        )
        if should_watch:
            reason = "more evidence is needed before drawing a conclusion"
            if context.existing_thread:
                return CuriosityAssessment(
                    disposition=CuriosityDisposition.WATCH,
                    reason="an existing Open Thread already covers this uncertainty",
                )
            return CuriosityAssessment(
                disposition=CuriosityDisposition.WATCH,
                reason=reason,
                thread_candidate=self._thread_candidate(observation, reason, 3600),
            )

        if attention.maturity in {
            ObservationMaturity.PATTERN,
            ObservationMaturity.EXPECTATION,
        }:
            return CuriosityAssessment(
                disposition=CuriosityDisposition.CORRELATE,
                reason="a mature observation should be compared with future evidence",
                thread_candidate=(
                    None
                    if context.existing_thread
                    else self._thread_candidate(
                        observation,
                        "compare the mature observation with future evidence",
                        7200,
                    )
                ),
            )

        return CuriosityAssessment(
            disposition=CuriosityDisposition.NONE,
            reason="the observation does not justify an unfinished thought",
        )

    @staticmethod
    def _thread_candidate(
        observation: ObservationEnvelope,
        reason: str,
        expires_after_seconds: int,
    ) -> CuriosityThreadCandidate:
        return CuriosityThreadCandidate(
            subject=observation.event_type,
            reason=reason,
            expires_after_seconds=expires_after_seconds,
        )

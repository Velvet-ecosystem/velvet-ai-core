# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic confidence calibration and explainable judgment.

Judgment evaluates whether bounded evidence is ready to become a presentation
candidate. It does not speak, create operational proposals, write canonical
memory, call tools, or grant authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .attention import AttentionAssessment, ObservationMaturity
from .cognition import ObservationEnvelope
from .curiosity import CuriosityAssessment, CuriosityDisposition


class ConfidenceBand(str, Enum):
    BLOCKED = "blocked"
    INSUFFICIENT = "insufficient"
    TENTATIVE = "tentative"
    SUPPORTED = "supported"
    STRONG = "strong"


class JudgmentDisposition(str, Enum):
    BLOCKED = "blocked"
    OBSERVE = "observe"
    QUESTION = "question"
    CORRELATE = "correlate"
    READY = "ready"
    DEFER_TO_SAFETY = "defer_to_safety"


@dataclass(frozen=True)
class JudgmentContext:
    """Verified evidence factors for one candidate claim."""

    candidate_claim: Optional[str] = None
    source_reliability: float = 0.5
    evidence_completeness: float = 0.0
    freshness: float = 1.0
    corroborating_sources: int = 0
    contradiction: float = 0.0
    missing_evidence: Tuple[str, ...] = ()
    integrity_aligned: bool = True
    continuity_verified: bool = True
    runtime_context_verified: bool = True

    def __post_init__(self) -> None:
        for value in (
            self.source_reliability,
            self.evidence_completeness,
            self.freshness,
            self.contradiction,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("judgment factors must be between 0 and 1")
        if self.corroborating_sources < 0:
            raise ValueError("corroborating_sources cannot be negative")
        if self.candidate_claim is not None and not self.candidate_claim.strip():
            raise ValueError("candidate_claim cannot be blank")
        if any(not item.strip() for item in self.missing_evidence):
            raise ValueError("missing_evidence entries cannot be blank")


@dataclass(frozen=True)
class JudgmentAssessment:
    confidence: float
    band: ConfidenceBand
    disposition: JudgmentDisposition
    reasons: Tuple[str, ...]
    claim: Optional[str] = None
    missing_evidence: Tuple[str, ...] = ()
    presentation_candidate: bool = False
    canonical: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.reasons:
            raise ValueError("judgment reasons are required")
        if self.presentation_candidate:
            if self.disposition is not JudgmentDisposition.READY:
                raise ValueError("only ready judgments may become presentation candidates")
            if self.claim is None:
                raise ValueError("presentation candidates require a claim")
            if self.band not in {ConfidenceBand.SUPPORTED, ConfidenceBand.STRONG}:
                raise ValueError("presentation candidates require supported evidence")
        if self.canonical:
            raise ValueError("judgment assessments must remain non-canonical")
        if self.authority != "none":
            raise ValueError("judgment cannot carry authority")


class JudgmentEngine:
    """Calibrate evidence and expose why a claim is or is not ready."""

    _MATURITY_BONUS = {
        ObservationMaturity.NEW: 0.00,
        ObservationMaturity.REPEATED: 0.03,
        ObservationMaturity.CONFIRMED: 0.06,
        ObservationMaturity.PATTERN: 0.08,
        ObservationMaturity.EXPECTATION: 0.10,
    }

    def assess(
        self,
        observation: ObservationEnvelope,
        attention: AttentionAssessment,
        curiosity: CuriosityAssessment,
        context: JudgmentContext,
    ) -> JudgmentAssessment:
        blocked_reasons = []
        if not context.integrity_aligned:
            blocked_reasons.append("integrity-not-aligned")
        if not context.continuity_verified:
            blocked_reasons.append("continuity-not-verified")
        if not context.runtime_context_verified:
            blocked_reasons.append("runtime-context-not-verified")

        if blocked_reasons:
            return JudgmentAssessment(
                confidence=0.0,
                band=ConfidenceBand.BLOCKED,
                disposition=JudgmentDisposition.BLOCKED,
                reasons=tuple(blocked_reasons),
                claim=context.candidate_claim,
                missing_evidence=context.missing_evidence,
            )

        if (
            attention.priority == "critical"
            or "safety-relevant" in attention.reasons
            or curiosity.disposition is CuriosityDisposition.DEFER_TO_SAFETY
        ):
            return JudgmentAssessment(
                confidence=0.0,
                band=ConfidenceBand.BLOCKED,
                disposition=JudgmentDisposition.DEFER_TO_SAFETY,
                reasons=("safety-path-owns-next-judgment",),
                claim=context.candidate_claim,
                missing_evidence=context.missing_evidence,
            )

        score = (
            observation.confidence * 0.30
            + attention.score * 0.20
            + context.source_reliability * 0.20
            + context.evidence_completeness * 0.15
            + context.freshness * 0.10
            + min(context.corroborating_sources, 3) / 3.0 * 0.05
            + self._MATURITY_BONUS[attention.maturity]
        )
        score -= context.contradiction * 0.35
        score -= min(len(context.missing_evidence), 3) * 0.08
        score = max(0.0, min(score, 1.0))

        reasons = [
            f"maturity:{attention.maturity.value}",
            f"attention:{attention.priority}",
        ]
        if context.source_reliability >= 0.7:
            reasons.append("reliable-source")
        if context.corroborating_sources:
            reasons.append("corroborated")
        if context.evidence_completeness >= 0.7:
            reasons.append("evidence-mostly-complete")
        if context.contradiction >= 0.2:
            reasons.append("contradictory-evidence")
        if context.missing_evidence:
            reasons.append("required-evidence-missing")
        if curiosity.disposition is CuriosityDisposition.QUESTION_CANDIDATE:
            reasons.append("curiosity-question-candidate")
        elif curiosity.disposition in {
            CuriosityDisposition.WATCH,
            CuriosityDisposition.CORRELATE,
        }:
            reasons.append("curiosity-still-open")

        if observation.simulated:
            score = min(score, 0.49)
            reasons.append("simulated-evidence-cap")

        confidence = round(score, 4)
        band = self._band(confidence)

        if context.missing_evidence:
            band = ConfidenceBand.INSUFFICIENT
            disposition = (
                JudgmentDisposition.QUESTION
                if curiosity.disposition is CuriosityDisposition.QUESTION_CANDIDATE
                else JudgmentDisposition.OBSERVE
            )
        elif context.contradiction >= 0.6:
            disposition = (
                JudgmentDisposition.QUESTION
                if curiosity.disposition is CuriosityDisposition.QUESTION_CANDIDATE
                else JudgmentDisposition.CORRELATE
            )
        elif observation.simulated:
            disposition = JudgmentDisposition.CORRELATE
        elif context.candidate_claim is None:
            disposition = JudgmentDisposition.OBSERVE
        elif band is ConfidenceBand.INSUFFICIENT:
            disposition = JudgmentDisposition.OBSERVE
        elif band is ConfidenceBand.TENTATIVE:
            disposition = (
                JudgmentDisposition.QUESTION
                if curiosity.disposition is CuriosityDisposition.QUESTION_CANDIDATE
                else JudgmentDisposition.CORRELATE
            )
        else:
            disposition = JudgmentDisposition.READY

        return JudgmentAssessment(
            confidence=confidence,
            band=band,
            disposition=disposition,
            reasons=tuple(reasons),
            claim=context.candidate_claim,
            missing_evidence=context.missing_evidence,
            presentation_candidate=disposition is JudgmentDisposition.READY,
        )

    @staticmethod
    def _band(confidence: float) -> ConfidenceBand:
        if confidence < 0.35:
            return ConfidenceBand.INSUFFICIENT
        if confidence < 0.60:
            return ConfidenceBand.TENTATIVE
        if confidence < 0.82:
            return ConfidenceBand.SUPPORTED
        return ConfidenceBand.STRONG

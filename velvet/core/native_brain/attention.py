# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic attention and observation-maturity contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .cognition import ObservationEnvelope


class ObservationMaturity(str, Enum):
    NEW = "new"
    REPEATED = "repeated"
    CONFIRMED = "confirmed"
    PATTERN = "pattern"
    EXPECTATION = "expectation"


@dataclass(frozen=True)
class AttentionContext:
    repetition_count: int = 1
    corroborating_sources: int = 0
    historical_matches: int = 0
    owner_relevance: float = 0.0
    novelty: float = 0.0
    safety_relevance: float = 0.0

    def __post_init__(self) -> None:
        if self.repetition_count < 1:
            raise ValueError("repetition_count must be at least one")
        if self.corroborating_sources < 0 or self.historical_matches < 0:
            raise ValueError("source and history counts cannot be negative")
        for value in (self.owner_relevance, self.novelty, self.safety_relevance):
            if not 0.0 <= value <= 1.0:
                raise ValueError("attention factors must be between 0 and 1")


@dataclass(frozen=True)
class AttentionAssessment:
    maturity: ObservationMaturity
    score: float
    priority: str
    reasons: tuple[str, ...]
    authority: str = "none"


class AttentionEngine:
    """Score attention without models, learning, or operational authority."""

    def assess(
        self, observation: ObservationEnvelope, context: AttentionContext
    ) -> AttentionAssessment:
        maturity = self._maturity(context)
        score = min(
            1.0,
            observation.confidence * 0.25
            + context.novelty * 0.20
            + context.owner_relevance * 0.20
            + context.safety_relevance * 0.30
            + min(context.repetition_count, 5) / 5.0 * 0.05,
        )

        reasons = [f"maturity:{maturity.value}"]
        if context.safety_relevance >= 0.6:
            reasons.append("safety-relevant")
        if context.owner_relevance >= 0.6:
            reasons.append("owner-relevant")
        if context.novelty >= 0.6:
            reasons.append("novel")
        if context.corroborating_sources:
            reasons.append("corroborated")
        if context.historical_matches:
            reasons.append("historical-match")

        if context.safety_relevance >= 0.8:
            priority = "critical"
        elif score >= 0.65:
            priority = "high"
        elif score >= 0.35:
            priority = "normal"
        else:
            priority = "low"

        return AttentionAssessment(
            maturity=maturity,
            score=round(score, 4),
            priority=priority,
            reasons=tuple(reasons),
        )

    @staticmethod
    def _maturity(context: AttentionContext) -> ObservationMaturity:
        if context.historical_matches >= 3 and context.repetition_count >= 5:
            return ObservationMaturity.EXPECTATION
        if context.historical_matches >= 1 and context.repetition_count >= 4:
            return ObservationMaturity.PATTERN
        if context.corroborating_sources >= 1 and context.repetition_count >= 2:
            return ObservationMaturity.CONFIRMED
        if context.repetition_count >= 2:
            return ObservationMaturity.REPEATED
        return ObservationMaturity.NEW

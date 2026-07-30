"""Deterministic freshness review for cross-organ evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from uuid import uuid4

from .models import (
    EvidenceContribution,
    EvidenceFreshness,
    FreshnessDisposition,
)


@dataclass(frozen=True)
class EvidenceFreshnessEvaluator:
    """Decay confidence with age without mutating the source contribution."""

    fresh_for_seconds: float = 30.0
    stale_after_seconds: float = 300.0

    def __post_init__(self) -> None:
        if self.fresh_for_seconds < 0.0:
            raise ValueError("fresh_for_seconds must be non-negative")
        if self.stale_after_seconds <= self.fresh_for_seconds:
            raise ValueError(
                "stale_after_seconds must be greater than fresh_for_seconds"
            )

    def evaluate(
        self,
        contribution: EvidenceContribution,
        now: datetime | None = None,
    ) -> EvidenceFreshness:
        evaluated_at = now or datetime.now(timezone.utc)
        base_confidence = contribution.confidence

        if contribution.observed_at.tzinfo is None or evaluated_at.tzinfo is None:
            return self._record(
                contribution,
                evaluated_at,
                FreshnessDisposition.INVALID,
                0.0,
                0.0,
                "Evidence timestamps must be timezone-aware.",
            )

        age_seconds = (evaluated_at - contribution.observed_at).total_seconds()

        if not 0.0 <= base_confidence <= 1.0:
            return self._record(
                contribution,
                evaluated_at,
                FreshnessDisposition.INVALID,
                age_seconds,
                0.0,
                "Base confidence is outside the bounded range.",
            )

        if age_seconds < 0.0:
            return self._record(
                contribution,
                evaluated_at,
                FreshnessDisposition.INVALID,
                age_seconds,
                0.0,
                "Evidence timestamp is in the future.",
            )

        if age_seconds <= self.fresh_for_seconds:
            return self._record(
                contribution,
                evaluated_at,
                FreshnessDisposition.FRESH,
                age_seconds,
                base_confidence,
                "Evidence remains inside the fresh window.",
            )

        if age_seconds >= self.stale_after_seconds:
            return self._record(
                contribution,
                evaluated_at,
                FreshnessDisposition.STALE,
                age_seconds,
                0.0,
                "Evidence exceeded the stale threshold.",
            )

        decay_window = self.stale_after_seconds - self.fresh_for_seconds
        remaining = self.stale_after_seconds - age_seconds
        decay_factor = remaining / decay_window
        effective_confidence = round(base_confidence * decay_factor, 6)
        return self._record(
            contribution,
            evaluated_at,
            FreshnessDisposition.AGING,
            age_seconds,
            effective_confidence,
            "Evidence confidence was reduced because the finding is aging.",
        )

    def evaluate_many(
        self,
        contributions: Iterable[EvidenceContribution],
        now: datetime | None = None,
    ) -> tuple[EvidenceFreshness, ...]:
        evaluated_at = now or datetime.now(timezone.utc)
        return tuple(
            self.evaluate(contribution, evaluated_at)
            for contribution in contributions
        )

    @staticmethod
    def _record(
        contribution: EvidenceContribution,
        evaluated_at: datetime,
        disposition: FreshnessDisposition,
        age_seconds: float,
        effective_confidence: float,
        rationale: str,
    ) -> EvidenceFreshness:
        return EvidenceFreshness(
            freshness_id=str(uuid4()),
            contribution_id=contribution.contribution_id,
            disposition=disposition,
            age_seconds=round(age_seconds, 6),
            base_confidence=contribution.confidence,
            effective_confidence=effective_confidence,
            rationale=rationale,
            evaluated_at=evaluated_at,
        )

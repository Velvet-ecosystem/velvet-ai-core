"""Deterministic fusion of cross-organ evidence without granting authority."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable
from uuid import uuid4

from .freshness import EvidenceFreshnessEvaluator
from .models import (
    EvidenceContribution,
    EvidenceFusion,
    FreshnessDisposition,
    FusionDisposition,
)


@dataclass(frozen=True)
class EvidenceFusionEngine:
    """Combine current organ findings while preserving age and disagreement."""

    minimum_contributors: int = 2
    freshness: EvidenceFreshnessEvaluator = field(
        default_factory=EvidenceFreshnessEvaluator
    )

    def fuse(
        self,
        subject: str,
        contributions: Iterable[EvidenceContribution],
        now: datetime | None = None,
    ) -> EvidenceFusion:
        items = tuple(contributions)
        if not subject.strip():
            raise ValueError("fusion subject must be non-empty")

        freshness_records = self.freshness.evaluate_many(items, now)
        pairs = tuple(zip(items, freshness_records))
        active_pairs = tuple(
            (item, freshness)
            for item, freshness in pairs
            if freshness.disposition
            in (FreshnessDisposition.FRESH, FreshnessDisposition.AGING)
            and freshness.effective_confidence > 0.0
        )
        stale_ids = tuple(
            item.contribution_id
            for item, freshness in pairs
            if freshness.disposition is FreshnessDisposition.STALE
        )
        invalid_ids = tuple(
            item.contribution_id
            for item, freshness in pairs
            if freshness.disposition is FreshnessDisposition.INVALID
        )

        if not items:
            return EvidenceFusion(
                fusion_id=str(uuid4()),
                subject=subject.strip(),
                contribution_ids=(),
                disposition=FusionDisposition.INSUFFICIENT_EVIDENCE,
                confidence=0.0,
                rationale="No evidence contributions were supplied.",
            )

        organ_names = {item.organ_name for item, _ in active_pairs}
        claims = {item.claim for item, _ in active_pairs}
        confidence = (
            round(
                sum(
                    freshness.effective_confidence
                    for _, freshness in active_pairs
                )
                / len(active_pairs),
                6,
            )
            if active_pairs
            else 0.0
        )

        if len(organ_names) < self.minimum_contributors:
            disposition = FusionDisposition.INSUFFICIENT_EVIDENCE
            rationale = (
                "Not enough distinct organs supplied current usable evidence."
            )
        elif len(claims) > 1:
            disposition = FusionDisposition.CONFLICTED
            rationale = (
                "Current organs supplied conflicting findings; disagreement is preserved."
            )
        else:
            disposition = FusionDisposition.COHERENT
            rationale = "Distinct organs supplied a coherent current claim."

        exclusions: list[str] = []
        if stale_ids:
            exclusions.append(f"{len(stale_ids)} stale contribution(s) excluded")
        if invalid_ids:
            exclusions.append(f"{len(invalid_ids)} invalid contribution(s) excluded")
        if exclusions:
            rationale = f"{rationale} {'; '.join(exclusions)}."

        return EvidenceFusion(
            fusion_id=str(uuid4()),
            subject=subject.strip(),
            contribution_ids=tuple(item.contribution_id for item in items),
            disposition=disposition,
            confidence=confidence,
            rationale=rationale,
            freshness_ids=tuple(
                freshness.freshness_id for freshness in freshness_records
            ),
            active_contribution_ids=tuple(
                item.contribution_id for item, _ in active_pairs
            ),
            stale_contribution_ids=stale_ids,
            invalid_contribution_ids=invalid_ids,
        )

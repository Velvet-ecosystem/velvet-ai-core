"""Deterministic fusion of cross-organ evidence without granting authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import uuid4

from .models import EvidenceContribution, EvidenceFusion, FusionDisposition


@dataclass(frozen=True)
class EvidenceFusionEngine:
    """Combine organ findings while preserving disagreement and uncertainty."""

    minimum_contributors: int = 2

    def fuse(
        self,
        subject: str,
        contributions: Iterable[EvidenceContribution],
    ) -> EvidenceFusion:
        items = tuple(contributions)
        if not subject.strip():
            raise ValueError("fusion subject must be non-empty")
        if not items:
            return EvidenceFusion(
                fusion_id=str(uuid4()),
                subject=subject.strip(),
                contribution_ids=(),
                disposition=FusionDisposition.INSUFFICIENT_EVIDENCE,
                confidence=0.0,
                rationale="No evidence contributions were supplied.",
            )

        organ_names = {item.organ_name for item in items}
        claims = {item.claim for item in items}
        bounded = all(0.0 <= item.confidence <= 1.0 for item in items)
        mean_confidence = sum(item.confidence for item in items) / len(items)

        if not bounded:
            disposition = FusionDisposition.CONFLICTED
            rationale = "At least one contribution has confidence outside the bounded range."
        elif len(organ_names) < self.minimum_contributors:
            disposition = FusionDisposition.INSUFFICIENT_EVIDENCE
            rationale = "Not enough distinct organs contributed evidence."
        elif len(claims) > 1:
            disposition = FusionDisposition.CONFLICTED
            rationale = "Organs reported conflicting claims; disagreement is preserved."
        else:
            disposition = FusionDisposition.COHERENT
            rationale = "Distinct organs reported a coherent claim."

        return EvidenceFusion(
            fusion_id=str(uuid4()),
            subject=subject.strip(),
            contribution_ids=tuple(item.contribution_id for item in items),
            disposition=disposition,
            confidence=mean_confidence,
            rationale=rationale,
        )

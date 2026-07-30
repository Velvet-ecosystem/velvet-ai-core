"""Deterministic, non-authoritative review of completed decision receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import DecisionReceipt, ReflectionReview, ReviewDisposition


@dataclass(frozen=True)
class ReceiptReviewer:
    """Review receipts without rewriting them or changing system authority."""

    low_confidence_threshold: float = 0.5

    def review(self, receipt: DecisionReceipt) -> ReflectionReview:
        evaluation = receipt.judgment.evaluation
        notes: list[str] = []
        disposition = ReviewDisposition.ACCEPTED

        if not 0.0 <= evaluation.confidence <= 1.0:
            disposition = ReviewDisposition.FLAGGED
            notes.append("confidence is outside the bounded range")
        elif evaluation.confidence < self.low_confidence_threshold:
            disposition = ReviewDisposition.FLAGGED
            notes.append("confidence is below the review threshold")

        if not evaluation.reasons:
            disposition = ReviewDisposition.FLAGGED
            notes.append("evaluation has no evidence reasons")

        if not receipt.judgment.rationale.strip():
            disposition = ReviewDisposition.FLAGGED
            notes.append("judgment rationale is empty")

        if not notes:
            notes.append("receipt is internally complete")

        return ReflectionReview(
            receipt_id=receipt.receipt_id,
            disposition=disposition,
            notes=tuple(notes),
        )

    def review_many(
        self, receipts: Iterable[DecisionReceipt]
    ) -> tuple[ReflectionReview, ...]:
        return tuple(self.review(receipt) for receipt in receipts)

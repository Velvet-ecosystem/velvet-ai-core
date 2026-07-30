"""Bounded learning-proposal generation for Velvet's Native Brain.

This module never changes weights, policy, runtime state, or behavior. It only
turns flagged reflection records into immutable proposals for later review.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import uuid4

from .models import (
    LearningDisposition,
    LearningProposal,
    ReflectionReview,
    ReviewDisposition,
)


@dataclass(frozen=True)
class LearningProposalBuilder:
    """Create non-executing learning proposals from append-only reviews."""

    minimum_flagged_reviews: int = 1

    def propose(
        self, reviews: Iterable[ReflectionReview], subject: str
    ) -> LearningProposal:
        review_tuple = tuple(reviews)
        flagged = tuple(
            review
            for review in review_tuple
            if review.disposition is ReviewDisposition.FLAGGED
        )

        if not subject.strip():
            raise ValueError("learning proposal subject must be non-empty")

        if len(flagged) < self.minimum_flagged_reviews:
            disposition = LearningDisposition.INSUFFICIENT_EVIDENCE
            rationale = "Not enough flagged reviews to form a learning proposal."
        else:
            disposition = LearningDisposition.PROPOSED
            rationale = (
                "Flagged receipt reviews suggest a bounded candidate for later "
                "human or Court-governed promotion review."
            )

        return LearningProposal(
            proposal_id=str(uuid4()),
            subject=subject.strip(),
            source_review_ids=tuple(review.review_id for review in flagged),
            source_receipt_ids=tuple(review.receipt_id for review in flagged),
            disposition=disposition,
            rationale=rationale,
        )

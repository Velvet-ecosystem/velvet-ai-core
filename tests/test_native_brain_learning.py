"""Tests for proposal-only Native Brain learning integration."""

import unittest

from ai_brain.native_brain import (
    LearningDisposition,
    LearningProposalBuilder,
    NativeBrain,
    ReflectionReview,
    ReviewDisposition,
)


class LearningProposalTests(unittest.TestCase):
    def test_flagged_review_creates_proposal_without_applying_changes(self) -> None:
        review = ReflectionReview(
            receipt_id="receipt-1",
            disposition=ReviewDisposition.FLAGGED,
            notes=("confidence is below the review threshold",),
        )

        proposal = LearningProposalBuilder().propose(
            (review,), "sensor confidence calibration"
        )

        self.assertEqual(proposal.disposition, LearningDisposition.PROPOSED)
        self.assertEqual(proposal.source_review_ids, (review.review_id,))
        self.assertEqual(proposal.source_receipt_ids, ("receipt-1",))
        self.assertFalse(proposal.changes_applied)

    def test_accepted_reviews_do_not_form_learning_evidence(self) -> None:
        review = ReflectionReview(
            receipt_id="receipt-2",
            disposition=ReviewDisposition.ACCEPTED,
            notes=("receipt is internally complete",),
        )

        proposal = LearningProposalBuilder().propose((review,), "door event handling")

        self.assertEqual(
            proposal.disposition, LearningDisposition.INSUFFICIENT_EVIDENCE
        )
        self.assertEqual(proposal.source_review_ids, ())
        self.assertFalse(proposal.changes_applied)

    def test_empty_subject_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            LearningProposalBuilder().propose((), "   ")

    def test_native_brain_proposal_does_not_mutate_review(self) -> None:
        brain = NativeBrain()
        receipt = brain.process({"type": "sensor.reading", "source": "sensor"})
        review = brain.reflect(receipt)

        original_notes = review.notes
        proposal = brain.propose_learning((review,), "review completeness")

        self.assertEqual(review.notes, original_notes)
        self.assertFalse(proposal.changes_applied)


if __name__ == "__main__":
    unittest.main()

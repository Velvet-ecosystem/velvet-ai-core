"""Additional evidence-link tests for bounded learning proposals."""

import unittest

from ai_brain.native_brain import (
    LearningDisposition,
    LearningProposalBuilder,
    ReflectionReview,
    ReviewDisposition,
)


class LearningEvidenceTests(unittest.TestCase):
    def test_only_flagged_reviews_are_linked(self) -> None:
        accepted = ReflectionReview(
            receipt_id="receipt-ok",
            disposition=ReviewDisposition.ACCEPTED,
        )
        flagged = ReflectionReview(
            receipt_id="receipt-flagged",
            disposition=ReviewDisposition.FLAGGED,
            notes=("low confidence",),
        )

        proposal = LearningProposalBuilder().propose(
            (accepted, flagged), "confidence calibration"
        )

        self.assertEqual(proposal.disposition, LearningDisposition.PROPOSED)
        self.assertEqual(proposal.source_review_ids, (flagged.review_id,))
        self.assertEqual(proposal.source_receipt_ids, ("receipt-flagged",))

    def test_minimum_evidence_threshold_is_enforced(self) -> None:
        flagged = ReflectionReview(
            receipt_id="receipt-1",
            disposition=ReviewDisposition.FLAGGED,
        )

        proposal = LearningProposalBuilder(minimum_flagged_reviews=2).propose(
            (flagged,), "threshold review"
        )

        self.assertEqual(
            proposal.disposition, LearningDisposition.INSUFFICIENT_EVIDENCE
        )
        self.assertFalse(proposal.changes_applied)


if __name__ == "__main__":
    unittest.main()

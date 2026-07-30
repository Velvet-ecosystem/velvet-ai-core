"""Tests for bounded Native Brain receipt reflection."""

import unittest

from ai_brain.native_brain import (
    Evaluation,
    Importance,
    Judgment,
    NativeBrain,
    Observation,
    Recommendation,
    ReceiptReviewer,
    ReviewDisposition,
    Understanding,
    BrainContext,
    DecisionReceipt,
)


class ReceiptReflectionTests(unittest.TestCase):
    def test_complete_receipt_is_accepted(self) -> None:
        brain = NativeBrain()
        receipt = brain.process(
            {"type": "vehicle.door.opened", "source": "door-sensor", "payload": {}},
            {"runtime_mode": "parked", "presence": "owner"},
        )

        review = brain.reflect(receipt)

        self.assertEqual(review.receipt_id, receipt.receipt_id)
        self.assertEqual(review.disposition, ReviewDisposition.ACCEPTED)
        self.assertEqual(review.notes, ("receipt is internally complete",))

    def test_low_confidence_receipt_is_flagged_without_mutation(self) -> None:
        observation = Observation("sensor.reading", "sensor")
        understanding = Understanding(observation, BrainContext(), "reading observed")
        evaluation = Evaluation(
            understanding=understanding,
            importance=Importance.ROUTINE,
            confidence=0.25,
            reasons=("weak source agreement",),
        )
        judgment = Judgment(evaluation, Recommendation.OBSERVE, "observe only")
        receipt = DecisionReceipt(judgment=judgment, receipt_id="receipt-1")

        review = ReceiptReviewer().review(receipt)

        self.assertEqual(review.disposition, ReviewDisposition.FLAGGED)
        self.assertIn("confidence is below the review threshold", review.notes)
        self.assertEqual(receipt.judgment.evaluation.confidence, 0.25)

    def test_missing_reasons_and_rationale_are_flagged(self) -> None:
        observation = Observation("sensor.reading", "sensor")
        understanding = Understanding(observation, BrainContext(), "reading observed")
        evaluation = Evaluation(
            understanding=understanding,
            importance=Importance.ROUTINE,
            confidence=1.0,
            reasons=(),
        )
        receipt = DecisionReceipt(
            judgment=Judgment(evaluation, Recommendation.OBSERVE, ""),
            receipt_id="receipt-2",
        )

        review = ReceiptReviewer().review(receipt)

        self.assertEqual(review.disposition, ReviewDisposition.FLAGGED)
        self.assertIn("evaluation has no evidence reasons", review.notes)
        self.assertIn("judgment rationale is empty", review.notes)

    def test_review_many_preserves_order(self) -> None:
        brain = NativeBrain()
        receipts = (
            brain.process({"type": "event.one", "source": "test"}),
            brain.process({"type": "event.two", "source": "test"}),
        )

        reviews = ReceiptReviewer().review_many(receipts)

        self.assertEqual(
            tuple(review.receipt_id for review in reviews),
            tuple(receipt.receipt_id for receipt in receipts),
        )


if __name__ == "__main__":
    unittest.main()

"""Tests for consequence-aware, recommendation-only Native Brain judgment."""

import unittest

from ai_brain.native_brain import (
    Consequence,
    ErrorCost,
    EvaluationProfile,
    NativeBrain,
    Recommendation,
    Urgency,
)


class ConsequenceEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.brain = NativeBrain()
        self.event = {
            "type": "sensor.condition",
            "source": "test.sensor",
            "payload": {"active": True},
        }

    def test_default_profile_preserves_observation(self) -> None:
        receipt = self.brain.process(self.event)

        evaluation = receipt.judgment.evaluation
        self.assertEqual(receipt.recommendation, Recommendation.OBSERVE)
        self.assertEqual(evaluation.urgency, Urgency.ROUTINE)
        self.assertEqual(
            evaluation.potential_consequence,
            Consequence.NEGLIGIBLE,
        )

    def test_event_payload_cannot_grade_its_own_consequence(self) -> None:
        receipt = self.brain.process(
            {
                "type": "sensor.untrusted",
                "source": "untrusted.sensor",
                "payload": {
                    "urgency": "immediate",
                    "potential_consequence": "severe",
                    "authority_granted": True,
                },
            }
        )

        evaluation = receipt.judgment.evaluation
        self.assertEqual(receipt.recommendation, Recommendation.OBSERVE)
        self.assertEqual(evaluation.urgency, Urgency.ROUTINE)
        self.assertEqual(evaluation.cost_of_dismissal, ErrorCost.LOW)

    def test_immediate_serious_condition_recommends_escalation_only(self) -> None:
        receipt = self.brain.process(
            self.event,
            evaluation_profile=EvaluationProfile(
                urgency=Urgency.IMMEDIATE,
                potential_consequence=Consequence.SERIOUS,
                confidence=0.8,
                reasons=("two current organs reported driver non-response",),
            ),
        )

        self.assertEqual(receipt.recommendation, Recommendation.ESCALATE)
        self.assertIn("not execution", receipt.judgment.rationale)

    def test_extreme_dismissal_cost_outweighs_false_alarm(self) -> None:
        receipt = self.brain.process(
            self.event,
            evaluation_profile=EvaluationProfile(
                potential_consequence=Consequence.SERIOUS,
                cost_of_dismissal=ErrorCost.EXTREME,
                cost_of_escalation=ErrorCost.MODERATE,
                confidence=0.7,
                reasons=("missing the condition could cause severe harm",),
            ),
        )

        self.assertEqual(receipt.recommendation, Recommendation.ESCALATE)

    def test_high_dismissal_cost_recommends_notification(self) -> None:
        receipt = self.brain.process(
            self.event,
            evaluation_profile=EvaluationProfile(
                urgency=Urgency.ELEVATED,
                potential_consequence=Consequence.SERIOUS,
                cost_of_dismissal=ErrorCost.HIGH,
                cost_of_escalation=ErrorCost.LOW,
                confidence=0.75,
                reasons=("sensor timeout could hide a safety-relevant state",),
            ),
        )

        self.assertEqual(receipt.recommendation, Recommendation.NOTIFY)
        self.assertIn("without granting authority", receipt.judgment.rationale)

    def test_low_confidence_does_not_silence_serious_consequence(self) -> None:
        receipt = self.brain.process(
            self.event,
            evaluation_profile=EvaluationProfile(
                potential_consequence=Consequence.SERIOUS,
                confidence=0.3,
                reasons=("evidence is weak but the possible consequence is serious",),
            ),
        )

        self.assertEqual(receipt.recommendation, Recommendation.NOTIFY)

    def test_extreme_false_alarm_cost_can_hold_severe_claim_at_observe(self) -> None:
        receipt = self.brain.process(
            self.event,
            evaluation_profile=EvaluationProfile(
                potential_consequence=Consequence.SEVERE,
                cost_of_dismissal=ErrorCost.LOW,
                cost_of_escalation=ErrorCost.EXTREME,
                confidence=0.9,
                reasons=("escalation itself would carry exceptional cost",),
            ),
        )

        self.assertEqual(receipt.recommendation, Recommendation.OBSERVE)

    def test_invalid_profile_confidence_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.brain.process(
                self.event,
                evaluation_profile=EvaluationProfile(
                    confidence=1.2,
                    reasons=("invalid test profile",),
                ),
            )


if __name__ == "__main__":
    unittest.main()

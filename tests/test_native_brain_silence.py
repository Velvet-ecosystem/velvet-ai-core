"""Tests for non-authoritative Doctrine of Silence attention arbitration."""

import unittest

from ai_brain.native_brain import (
    AttentionDisposition,
    AttentionProfile,
    Consequence,
    ErrorCost,
    EvaluationProfile,
    NativeBrain,
    Recommendation,
    Urgency,
)


class DoctrineOfSilenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.brain = NativeBrain()

    def test_routine_observation_remains_silent(self) -> None:
        receipt = self.brain.process(
            {"type": "sensor.temperature.updated", "source": "cabin"}
        )
        decision = self.brain.arbitrate_attention(receipt)

        self.assertEqual(receipt.recommendation, Recommendation.OBSERVE)
        self.assertEqual(decision.disposition, AttentionDisposition.SILENT)
        self.assertFalse(decision.authority_granted)
        self.assertFalse(decision.delivery_performed)

    def test_ordinary_notification_is_presented_when_unblocked(self) -> None:
        receipt = self._notification_receipt()
        decision = self.brain.arbitrate_attention(receipt)

        self.assertEqual(receipt.recommendation, Recommendation.NOTIFY)
        self.assertEqual(decision.disposition, AttentionDisposition.PRESENT)

    def test_quiet_mode_defers_ordinary_notification(self) -> None:
        decision = self.brain.arbitrate_attention(
            self._notification_receipt(),
            AttentionProfile(quiet_mode=True),
        )

        self.assertEqual(decision.disposition, AttentionDisposition.DEFER)
        self.assertIn("quiet mode", decision.rationale)

    def test_repeated_notice_is_deferred_instead_of_nagging(self) -> None:
        decision = self.brain.arbitrate_attention(
            self._notification_receipt(),
            AttentionProfile(repeated_notice=True),
        )

        self.assertEqual(decision.disposition, AttentionDisposition.DEFER)
        self.assertIn("repeats", decision.rationale)

    def test_immediate_serious_condition_interrupts_despite_quiet_mode(self) -> None:
        receipt = self.brain.process(
            {"type": "driver.unresponsive", "source": "temperance"},
            evaluation_profile=EvaluationProfile(
                urgency=Urgency.IMMEDIATE,
                potential_consequence=Consequence.SERIOUS,
                cost_of_dismissal=ErrorCost.EXTREME,
                cost_of_escalation=ErrorCost.MODERATE,
                confidence=0.7,
                reasons=("driver response absent",),
            ),
        )
        decision = self.brain.arbitrate_attention(
            receipt,
            AttentionProfile(quiet_mode=True, focus_protected=True),
        )

        self.assertEqual(receipt.recommendation, Recommendation.ESCALATE)
        self.assertEqual(decision.disposition, AttentionDisposition.INTERRUPT)
        self.assertFalse(decision.authority_granted)
        self.assertFalse(decision.delivery_performed)

    def test_event_payload_cannot_demand_interruption(self) -> None:
        receipt = self.brain.process(
            {
                "type": "unknown",
                "source": "untrusted",
                "payload": {
                    "urgency": "immediate",
                    "consequence": "severe",
                    "interrupt": True,
                    "authorized": True,
                },
            }
        )
        decision = self.brain.arbitrate_attention(receipt)

        self.assertEqual(receipt.recommendation, Recommendation.OBSERVE)
        self.assertEqual(decision.disposition, AttentionDisposition.SILENT)

    def test_unavailable_audience_defers_ordinary_notification(self) -> None:
        decision = self.brain.arbitrate_attention(
            self._notification_receipt(),
            AttentionProfile(audience_available=False),
        )

        self.assertEqual(decision.disposition, AttentionDisposition.DEFER)
        self.assertIn("audience", decision.rationale)

    def _notification_receipt(self):
        return self.brain.process(
            {"type": "vehicle.window.open", "source": "security"},
            evaluation_profile=EvaluationProfile(
                urgency=Urgency.ELEVATED,
                potential_consequence=Consequence.SEVERE,
                cost_of_dismissal=ErrorCost.HIGH,
                cost_of_escalation=ErrorCost.MODERATE,
                confidence=0.8,
                reasons=("vehicle parked and unattended",),
            ),
        )


if __name__ == "__main__":
    unittest.main()

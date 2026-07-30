"""Tests for the deterministic Native Brain Sprint 1 spine."""

import unittest

from ai_brain.native_brain import NativeBrain
from ai_brain.native_brain.models import Importance, Recommendation


class NativeBrainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.brain = NativeBrain()

    def test_process_builds_contextual_receipt(self) -> None:
        receipt = self.brain.process(
            {
                "type": "vehicle.door.front_left.opened",
                "source": "door_sensor.front_left",
                "payload": {"open": True},
            },
            {
                "runtime_mode": "parked",
                "court_permissions": ("observe",),
                "presence": "owner",
                "active_scene": "home",
                "recent_events": ("owner.authenticated",),
                "active_organs": ("security",),
                "world_state": {"alarm_armed": False},
            },
        )

        understanding = receipt.judgment.evaluation.understanding
        self.assertEqual(
            understanding.observation.event_type,
            "vehicle.door.front_left.opened",
        )
        self.assertEqual(understanding.context.runtime_mode, "parked")
        self.assertEqual(understanding.context.presence, "owner")
        self.assertIn("runtime_mode=parked", understanding.summary)
        self.assertEqual(receipt.recommendation, Recommendation.OBSERVE)
        self.assertTrue(receipt.receipt_id)

    def test_unknown_event_uses_conservative_defaults(self) -> None:
        receipt = self.brain.process({})

        evaluation = receipt.judgment.evaluation
        observation = evaluation.understanding.observation
        context = evaluation.understanding.context

        self.assertEqual(observation.event_type, "unknown")
        self.assertEqual(observation.source, "unknown")
        self.assertEqual(context.runtime_mode, "unknown")
        self.assertEqual(context.presence, "unknown")
        self.assertEqual(evaluation.importance, Importance.ROUTINE)
        self.assertEqual(receipt.recommendation, Recommendation.OBSERVE)

    def test_receipts_are_unique(self) -> None:
        event = {"type": "sensor.heartbeat", "source": "seat.driver"}
        first = self.brain.process(event)
        second = self.brain.process(event)

        self.assertNotEqual(first.receipt_id, second.receipt_id)

    def test_brain_returns_recommendation_without_execution(self) -> None:
        receipt = self.brain.process(
            {"type": "vehicle.temperature.updated", "source": "engine"},
            {"court_permissions": ()},
        )

        self.assertEqual(receipt.recommendation, Recommendation.OBSERVE)
        self.assertEqual(
            receipt.judgment.rationale,
            "Sprint 1 defaults to observation without action.",
        )


if __name__ == "__main__":
    unittest.main()

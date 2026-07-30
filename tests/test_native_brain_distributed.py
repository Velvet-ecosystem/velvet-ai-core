"""Tests for Unified-Organ distributed reasoning coordination."""

import unittest

from ai_brain.native_brain import (
    CapabilityAdvertisement,
    DistributedReasoningCoordinator,
    HandoffDisposition,
    NativeBrain,
    ReasoningTask,
)


class DistributedReasoningTests(unittest.TestCase):
    def test_selects_lowest_load_healthy_capable_organ(self) -> None:
        task = ReasoningTask("task-1", "audio.fusion", "Fuse cabin microphones")
        advertisements = (
            CapabilityAdvertisement("Velour", ("audio.fusion",), 0.6),
            CapabilityAdvertisement("Nova", ("audio.fusion",), 0.2),
        )
        handoff = NativeBrain().offer_reasoning_task(task, advertisements)
        self.assertEqual(handoff.target_organ, "Nova")
        self.assertEqual(handoff.disposition, HandoffDisposition.OFFERED)
        self.assertFalse(handoff.authority_granted)
        self.assertFalse(handoff.execution_performed)

    def test_unavailable_or_unhealthy_organs_are_skipped(self) -> None:
        task = ReasoningTask("task-2", "security.review", "Review perimeter event")
        advertisements = (
            CapabilityAdvertisement("Sarah", ("security.review",), 0.1, healthy=False),
            CapabilityAdvertisement("Velour", ("security.review",), 0.2, available=False),
        )
        handoff = DistributedReasoningCoordinator().offer(task, advertisements)
        self.assertEqual(handoff.disposition, HandoffDisposition.ESCALATE)
        self.assertIsNone(handoff.target_organ)

    def test_overloaded_organ_may_refuse(self) -> None:
        task = ReasoningTask("task-3", "archive.search", "Search continuity records")
        handoff = DistributedReasoningCoordinator().refuse(
            task, "Velour", "Current load exceeds safe limit"
        )
        self.assertEqual(handoff.disposition, HandoffDisposition.REFUSED)
        self.assertFalse(handoff.authority_granted)

    def test_selection_is_deterministic_on_equal_load(self) -> None:
        task = ReasoningTask("task-4", "sensor.fusion", "Fuse seat observations")
        advertisements = (
            CapabilityAdvertisement("Temperance", ("sensor.fusion",), 0.3),
            CapabilityAdvertisement("Jade", ("sensor.fusion",), 0.3),
        )
        handoff = DistributedReasoningCoordinator().offer(task, advertisements)
        self.assertEqual(handoff.target_organ, "Jade")


if __name__ == "__main__":
    unittest.main()

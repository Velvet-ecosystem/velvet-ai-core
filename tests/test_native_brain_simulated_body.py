"""Tests for Native Brain's hardware-equivalent simulated-body layer."""

import unittest
from datetime import datetime, timezone

from ai_brain.native_brain import (
    BodyPracticeSkeleton,
    FakeOrganAdapter,
    FaultProfile,
    HardwareOrganAdapter,
    NativeBrain,
    OrganContract,
)


class SimulatedBodyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 31, 6, 0, tzinfo=timezone.utc)
        self.contract = OrganContract(
            organ_name="jade.cabin_temperature",
            event_type="cabin.temperature.observed",
            source="jade-temperature-adapter",
        )

    def test_hardware_and_fake_use_same_event_and_receipt_paths(self) -> None:
        receipts = []
        skeleton = BodyPracticeSkeleton(NativeBrain(), receipts.append)
        hardware = HardwareOrganAdapter(
            self.contract,
            lambda: {"temperature_c": 22.0},
            clock=lambda: self.now,
        )
        fake = FakeOrganAdapter.mirror(
            hardware,
            lambda: {"temperature_c": 23.0},
            clock=lambda: self.now,
        )

        hardware_cycle = skeleton.run(hardware)
        fake_cycle = skeleton.run(fake)

        self.assertEqual(len(receipts), 2)
        self.assertEqual(
            hardware_cycle.emission.record["event_type"],
            fake_cycle.emission.record["event_type"],
        )
        self.assertEqual(
            hardware_cycle.emission.record["source"],
            fake_cycle.emission.record["source"],
        )
        self.assertTrue(hardware_cycle.receipt_recorded)
        self.assertTrue(fake_cycle.receipt_recorded)
        self.assertEqual(
            hardware_cycle.receipt.judgment.evaluation.understanding.observation.payload[
                "_event_protocol"
            ]["origin"],
            "hardware",
        )
        self.assertEqual(
            fake_cycle.receipt.judgment.evaluation.understanding.observation.payload[
                "_event_protocol"
            ]["origin"],
            "simulation",
        )

    def test_faults_inject_delay_noise_impossible_value_and_stale_timestamp(self) -> None:
        delays = []
        fake = FakeOrganAdapter(
            self.contract,
            lambda: {
                "temperature_c": 20.0,
                "sensor": {"status": "ok"},
            },
            faults=FaultProfile(
                delay_seconds=0.25,
                stale_by_seconds=30.0,
                noise={"temperature_c": 2.0},
                impossible_values={"sensor.status": "molten"},
                seed=7,
            ),
            clock=lambda: self.now,
            sleeper=delays.append,
        )

        emission = fake.emit()

        self.assertEqual(delays, [0.25])
        self.assertFalse(emission.dropped)
        self.assertNotEqual(emission.record["payload"]["temperature_c"], 20.0)
        self.assertGreaterEqual(emission.record["payload"]["temperature_c"], 18.0)
        self.assertLessEqual(emission.record["payload"]["temperature_c"], 22.0)
        self.assertEqual(
            emission.record["payload"]["sensor"]["status"],
            "molten",
        )
        self.assertEqual(
            emission.record["timestamp"],
            "2026-07-31T05:59:30+00:00",
        )
        self.assertIn("fault injection: delay", emission.reasons)
        self.assertIn("fault injection: stale timestamp", emission.reasons)

    def test_dropout_never_enters_event_or_receipt_path(self) -> None:
        receipts = []
        skeleton = BodyPracticeSkeleton(NativeBrain(), receipts.append)
        fake = FakeOrganAdapter(
            self.contract,
            lambda: {"temperature_c": 20.0},
            faults=FaultProfile(dropout_rate=1.0, seed=1),
            clock=lambda: self.now,
        )

        cycle = skeleton.run(fake)

        self.assertTrue(cycle.dropped)
        self.assertEqual(receipts, [])
        self.assertIsNone(cycle.receipt)
        self.assertFalse(cycle.receipt_recorded)

    def test_impossible_authority_value_is_rejected_by_normal_event_boundary(self) -> None:
        skeleton = BodyPracticeSkeleton(NativeBrain())
        fake = FakeOrganAdapter(
            self.contract,
            lambda: {"temperature_c": 20.0},
            faults=FaultProfile(
                impossible_values={"executor_name": "forbidden-direct-actuator"}
            ),
            clock=lambda: self.now,
        )

        with self.assertRaises(ValueError):
            skeleton.run(fake)


if __name__ == "__main__":
    unittest.main()

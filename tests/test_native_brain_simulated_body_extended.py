"""Extended failure injection tests for the simulated body."""

import unittest
from datetime import datetime, timezone

from ai_brain.native_brain import (
    BodyPracticeSkeleton,
    EventProtocolError,
    FakeOrganAdapter,
    FaultProfile,
    NativeBrain,
    OrganContract,
)


class ExtendedSimulatedBodyTests(unittest.TestCase):
    def setUp(self):
        self.contract = OrganContract(
            organ_name="Jade",
            event_type="cabin.sensor.observed",
            source="cabin-sensor",
        )
        self.clock = lambda: datetime(2026, 7, 31, tzinfo=timezone.utc)

    def test_sudden_disconnect_and_recovery_are_stateful(self):
        adapter = FakeOrganAdapter(
            contract=self.contract,
            reader=lambda: {"temperature_c": 22.0},
            faults=FaultProfile(
                disconnect_on_attempt=2,
                recover_on_attempt=4,
            ),
            clock=self.clock,
        )

        first = adapter.emit()
        second = adapter.emit()
        third = adapter.emit()
        fourth = adapter.emit()

        self.assertFalse(first.dropped)
        self.assertTrue(second.dropped)
        self.assertTrue(third.dropped)
        self.assertFalse(fourth.dropped)
        self.assertIn("fault injection: recovery", fourth.reasons)

    def test_low_voltage_and_degraded_confidence_are_injected(self):
        adapter = FakeOrganAdapter(
            contract=self.contract,
            reader=lambda: {
                "power": {"voltage": 12.6},
                "sensor": {"confidence": 0.98},
            },
            faults=FaultProfile(
                low_voltage={"power.voltage": 9.4},
                degraded_confidence={"sensor.confidence": 0.25},
            ),
            clock=self.clock,
        )

        emission = adapter.emit()
        payload = emission.record["payload"]
        self.assertEqual(payload["power"]["voltage"], 9.4)
        self.assertEqual(payload["sensor"]["confidence"], 0.25)

    def test_malformed_payload_is_rejected_by_normal_event_protocol(self):
        adapter = FakeOrganAdapter(
            contract=self.contract,
            reader=lambda: {"temperature_c": 22.0},
            faults=FaultProfile(
                malformed_payload_enabled=True,
                malformed_payload=["not", "a", "mapping"],
            ),
            clock=self.clock,
        )
        skeleton = BodyPracticeSkeleton(NativeBrain())

        with self.assertRaises(EventProtocolError):
            skeleton.run(adapter)

    def test_recovery_requires_a_later_disconnect_attempt(self):
        with self.assertRaises(ValueError):
            FaultProfile(
                disconnect_on_attempt=3,
                recover_on_attempt=3,
            )


if __name__ == "__main__":
    unittest.main()

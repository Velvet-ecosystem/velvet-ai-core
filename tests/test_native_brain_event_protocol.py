"""Tests for the Native Brain Event Protocol boundary."""

import unittest

from ai_brain.native_brain import EventProtocolAdapter, EventProtocolError, NativeBrain


class EventProtocolAdapterTests(unittest.TestCase):
    def test_normalizes_observation_event(self) -> None:
        adapter = EventProtocolAdapter()
        event = adapter.normalize(
            {
                "event_id": "evt-1",
                "event_type": "DECODED_CAN_SIGNAL_OBSERVED",
                "source": "velvet-vehicle-can",
                "schema_version": "1.0",
                "payload": {"signal": "engine_rpm", "value": 812},
            }
        )

        self.assertEqual(event["type"], "DECODED_CAN_SIGNAL_OBSERVED")
        self.assertEqual(event["source"], "velvet-vehicle-can")
        self.assertEqual(event["payload"]["signal"], "engine_rpm")
        self.assertEqual(event["payload"]["_event_protocol"]["event_id"], "evt-1")

    def test_rejects_authority_bearing_observation_payload(self) -> None:
        adapter = EventProtocolAdapter()

        with self.assertRaises(EventProtocolError):
            adapter.normalize(
                {
                    "event_type": "vehicle.door.observed",
                    "source": "door-sensor",
                    "payload": {"state": "open", "executor_name": "door-lock"},
                }
            )

    def test_brain_processes_protocol_event_without_execution(self) -> None:
        brain = NativeBrain()
        receipt = brain.process_protocol_event(
            {
                "event_type": "vehicle.door.front_left.opened",
                "source": "cabin-sensor",
                "payload": {"state": "open"},
            },
            {"runtime_mode": "parked", "presence": "owner"},
        )

        self.assertEqual(receipt.judgment.evaluation.understanding.observation.event_type,
                         "vehicle.door.front_left.opened")
        self.assertEqual(receipt.recommendation.value, "observe")

    def test_requires_event_type_source_and_mapping_payload(self) -> None:
        adapter = EventProtocolAdapter()

        for record in (
            {"source": "sensor", "payload": {}},
            {"event_type": "sensor.reading", "payload": {}},
            {"event_type": "sensor.reading", "source": "sensor", "payload": []},
        ):
            with self.subTest(record=record):
                with self.assertRaises(EventProtocolError):
                    adapter.normalize(record)


if __name__ == "__main__":
    unittest.main()

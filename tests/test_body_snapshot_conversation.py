import unittest

from velvet.core.native_brain.body_snapshot_conversation import (
    BODY_STATE_SNAPSHOT_SCHEMA,
    BodySnapshotConversationResolver,
    validate_body_snapshot,
)
from velvet.core.native_brain.conversation_ingress import (
    ConversationMeaningKind,
    ConversationWorkRequest,
)


def request(text, *, requires_authority_check=False):
    return ConversationWorkRequest(
        conversation_id="conversation-test",
        turn_id="conversation-test:1",
        turn_number=1,
        text=text,
        modality="text",
        audience="owner",
        act="question",
        strategy="answer",
        requires_authority_check=requires_authority_check,
        may_speak=True,
    )


def sensor_record(
    sensor_type,
    data,
    *,
    module_id,
    timestamp=100.0,
    confidence=0.95,
    stale_after_ms=5000,
    receipt_id="receipt-1",
    raw_reference="local:test",
):
    return {
        "event_id": receipt_id,
        "event_type": "SENSOR_PACKET_OBSERVED",
        "source": module_id,
        "family": "sensor",
        "schema_version": "1.0",
        "timestamp": timestamp,
        "node_id": "founder-up2",
        "organ_name": "Velvet",
        "payload": {
            "module_id": module_id,
            "node_id": "founder-up2",
            "owning_handmaiden": "Velvet",
            "timestamp": timestamp,
            "monotonic_time": 50.0,
            "sensor_type": sensor_type,
            "interface_type": "test",
            "health_state": "ONLINE",
            "confidence": confidence,
            "payload": dict(data),
            "receipt_id": receipt_id,
            "source_clock": "device",
            "stale_after_ms": stale_after_ms,
            "calibration_version": "test-v1",
            "degraded_reason": None,
            "raw_reference": raw_reference,
        },
    }


def snapshot(records):
    return {
        "schema": BODY_STATE_SNAPSHOT_SCHEMA,
        "captured_at": 100.0,
        "generated_monotonic": 50.0,
        "record_count": len(records),
        "sensor_count": len(records),
        "health_event_count": 0,
        "records": list(records),
        "receipt_ids": [record["payload"]["receipt_id"] for record in records],
        "mode": "display-only",
        "read_only": True,
        "authority": "none",
        "actuation_granted": False,
        "actuation_performed": False,
    }


class BodySnapshotConversationResolverTests(unittest.TestCase):
    def test_cabin_temperature_is_grounded_from_environmental_record(self):
        document = snapshot(
            [
                sensor_record(
                    "environmental_conditions",
                    {
                        "cabin_temperature_c": 21.5,
                        "outside_temperature_c": 12.0,
                        "ambient_light_lux": 44.0,
                        "relative_humidity_percent": 38.0,
                    },
                    module_id="environmental-sensors-main",
                )
            ]
        )
        resolver = BodySnapshotConversationResolver(lambda: document, wall_clock=lambda: 101.0)

        meaning = resolver(request("What is the cabin temperature?"))

        self.assertEqual(meaning.response_kind, ConversationMeaningKind.FACT)
        self.assertEqual(meaning.fact_id, "cabin.temperature")
        self.assertEqual(meaning.value, 21.5)
        self.assertEqual(meaning.unit, "C")
        self.assertEqual(meaning.confidence, 0.95)
        self.assertIn("receipt:receipt-1", meaning.source_refs)
        self.assertNotIn("stale", meaning.qualifiers)

    def test_stale_environmental_fact_is_explicitly_qualified(self):
        document = snapshot(
            [
                sensor_record(
                    "environmental_conditions",
                    {
                        "cabin_temperature_c": 20.0,
                        "outside_temperature_c": 8.0,
                        "ambient_light_lux": 10.0,
                        "relative_humidity_percent": 50.0,
                    },
                    module_id="environmental-sensors-main",
                    timestamp=100.0,
                    stale_after_ms=5000,
                )
            ]
        )
        resolver = BodySnapshotConversationResolver(lambda: document, wall_clock=lambda: 106.0)

        meaning = resolver(request("How cold is it in here?"))

        self.assertEqual(meaning.fact_id, "cabin.temperature")
        self.assertIn("stale", meaning.qualifiers)

    def test_ignition_state_does_not_claim_engine_running(self):
        document = snapshot(
            [
                sensor_record(
                    "vehicle_power_state",
                    {
                        "voltage_v": 13.8,
                        "ignition_on": True,
                        "ignition_state": "ON",
                        "voltage_band": "CHARGING",
                        "engine_running_inferred": False,
                    },
                    module_id="vehicle-power-main",
                    stale_after_ms=3000,
                )
            ]
        )
        resolver = BodySnapshotConversationResolver(lambda: document, wall_clock=lambda: 101.0)

        ignition = resolver(request("Is the ignition on?"))
        engine = resolver(request("Is the engine running?"))

        self.assertEqual(ignition.response_kind, ConversationMeaningKind.FACT)
        self.assertEqual(ignition.fact_id, "ignition.state")
        self.assertEqual(ignition.value, "ON")
        self.assertEqual(engine.response_kind, ConversationMeaningKind.UNAVAILABLE)

    def test_vehicle_speed_uses_only_valid_gnss_fix(self):
        valid = snapshot(
            [
                sensor_record(
                    "gnss_fix",
                    {"has_fix": True, "speed_kmh": 82.4},
                    module_id="gnss-main",
                    confidence=0.88,
                    stale_after_ms=3000,
                )
            ]
        )
        invalid = snapshot(
            [
                sensor_record(
                    "gnss_fix",
                    {"has_fix": False},
                    module_id="gnss-main",
                    confidence=0.2,
                    stale_after_ms=3000,
                )
            ]
        )

        good = BodySnapshotConversationResolver(lambda: valid, wall_clock=lambda: 101.0)(
            request("How fast are we going?")
        )
        missing = BodySnapshotConversationResolver(lambda: invalid, wall_clock=lambda: 101.0)(
            request("What is the current speed?")
        )

        self.assertEqual(good.fact_id, "vehicle.speed")
        self.assertEqual(good.value, 82.4)
        self.assertEqual(good.unit, "km/h")
        self.assertEqual(missing.response_kind, ConversationMeaningKind.UNAVAILABLE)
        self.assertIn("navigation-fix-unavailable", missing.qualifiers)

    def test_action_turn_requests_runtime_authority_without_reading_snapshot(self):
        def should_not_run():
            raise AssertionError("snapshot provider should not run for action turn")

        resolver = BodySnapshotConversationResolver(should_not_run)
        meaning = resolver(request("Open the window", requires_authority_check=True))

        self.assertEqual(meaning.response_kind, ConversationMeaningKind.AUTHORITY_REQUIRED)
        self.assertEqual(meaning.authority, "none")
        self.assertFalse(meaning.grants_authority)
        self.assertFalse(meaning.grants_execution)
        self.assertFalse(meaning.grants_actuation)

    def test_unknown_fact_returns_unavailable_without_inference(self):
        resolver = BodySnapshotConversationResolver(lambda: snapshot([]), wall_clock=lambda: 101.0)
        meaning = resolver(request("Is the engine healthy?"))
        self.assertEqual(meaning.response_kind, ConversationMeaningKind.UNAVAILABLE)

    def test_snapshot_posture_must_remain_read_only_and_no_authority(self):
        document = snapshot([])
        validate_body_snapshot(document)

        unsafe = dict(document)
        unsafe["authority"] = "owner"
        with self.assertRaisesRegex(ValueError, "cannot carry authority"):
            validate_body_snapshot(unsafe)

        unsafe = dict(document)
        unsafe["actuation_granted"] = True
        with self.assertRaisesRegex(ValueError, "cannot grant actuation"):
            validate_body_snapshot(unsafe)


if __name__ == "__main__":
    unittest.main()

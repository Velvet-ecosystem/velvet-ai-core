import unittest

from velvet.core.ghost_can import (
    GHOST_CAN_ACTION,
    GHOST_CAN_EVENT_TYPE,
    GHOST_CAN_TARGET,
    build_ghost_can_proposal,
    evaluate_ghost_can_proposal,
    ghost_can_memory_record,
    summarize_ghost_can_observation,
    validate_ghost_can_observation,
)
from velvet.core.schemas.topics import Topics


def ghost_payload():
    return {
        "event_type": GHOST_CAN_EVENT_TYPE,
        "vehicle_profile": "Jarred Tiburon",
        "source": "test fixture",
        "read_only": True,
        "synthetic_fixture": True,
        "synthetic": True,
        "physical_bus_opened": False,
        "hardware_bus_opened": False,
        "can_transmission_attempted": False,
        "can_transmission_performed": False,
        "actuation_granted": False,
        "actuation_performed": False,
        "authority_granted": False,
        "signals": {
            "vehicle_speed": {"value": 0, "unit": "km/h", "confidence": 1.0},
            "engine_rpm": {"value": 0, "unit": "rpm", "confidence": 0.96},
            "o2_fault": {"value": "simulated", "unit": "", "confidence": 0.87},
        },
    }


class GhostCanCoreTests(unittest.TestCase):
    def test_validate_accepts_synthetic_read_only_payload(self):
        out = validate_ghost_can_observation(ghost_payload())
        self.assertEqual(out["event_type"], GHOST_CAN_EVENT_TYPE)
        self.assertIs(out["read_only"], True)

    def test_validate_rejects_missing_safety_flag(self):
        payload = ghost_payload()
        payload["can_transmission_attempted"] = True
        with self.assertRaisesRegex(ValueError, "can_transmission_attempted"):
            validate_ghost_can_observation(payload)

    def test_validate_rejects_authority_keys_anywhere(self):
        payload = ghost_payload()
        payload["signals"]["vehicle_speed"]["command"] = "write frame"
        with self.assertRaisesRegex(ValueError, "forbidden authority key"):
            validate_ghost_can_observation(payload)

    def test_proposal_creates_descriptive_intent_only(self):
        intent = build_ghost_can_proposal(
            ghost_payload(), actor="velvet-test"
        ).to_intent()
        self.assertEqual(intent.action, GHOST_CAN_ACTION)
        self.assertEqual(intent.target, GHOST_CAN_TARGET)
        self.assertIs(intent.requires_physical_presence, False)
        self.assertIs(intent.privilege_elevation, False)
        self.assertNotIn("executor", intent.parameters)

    def test_court_authorizes_description_not_physical_action(self):
        receipt = evaluate_ghost_can_proposal(
            build_ghost_can_proposal(ghost_payload())
        )
        self.assertIs(receipt.authorized, True)
        self.assertEqual(receipt.intent_action, GHOST_CAN_ACTION)
        self.assertIsNone(receipt.executor)

    def test_memory_record_preserves_observation_boundary(self):
        data = ghost_can_memory_record(
            ghost_payload(), receipt_id="r-demo"
        ).to_dict()
        self.assertEqual(data["kind"], "observation")
        self.assertEqual(data["authority_status"], "observation_only")
        self.assertEqual(
            data["payload"]["authority_boundary"],
            "observation_only_no_physical_authority",
        )

    def test_summary_names_no_authority(self):
        summary = summarize_ghost_can_observation(ghost_payload())
        self.assertIn("Jarred Tiburon", summary)
        self.assertIn("no physical bus opened", summary)
        self.assertIn("no authority granted", summary)

    def test_topics_exports_ghost_can_event_name(self):
        self.assertEqual(
            Topics.VEHICLE_CAN_GHOST_OBSERVATION,
            GHOST_CAN_EVENT_TYPE,
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from velvet.core.ghost_can import GHOST_CAN_EVENT_TYPE
from velvet.core.native_brain import (
    BrainstemRouter,
    LLMPolishRequest,
    NativeBrainSafetyError,
    NativeBrainState,
    OptionalLLMAdapter,
    RubyStem,
    VelourStem,
    run_native_brain_ghost_loop,
    validate_no_authority_payload,
)


def ghost_payload():
    return {
        "event_type": GHOST_CAN_EVENT_TYPE,
        "vehicle_profile": "Jarred Tiburon",
        "source": "native brain test fixture",
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
            "ignition_state": {"value": "off", "unit": "", "confidence": 1.0},
            "o2_fault": {"value": "simulated", "unit": "", "confidence": 0.87},
        },
    }


class NativeBrainV0Tests(unittest.TestCase):
    def test_native_state_updates_from_ghost_observation(self):
        state = NativeBrainState()
        state.update_from_ghost_observation(ghost_payload())
        self.assertEqual(state.vehicle_state["vehicle_speed"], 0)
        self.assertEqual(state.vehicle_state["engine_rpm"], 0)
        self.assertEqual(state.vehicle_state["ignition_state"], "off")
        self.assertEqual(state.known_faults["o2_fault"], "simulated")
        self.assertIn(GHOST_CAN_EVENT_TYPE, state.recent_events)

    def test_native_safety_requires_read_only_flags(self):
        payload = ghost_payload()
        payload["read_only"] = False
        with self.assertRaisesRegex(NativeBrainSafetyError, "read_only"):
            validate_no_authority_payload(payload)

    def test_native_safety_blocks_vehicle_authority_words_anywhere(self):
        payload = ghost_payload()
        payload["signals"]["engine_rpm"]["start_vehicle"] = True
        with self.assertRaisesRegex(NativeBrainSafetyError, "forbidden authority key"):
            validate_no_authority_payload(payload)

    def test_brainstem_marks_safe_ghost_observation_low_priority(self):
        decision = BrainstemRouter().assess(ghost_payload())
        self.assertEqual(decision.priority, "low")
        self.assertFalse(decision.blocked)

    def test_brainstem_blocks_authority_payloads(self):
        payload = ghost_payload()
        payload["executor"] = "sneaky-body-lane"
        decision = BrainstemRouter().assess(payload)
        self.assertEqual(decision.priority, "critical")
        self.assertTrue(decision.blocked)

    def test_ruby_and_velour_interpret_first_loop_domains(self):
        payload = ghost_payload()
        ruby = RubyStem().interpret(payload)
        velour = VelourStem().interpret(payload)
        self.assertTrue(ruby.domain_match)
        self.assertFalse(ruby.authority_requested)
        self.assertIn("o2_fault=simulated", ruby.summary)
        self.assertEqual(ruby.handoff, ["velour"])
        self.assertTrue(velour.domain_match)
        self.assertTrue(velour.suggested_memory["continuity_candidate"])
        self.assertFalse(velour.authority_requested)

    def test_native_brain_ghost_loop_produces_no_llm_response(self):
        data = run_native_brain_ghost_loop(ghost_payload()).to_dict()
        self.assertEqual(data["kind"], "native_brain_response")
        self.assertEqual(data["event_type"], GHOST_CAN_EVENT_TYPE)
        self.assertEqual(data["attention"]["priority"], "low")
        self.assertEqual(data["stems_consulted"], ["ruby", "velour"])
        self.assertEqual(data["memory_note"]["kind"], "observation_only")
        self.assertFalse(data["authority"]["requested"])
        self.assertFalse(data["authority"]["granted"])
        self.assertFalse(data["authority"]["hardware_touched"])
        self.assertIn("No authority requested", data["response"])

    def test_llm_adapter_is_optional_and_cannot_add_authority_claims(self):
        adapter = OptionalLLMAdapter()
        request = LLMPolishRequest("Jarred Tiburon observed. No authority requested.")
        self.assertEqual(adapter.polish(request), request.skeleton)
        with self.assertRaisesRegex(NativeBrainSafetyError, "authority boundary"):
            adapter.polish(request, lambda text: text + " Authority granted.")


if __name__ == "__main__":
    unittest.main()

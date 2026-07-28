import pytest

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


def test_native_state_updates_from_ghost_observation():
    state = NativeBrainState()
    state.update_from_ghost_observation(ghost_payload())
    assert state.vehicle_state["vehicle_speed"] == 0
    assert state.vehicle_state["engine_rpm"] == 0
    assert state.vehicle_state["ignition_state"] == "off"
    assert state.known_faults["o2_fault"] == "simulated"
    assert GHOST_CAN_EVENT_TYPE in state.recent_events


def test_native_safety_requires_read_only_flags():
    payload = ghost_payload()
    payload["read_only"] = False
    with pytest.raises(NativeBrainSafetyError, match="read_only"):
        validate_no_authority_payload(payload)


def test_native_safety_blocks_vehicle_authority_words_anywhere():
    payload = ghost_payload()
    payload["signals"]["engine_rpm"]["start_vehicle"] = True
    with pytest.raises(NativeBrainSafetyError, match="forbidden authority key"):
        validate_no_authority_payload(payload)


def test_brainstem_marks_safe_ghost_observation_low_priority():
    decision = BrainstemRouter().assess(ghost_payload())
    assert decision.priority == "low"
    assert decision.blocked is False


def test_brainstem_blocks_authority_payloads():
    payload = ghost_payload()
    payload["executor"] = "sneaky-body-lane"
    decision = BrainstemRouter().assess(payload)
    assert decision.priority == "critical"
    assert decision.blocked is True


def test_ruby_and_velour_interpret_first_loop_domains():
    payload = ghost_payload()
    ruby = RubyStem().interpret(payload)
    velour = VelourStem().interpret(payload)
    assert ruby.domain_match is True
    assert ruby.authority_requested is False
    assert "o2_fault=simulated" in ruby.summary
    assert ruby.handoff == ["velour"]
    assert velour.domain_match is True
    assert velour.suggested_memory["continuity_candidate"] is True
    assert velour.authority_requested is False


def test_native_brain_ghost_loop_produces_no_llm_response():
    data = run_native_brain_ghost_loop(ghost_payload()).to_dict()
    assert data["kind"] == "native_brain_response"
    assert data["event_type"] == GHOST_CAN_EVENT_TYPE
    assert data["attention"]["priority"] == "low"
    assert data["stems_consulted"] == ["ruby", "velour"]
    assert data["memory_note"]["kind"] == "observation_only"
    assert data["authority"]["requested"] is False
    assert data["authority"]["granted"] is False
    assert data["authority"]["hardware_touched"] is False
    assert "No authority requested" in data["response"]


def test_llm_adapter_is_optional_and_cannot_add_authority_claims():
    adapter = OptionalLLMAdapter()
    request = LLMPolishRequest("Jarred Tiburon observed. No authority requested.")
    assert adapter.polish(request) == request.skeleton
    with pytest.raises(NativeBrainSafetyError, match="authority boundary"):
        adapter.polish(request, lambda text: text + " Authority granted.")

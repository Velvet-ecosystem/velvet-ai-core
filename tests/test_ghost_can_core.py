import pytest

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


def test_validate_accepts_synthetic_read_only_payload():
    out = validate_ghost_can_observation(ghost_payload())
    assert out["event_type"] == GHOST_CAN_EVENT_TYPE
    assert out["read_only"] is True


def test_validate_rejects_missing_safety_flag():
    payload = ghost_payload(); payload["can_transmission_attempted"] = True
    with pytest.raises(ValueError, match="can_transmission_attempted"):
        validate_ghost_can_observation(payload)


def test_validate_rejects_authority_keys_anywhere():
    payload = ghost_payload(); payload["signals"]["vehicle_speed"]["command"] = "write frame"
    with pytest.raises(ValueError, match="forbidden authority key"):
        validate_ghost_can_observation(payload)


def test_proposal_creates_descriptive_intent_only():
    intent = build_ghost_can_proposal(ghost_payload(), actor="velvet-test").to_intent()
    assert intent.action == GHOST_CAN_ACTION
    assert intent.target == GHOST_CAN_TARGET
    assert intent.requires_physical_presence is False
    assert intent.privilege_elevation is False
    assert "executor" not in intent.parameters


def test_court_authorizes_description_not_physical_action():
    receipt = evaluate_ghost_can_proposal(build_ghost_can_proposal(ghost_payload()))
    assert receipt.authorized is True
    assert receipt.intent_action == GHOST_CAN_ACTION
    assert receipt.executor is None


def test_memory_record_preserves_observation_boundary():
    data = ghost_can_memory_record(ghost_payload(), receipt_id="r-demo").to_dict()
    assert data["kind"] == "observation"
    assert data["authority_status"] == "observation_only"
    assert data["payload"]["authority_boundary"] == "observation_only_no_physical_authority"


def test_summary_names_no_authority():
    summary = summarize_ghost_can_observation(ghost_payload())
    assert "Jarred Tiburon" in summary
    assert "no physical bus opened" in summary
    assert "no authority granted" in summary


def test_topics_exports_ghost_can_event_name():
    assert Topics.VEHICLE_CAN_GHOST_OBSERVATION == GHOST_CAN_EVENT_TYPE

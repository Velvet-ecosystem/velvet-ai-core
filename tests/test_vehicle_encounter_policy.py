import pytest

from velvet_ai_core.vehicle_encounter_policy import (
    EncounterClass,
    VehicleEncounterPolicy,
)


def test_emergency_services_get_longer_but_bounded_same_trip_retention():
    emergency = VehicleEncounterPolicy.decision(EncounterClass.EMERGENCY_SERVICE)
    ordinary = VehicleEncounterPolicy.decision(EncounterClass.ORDINARY_VEHICLE)

    assert emergency.retention_seconds > ordinary.retention_seconds
    assert emergency.retention_seconds == 6 * 60 * 60
    assert emergency.safety_priority == "high"
    assert emergency.allow_cross_session_link is False
    assert emergency.local_only is True


def test_ordinary_vehicle_recognition_is_short_lived_and_low_priority():
    decision = VehicleEncounterPolicy.decision(EncounterClass.ORDINARY_VEHICLE)

    assert decision.retention_seconds == 15 * 60
    assert decision.safety_priority == "low"
    assert decision.purpose == "short-lived immediate traffic context only"


def test_passive_recognition_never_creates_persistent_identity():
    for encounter_class in EncounterClass:
        decision = VehicleEncounterPolicy.decision(encounter_class)
        assert decision.allow_persistent_identifier is False
        assert decision.allow_external_identity_enrichment is False
        assert decision.allow_plate_as_persistent_key is False
        assert decision.allow_cross_session_link is False


def test_retention_requests_are_clamped_to_policy_maximum():
    assert VehicleEncounterPolicy.clamp_retention(
        EncounterClass.ORDINARY_VEHICLE,
        24 * 60 * 60,
    ) == 15 * 60

    assert VehicleEncounterPolicy.clamp_retention(
        EncounterClass.EMERGENCY_SERVICE,
        24 * 60 * 60,
    ) == 6 * 60 * 60


def test_negative_retention_request_fails_closed():
    with pytest.raises(ValueError):
        VehicleEncounterPolicy.clamp_retention(
            EncounterClass.ORDINARY_VEHICLE,
            -1,
        )

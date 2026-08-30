import unittest

from velvet_ai_core.vehicle_encounter_policy import (
    EncounterClass,
    VehicleEncounterPolicy,
)


class VehicleEncounterPolicyTests(unittest.TestCase):
    def test_emergency_services_get_longer_but_bounded_same_trip_retention(self):
        emergency = VehicleEncounterPolicy.decision(EncounterClass.EMERGENCY_SERVICE)
        ordinary = VehicleEncounterPolicy.decision(EncounterClass.ORDINARY_VEHICLE)

        self.assertGreater(emergency.retention_seconds, ordinary.retention_seconds)
        self.assertEqual(emergency.retention_seconds, 6 * 60 * 60)
        self.assertEqual(emergency.safety_priority, "high")
        self.assertFalse(emergency.allow_cross_session_link)
        self.assertTrue(emergency.local_only)

    def test_ordinary_vehicle_recognition_is_short_lived_and_low_priority(self):
        decision = VehicleEncounterPolicy.decision(EncounterClass.ORDINARY_VEHICLE)

        self.assertEqual(decision.retention_seconds, 15 * 60)
        self.assertEqual(decision.safety_priority, "low")
        self.assertEqual(decision.purpose, "short-lived immediate traffic context only")

    def test_passive_recognition_never_creates_persistent_identity(self):
        for encounter_class in EncounterClass:
            decision = VehicleEncounterPolicy.decision(encounter_class)
            self.assertFalse(decision.allow_persistent_identifier)
            self.assertFalse(decision.allow_external_identity_enrichment)
            self.assertFalse(decision.allow_plate_as_persistent_key)
            self.assertFalse(decision.allow_cross_session_link)

    def test_retention_requests_are_clamped_to_policy_maximum(self):
        self.assertEqual(
            VehicleEncounterPolicy.clamp_retention(
                EncounterClass.ORDINARY_VEHICLE,
                24 * 60 * 60,
            ),
            15 * 60,
        )
        self.assertEqual(
            VehicleEncounterPolicy.clamp_retention(
                EncounterClass.EMERGENCY_SERVICE,
                24 * 60 * 60,
            ),
            6 * 60 * 60,
        )

    def test_negative_retention_request_fails_closed(self):
        with self.assertRaises(ValueError):
            VehicleEncounterPolicy.clamp_retention(
                EncounterClass.ORDINARY_VEHICLE,
                -1,
            )


if __name__ == "__main__":
    unittest.main()

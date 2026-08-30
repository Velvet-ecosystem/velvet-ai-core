"""Privacy-first policy for passive recognition of nearby vehicles.

This module governs *recognition continuity*, not sensing, identity, communications,
or physical action. It deliberately privileges emergency-service safety use cases
while keeping ordinary vehicle recognition short-lived and non-profile-building.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EncounterClass(str, Enum):
    EMERGENCY_SERVICE = "emergency_service"
    ORDINARY_VEHICLE = "ordinary_vehicle"


@dataclass(frozen=True)
class EncounterPolicyDecision:
    encounter_class: EncounterClass
    retention_seconds: int
    safety_priority: str
    allow_cross_session_link: bool
    allow_persistent_identifier: bool
    allow_external_identity_enrichment: bool
    allow_plate_as_persistent_key: bool
    local_only: bool
    purpose: str


class VehicleEncounterPolicy:
    """Fail-closed retention and privacy policy for passive vehicle recognition."""

    ORDINARY_RETENTION_SECONDS = 15 * 60
    EMERGENCY_RETENTION_SECONDS = 6 * 60 * 60

    @classmethod
    def decision(cls, encounter_class: EncounterClass) -> EncounterPolicyDecision:
        if encounter_class is EncounterClass.EMERGENCY_SERVICE:
            return EncounterPolicyDecision(
                encounter_class=encounter_class,
                retention_seconds=cls.EMERGENCY_RETENTION_SECONDS,
                safety_priority="high",
                allow_cross_session_link=False,
                allow_persistent_identifier=False,
                allow_external_identity_enrichment=False,
                allow_plate_as_persistent_key=False,
                local_only=True,
                purpose="same-trip emergency-service safety continuity",
            )

        if encounter_class is EncounterClass.ORDINARY_VEHICLE:
            return EncounterPolicyDecision(
                encounter_class=encounter_class,
                retention_seconds=cls.ORDINARY_RETENTION_SECONDS,
                safety_priority="low",
                allow_cross_session_link=False,
                allow_persistent_identifier=False,
                allow_external_identity_enrichment=False,
                allow_plate_as_persistent_key=False,
                local_only=True,
                purpose="short-lived immediate traffic context only",
            )

        raise ValueError("unsupported encounter class")

    @classmethod
    def clamp_retention(cls, encounter_class: EncounterClass, requested_seconds: int) -> int:
        """Bound retention to the maximum allowed for the encounter class."""
        if requested_seconds < 0:
            raise ValueError("requested_seconds must be non-negative")
        return min(requested_seconds, cls.decision(encounter_class).retention_seconds)

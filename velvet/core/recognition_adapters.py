"""Hardware-facing recognition adapter contracts.

Adapters normalize device-specific readings into RecognitionObservation objects.
They do not fuse identity, grant trust, authorize capabilities, or execute action.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional
from uuid import uuid4

from .recognition_evidence import RecognitionModality, RecognitionObservation


class AdapterHealth(str, Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class AdapterContext:
    candidate_entity_id: str
    observed_at: float
    frame_id: Optional[str] = None
    location_id: Optional[str] = None
    body_position: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.candidate_entity_id.strip():
            raise ValueError("candidate_entity_id is required")
        if self.observed_at < 0:
            raise ValueError("observed_at must be non-negative")


@dataclass(frozen=True)
class AdapterReading:
    confidence: float
    receipt_id: str
    details: Mapping[str, Any] = field(default_factory=dict)
    raw_reference: Optional[str] = None
    trusted_credential: bool = False
    simulated: bool = False
    health: AdapterHealth = AdapterHealth.ONLINE

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if not self.receipt_id.strip():
            raise ValueError("receipt_id is required")
        if not isinstance(self.details, Mapping):
            raise ValueError("details must be a mapping")
        if not isinstance(self.health, AdapterHealth):
            object.__setattr__(self, "health", AdapterHealth(self.health))


class RecognitionAdapter(ABC):
    """Normalize one hardware or simulated reading into bounded evidence."""

    modality: RecognitionModality = RecognitionModality.UNKNOWN

    def __init__(self, module_id: str, node_id: str) -> None:
        if not module_id.strip() or not node_id.strip():
            raise ValueError("module_id and node_id are required")
        self.module_id = module_id
        self.node_id = node_id

    @abstractmethod
    def read(self, context: AdapterContext) -> AdapterReading:
        """Read one device sample without making an identity decision."""

    def observe(self, context: AdapterContext) -> RecognitionObservation:
        reading = self.read(context)
        if reading.health == AdapterHealth.FAILED:
            raise RuntimeError("adapter reading failed")
        details = dict(reading.details)
        details["adapter_health"] = reading.health.value
        return RecognitionObservation(
            observation_id=str(uuid4()),
            candidate_entity_id=context.candidate_entity_id,
            modality=self.modality,
            source_module_id=self.module_id,
            source_node_id=self.node_id,
            observed_at=float(context.observed_at),
            confidence=float(reading.confidence),
            receipt_id=reading.receipt_id,
            frame_id=context.frame_id,
            location_id=context.location_id,
            body_position=context.body_position,
            raw_reference=reading.raw_reference,
            details=details,
            trusted_credential=bool(reading.trusted_credential),
            simulated=bool(reading.simulated),
        )


class CameraRecognitionAdapter(RecognitionAdapter):
    modality = RecognitionModality.IMAGE


class VoiceRecognitionAdapter(RecognitionAdapter):
    modality = RecognitionModality.VOICE


class NfcRecognitionAdapter(RecognitionAdapter):
    modality = RecognitionModality.NFC


class SeatPresenceRecognitionAdapter(RecognitionAdapter):
    modality = RecognitionModality.BEHAVIOR

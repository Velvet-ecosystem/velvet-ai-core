"""End-to-end simulated recognition bench path for Native Brain.

The bench uses the same recognition, identity, Event Protocol, and context
contracts intended for hardware adapters. It produces descriptive evidence only
and cannot authorize capabilities or execute physical action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple
from uuid import uuid4

from velvet.core.identity_transitions import (
    IdentityTransitionEngine,
    IdentityTransitionResult,
)
from velvet.core.recognition_evidence import (
    RecognitionEvidenceFusion,
    RecognitionFusion,
    RecognitionModality,
    RecognitionObservation,
)
from velvet.core.schemas.world_model import EntityIdentity
from velvet.core.world_event_bridge import WorldEventBridge, WorldEventEnvelope

from .world_context import ContextFact, NativeBrainWorldContextProjector


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


@dataclass(frozen=True)
class SimulatedRecognitionScenario:
    candidate_entity_id: str
    observed_at: float
    frame_id: str = "vehicle-cabin"
    location_id: str = "driver-zone"
    body_position: str = "driver-seat"
    face_confidence: float = 0.91
    voice_confidence: float = 0.88
    nfc_confidence: float = 1.0
    seat_confidence: float = 0.97
    include_face: bool = True
    include_voice: bool = True
    include_nfc: bool = True
    include_seat: bool = True
    trusted_nfc: bool = True
    observations_simulated: bool = True
    conflicting_seat_position: bool = False

    def __post_init__(self) -> None:
        for name in (
            "candidate_entity_id",
            "frame_id",
            "location_id",
            "body_position",
        ):
            _require_text(name, getattr(self, name))
        if self.observed_at < 0:
            raise ValueError("observed_at must be non-negative")
        for name in (
            "face_confidence",
            "voice_confidence",
            "nfc_confidence",
            "seat_confidence",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError("%s must be between 0.0 and 1.0" % name)


@dataclass(frozen=True)
class RecognitionBenchResult:
    observations: Tuple[RecognitionObservation, ...]
    fusion: RecognitionFusion
    identity_result: IdentityTransitionResult
    recognition_event: WorldEventEnvelope
    identity_event: WorldEventEnvelope
    recognition_fact: ContextFact
    identity_fact: ContextFact
    authority_granted: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        if self.authority_granted or self.execution_performed:
            raise ValueError("recognition bench results cannot claim authority")


class SimulatedRecognitionAdapters:
    """Create realistic adapter observations without hardware dependencies."""

    @staticmethod
    def camera(scenario: SimulatedRecognitionScenario) -> RecognitionObservation:
        return SimulatedRecognitionAdapters._observation(
            scenario,
            RecognitionModality.IMAGE,
            "sim.camera.cabin",
            scenario.face_confidence,
            details={"detector": "simulated-face", "match": "candidate"},
        )

    @staticmethod
    def voice(scenario: SimulatedRecognitionScenario) -> RecognitionObservation:
        return SimulatedRecognitionAdapters._observation(
            scenario,
            RecognitionModality.VOICE,
            "sim.microphone.cabin",
            scenario.voice_confidence,
            details={"detector": "simulated-speaker", "phrase_present": True},
        )

    @staticmethod
    def nfc(scenario: SimulatedRecognitionScenario) -> RecognitionObservation:
        return SimulatedRecognitionAdapters._observation(
            scenario,
            RecognitionModality.NFC,
            "sim.nfc.owner-token",
            scenario.nfc_confidence,
            trusted_credential=scenario.trusted_nfc,
            details={"credential_class": "owner-token"},
        )

    @staticmethod
    def seat(scenario: SimulatedRecognitionScenario) -> RecognitionObservation:
        body_position = (
            "passenger-seat"
            if scenario.conflicting_seat_position
            else scenario.body_position
        )
        return SimulatedRecognitionAdapters._observation(
            scenario,
            RecognitionModality.BEHAVIOR,
            "sim.seat.driver-presence",
            scenario.seat_confidence,
            body_position=body_position,
            details={"occupied": True, "presence_pattern": "stable"},
        )

    @staticmethod
    def collect(
        scenario: SimulatedRecognitionScenario,
    ) -> Tuple[RecognitionObservation, ...]:
        observations = []
        if scenario.include_face:
            observations.append(SimulatedRecognitionAdapters.camera(scenario))
        if scenario.include_voice:
            observations.append(SimulatedRecognitionAdapters.voice(scenario))
        if scenario.include_nfc:
            observations.append(SimulatedRecognitionAdapters.nfc(scenario))
        if scenario.include_seat:
            observations.append(SimulatedRecognitionAdapters.seat(scenario))
        return tuple(observations)

    @staticmethod
    def _observation(
        scenario: SimulatedRecognitionScenario,
        modality: RecognitionModality,
        source_module_id: str,
        confidence: float,
        details: Mapping[str, Any],
        trusted_credential: bool = False,
        body_position: Optional[str] = None,
    ) -> RecognitionObservation:
        return RecognitionObservation(
            observation_id=str(uuid4()),
            candidate_entity_id=scenario.candidate_entity_id,
            modality=modality,
            source_module_id=source_module_id,
            source_node_id="simulated-body-node",
            observed_at=float(scenario.observed_at),
            confidence=float(confidence),
            receipt_id="receipt.%s" % uuid4(),
            frame_id=scenario.frame_id,
            location_id=scenario.location_id,
            body_position=body_position or scenario.body_position,
            raw_reference="sim://%s" % source_module_id,
            details=dict(details),
            trusted_credential=trusted_credential,
            simulated=scenario.observations_simulated,
        )


class RecognitionBenchPipeline:
    """Run the complete recognition-to-context path with no execution path."""

    def __init__(
        self,
        fusion: Optional[RecognitionEvidenceFusion] = None,
        identity_engine: Optional[IdentityTransitionEngine] = None,
        event_bridge: Optional[WorldEventBridge] = None,
        context_projector: Optional[NativeBrainWorldContextProjector] = None,
    ) -> None:
        self._fusion = fusion or RecognitionEvidenceFusion()
        self._identity_engine = identity_engine or IdentityTransitionEngine()
        self._event_bridge = event_bridge or WorldEventBridge(
            source="velvet-ai-core.recognition-bench",
            node_id="simulated-body-node",
            organ_name="native-brain",
        )
        self._context = context_projector or NativeBrainWorldContextProjector()

    def run(
        self,
        identity: EntityIdentity,
        scenario: SimulatedRecognitionScenario,
    ) -> RecognitionBenchResult:
        if identity.entity_id != scenario.candidate_entity_id:
            raise ValueError("identity and recognition candidate must match")

        observations = SimulatedRecognitionAdapters.collect(scenario)
        fusion = self._fusion.fuse(scenario.candidate_entity_id, observations)

        updated_identity = identity
        identity_result = None
        for evidence in fusion.identity_evidence:
            identity_result = self._identity_engine.add_evidence(
                updated_identity,
                evidence,
            )
            updated_identity = identity_result.identity

        if identity_result is None:
            raise ValueError("recognition fusion produced no identity evidence")

        recognition_event = self._event_bridge.from_recognition_fusion(
            fusion,
            scenario.observed_at,
        )
        identity_event = self._event_bridge.from_identity_transition(
            identity_result.record,
            scenario.observed_at,
        )
        recognition_fact = self._context.ingest(
            recognition_event,
            now=scenario.observed_at,
        )
        identity_fact = self._context.ingest(
            identity_event,
            now=scenario.observed_at,
        )
        if recognition_fact is None or identity_fact is None:
            raise ValueError("bench events unexpectedly duplicated")

        return RecognitionBenchResult(
            observations=observations,
            fusion=fusion,
            identity_result=identity_result,
            recognition_event=recognition_event,
            identity_event=identity_event,
            recognition_fact=recognition_fact,
            identity_fact=identity_fact,
        )

    def context_snapshot(self, now: float):
        return self._context.snapshot(now)

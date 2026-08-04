"""Multimodal recognition evidence for Velvet's descriptive identity model.

Recognition adapters emit bounded observations. This module correlates image,
sound, credential, device-presence, and behavior evidence without assigning a
role, ownership, authority, or execution permission.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Tuple
from uuid import uuid4

from .schemas.world_model import IdentityEvidence


class RecognitionModality(str, Enum):
    IMAGE = "IMAGE"
    VOICE = "VOICE"
    NFC = "NFC"
    DEVICE_PRESENCE = "DEVICE_PRESENCE"
    BEHAVIOR = "BEHAVIOR"
    TOUCH = "TOUCH"
    GAIT = "GAIT"
    LOCATION = "LOCATION"
    UNKNOWN = "UNKNOWN"


class RecognitionDisposition(str, Enum):
    INSUFFICIENT = "INSUFFICIENT"
    POSSIBLE = "POSSIBLE"
    LIKELY = "LIKELY"
    CORROBORATED = "CORROBORATED"
    DISPUTED = "DISPUTED"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


def _bounded(name: str, value: float) -> None:
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError("%s must be between 0.0 and 1.0" % name)


@dataclass(frozen=True)
class RecognitionObservation:
    """One adapter-produced candidate match with explicit provenance."""

    observation_id: str
    candidate_entity_id: str
    modality: RecognitionModality
    source_module_id: str
    source_node_id: str
    observed_at: float
    confidence: float
    receipt_id: str
    frame_id: Optional[str] = None
    location_id: Optional[str] = None
    body_position: Optional[str] = None
    raw_reference: Optional[str] = None
    details: Mapping[str, Any] = field(default_factory=dict)
    trusted_credential: bool = False
    simulated: bool = False
    authority_granted: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "observation_id",
            "candidate_entity_id",
            "source_module_id",
            "source_node_id",
            "receipt_id",
        ):
            _require_text(name, getattr(self, name))
        if not isinstance(self.modality, RecognitionModality):
            object.__setattr__(
                self, "modality", RecognitionModality(self.modality)
            )
        if float(self.observed_at) < 0:
            raise ValueError("observed_at must be non-negative")
        _bounded("confidence", self.confidence)
        if not isinstance(self.details, Mapping):
            raise ValueError("details must be a mapping")
        for name in ("frame_id", "location_id", "body_position", "raw_reference"):
            value = getattr(self, name)
            if value is not None:
                _require_text(name, value)
        if self.authority_granted or self.execution_performed:
            raise ValueError("recognition observations cannot claim authority or execution")

    def to_identity_evidence(self) -> IdentityEvidence:
        details = {
            "candidate_entity_id": self.candidate_entity_id,
            "modality": self.modality.value,
            "source_module_id": self.source_module_id,
            "source_node_id": self.source_node_id,
            "frame_id": self.frame_id,
            "location_id": self.location_id,
            "body_position": self.body_position,
            "raw_reference": self.raw_reference,
            "trusted_credential": bool(self.trusted_credential),
            "simulated": bool(self.simulated),
            "features": dict(self.details),
        }
        return IdentityEvidence(
            evidence_id=self.observation_id,
            evidence_type="recognition.%s" % self.modality.value.lower(),
            source=self.source_module_id,
            observed_at=float(self.observed_at),
            confidence=float(self.confidence),
            receipt_id=self.receipt_id,
            details=details,
        )


@dataclass(frozen=True)
class RecognitionFusionPolicy:
    correlation_window_seconds: float = 5.0
    possible_threshold: float = 0.45
    likely_threshold: float = 0.70
    corroborated_threshold: float = 0.82
    minimum_modalities_for_likely: int = 2
    minimum_modalities_for_corroborated: int = 3
    disagreement_margin: float = 0.12

    def __post_init__(self) -> None:
        if self.correlation_window_seconds <= 0:
            raise ValueError("correlation_window_seconds must be positive")
        for name in (
            "possible_threshold",
            "likely_threshold",
            "corroborated_threshold",
            "disagreement_margin",
        ):
            _bounded(name, getattr(self, name))
        if not (
            self.possible_threshold
            <= self.likely_threshold
            <= self.corroborated_threshold
        ):
            raise ValueError("recognition thresholds must be ordered")
        if self.minimum_modalities_for_likely < 1:
            raise ValueError("minimum_modalities_for_likely must be positive")
        if self.minimum_modalities_for_corroborated < self.minimum_modalities_for_likely:
            raise ValueError("corroborated modality count cannot be lower than likely")


@dataclass(frozen=True)
class RecognitionFusion:
    """Append-only multimodal identity evidence summary."""

    fusion_id: str
    candidate_entity_id: str
    disposition: RecognitionDisposition
    confidence: float
    modality_count: int
    source_count: int
    observation_ids: Tuple[str, ...]
    receipt_ids: Tuple[str, ...]
    conflicting_candidate_ids: Tuple[str, ...]
    rationale: str
    identity_evidence: Tuple[IdentityEvidence, ...]
    authority_granted: bool = False
    execution_performed: bool = False


class RecognitionEvidenceFusion:
    """Correlate candidate observations without verifying or authorizing identity."""

    def __init__(self, policy: RecognitionFusionPolicy = RecognitionFusionPolicy()) -> None:
        self._policy = policy

    def fuse(
        self,
        candidate_entity_id: str,
        observations: Tuple[RecognitionObservation, ...],
    ) -> RecognitionFusion:
        _require_text("candidate_entity_id", candidate_entity_id)
        if not observations:
            return self._result(
                candidate_entity_id,
                (),
                RecognitionDisposition.INSUFFICIENT,
                0.0,
                (),
                "no recognition observations were supplied",
            )

        matching = tuple(
            item for item in observations
            if item.candidate_entity_id == candidate_entity_id
        )
        conflicting = tuple(
            item for item in observations
            if item.candidate_entity_id != candidate_entity_id
        )
        if not matching:
            return self._result(
                candidate_entity_id,
                (),
                RecognitionDisposition.INSUFFICIENT,
                0.0,
                tuple(sorted({item.candidate_entity_id for item in conflicting})),
                "no observations support the requested candidate",
            )

        times = [float(item.observed_at) for item in matching]
        if max(times) - min(times) > self._policy.correlation_window_seconds:
            return self._result(
                candidate_entity_id,
                matching,
                RecognitionDisposition.INSUFFICIENT,
                self._weighted_confidence(matching),
                tuple(sorted({item.candidate_entity_id for item in conflicting})),
                "supporting observations fall outside the correlation window",
            )

        frames = {item.frame_id for item in matching if item.frame_id is not None}
        locations = {item.location_id for item in matching if item.location_id is not None}
        positions = {item.body_position for item in matching if item.body_position is not None}
        if len(frames) > 1 or len(locations) > 1 or len(positions) > 1:
            return self._result(
                candidate_entity_id,
                matching,
                RecognitionDisposition.DISPUTED,
                self._weighted_confidence(matching),
                tuple(sorted({item.candidate_entity_id for item in conflicting})),
                "supporting observations disagree on frame, location, or body position",
            )

        confidence = self._weighted_confidence(matching)
        modality_count = len({item.modality for item in matching})
        conflict_ids = tuple(sorted({item.candidate_entity_id for item in conflicting}))
        strongest_conflict = max(
            (item.confidence for item in conflicting), default=0.0
        )
        if strongest_conflict >= confidence - self._policy.disagreement_margin:
            disposition = RecognitionDisposition.DISPUTED
            rationale = "a competing candidate has materially similar support"
        elif (
            confidence >= self._policy.corroborated_threshold
            and modality_count >= self._policy.minimum_modalities_for_corroborated
            and any(item.trusted_credential and not item.simulated for item in matching)
        ):
            disposition = RecognitionDisposition.CORROBORATED
            rationale = "independent modalities and a real trusted credential corroborate the candidate"
        elif (
            confidence >= self._policy.likely_threshold
            and modality_count >= self._policy.minimum_modalities_for_likely
        ):
            disposition = RecognitionDisposition.LIKELY
            rationale = "multiple independent modalities support the candidate"
        elif confidence >= self._policy.possible_threshold:
            disposition = RecognitionDisposition.POSSIBLE
            rationale = "bounded evidence supports the candidate but lacks corroboration"
        else:
            disposition = RecognitionDisposition.INSUFFICIENT
            rationale = "recognition confidence remains below the possible threshold"

        return self._result(
            candidate_entity_id,
            matching,
            disposition,
            confidence,
            conflict_ids,
            rationale,
        )

    @staticmethod
    def _weighted_confidence(
        observations: Tuple[RecognitionObservation, ...]
    ) -> float:
        if not observations:
            return 0.0
        best_by_modality = {}
        for item in observations:
            current = best_by_modality.get(item.modality)
            if current is None or item.confidence > current.confidence:
                best_by_modality[item.modality] = item
        weights = []
        for item in best_by_modality.values():
            weight = 1.15 if item.trusted_credential and not item.simulated else 1.0
            weights.append((float(item.confidence), weight))
        total_weight = sum(weight for _, weight in weights)
        return round(sum(value * weight for value, weight in weights) / total_weight, 6)

    def _result(
        self,
        candidate_entity_id: str,
        observations: Tuple[RecognitionObservation, ...],
        disposition: RecognitionDisposition,
        confidence: float,
        conflicting_candidate_ids: Tuple[str, ...],
        rationale: str,
    ) -> RecognitionFusion:
        evidence = tuple(item.to_identity_evidence() for item in observations)
        return RecognitionFusion(
            fusion_id=str(uuid4()),
            candidate_entity_id=candidate_entity_id,
            disposition=disposition,
            confidence=float(confidence),
            modality_count=len({item.modality for item in observations}),
            source_count=len({item.source_module_id for item in observations}),
            observation_ids=tuple(item.observation_id for item in observations),
            receipt_ids=tuple(dict.fromkeys(item.receipt_id for item in observations)),
            conflicting_candidate_ids=conflicting_candidate_ids,
            rationale=rationale,
            identity_evidence=evidence,
        )

"""Translate descriptive world-model outcomes into Event Protocol records.

This bridge follows the same dependency-free envelope shape used by
``SensorPacket.to_event_protocol``. It publishes observations and transition
outcomes only. It cannot grant authority, authorize capability use, or report
physical execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple

from .identity_transitions import IdentityTransitionRecord
from .recognition_evidence import RecognitionFusion
from .spatial_transitions import SpatialTransitionRecord
from .temporal_transitions import TemporalTransitionRecord
from .world_state import WorldUpdateRecord


class WorldEventType(str, Enum):
    WORLD_ENTITY_UPDATED = "WORLD_ENTITY_UPDATED"
    WORLD_ENTITY_UPDATE_REJECTED = "WORLD_ENTITY_UPDATE_REJECTED"
    SPATIAL_RELATION_CHANGED = "SPATIAL_RELATION_CHANGED"
    SPATIAL_RELATION_REJECTED = "SPATIAL_RELATION_REJECTED"
    TEMPORAL_STATE_CHANGED = "TEMPORAL_STATE_CHANGED"
    TEMPORAL_STATE_REJECTED = "TEMPORAL_STATE_REJECTED"
    IDENTITY_STATE_CHANGED = "IDENTITY_STATE_CHANGED"
    IDENTITY_STATE_REJECTED = "IDENTITY_STATE_REJECTED"
    RECOGNITION_EVIDENCE_FUSED = "RECOGNITION_EVIDENCE_FUSED"
    RECOGNITION_EVIDENCE_DISPUTED = "RECOGNITION_EVIDENCE_DISPUTED"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


def _safe_receipts(receipt_ids: Tuple[str, ...]) -> Tuple[str, ...]:
    result = []
    for receipt_id in receipt_ids:
        _require_text("receipt_id", receipt_id)
        if receipt_id not in result:
            result.append(receipt_id)
    return tuple(result)


@dataclass(frozen=True)
class WorldEventEnvelope:
    """Dependency-free Event Protocol record for descriptive world changes."""

    event_id: str
    event_type: WorldEventType
    source: str
    timestamp: float
    node_id: str
    organ_name: str
    entity_id: str
    payload: Mapping[str, Any]
    receipt_ids: Tuple[str, ...] = ()
    family: str = "world"
    schema_version: str = "1.0"
    authority_granted: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "event_id",
            "source",
            "node_id",
            "organ_name",
            "entity_id",
            "family",
            "schema_version",
        ):
            _require_text(name, getattr(self, name))
        if float(self.timestamp) < 0:
            raise ValueError("timestamp must be non-negative")
        if not isinstance(self.event_type, WorldEventType):
            object.__setattr__(self, "event_type", WorldEventType(self.event_type))
        if not isinstance(self.payload, Mapping):
            raise ValueError("payload must be a mapping")
        object.__setattr__(self, "receipt_ids", _safe_receipts(self.receipt_ids))
        if self.authority_granted or self.execution_performed:
            raise ValueError("world events cannot claim authority or execution")

    def to_event_protocol(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source,
            "family": self.family,
            "schema_version": self.schema_version,
            "timestamp": float(self.timestamp),
            "node_id": self.node_id,
            "organ_name": self.organ_name,
            "entity_id": self.entity_id,
            "receipt_ids": list(self.receipt_ids),
            "payload": dict(self.payload),
            "authority_granted": False,
            "execution_performed": False,
        }


class WorldEventBridge:
    """Build standard descriptive events from world-model transition records."""

    def __init__(
        self,
        source: str = "velvet-ai-core.world-model",
        node_id: str = "unbound-node",
        organ_name: str = "native-brain",
    ) -> None:
        for name, value in (
            ("source", source),
            ("node_id", node_id),
            ("organ_name", organ_name),
        ):
            _require_text(name, value)
        self._source = source
        self._node_id = node_id
        self._organ_name = organ_name

    def from_world_update(
        self,
        record: WorldUpdateRecord,
        timestamp: float,
    ) -> WorldEventEnvelope:
        rejected = record.disposition.value.startswith("REJECTED_")
        event_type = (
            WorldEventType.WORLD_ENTITY_UPDATE_REJECTED
            if rejected
            else WorldEventType.WORLD_ENTITY_UPDATED
        )
        return self._envelope(
            event_id=record.update_id,
            event_type=event_type,
            entity_id=record.entity_id,
            timestamp=timestamp,
            receipt_ids=record.source_receipt_ids,
            payload={
                "disposition": record.disposition.value,
                "incoming_sequence": record.incoming_sequence,
                "current_sequence": record.current_sequence,
                "incoming_monotonic_time": record.incoming_monotonic_time,
                "current_monotonic_time": record.current_monotonic_time,
                "reason": record.reason,
            },
        )

    def from_spatial_transition(
        self,
        record: SpatialTransitionRecord,
        timestamp: float,
    ) -> WorldEventEnvelope:
        rejected = record.disposition.value.startswith("REJECTED_")
        return self._envelope(
            event_id=record.transition_id,
            event_type=(
                WorldEventType.SPATIAL_RELATION_REJECTED
                if rejected
                else WorldEventType.SPATIAL_RELATION_CHANGED
            ),
            entity_id=record.entity_id,
            timestamp=timestamp,
            receipt_ids=record.receipt_ids,
            payload={
                "relation_id": record.relation_id,
                "previous_relation_id": record.previous_relation_id,
                "disposition": record.disposition.value,
                "reason": record.reason,
            },
        )

    def from_temporal_transition(
        self,
        record: TemporalTransitionRecord,
        timestamp: float,
    ) -> WorldEventEnvelope:
        rejected = record.transition_type.value.startswith("REJECTED_")
        return self._envelope(
            event_id=record.transition_id,
            event_type=(
                WorldEventType.TEMPORAL_STATE_REJECTED
                if rejected
                else WorldEventType.TEMPORAL_STATE_CHANGED
            ),
            entity_id=record.entity_id,
            timestamp=timestamp,
            receipt_ids=record.source_receipt_ids,
            payload={
                "transition_type": record.transition_type.value,
                "previous_sequence": record.previous_sequence,
                "incoming_sequence": record.incoming_sequence,
                "previous_monotonic_time": record.previous_monotonic_time,
                "incoming_monotonic_time": record.incoming_monotonic_time,
                "gap_id": record.gap_id,
                "reason": record.reason,
            },
        )

    def from_identity_transition(
        self,
        record: IdentityTransitionRecord,
        timestamp: float,
    ) -> WorldEventEnvelope:
        rejected = record.disposition.value.startswith("REJECTED_")
        return self._envelope(
            event_id=record.transition_id,
            event_type=(
                WorldEventType.IDENTITY_STATE_REJECTED
                if rejected
                else WorldEventType.IDENTITY_STATE_CHANGED
            ),
            entity_id=record.entity_id,
            timestamp=timestamp,
            receipt_ids=record.receipt_ids,
            payload={
                "disposition": record.disposition.value,
                "previous_status": record.previous_status.value,
                "new_status": record.new_status.value,
                "evidence_ids": list(record.evidence_ids),
                "related_entity_id": record.related_entity_id,
                "reason": record.reason,
            },
        )

    def from_recognition_fusion(
        self,
        fusion: RecognitionFusion,
        timestamp: float,
    ) -> WorldEventEnvelope:
        disputed = fusion.disposition.value == "DISPUTED"
        return self._envelope(
            event_id=fusion.fusion_id,
            event_type=(
                WorldEventType.RECOGNITION_EVIDENCE_DISPUTED
                if disputed
                else WorldEventType.RECOGNITION_EVIDENCE_FUSED
            ),
            entity_id=fusion.candidate_entity_id,
            timestamp=timestamp,
            receipt_ids=fusion.receipt_ids,
            payload={
                "disposition": fusion.disposition.value,
                "confidence": float(fusion.confidence),
                "modality_count": fusion.modality_count,
                "source_count": fusion.source_count,
                "observation_ids": list(fusion.observation_ids),
                "conflicting_candidate_ids": list(
                    fusion.conflicting_candidate_ids
                ),
                "rationale": fusion.rationale,
            },
        )

    def _envelope(
        self,
        event_id: str,
        event_type: WorldEventType,
        entity_id: str,
        timestamp: float,
        receipt_ids: Tuple[str, ...],
        payload: Mapping[str, Any],
    ) -> WorldEventEnvelope:
        return WorldEventEnvelope(
            event_id=event_id,
            event_type=event_type,
            source=self._source,
            timestamp=timestamp,
            node_id=self._node_id,
            organ_name=self._organ_name,
            entity_id=entity_id,
            receipt_ids=receipt_ids,
            payload=payload,
        )

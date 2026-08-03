"""Descriptive world-model contracts for Velvet's shared concrete reality.

These records describe identity, time, space, and current state. They do not
mutate Runtime, grant authority, select executors, or perform physical action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple


class IdentityStatus(str, Enum):
    KNOWN = "KNOWN"
    LIKELY = "LIKELY"
    POSSIBLE = "POSSIBLE"
    DISPUTED = "DISPUTED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class EntityLifecycle(str, Enum):
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    MISSING = "MISSING"
    RETIRED = "RETIRED"
    DESTROYED = "DESTROYED"
    SUCCEEDED = "SUCCEEDED"
    UNKNOWN = "UNKNOWN"


class SpatialRelationType(str, Enum):
    LOCATED_IN = "LOCATED_IN"
    ATTACHED_TO = "ATTACHED_TO"
    NEAR = "NEAR"
    REACHABLE_FROM = "REACHABLE_FROM"
    VISIBLE_FROM = "VISIBLE_FROM"
    INSIDE_BOUNDARY = "INSIDE_BOUNDARY"
    OUTSIDE_BOUNDARY = "OUTSIDE_BOUNDARY"
    UNKNOWN = "UNKNOWN"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


def _bounded_confidence(name: str, value: float) -> None:
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError("%s must be between 0.0 and 1.0" % name)


@dataclass(frozen=True)
class IdentityEvidence:
    """Evidence supporting one identity claim without granting authority."""

    evidence_id: str
    evidence_type: str
    source: str
    observed_at: float
    confidence: float
    receipt_id: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("evidence_id", "evidence_type", "source", "receipt_id"):
            _require_text(name, getattr(self, name))
        if float(self.observed_at) < 0:
            raise ValueError("observed_at must be non-negative")
        _bounded_confidence("confidence", self.confidence)
        if not isinstance(self.details, Mapping):
            raise ValueError("details must be a mapping")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "source": self.source,
            "observed_at": float(self.observed_at),
            "confidence": float(self.confidence),
            "receipt_id": self.receipt_id,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class EntityIdentity:
    """Stable identity record separated from role and authority."""

    entity_id: str
    entity_type: str
    canonical_name: str
    status: IdentityStatus
    confidence: float
    aliases: Tuple[str, ...] = ()
    lineage_parent_id: Optional[str] = None
    evidence: Tuple[IdentityEvidence, ...] = ()

    def __post_init__(self) -> None:
        for name in ("entity_id", "entity_type", "canonical_name"):
            _require_text(name, getattr(self, name))
        if not isinstance(self.status, IdentityStatus):
            object.__setattr__(self, "status", IdentityStatus(self.status))
        _bounded_confidence("confidence", self.confidence)
        if self.lineage_parent_id is not None:
            _require_text("lineage_parent_id", self.lineage_parent_id)
        for alias in self.aliases:
            _require_text("alias", alias)
        if self.lineage_parent_id == self.entity_id:
            raise ValueError("an entity cannot be its own lineage parent")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "canonical_name": self.canonical_name,
            "status": self.status.value,
            "confidence": float(self.confidence),
            "aliases": list(self.aliases),
            "lineage_parent_id": self.lineage_parent_id,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True)
class TemporalState:
    """Time posture for current, historical, predicted, or uncertain state."""

    observed_at: float
    received_at: float
    monotonic_time: float
    valid_from: float
    valid_until: Optional[float]
    stale_after_ms: int
    sequence: Optional[int] = None
    estimated: bool = False
    disputed: bool = False

    def __post_init__(self) -> None:
        for name in ("observed_at", "received_at", "monotonic_time", "valid_from"):
            if float(getattr(self, name)) < 0:
                raise ValueError("%s must be non-negative" % name)
        if self.valid_until is not None and self.valid_until < self.valid_from:
            raise ValueError("valid_until cannot precede valid_from")
        if int(self.stale_after_ms) <= 0:
            raise ValueError("stale_after_ms must be positive")
        if self.sequence is not None and int(self.sequence) < 0:
            raise ValueError("sequence must be non-negative")

    def is_stale(self, now_monotonic: float) -> bool:
        if now_monotonic < self.monotonic_time:
            return False
        return (
            (now_monotonic - self.monotonic_time) * 1000.0
            > float(self.stale_after_ms)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observed_at": float(self.observed_at),
            "received_at": float(self.received_at),
            "monotonic_time": float(self.monotonic_time),
            "valid_from": float(self.valid_from),
            "valid_until": (
                float(self.valid_until) if self.valid_until is not None else None
            ),
            "stale_after_ms": int(self.stale_after_ms),
            "sequence": self.sequence,
            "estimated": bool(self.estimated),
            "disputed": bool(self.disputed),
        }


@dataclass(frozen=True)
class SpatialRelation:
    """One evidence-backed relationship between two entities or frames."""

    relation_id: str
    subject_entity_id: str
    relation_type: SpatialRelationType
    object_entity_id: str
    frame_id: str
    confidence: float
    observed_at: float
    receipt_id: str
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "relation_id",
            "subject_entity_id",
            "object_entity_id",
            "frame_id",
            "receipt_id",
        ):
            _require_text(name, getattr(self, name))
        if not isinstance(self.relation_type, SpatialRelationType):
            object.__setattr__(
                self,
                "relation_type",
                SpatialRelationType(self.relation_type),
            )
        _bounded_confidence("confidence", self.confidence)
        if float(self.observed_at) < 0:
            raise ValueError("observed_at must be non-negative")
        if not isinstance(self.attributes, Mapping):
            raise ValueError("attributes must be a mapping")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "subject_entity_id": self.subject_entity_id,
            "relation_type": self.relation_type.value,
            "object_entity_id": self.object_entity_id,
            "frame_id": self.frame_id,
            "confidence": float(self.confidence),
            "observed_at": float(self.observed_at),
            "receipt_id": self.receipt_id,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class WorldEntity:
    """Immutable descriptive snapshot of one entity in Velvet's shared world."""

    identity: EntityIdentity
    temporal: TemporalState
    lifecycle: EntityLifecycle = EntityLifecycle.UNKNOWN
    roles: Tuple[str, ...] = ()
    state: Mapping[str, Any] = field(default_factory=dict)
    spatial_relations: Tuple[SpatialRelation, ...] = ()
    source_receipt_ids: Tuple[str, ...] = ()
    authority_granted: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.lifecycle, EntityLifecycle):
            object.__setattr__(self, "lifecycle", EntityLifecycle(self.lifecycle))
        if not isinstance(self.state, Mapping):
            raise ValueError("state must be a mapping")
        for role in self.roles:
            _require_text("role", role)
        for receipt_id in self.source_receipt_ids:
            _require_text("source_receipt_id", receipt_id)
        if self.authority_granted:
            raise ValueError("world entities cannot grant authority")
        if self.execution_performed:
            raise ValueError("world entities cannot claim execution")
        for relation in self.spatial_relations:
            if relation.subject_entity_id != self.identity.entity_id:
                raise ValueError(
                    "spatial relation subject must match world entity identity"
                )

    @property
    def entity_id(self) -> str:
        return self.identity.entity_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "temporal": self.temporal.to_dict(),
            "lifecycle": self.lifecycle.value,
            "roles": list(self.roles),
            "state": dict(self.state),
            "spatial_relations": [item.to_dict() for item in self.spatial_relations],
            "source_receipt_ids": list(self.source_receipt_ids),
            "authority_granted": False,
            "execution_performed": False,
        }

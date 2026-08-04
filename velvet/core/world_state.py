"""Guarded in-memory state container for Velvet's descriptive world model.

The store accepts immutable ``WorldEntity`` snapshots, preserves append-only
update records, and exposes a current view. It does not persist to disk, grant
authority, execute work, or replace Runtime, Event Protocol, or Receipts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Mapping, Optional, Tuple
from uuid import uuid4

from .schemas.world_model import WorldEntity


class WorldUpdateDisposition(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED_OLDER_SEQUENCE = "REJECTED_OLDER_SEQUENCE"
    REJECTED_OLDER_TIME = "REJECTED_OLDER_TIME"
    REJECTED_IDENTITY_CHANGE = "REJECTED_IDENTITY_CHANGE"
    REJECTED_AUTHORITY_CLAIM = "REJECTED_AUTHORITY_CLAIM"


@dataclass(frozen=True)
class WorldUpdateRecord:
    """Append-only outcome for one attempted world-state update."""

    update_id: str
    entity_id: str
    disposition: WorldUpdateDisposition
    incoming_sequence: Optional[int]
    current_sequence: Optional[int]
    incoming_monotonic_time: float
    current_monotonic_time: Optional[float]
    source_receipt_ids: Tuple[str, ...]
    reason: str
    authority_granted: bool = False
    execution_performed: bool = False


@dataclass(frozen=True)
class WorldView:
    """Immutable snapshot of the store's current descriptive state."""

    revision: int
    entities: Mapping[str, WorldEntity] = field(default_factory=dict)
    authority_granted: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        if self.revision < 0:
            raise ValueError("revision must be non-negative")
        if self.authority_granted or self.execution_performed:
            raise ValueError("world views cannot claim authority or execution")

    def get(self, entity_id: str) -> Optional[WorldEntity]:
        return self.entities.get(entity_id)


class WorldStateStore:
    """Keep one current entity view while preserving every update outcome."""

    def __init__(self) -> None:
        self._entities: Dict[str, WorldEntity] = {}
        self._history: list[WorldUpdateRecord] = []
        self._revision = 0

    @property
    def revision(self) -> int:
        return self._revision

    def current(self, entity_id: str) -> Optional[WorldEntity]:
        return self._entities.get(entity_id)

    def view(self) -> WorldView:
        return WorldView(
            revision=self._revision,
            entities=dict(self._entities),
        )

    def history(self, entity_id: Optional[str] = None) -> Tuple[WorldUpdateRecord, ...]:
        if entity_id is None:
            return tuple(self._history)
        return tuple(
            record for record in self._history if record.entity_id == entity_id
        )

    def apply(self, incoming: WorldEntity) -> WorldUpdateRecord:
        """Accept a newer compatible snapshot or record why it was rejected."""

        if incoming.authority_granted or incoming.execution_performed:
            return self._record(
                incoming,
                WorldUpdateDisposition.REJECTED_AUTHORITY_CLAIM,
                "world-state input cannot claim authority or execution",
            )

        current = self._entities.get(incoming.entity_id)
        if current is None:
            self._entities[incoming.entity_id] = incoming
            self._revision += 1
            return self._record(
                incoming,
                WorldUpdateDisposition.ACCEPTED,
                "first snapshot for entity",
            )

        if not self._same_identity(current, incoming):
            return self._record(
                incoming,
                WorldUpdateDisposition.REJECTED_IDENTITY_CHANGE,
                "existing entity identity cannot be silently rewritten",
                current,
            )

        incoming_sequence = incoming.temporal.sequence
        current_sequence = current.temporal.sequence
        if (
            incoming_sequence is not None
            and current_sequence is not None
            and incoming_sequence <= current_sequence
        ):
            return self._record(
                incoming,
                WorldUpdateDisposition.REJECTED_OLDER_SEQUENCE,
                "incoming sequence must be greater than current sequence",
                current,
            )

        if incoming.temporal.monotonic_time < current.temporal.monotonic_time:
            return self._record(
                incoming,
                WorldUpdateDisposition.REJECTED_OLDER_TIME,
                "incoming monotonic time precedes current state",
                current,
            )

        if (
            incoming_sequence is None
            and current_sequence is None
            and incoming.temporal.monotonic_time
            == current.temporal.monotonic_time
        ):
            return self._record(
                incoming,
                WorldUpdateDisposition.REJECTED_OLDER_TIME,
                "unsequenced updates require increasing monotonic time",
                current,
            )

        self._entities[incoming.entity_id] = incoming
        self._revision += 1
        return self._record(
            incoming,
            WorldUpdateDisposition.ACCEPTED,
            "newer compatible snapshot accepted",
            current,
        )

    @staticmethod
    def _same_identity(current: WorldEntity, incoming: WorldEntity) -> bool:
        """Require stable identity fields; evidence and confidence may evolve."""

        return (
            current.identity.entity_id == incoming.identity.entity_id
            and current.identity.entity_type == incoming.identity.entity_type
            and current.identity.canonical_name == incoming.identity.canonical_name
            and current.identity.lineage_parent_id
            == incoming.identity.lineage_parent_id
        )

    def _record(
        self,
        incoming: WorldEntity,
        disposition: WorldUpdateDisposition,
        reason: str,
        current: Optional[WorldEntity] = None,
    ) -> WorldUpdateRecord:
        record = WorldUpdateRecord(
            update_id=str(uuid4()),
            entity_id=incoming.entity_id,
            disposition=disposition,
            incoming_sequence=incoming.temporal.sequence,
            current_sequence=(
                current.temporal.sequence if current is not None else None
            ),
            incoming_monotonic_time=float(incoming.temporal.monotonic_time),
            current_monotonic_time=(
                float(current.temporal.monotonic_time)
                if current is not None
                else None
            ),
            source_receipt_ids=tuple(incoming.source_receipt_ids),
            reason=reason,
        )
        self._history.append(record)
        return record

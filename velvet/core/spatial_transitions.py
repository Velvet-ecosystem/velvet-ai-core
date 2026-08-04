"""Guarded spatial transition handling for Velvet's descriptive world model.

Spatial evidence may add, replace, expire, or dispute relationships. These
operations never infer access, permission, reachability, or execution authority
from coordinates, visibility, proximity, or containment.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple
from uuid import uuid4

from .schemas.world_model import SpatialRelation, WorldEntity


class SpatialTransitionDisposition(str, Enum):
    ADDED = "ADDED"
    REPLACED = "REPLACED"
    EXPIRED = "EXPIRED"
    DISPUTED = "DISPUTED"
    REJECTED_ENTITY_MISMATCH = "REJECTED_ENTITY_MISMATCH"
    REJECTED_OLDER_EVIDENCE = "REJECTED_OLDER_EVIDENCE"
    REJECTED_UNKNOWN_RELATION = "REJECTED_UNKNOWN_RELATION"
    REJECTED_AUTHORITY_CLAIM = "REJECTED_AUTHORITY_CLAIM"


@dataclass(frozen=True)
class SpatialTransitionRecord:
    transition_id: str
    entity_id: str
    relation_id: str
    disposition: SpatialTransitionDisposition
    previous_relation_id: Optional[str]
    receipt_ids: Tuple[str, ...]
    reason: str
    authority_granted: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        if self.authority_granted or self.execution_performed:
            raise ValueError("spatial transitions cannot claim authority or execution")


@dataclass(frozen=True)
class SpatialTransitionResult:
    entity: WorldEntity
    record: SpatialTransitionRecord


class SpatialTransitionEngine:
    """Apply explicit spatial relationship changes to immutable entity snapshots."""

    def add_or_replace(
        self,
        entity: WorldEntity,
        relation: SpatialRelation,
        replace_relation_id: Optional[str] = None,
    ) -> SpatialTransitionResult:
        if entity.authority_granted or entity.execution_performed:
            return self._unchanged(
                entity,
                relation,
                SpatialTransitionDisposition.REJECTED_AUTHORITY_CLAIM,
                "world entity cannot claim authority or execution",
            )
        if relation.subject_entity_id != entity.entity_id:
            return self._unchanged(
                entity,
                relation,
                SpatialTransitionDisposition.REJECTED_ENTITY_MISMATCH,
                "relation subject does not match entity identity",
            )

        existing = list(entity.spatial_relations)
        previous = None
        if replace_relation_id is not None:
            previous = next(
                (item for item in existing if item.relation_id == replace_relation_id),
                None,
            )
            if previous is None:
                return self._unchanged(
                    entity,
                    relation,
                    SpatialTransitionDisposition.REJECTED_UNKNOWN_RELATION,
                    "replacement relation was not found",
                )
            if relation.observed_at < previous.observed_at:
                return self._unchanged(
                    entity,
                    relation,
                    SpatialTransitionDisposition.REJECTED_OLDER_EVIDENCE,
                    "replacement evidence predates the current relation",
                    previous,
                )
            existing = [
                item for item in existing if item.relation_id != replace_relation_id
            ]

        if any(item.relation_id == relation.relation_id for item in existing):
            current = next(
                item for item in existing if item.relation_id == relation.relation_id
            )
            if relation.observed_at <= current.observed_at:
                return self._unchanged(
                    entity,
                    relation,
                    SpatialTransitionDisposition.REJECTED_OLDER_EVIDENCE,
                    "relation identifier already has equal or newer evidence",
                    current,
                )
            existing = [
                item for item in existing if item.relation_id != relation.relation_id
            ]
            previous = current

        existing.append(relation)
        disposition = (
            SpatialTransitionDisposition.REPLACED
            if previous is not None
            else SpatialTransitionDisposition.ADDED
        )
        updated = self._with_relations(entity, tuple(existing), relation.receipt_id)
        return SpatialTransitionResult(
            entity=updated,
            record=self._record(
                entity.entity_id,
                relation,
                disposition,
                "spatial relation accepted as descriptive evidence",
                previous,
            ),
        )

    def expire(
        self,
        entity: WorldEntity,
        relation_id: str,
        receipt_id: str,
    ) -> SpatialTransitionResult:
        relation = next(
            (item for item in entity.spatial_relations if item.relation_id == relation_id),
            None,
        )
        if relation is None:
            placeholder = SpatialRelation(
                relation_id=relation_id,
                subject_entity_id=entity.entity_id,
                relation_type="UNKNOWN",
                object_entity_id="unknown",
                frame_id="unknown",
                confidence=0.0,
                observed_at=entity.temporal.observed_at,
                receipt_id=receipt_id,
            )
            return self._unchanged(
                entity,
                placeholder,
                SpatialTransitionDisposition.REJECTED_UNKNOWN_RELATION,
                "relation to expire was not found",
            )

        remaining = tuple(
            item for item in entity.spatial_relations if item.relation_id != relation_id
        )
        updated = self._with_relations(entity, remaining, receipt_id)
        return SpatialTransitionResult(
            entity=updated,
            record=SpatialTransitionRecord(
                transition_id=str(uuid4()),
                entity_id=entity.entity_id,
                relation_id=relation_id,
                disposition=SpatialTransitionDisposition.EXPIRED,
                previous_relation_id=relation_id,
                receipt_ids=(relation.receipt_id, receipt_id),
                reason="relation expired; history remains in transition evidence",
            ),
        )

    def dispute(
        self,
        entity: WorldEntity,
        relation_id: str,
        receipt_id: str,
        reason: str,
    ) -> SpatialTransitionResult:
        relation = next(
            (item for item in entity.spatial_relations if item.relation_id == relation_id),
            None,
        )
        if relation is None:
            placeholder = SpatialRelation(
                relation_id=relation_id,
                subject_entity_id=entity.entity_id,
                relation_type="UNKNOWN",
                object_entity_id="unknown",
                frame_id="unknown",
                confidence=0.0,
                observed_at=entity.temporal.observed_at,
                receipt_id=receipt_id,
            )
            return self._unchanged(
                entity,
                placeholder,
                SpatialTransitionDisposition.REJECTED_UNKNOWN_RELATION,
                "relation to dispute was not found",
            )

        attributes = dict(relation.attributes)
        attributes["disputed"] = True
        attributes["dispute_reason"] = reason
        attributes["dispute_receipt_id"] = receipt_id
        disputed = SpatialRelation(
            relation_id=relation.relation_id,
            subject_entity_id=relation.subject_entity_id,
            relation_type=relation.relation_type,
            object_entity_id=relation.object_entity_id,
            frame_id=relation.frame_id,
            confidence=relation.confidence,
            observed_at=relation.observed_at,
            receipt_id=relation.receipt_id,
            attributes=attributes,
        )
        relations = tuple(
            disputed if item.relation_id == relation_id else item
            for item in entity.spatial_relations
        )
        updated = self._with_relations(entity, relations, receipt_id)
        return SpatialTransitionResult(
            entity=updated,
            record=SpatialTransitionRecord(
                transition_id=str(uuid4()),
                entity_id=entity.entity_id,
                relation_id=relation_id,
                disposition=SpatialTransitionDisposition.DISPUTED,
                previous_relation_id=relation_id,
                receipt_ids=(relation.receipt_id, receipt_id),
                reason=reason,
            ),
        )

    @staticmethod
    def _with_relations(
        entity: WorldEntity,
        relations: Tuple[SpatialRelation, ...],
        receipt_id: str,
    ) -> WorldEntity:
        receipts = list(entity.source_receipt_ids)
        if receipt_id not in receipts:
            receipts.append(receipt_id)
        return WorldEntity(
            identity=entity.identity,
            temporal=entity.temporal,
            lifecycle=entity.lifecycle,
            roles=entity.roles,
            state=entity.state,
            spatial_relations=relations,
            source_receipt_ids=tuple(receipts),
        )

    def _unchanged(
        self,
        entity: WorldEntity,
        relation: SpatialRelation,
        disposition: SpatialTransitionDisposition,
        reason: str,
        previous: Optional[SpatialRelation] = None,
    ) -> SpatialTransitionResult:
        return SpatialTransitionResult(
            entity=entity,
            record=self._record(
                entity.entity_id,
                relation,
                disposition,
                reason,
                previous,
            ),
        )

    @staticmethod
    def _record(
        entity_id: str,
        relation: SpatialRelation,
        disposition: SpatialTransitionDisposition,
        reason: str,
        previous: Optional[SpatialRelation] = None,
    ) -> SpatialTransitionRecord:
        receipts = [relation.receipt_id]
        if previous is not None and previous.receipt_id not in receipts:
            receipts.insert(0, previous.receipt_id)
        return SpatialTransitionRecord(
            transition_id=str(uuid4()),
            entity_id=entity_id,
            relation_id=relation.relation_id,
            disposition=disposition,
            previous_relation_id=(
                previous.relation_id if previous is not None else None
            ),
            receipt_ids=tuple(receipts),
            reason=reason,
        )

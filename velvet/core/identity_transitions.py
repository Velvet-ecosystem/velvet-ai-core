"""Guarded identity transitions for Velvet's descriptive world model.

Identity evidence may strengthen, weaken, dispute, alias, retire, or establish
lineage for an entity. These transitions never grant authority, assign roles,
transfer ownership, or perform execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple
from uuid import uuid4

from .schemas.world_model import EntityIdentity, IdentityEvidence, IdentityStatus


class IdentityTransitionDisposition(str, Enum):
    EVIDENCE_ACCEPTED = "EVIDENCE_ACCEPTED"
    ALIAS_ACCEPTED = "ALIAS_ACCEPTED"
    DISPUTED = "DISPUTED"
    RETIRED = "RETIRED"
    SUCCESSOR_CREATED = "SUCCESSOR_CREATED"
    DUPLICATE_FLAGGED = "DUPLICATE_FLAGGED"
    REJECTED_DUPLICATE_EVIDENCE = "REJECTED_DUPLICATE_EVIDENCE"
    REJECTED_ENTITY_MISMATCH = "REJECTED_ENTITY_MISMATCH"
    REJECTED_INVALID_PROMOTION = "REJECTED_INVALID_PROMOTION"
    REJECTED_AUTHORITY_CLAIM = "REJECTED_AUTHORITY_CLAIM"


@dataclass(frozen=True)
class IdentityPolicy:
    possible_threshold: float = 0.25
    likely_threshold: float = 0.60
    known_threshold: float = 0.85
    minimum_known_sources: int = 2

    def __post_init__(self) -> None:
        if not 0.0 <= self.possible_threshold < self.likely_threshold:
            raise ValueError("possible threshold must be below likely threshold")
        if not self.likely_threshold < self.known_threshold <= 1.0:
            raise ValueError("likely threshold must be below known threshold")
        if self.minimum_known_sources < 2:
            raise ValueError("known identity requires at least two sources")


@dataclass(frozen=True)
class IdentityTransitionRecord:
    transition_id: str
    entity_id: str
    disposition: IdentityTransitionDisposition
    previous_status: IdentityStatus
    new_status: IdentityStatus
    evidence_ids: Tuple[str, ...]
    receipt_ids: Tuple[str, ...]
    reason: str
    related_entity_id: Optional[str] = None
    authority_granted: bool = False
    execution_performed: bool = False


@dataclass(frozen=True)
class IdentityTransitionResult:
    identity: EntityIdentity
    record: IdentityTransitionRecord
    successor: Optional[EntityIdentity] = None


class IdentityTransitionEngine:
    """Apply append-only identity changes without creating permission."""

    def __init__(self, policy: IdentityPolicy = IdentityPolicy()) -> None:
        self._policy = policy

    def add_evidence(
        self,
        identity: EntityIdentity,
        evidence: IdentityEvidence,
    ) -> IdentityTransitionResult:
        if any(item.evidence_id == evidence.evidence_id for item in identity.evidence):
            return self._result(
                identity,
                IdentityTransitionDisposition.REJECTED_DUPLICATE_EVIDENCE,
                identity.status,
                "evidence identifier already exists",
            )

        evidence_items = identity.evidence + (evidence,)
        status, confidence = self._evaluate(identity.status, evidence_items)
        updated = EntityIdentity(
            entity_id=identity.entity_id,
            entity_type=identity.entity_type,
            canonical_name=identity.canonical_name,
            status=status,
            confidence=confidence,
            aliases=identity.aliases,
            lineage_parent_id=identity.lineage_parent_id,
            evidence=evidence_items,
        )
        return self._result(
            updated,
            IdentityTransitionDisposition.EVIDENCE_ACCEPTED,
            identity.status,
            "identity evidence accepted and status recalculated",
        )

    def add_alias(
        self,
        identity: EntityIdentity,
        alias: str,
        receipt_id: str,
    ) -> IdentityTransitionResult:
        alias = alias.strip()
        if not alias:
            raise ValueError("alias must be non-empty")
        if not receipt_id.strip():
            raise ValueError("receipt_id must be non-empty")
        aliases = identity.aliases
        if alias not in aliases and alias != identity.canonical_name:
            aliases = aliases + (alias,)
        updated = EntityIdentity(
            entity_id=identity.entity_id,
            entity_type=identity.entity_type,
            canonical_name=identity.canonical_name,
            status=identity.status,
            confidence=identity.confidence,
            aliases=aliases,
            lineage_parent_id=identity.lineage_parent_id,
            evidence=identity.evidence,
        )
        return self._result(
            updated,
            IdentityTransitionDisposition.ALIAS_ACCEPTED,
            identity.status,
            "alias recorded without creating a new identity",
            extra_receipts=(receipt_id,),
        )

    def dispute(
        self,
        identity: EntityIdentity,
        evidence: IdentityEvidence,
        related_entity_id: Optional[str] = None,
    ) -> IdentityTransitionResult:
        evidence_items = identity.evidence
        if not any(item.evidence_id == evidence.evidence_id for item in evidence_items):
            evidence_items = evidence_items + (evidence,)
        updated = EntityIdentity(
            entity_id=identity.entity_id,
            entity_type=identity.entity_type,
            canonical_name=identity.canonical_name,
            status=IdentityStatus.DISPUTED,
            confidence=min(identity.confidence, evidence.confidence),
            aliases=identity.aliases,
            lineage_parent_id=identity.lineage_parent_id,
            evidence=evidence_items,
        )
        return self._result(
            updated,
            IdentityTransitionDisposition.DISPUTED,
            identity.status,
            "identity dispute recorded without erasing prior evidence",
            related_entity_id=related_entity_id,
        )

    def flag_duplicate(
        self,
        identity: EntityIdentity,
        possible_duplicate_entity_id: str,
        receipt_id: str,
    ) -> IdentityTransitionResult:
        if not possible_duplicate_entity_id.strip() or not receipt_id.strip():
            raise ValueError("duplicate entity and receipt identifiers are required")
        updated = EntityIdentity(
            entity_id=identity.entity_id,
            entity_type=identity.entity_type,
            canonical_name=identity.canonical_name,
            status=IdentityStatus.DISPUTED,
            confidence=identity.confidence,
            aliases=identity.aliases,
            lineage_parent_id=identity.lineage_parent_id,
            evidence=identity.evidence,
        )
        return self._result(
            updated,
            IdentityTransitionDisposition.DUPLICATE_FLAGGED,
            identity.status,
            "possible duplicate or fork requires explicit resolution",
            related_entity_id=possible_duplicate_entity_id,
            extra_receipts=(receipt_id,),
        )

    def create_successor(
        self,
        predecessor: EntityIdentity,
        successor_entity_id: str,
        successor_name: str,
        evidence: IdentityEvidence,
    ) -> IdentityTransitionResult:
        if successor_entity_id == predecessor.entity_id:
            raise ValueError("successor must have a distinct entity_id")
        if not successor_entity_id.strip() or not successor_name.strip():
            raise ValueError("successor identity fields must be non-empty")

        successor_status, successor_confidence = self._evaluate(
            IdentityStatus.UNKNOWN,
            (evidence,),
        )
        successor = EntityIdentity(
            entity_id=successor_entity_id,
            entity_type=predecessor.entity_type,
            canonical_name=successor_name,
            status=successor_status,
            confidence=successor_confidence,
            aliases=(),
            lineage_parent_id=predecessor.entity_id,
            evidence=(evidence,),
        )
        return self._result(
            predecessor,
            IdentityTransitionDisposition.SUCCESSOR_CREATED,
            predecessor.status,
            "successor lineage created without claiming physical sameness",
            related_entity_id=successor_entity_id,
            successor=successor,
        )

    def retire(
        self,
        identity: EntityIdentity,
        receipt_id: str,
    ) -> IdentityTransitionResult:
        if not receipt_id.strip():
            raise ValueError("receipt_id must be non-empty")
        updated = EntityIdentity(
            entity_id=identity.entity_id,
            entity_type=identity.entity_type,
            canonical_name=identity.canonical_name,
            status=IdentityStatus.REJECTED,
            confidence=identity.confidence,
            aliases=identity.aliases,
            lineage_parent_id=identity.lineage_parent_id,
            evidence=identity.evidence,
        )
        return self._result(
            updated,
            IdentityTransitionDisposition.RETIRED,
            identity.status,
            "identity retired from current recognition without deleting history",
            extra_receipts=(receipt_id,),
        )

    def _evaluate(
        self,
        current_status: IdentityStatus,
        evidence_items: Tuple[IdentityEvidence, ...],
    ) -> Tuple[IdentityStatus, float]:
        if not evidence_items:
            return IdentityStatus.UNKNOWN, 0.0

        confidence = round(
            sum(item.confidence for item in evidence_items) / len(evidence_items),
            6,
        )
        distinct_sources = {item.source for item in evidence_items}

        if (
            confidence >= self._policy.known_threshold
            and len(distinct_sources) >= self._policy.minimum_known_sources
        ):
            return IdentityStatus.KNOWN, confidence
        if confidence >= self._policy.likely_threshold:
            return IdentityStatus.LIKELY, confidence
        if confidence >= self._policy.possible_threshold:
            return IdentityStatus.POSSIBLE, confidence
        return IdentityStatus.UNKNOWN, confidence

    def _result(
        self,
        identity: EntityIdentity,
        disposition: IdentityTransitionDisposition,
        previous_status: IdentityStatus,
        reason: str,
        related_entity_id: Optional[str] = None,
        extra_receipts: Tuple[str, ...] = (),
        successor: Optional[EntityIdentity] = None,
    ) -> IdentityTransitionResult:
        evidence_ids = tuple(item.evidence_id for item in identity.evidence)
        receipt_ids = tuple(item.receipt_id for item in identity.evidence)
        for receipt_id in extra_receipts:
            if receipt_id not in receipt_ids:
                receipt_ids += (receipt_id,)
        record = IdentityTransitionRecord(
            transition_id=str(uuid4()),
            entity_id=identity.entity_id,
            disposition=disposition,
            previous_status=previous_status,
            new_status=identity.status,
            evidence_ids=evidence_ids,
            receipt_ids=receipt_ids,
            reason=reason,
            related_entity_id=related_entity_id,
        )
        return IdentityTransitionResult(identity=identity, record=record, successor=successor)

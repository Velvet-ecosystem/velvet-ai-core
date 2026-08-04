"""Guarded temporal transition handling for Velvet's descriptive world model.

Temporal transitions preserve sequence, gaps, estimates, disputes, recovery, and
state duration without rewriting history or granting authority.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Optional, Tuple
from uuid import uuid4

from .schemas.world_model import TemporalState, WorldEntity


class TemporalTransitionType(str, Enum):
    ADVANCE = "ADVANCE"
    GAP_OPENED = "GAP_OPENED"
    GAP_CLOSED = "GAP_CLOSED"
    ESTIMATED = "ESTIMATED"
    DISPUTED = "DISPUTED"
    REJECTED_OLDER_SEQUENCE = "REJECTED_OLDER_SEQUENCE"
    REJECTED_OLDER_TIME = "REJECTED_OLDER_TIME"
    REJECTED_INVALID_GAP = "REJECTED_INVALID_GAP"


@dataclass(frozen=True)
class TemporalGap:
    gap_id: str
    entity_id: str
    started_at: float
    started_monotonic: float
    reason: str
    receipt_id: str
    ended_at: Optional[float] = None
    ended_monotonic: Optional[float] = None
    recovery_receipt_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.started_at < 0 or self.started_monotonic < 0:
            raise ValueError("gap start times must be non-negative")
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("gap end cannot precede gap start")
        if (
            self.ended_monotonic is not None
            and self.ended_monotonic < self.started_monotonic
        ):
            raise ValueError("gap monotonic end cannot precede start")

    @property
    def open(self) -> bool:
        return self.ended_at is None

    def duration_seconds(self) -> Optional[float]:
        if self.ended_at is None:
            return None
        return self.ended_at - self.started_at


@dataclass(frozen=True)
class TemporalTransitionRecord:
    transition_id: str
    entity_id: str
    transition_type: TemporalTransitionType
    previous_sequence: Optional[int]
    incoming_sequence: Optional[int]
    previous_monotonic_time: float
    incoming_monotonic_time: float
    source_receipt_ids: Tuple[str, ...]
    reason: str
    gap_id: Optional[str] = None
    authority_granted: bool = False
    execution_performed: bool = False


@dataclass(frozen=True)
class TemporalTransitionResult:
    entity: WorldEntity
    record: TemporalTransitionRecord
    gaps: Tuple[TemporalGap, ...] = ()


class TemporalTransitionManager:
    """Apply explicit temporal changes while preserving interruption history."""

    def advance(
        self,
        current: WorldEntity,
        incoming: TemporalState,
        source_receipt_ids: Tuple[str, ...],
    ) -> TemporalTransitionResult:
        disposition = self._validate_advance(current.temporal, incoming)
        if disposition is not None:
            return TemporalTransitionResult(
                entity=current,
                record=self._record(
                    current,
                    incoming,
                    disposition,
                    source_receipt_ids,
                    "incoming temporal state is not newer than current state",
                ),
            )

        merged_receipts = list(current.source_receipt_ids)
        for receipt_id in source_receipt_ids:
            if receipt_id not in merged_receipts:
                merged_receipts.append(receipt_id)

        updated = replace(
            current,
            temporal=incoming,
            source_receipt_ids=tuple(merged_receipts),
        )
        transition_type = (
            TemporalTransitionType.DISPUTED
            if incoming.disputed
            else TemporalTransitionType.ESTIMATED
            if incoming.estimated
            else TemporalTransitionType.ADVANCE
        )
        return TemporalTransitionResult(
            entity=updated,
            record=self._record(
                current,
                incoming,
                transition_type,
                source_receipt_ids,
                "newer temporal state accepted",
            ),
        )

    def open_gap(
        self,
        current: WorldEntity,
        started_at: float,
        started_monotonic: float,
        reason: str,
        receipt_id: str,
        existing_gaps: Tuple[TemporalGap, ...] = (),
    ) -> TemporalTransitionResult:
        if any(gap.open for gap in existing_gaps):
            record = self._record(
                current,
                current.temporal,
                TemporalTransitionType.REJECTED_INVALID_GAP,
                (receipt_id,),
                "an open temporal gap already exists",
            )
            return TemporalTransitionResult(current, record, existing_gaps)
        if started_monotonic < current.temporal.monotonic_time:
            record = self._record(
                current,
                current.temporal,
                TemporalTransitionType.REJECTED_OLDER_TIME,
                (receipt_id,),
                "gap cannot begin before current monotonic time",
            )
            return TemporalTransitionResult(current, record, existing_gaps)

        gap = TemporalGap(
            gap_id=str(uuid4()),
            entity_id=current.entity_id,
            started_at=float(started_at),
            started_monotonic=float(started_monotonic),
            reason=reason,
            receipt_id=receipt_id,
        )
        disputed_temporal = replace(current.temporal, disputed=True)
        updated = replace(current, temporal=disputed_temporal)
        record = self._record(
            current,
            disputed_temporal,
            TemporalTransitionType.GAP_OPENED,
            (receipt_id,),
            reason,
            gap.gap_id,
        )
        return TemporalTransitionResult(updated, record, existing_gaps + (gap,))

    def close_gap(
        self,
        current: WorldEntity,
        ended_at: float,
        ended_monotonic: float,
        recovery_receipt_id: str,
        existing_gaps: Tuple[TemporalGap, ...],
        recovered_state: Optional[TemporalState] = None,
    ) -> TemporalTransitionResult:
        open_indexes = [i for i, gap in enumerate(existing_gaps) if gap.open]
        if len(open_indexes) != 1:
            record = self._record(
                current,
                current.temporal,
                TemporalTransitionType.REJECTED_INVALID_GAP,
                (recovery_receipt_id,),
                "exactly one open temporal gap is required for recovery",
            )
            return TemporalTransitionResult(current, record, existing_gaps)

        index = open_indexes[0]
        gap = existing_gaps[index]
        closed = replace(
            gap,
            ended_at=float(ended_at),
            ended_monotonic=float(ended_monotonic),
            recovery_receipt_id=recovery_receipt_id,
        )
        gaps = list(existing_gaps)
        gaps[index] = closed

        if recovered_state is None:
            recovered_state = replace(
                current.temporal,
                observed_at=float(ended_at),
                received_at=float(ended_at),
                monotonic_time=float(ended_monotonic),
                valid_from=float(ended_at),
                valid_until=None,
                disputed=False,
            )
        validation = self._validate_advance(current.temporal, recovered_state)
        if validation is not None:
            record = self._record(
                current,
                recovered_state,
                validation,
                (recovery_receipt_id,),
                "recovery state must be newer than the pre-gap state",
                gap.gap_id,
            )
            return TemporalTransitionResult(current, record, existing_gaps)

        receipts = list(current.source_receipt_ids)
        if recovery_receipt_id not in receipts:
            receipts.append(recovery_receipt_id)
        updated = replace(
            current,
            temporal=recovered_state,
            source_receipt_ids=tuple(receipts),
        )
        record = self._record(
            current,
            recovered_state,
            TemporalTransitionType.GAP_CLOSED,
            (recovery_receipt_id,),
            "recovery created a new current observation; the gap remains in history",
            gap.gap_id,
        )
        return TemporalTransitionResult(updated, record, tuple(gaps))

    @staticmethod
    def duration_seconds(entity: WorldEntity, now: float) -> float:
        if now < entity.temporal.valid_from:
            raise ValueError("now cannot precede valid_from")
        end = entity.temporal.valid_until
        return (end if end is not None else now) - entity.temporal.valid_from

    @staticmethod
    def _validate_advance(
        current: TemporalState,
        incoming: TemporalState,
    ) -> Optional[TemporalTransitionType]:
        if (
            current.sequence is not None
            and incoming.sequence is not None
            and incoming.sequence <= current.sequence
        ):
            return TemporalTransitionType.REJECTED_OLDER_SEQUENCE
        if incoming.monotonic_time <= current.monotonic_time:
            return TemporalTransitionType.REJECTED_OLDER_TIME
        return None

    @staticmethod
    def _record(
        current: WorldEntity,
        incoming: TemporalState,
        transition_type: TemporalTransitionType,
        source_receipt_ids: Tuple[str, ...],
        reason: str,
        gap_id: Optional[str] = None,
    ) -> TemporalTransitionRecord:
        return TemporalTransitionRecord(
            transition_id=str(uuid4()),
            entity_id=current.entity_id,
            transition_type=transition_type,
            previous_sequence=current.temporal.sequence,
            incoming_sequence=incoming.sequence,
            previous_monotonic_time=float(current.temporal.monotonic_time),
            incoming_monotonic_time=float(incoming.monotonic_time),
            source_receipt_ids=tuple(source_receipt_ids),
            reason=reason,
            gap_id=gap_id,
        )

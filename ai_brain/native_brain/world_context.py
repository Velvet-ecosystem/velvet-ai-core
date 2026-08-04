"""Bounded Native Brain context projection for descriptive world events.

This module consumes Event Protocol-shaped world events and creates reasoning
context only. It does not authorize capabilities, select executors, mutate
Runtime, or claim physical execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple

from velvet.core.world_event_bridge import WorldEventEnvelope, WorldEventType


class ContextFactDisposition(str, Enum):
    CURRENT = "CURRENT"
    AGING = "AGING"
    STALE = "STALE"
    DISPUTED = "DISPUTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class WorldContextPolicy:
    current_for_seconds: float = 5.0
    stale_after_seconds: float = 30.0
    max_facts_per_entity: int = 32

    def __post_init__(self) -> None:
        if self.current_for_seconds <= 0:
            raise ValueError("current_for_seconds must be positive")
        if self.stale_after_seconds <= self.current_for_seconds:
            raise ValueError("stale_after_seconds must exceed current_for_seconds")
        if self.max_facts_per_entity <= 0:
            raise ValueError("max_facts_per_entity must be positive")


@dataclass(frozen=True)
class ContextFact:
    event_id: str
    entity_id: str
    event_type: WorldEventType
    observed_at: float
    disposition: ContextFactDisposition
    confidence: Optional[float]
    summary: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    receipt_ids: Tuple[str, ...] = ()
    authority_granted: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.entity_id.strip():
            raise ValueError("event_id and entity_id are required")
        if self.observed_at < 0:
            raise ValueError("observed_at must be non-negative")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.authority_granted or self.execution_performed:
            raise ValueError("context facts cannot claim authority or execution")


@dataclass(frozen=True)
class NativeBrainWorldContext:
    generated_at: float
    facts_by_entity: Mapping[str, Tuple[ContextFact, ...]]
    authority_granted: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        if self.generated_at < 0:
            raise ValueError("generated_at must be non-negative")
        if self.authority_granted or self.execution_performed:
            raise ValueError("reasoning context cannot claim authority or execution")

    def facts_for(self, entity_id: str) -> Tuple[ContextFact, ...]:
        return self.facts_by_entity.get(entity_id, ())

    def latest(self, entity_id: str) -> Optional[ContextFact]:
        facts = self.facts_for(entity_id)
        return facts[-1] if facts else None


class NativeBrainWorldContextProjector:
    """Project descriptive world events into bounded reasoning context."""

    def __init__(self, policy: WorldContextPolicy = WorldContextPolicy()) -> None:
        self._policy = policy
        self._facts: Dict[str, list[ContextFact]] = {}
        self._seen_event_ids: set[str] = set()

    def ingest(
        self,
        event: WorldEventEnvelope,
        now: Optional[float] = None,
    ) -> Optional[ContextFact]:
        if event.event_id in self._seen_event_ids:
            return None
        if event.authority_granted or event.execution_performed:
            raise ValueError("world event cannot carry authority or execution")

        fact = self._fact_from_event(event, now if now is not None else event.timestamp)
        bucket = self._facts.setdefault(event.entity_id, [])
        bucket.append(fact)
        if len(bucket) > self._policy.max_facts_per_entity:
            del bucket[: len(bucket) - self._policy.max_facts_per_entity]
        self._seen_event_ids.add(event.event_id)
        return fact

    def snapshot(self, now: float) -> NativeBrainWorldContext:
        if now < 0:
            raise ValueError("now must be non-negative")
        refreshed: Dict[str, Tuple[ContextFact, ...]] = {}
        for entity_id, facts in self._facts.items():
            refreshed[entity_id] = tuple(
                self._refresh_disposition(fact, now) for fact in facts
            )
        return NativeBrainWorldContext(
            generated_at=now,
            facts_by_entity=refreshed,
        )

    def _fact_from_event(self, event: WorldEventEnvelope, now: float) -> ContextFact:
        payload = dict(event.payload)
        rejected = event.event_type.value.endswith("_REJECTED")
        disputed = event.event_type == WorldEventType.RECOGNITION_EVIDENCE_DISPUTED
        if payload.get("disposition") == "DISPUTED":
            disputed = True

        if rejected:
            disposition = ContextFactDisposition.REJECTED
        elif disputed:
            disposition = ContextFactDisposition.DISPUTED
        else:
            disposition = self._age_disposition(event.timestamp, now)

        confidence_value = payload.get("confidence")
        confidence = (
            float(confidence_value) if confidence_value is not None else None
        )
        return ContextFact(
            event_id=event.event_id,
            entity_id=event.entity_id,
            event_type=event.event_type,
            observed_at=float(event.timestamp),
            disposition=disposition,
            confidence=confidence,
            summary=self._summary(event.event_type, payload),
            payload=payload,
            receipt_ids=tuple(event.receipt_ids),
        )

    def _refresh_disposition(self, fact: ContextFact, now: float) -> ContextFact:
        if fact.disposition in (
            ContextFactDisposition.DISPUTED,
            ContextFactDisposition.REJECTED,
        ):
            return fact
        disposition = self._age_disposition(fact.observed_at, now)
        if disposition == fact.disposition:
            return fact
        return ContextFact(
            event_id=fact.event_id,
            entity_id=fact.entity_id,
            event_type=fact.event_type,
            observed_at=fact.observed_at,
            disposition=disposition,
            confidence=fact.confidence,
            summary=fact.summary,
            payload=fact.payload,
            receipt_ids=fact.receipt_ids,
        )

    def _age_disposition(
        self,
        observed_at: float,
        now: float,
    ) -> ContextFactDisposition:
        age = max(0.0, now - observed_at)
        if age <= self._policy.current_for_seconds:
            return ContextFactDisposition.CURRENT
        if age <= self._policy.stale_after_seconds:
            return ContextFactDisposition.AGING
        return ContextFactDisposition.STALE

    @staticmethod
    def _summary(event_type: WorldEventType, payload: Mapping[str, Any]) -> str:
        reason = payload.get("reason") or payload.get("rationale")
        disposition = payload.get("disposition") or payload.get("transition_type")
        pieces = [event_type.value]
        if disposition:
            pieces.append(str(disposition))
        if reason:
            pieces.append(str(reason))
        return ": ".join(pieces)

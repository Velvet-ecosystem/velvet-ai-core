# SPDX-License-Identifier: GPL-3.0-only
"""Canonical, public-safe record shape for Velvet memory events."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional


class MemoryKind(str, Enum):
    """Semantic classes that keep memory from collapsing into one vague bucket."""

    OBSERVATION = "observation"
    CONVERSATION = "conversation"
    INFERENCE = "inference"
    CANDIDATE = "candidate"
    FACT = "fact"
    DECISION = "decision"
    EXECUTION_RESULT = "execution_result"
    CONTINUITY = "continuity"
    SYSTEM = "system"


@dataclass(frozen=True)
class MemoryRecord:
    """One append-only memory record.

    The payload may remain private. Metadata is deliberately small and portable so
    Core, Continuity Spine, and Receipts can refer to the same event without
    merging their responsibilities.
    """

    kind: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    schema_version: int = 1
    source: Optional[str] = None
    confidence: Optional[float] = None
    authority_status: Optional[str] = None
    receipt_id: Optional[str] = None
    related_event_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, str) or not self.kind.strip():
            raise ValueError("memory kind must be a non-empty string")
        if not isinstance(self.payload, dict):
            raise TypeError("memory payload must be a dictionary")
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id must be a non-empty string")
        if not isinstance(self.timestamp, (int, float)):
            raise TypeError("timestamp must be numeric")
        if not isinstance(self.schema_version, int) or self.schema_version < 1:
            raise ValueError("schema_version must be a positive integer")
        if self.confidence is not None:
            if not isinstance(self.confidence, (int, float)):
                raise TypeError("confidence must be numeric")
            if not 0.0 <= float(self.confidence) <= 1.0:
                raise ValueError("confidence must be between 0.0 and 1.0")
        self._validate_string_list("related_event_ids", self.related_event_ids)
        self._validate_string_list("tags", self.tags)

    @staticmethod
    def _validate_string_list(name: str, values: Iterable[str]) -> None:
        if not isinstance(values, list):
            raise TypeError("{} must be a list".format(name))
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("{} must contain non-empty strings".format(name))

    def to_dict(self) -> Dict[str, Any]:
        record = {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "ts": float(self.timestamp),
            "kind": self.kind.strip(),
            "payload": self.payload,
        }
        optional = {
            "source": self.source,
            "confidence": self.confidence,
            "authority_status": self.authority_status,
            "receipt_id": self.receipt_id,
        }
        for key, value in optional.items():
            if value is not None:
                record[key] = value
        if self.related_event_ids:
            record["related_event_ids"] = list(self.related_event_ids)
        if self.tags:
            record["tags"] = list(self.tags)
        return record

    @classmethod
    def from_dict(cls, record: Dict[str, Any]) -> "MemoryRecord":
        if not isinstance(record, dict):
            raise TypeError("memory record must be a dictionary")
        return cls(
            schema_version=record.get("schema_version", 1),
            event_id=record["event_id"],
            timestamp=record.get("ts", record.get("timestamp")),
            kind=record["kind"],
            payload=record["payload"],
            source=record.get("source"),
            confidence=record.get("confidence"),
            authority_status=record.get("authority_status"),
            receipt_id=record.get("receipt_id"),
            related_event_ids=list(record.get("related_event_ids", [])),
            tags=list(record.get("tags", [])),
        )

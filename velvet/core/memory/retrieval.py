# SPDX-License-Identifier: GPL-3.0-only
from __future__ import annotations

import copy
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .associations import MemoryAssociationIndex
from .decay import MemoryDecayPolicy
from .recall import MemoryRecallRanker, RecallCandidate, RecallScore


@dataclass(frozen=True)
class RetrievedMemory:
    record: Dict[str, Any]
    score: RecallScore


class MemoryRetrievalService:
    MAX_LIMIT = 50

    def __init__(self, records: Iterable[Dict[str, Any]]) -> None:
        self._records = self._snapshot(records)
        self._by_id = {record["event_id"]: record for record in self._records}
        self._index = MemoryAssociationIndex()
        self._index.add_records(self._records)

    def retrieve(
        self,
        query_event_id: str,
        limit: int = 10,
        now: Optional[float] = None,
    ) -> List[RetrievedMemory]:
        self._require_event_id(query_event_id)
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise ValueError("limit must be an integer")
        if not 1 <= limit <= self.MAX_LIMIT:
            raise ValueError("limit must be between 1 and {}".format(self.MAX_LIMIT))
        if query_event_id not in self._by_id:
            return []
        timestamp = time.time() if now is None else now
        if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
            raise TypeError("now must be numeric")

        candidates = []
        matched = {}
        for event_id in self._index.neighbours(query_event_id):
            record = self._by_id.get(event_id)
            if record is None:
                continue
            event_timestamp = record.get("ts")
            if isinstance(event_timestamp, bool) or not isinstance(event_timestamp, (int, float)):
                continue
            decay = MemoryDecayPolicy.assess(
                age_seconds=max(0.0, float(timestamp) - float(event_timestamp)),
                tags=record.get("tags", []),
                authority_status=record.get("authority_status"),
            )
            candidates.append(
                RecallCandidate(
                    event_id=event_id,
                    association=1.0,
                    confidence=float(record.get("confidence", 0.5)),
                    salience=decay.salience,
                    authority_status=record.get("authority_status", "unknown"),
                )
            )
            matched[event_id] = record

        ranked = MemoryRecallRanker.rank(candidates)[:limit]
        return [
            RetrievedMemory(copy.deepcopy(matched[item.event_id]), item)
            for item in ranked
        ]

    @staticmethod
    def _snapshot(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        snapshot = []
        seen = set()
        for record in records:
            if not isinstance(record, dict):
                raise TypeError("memory records must be dictionaries")
            event_id = record.get("event_id")
            MemoryRetrievalService._require_event_id(event_id)
            if event_id in seen:
                raise ValueError("duplicate event_id: {}".format(event_id))
            seen.add(event_id)
            snapshot.append(copy.deepcopy(record))
        return snapshot

    @staticmethod
    def _require_event_id(event_id: str) -> None:
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id must be a non-empty string")

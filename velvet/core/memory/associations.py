# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic forward-link and backlink index for memory records."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, DefaultDict, Dict, Iterable, List, Set


class MemoryAssociationIndex:
    """Build exact associations from stable memory event identifiers."""

    def __init__(self) -> None:
        self._forward: DefaultDict[str, Set[str]] = defaultdict(set)
        self._backlinks: DefaultDict[str, Set[str]] = defaultdict(set)

    def add_record(self, record: Dict[str, Any]) -> None:
        event_id = self._event_id(record)
        related = record.get("related_event_ids", [])
        if related is None:
            related = []
        if not isinstance(related, list):
            raise TypeError("related_event_ids must be a list")

        for target in related:
            if not isinstance(target, str) or not target.strip():
                raise ValueError("related_event_ids must contain non-empty strings")
            if target == event_id:
                continue
            self._forward[event_id].add(target)
            self._backlinks[target].add(event_id)

    def add_records(self, records: Iterable[Dict[str, Any]]) -> None:
        for record in records:
            self.add_record(record)

    def forward_links(self, event_id: str) -> List[str]:
        self._require_event_id(event_id)
        return sorted(self._forward.get(event_id, set()))

    def backlinks(self, event_id: str) -> List[str]:
        self._require_event_id(event_id)
        return sorted(self._backlinks.get(event_id, set()))

    def neighbours(self, event_id: str) -> List[str]:
        self._require_event_id(event_id)
        combined = set(self._forward.get(event_id, set()))
        combined.update(self._backlinks.get(event_id, set()))
        return sorted(combined)

    def has_link(self, source_event_id: str, target_event_id: str) -> bool:
        self._require_event_id(source_event_id)
        self._require_event_id(target_event_id)
        return target_event_id in self._forward.get(source_event_id, set())

    @staticmethod
    def _event_id(record: Dict[str, Any]) -> str:
        if not isinstance(record, dict):
            raise TypeError("memory record must be a dictionary")
        event_id = record.get("event_id")
        MemoryAssociationIndex._require_event_id(event_id)
        return event_id

    @staticmethod
    def _require_event_id(event_id: str) -> None:
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id must be a non-empty string")

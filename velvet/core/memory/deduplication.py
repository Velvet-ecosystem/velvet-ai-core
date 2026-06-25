# SPDX-License-Identifier: GPL-3.0-only
"""Conservative exact-match duplicate detection for Velvet memory."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, DefaultDict, Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class DuplicateGroup:
    fingerprint: str
    event_ids: Tuple[str, ...]


class MemoryDuplicateDetector:
    """Find exact duplicate content without deleting or merging records."""

    def fingerprint(self, record: Dict[str, Any]) -> str:
        event_id = self._event_id(record)
        del event_id
        canonical = {
            "kind": record.get("kind"),
            "payload": record.get("payload"),
            "source": record.get("source"),
            "authority_status": record.get("authority_status"),
            "receipt_id": record.get("receipt_id"),
            "related_event_ids": sorted(record.get("related_event_ids", []) or []),
            "tags": sorted(record.get("tags", []) or []),
        }
        encoded = json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def duplicate_groups(
        self, records: Iterable[Dict[str, Any]]
    ) -> List[DuplicateGroup]:
        grouped: DefaultDict[str, List[str]] = defaultdict(list)
        for record in records:
            grouped[self.fingerprint(record)].append(self._event_id(record))

        duplicates = [
            DuplicateGroup(fingerprint, tuple(sorted(event_ids)))
            for fingerprint, event_ids in grouped.items()
            if len(event_ids) > 1
        ]
        return sorted(duplicates, key=lambda group: group.event_ids)

    def is_exact_duplicate(
        self, left: Dict[str, Any], right: Dict[str, Any]
    ) -> bool:
        return self.fingerprint(left) == self.fingerprint(right)

    @staticmethod
    def _event_id(record: Dict[str, Any]) -> str:
        if not isinstance(record, dict):
            raise TypeError("memory record must be a dictionary")
        event_id = record.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id must be a non-empty string")
        if not isinstance(record.get("payload"), dict):
            raise TypeError("memory payload must be a dictionary")
        kind = record.get("kind")
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError("memory kind must be a non-empty string")
        return event_id

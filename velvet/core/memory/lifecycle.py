# SPDX-License-Identifier: GPL-3.0-only
"""Pure transition builders for append-only Velvet memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class MemoryTransition:
    kind: str
    payload: Dict[str, Any]
    authority_status: str
    source: str = "memory-review"
    confidence: Optional[float] = None
    receipt_id: Optional[str] = None
    related_event_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_write_args(self) -> Dict[str, Any]:
        result = {
            "kind": self.kind,
            "payload": dict(self.payload),
            "source": self.source,
            "authority_status": self.authority_status,
            "related_event_ids": list(self.related_event_ids),
            "tags": list(self.tags),
        }
        if self.confidence is not None:
            result["confidence"] = self.confidence
        if self.receipt_id is not None:
            result["receipt_id"] = self.receipt_id
        return result


class MemoryLifecycle:
    """Describe memory changes without writing or authorizing them."""

    @staticmethod
    def candidate(
        payload: Dict[str, Any],
        source: str,
        confidence: Optional[float] = None,
    ) -> MemoryTransition:
        _require_text(source, "source")
        return MemoryTransition(
            kind="candidate",
            payload=dict(payload),
            source=source,
            confidence=confidence,
            authority_status="candidate",
            tags=["candidate"],
        )

    @staticmethod
    def reviewed_fact(
        candidate_event_id: str,
        payload: Dict[str, Any],
        reviewed_by: str,
        receipt_id: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> MemoryTransition:
        _require_text(candidate_event_id, "candidate_event_id")
        _require_text(reviewed_by, "reviewed_by")
        reviewed = dict(payload)
        reviewed["reviewed_by"] = reviewed_by
        return MemoryTransition(
            kind="fact",
            payload=reviewed,
            confidence=confidence,
            authority_status="accepted",
            receipt_id=receipt_id,
            related_event_ids=[candidate_event_id],
            tags=["candidate-reviewed"],
        )

    @staticmethod
    def confidence_revision(
        target_event_id: str,
        confidence: float,
        reason: str,
    ) -> MemoryTransition:
        _require_text(target_event_id, "target_event_id")
        _require_text(reason, "reason")
        return MemoryTransition(
            kind="inference",
            payload={"revision": "confidence", "reason": reason.strip()},
            confidence=confidence,
            authority_status="historical",
            related_event_ids=[target_event_id],
            tags=["confidence-revision"],
        )

    @staticmethod
    def supersession(
        target_event_id: str,
        replacement_kind: str,
        replacement_payload: Dict[str, Any],
        reviewed_by: str,
        reason: str,
        receipt_id: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> MemoryTransition:
        _require_text(target_event_id, "target_event_id")
        _require_text(replacement_kind, "replacement_kind")
        _require_text(reviewed_by, "reviewed_by")
        _require_text(reason, "reason")
        replacement = dict(replacement_payload)
        replacement.update(
            {
                "supersedes": target_event_id,
                "reviewed_by": reviewed_by,
                "reason": reason.strip(),
            }
        )
        return MemoryTransition(
            kind=replacement_kind,
            payload=replacement,
            confidence=confidence,
            authority_status="superseded",
            receipt_id=receipt_id,
            related_event_ids=[target_event_id],
            tags=["supersession"],
        )


def _require_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("{} must be a non-empty string".format(name))

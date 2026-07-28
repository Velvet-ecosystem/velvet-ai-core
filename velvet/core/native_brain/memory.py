# SPDX-License-Identifier: GPL-3.0-only
"""Native Brain v0 memory note builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class NativeMemoryNote:
    """A small pre-continuity memory note from the Native Brain loop."""

    kind: str
    source_event_type: str
    summary: str
    stems: List[str]
    public_safe: bool = True
    authority_requested: bool = False
    authority_granted: bool = False
    continuity_candidate: bool = False
    receipt_anchor: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.kind.strip():
            raise ValueError("memory note kind must be non-empty")
        if not self.source_event_type.strip():
            raise ValueError("source_event_type must be non-empty")
        if not self.summary.strip():
            raise ValueError("summary must be non-empty")
        if not isinstance(self.stems, list) or not all(self.stems):
            raise ValueError("stems must contain at least one non-empty name")

    def to_dict(self) -> Dict[str, Any]:
        out = {
            "kind": self.kind,
            "source_event_type": self.source_event_type,
            "summary": self.summary,
            "stems": list(self.stems),
            "public_safe": self.public_safe,
            "authority_requested": self.authority_requested,
            "authority_granted": self.authority_granted,
            "continuity_candidate": self.continuity_candidate,
        }
        if self.receipt_anchor:
            out["receipt_anchor"] = self.receipt_anchor
        if self.tags:
            out["tags"] = list(self.tags)
        return out

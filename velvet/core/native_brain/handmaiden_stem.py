# SPDX-License-Identifier: GPL-3.0-only
"""Bounded handmaiden stem model for Velvet Native Brain v0."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence


@dataclass(frozen=True)
class StemResult:
    stem: str
    domain_match: bool
    summary: str
    suggested_memory: Dict[str, Any] = field(default_factory=dict)
    authority_requested: bool = False
    blocked: bool = False
    handoff: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stem": self.stem,
            "domain_match": self.domain_match,
            "summary": self.summary,
            "suggested_memory": dict(self.suggested_memory),
            "authority_requested": self.authority_requested,
            "blocked": self.blocked,
            "handoff": list(self.handoff),
        }


@dataclass(frozen=True)
class HandmaidenStem:
    """A bounded named-organ specialty. It interprets and suggests only."""

    name: str
    title: str
    domain: Sequence[str]
    can_observe: Sequence[str]
    can_suggest: Sequence[str]
    must_not: Sequence[str]
    memory_scope: str
    handoff: Dict[str, str] = field(default_factory=dict)

    def handles(self, payload: Mapping[str, Any]) -> bool:
        signals = payload.get("signals", {})
        if isinstance(signals, Mapping):
            for signal_name in signals:
                if str(signal_name) in self.can_observe:
                    return True
        event_type = str(payload.get("event_type", ""))
        return any(item in event_type for item in self.domain)

    def interpret(self, payload: Mapping[str, Any]) -> StemResult:
        match = self.handles(payload)
        if not match:
            return StemResult(self.name, False, "%s did not match this observation." % self.name)
        return StemResult(
            stem=self.name,
            domain_match=True,
            summary="%s observed a domain event." % self.name,
            suggested_memory={"kind": self.memory_scope},
            authority_requested=False,
            handoff=list(self.handoff.values()),
        )

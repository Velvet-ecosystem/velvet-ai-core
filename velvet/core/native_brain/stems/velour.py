# SPDX-License-Identifier: GPL-3.0-only
"""Velour stem: continuity, memory, and receipt awareness."""

from __future__ import annotations

from typing import Any, Mapping

from velvet.core.ghost_can import GHOST_CAN_EVENT_TYPE
from ..handmaiden_stem import HandmaidenStem, StemResult


class VelourStem(HandmaidenStem):
    def __init__(self) -> None:
        super().__init__(
            name="velour",
            title="Continuity and Archive",
            domain=("memory", "continuity", "receipt", "archive"),
            can_observe=("vehicle_speed", "engine_rpm", "ignition_state", "o2_fault"),
            can_suggest=("memory_note", "continuity_candidate", "receipt_anchor"),
            must_not=("grant_authority", "upload", "rewrite_history"),
            memory_scope="observation_only",
            handoff={},
        )

    def interpret(self, payload: Mapping[str, Any]) -> StemResult:
        if payload.get("event_type") != GHOST_CAN_EVENT_TYPE:
            return StemResult(self.name, False, "Velour found no supported memory candidate.")

        profile = payload.get("vehicle_profile") or payload.get("profile") or "Ghost vehicle"
        summary = (
            "Velour marks %s as an observation-only continuity candidate. "
            "No authority, no hardware, no raw execution." % profile
        )
        return StemResult(
            stem=self.name,
            domain_match=True,
            summary=summary,
            suggested_memory={
                "kind": self.memory_scope,
                "continuity_candidate": True,
                "public_safe": True,
            },
            authority_requested=False,
            blocked=False,
            handoff=[],
        )

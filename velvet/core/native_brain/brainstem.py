# SPDX-License-Identifier: GPL-3.0-only
"""Native Brain v0 brainstem priority router."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from velvet.core.ghost_can import GHOST_CAN_EVENT_TYPE

from .safety import NativeBrainSafetyError, validate_no_authority_payload


@dataclass(frozen=True)
class BrainstemDecision:
    priority: str
    reason: str
    blocked: bool = False

    def to_dict(self):
        return {"priority": self.priority, "reason": self.reason, "blocked": self.blocked}


class BrainstemRouter:
    """Small priority router for the preserved first Native Brain loop."""

    def assess(self, payload: Mapping[str, Any]) -> BrainstemDecision:
        try:
            validate_no_authority_payload(payload)
        except NativeBrainSafetyError as exc:
            return BrainstemDecision("critical", str(exc), True)

        if payload.get("event_type") == GHOST_CAN_EVENT_TYPE:
            return BrainstemDecision(
                "low", "synthetic read-only ghost CAN observation", False
            )

        return BrainstemDecision(
            "background", "safe observation outside first Native Brain loop", False
        )

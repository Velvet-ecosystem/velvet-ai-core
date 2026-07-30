"""Deterministic load-sharing records for Velvet's Unified-Organ body.

This module coordinates recommendations only. It does not grant authority,
open network connections, execute tasks, or create independent agent identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import uuid4

from .models import (
    CapabilityAdvertisement,
    HandoffDisposition,
    ReasoningHandoff,
    ReasoningTask,
)


@dataclass(frozen=True)
class DistributedReasoningCoordinator:
    """Select a healthy capable organ using deterministic least-load ordering."""

    maximum_load: float = 0.85

    def offer(
        self,
        task: ReasoningTask,
        advertisements: Iterable[CapabilityAdvertisement],
    ) -> ReasoningHandoff:
        candidates = tuple(
            advertisement
            for advertisement in advertisements
            if task.capability in advertisement.capabilities
            and advertisement.available
            and advertisement.healthy
            and 0.0 <= advertisement.load <= self.maximum_load
        )

        if not candidates:
            return ReasoningHandoff(
                handoff_id=str(uuid4()),
                task_id=task.task_id,
                disposition=HandoffDisposition.ESCALATE,
                target_organ=None,
                rationale="No healthy available organ advertised the required capability.",
            )

        selected = min(candidates, key=lambda item: (item.load, item.organ_name))
        return ReasoningHandoff(
            handoff_id=str(uuid4()),
            task_id=task.task_id,
            disposition=HandoffDisposition.OFFERED,
            target_organ=selected.organ_name,
            rationale="Selected the healthy available capable organ with the lowest load.",
        )

    def refuse(self, task: ReasoningTask, organ_name: str, reason: str) -> ReasoningHandoff:
        if not organ_name.strip() or not reason.strip():
            raise ValueError("organ_name and reason must be non-empty")
        return ReasoningHandoff(
            handoff_id=str(uuid4()),
            task_id=task.task_id,
            disposition=HandoffDisposition.REFUSED,
            target_organ=organ_name.strip(),
            rationale=reason.strip(),
        )

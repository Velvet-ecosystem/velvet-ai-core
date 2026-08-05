"""Memory scheduling boundaries for active, quiet, and presence-required work."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class MemoryTempo(str, Enum):
    ACTIVE = "active"
    QUIET = "quiet"
    PRESENCE_REQUIRED = "presence_required"


class MemoryTask(str, Enum):
    FAST_RETRIEVAL = "fast_retrieval"
    CONTEXT_RECALL = "context_recall"
    OBSERVATION_CAPTURE = "observation_capture"
    INDEX_BUILD = "index_build"
    DUPLICATE_CLEANUP = "duplicate_cleanup"
    CONSOLIDATION = "consolidation"
    ARCHIVE_ORGANIZATION = "archive_organization"
    SUMMARIZATION = "summarization"
    DOCTRINE_CHANGE = "doctrine_change"
    IDENTITY_CHANGE = "identity_change"
    TRUST_BOUNDARY_CHANGE = "trust_boundary_change"
    MODULE_PROMOTION = "module_promotion"
    AUTHORITY_EXPANSION = "authority_expansion"
    PERMANENT_MEMORY_ADOPTION = "permanent_memory_adoption"


TASK_TEMPO: Dict[MemoryTask, MemoryTempo] = {
    MemoryTask.FAST_RETRIEVAL: MemoryTempo.ACTIVE,
    MemoryTask.CONTEXT_RECALL: MemoryTempo.ACTIVE,
    MemoryTask.OBSERVATION_CAPTURE: MemoryTempo.ACTIVE,
    MemoryTask.INDEX_BUILD: MemoryTempo.QUIET,
    MemoryTask.DUPLICATE_CLEANUP: MemoryTempo.QUIET,
    MemoryTask.CONSOLIDATION: MemoryTempo.QUIET,
    MemoryTask.ARCHIVE_ORGANIZATION: MemoryTempo.QUIET,
    MemoryTask.SUMMARIZATION: MemoryTempo.QUIET,
    MemoryTask.DOCTRINE_CHANGE: MemoryTempo.PRESENCE_REQUIRED,
    MemoryTask.IDENTITY_CHANGE: MemoryTempo.PRESENCE_REQUIRED,
    MemoryTask.TRUST_BOUNDARY_CHANGE: MemoryTempo.PRESENCE_REQUIRED,
    MemoryTask.MODULE_PROMOTION: MemoryTempo.PRESENCE_REQUIRED,
    MemoryTask.AUTHORITY_EXPANSION: MemoryTempo.PRESENCE_REQUIRED,
    MemoryTask.PERMANENT_MEMORY_ADOPTION: MemoryTempo.PRESENCE_REQUIRED,
}


@dataclass(frozen=True)
class DreamStateDecision:
    task: MemoryTask
    required_tempo: MemoryTempo
    allowed: bool
    prepare_only: bool
    refusal_reason: str
    authority_granted: bool = False


def decide_memory_task(
    task: MemoryTask,
    *,
    current_tempo: MemoryTempo,
    physical_presence_verified: bool,
    power_allows_background_work: bool,
) -> DreamStateDecision:
    required = TASK_TEMPO[task]

    if required == MemoryTempo.PRESENCE_REQUIRED:
        allowed = (
            current_tempo == MemoryTempo.PRESENCE_REQUIRED
            and physical_presence_verified
        )
        return DreamStateDecision(
            task=task,
            required_tempo=required,
            allowed=allowed,
            prepare_only=not allowed,
            refusal_reason="" if allowed else "owner_presence_required",
        )

    if required == MemoryTempo.QUIET:
        allowed = (
            current_tempo == MemoryTempo.QUIET
            and power_allows_background_work
        )
        return DreamStateDecision(
            task=task,
            required_tempo=required,
            allowed=allowed,
            prepare_only=False,
            refusal_reason="" if allowed else "quiet_phase_or_power_required",
        )

    allowed = current_tempo in (MemoryTempo.ACTIVE, MemoryTempo.QUIET)
    return DreamStateDecision(
        task=task,
        required_tempo=required,
        allowed=allowed,
        prepare_only=False,
        refusal_reason="" if allowed else "active_memory_phase_required",
    )

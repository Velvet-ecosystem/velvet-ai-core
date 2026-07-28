# SPDX-License-Identifier: GPL-3.0-only
"""Lightweight, non-authoritative cognition contracts for Native Brain."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


class CognitiveOutcome(str, Enum):
    OBSERVE = "observe"
    WAIT = "wait"
    SILENCE = "silence"
    QUESTION = "question"
    REMEMBER = "remember"
    CORRELATE = "correlate"
    SPEAK = "speak"
    PROPOSE = "propose"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class ObservationEnvelope:
    """A bounded observation, never an instruction or authority object."""

    event_type: str
    source: str
    payload: Mapping[str, Any]
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 1.0
    freshness_seconds: float | None = None
    simulated: bool = False
    read_only: bool = True

    def __post_init__(self) -> None:
        if not self.event_type.strip() or not self.source.strip():
            raise ValueError("event_type and source are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.read_only:
            raise ValueError("Native Brain accepts read-only observations only")


@dataclass(frozen=True)
class CognitiveDecision:
    outcome: CognitiveOutcome
    reason: str
    confidence: float
    interrupt: bool = False
    question: str | None = None
    proposal: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("reason is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.interrupt and self.outcome not in {CognitiveOutcome.SPEAK, CognitiveOutcome.ESCALATE}:
            raise ValueError("only speak or escalate decisions may interrupt")
        if self.outcome is CognitiveOutcome.QUESTION and not self.question:
            raise ValueError("question outcome requires question text")
        if self.outcome is CognitiveOutcome.PROPOSE and self.proposal is None:
            raise ValueError("proposal outcome requires a bounded proposal")

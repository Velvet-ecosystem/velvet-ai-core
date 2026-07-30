"""Shared data models for the Native Brain decision spine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Tuple


class Importance(str, Enum):
    """Initial deterministic importance levels."""

    ROUTINE = "routine"
    INTERESTING = "interesting"
    IMPORTANT = "important"
    CRITICAL = "critical"


class Recommendation(str, Enum):
    """Recommendations the brain may return without executing them."""

    IGNORE = "ignore"
    OBSERVE = "observe"
    NOTIFY = "notify"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class Observation:
    event_type: str
    source: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    observed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass(frozen=True)
class BrainContext:
    runtime_mode: str = "unknown"
    court_permissions: Tuple[str, ...] = ()
    presence: str = "unknown"
    active_scene: str | None = None
    recent_events: Tuple[str, ...] = ()
    active_organs: Tuple[str, ...] = ()
    world_state: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Understanding:
    observation: Observation
    context: BrainContext
    summary: str


@dataclass(frozen=True)
class Evaluation:
    understanding: Understanding
    importance: Importance
    confidence: float
    reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Judgment:
    evaluation: Evaluation
    recommendation: Recommendation
    rationale: str


@dataclass(frozen=True)
class DecisionReceipt:
    judgment: Judgment
    receipt_id: str
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def recommendation(self) -> Recommendation:
        return self.judgment.recommendation

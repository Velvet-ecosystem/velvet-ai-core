# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic cognitive heartbeat for Velvet Native Brain.

Every cycle checks its keys, evaluates presence, records a bounded trace, and
returns to rest. It never loops internally and never grants authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Tuple

from .cognition import CognitiveDecision, CognitiveOutcome, ObservationEnvelope
from .presence import PresenceContext, PresenceGate
from .self_orientation import NoDriftIntegrityGate, SelfOrientation


class CognitiveKey(str, Enum):
    IDENTITY = "identity"
    CONTINUITY = "continuity"
    CONTEXT = "context"
    OBSERVATION = "observation"
    INTEGRITY = "integrity"


class CycleStage(str, Enum):
    ORIENT_SELF = "orient-self"
    CHECK_KEYS = "check-keys"
    OBSERVE = "observe"
    PRESENCE = "presence"
    CHOOSE = "choose"
    REST = "rest"


@dataclass(frozen=True)
class KeyState:
    key: CognitiveKey
    satisfied: bool
    reason: str


@dataclass(frozen=True)
class CycleTraceEntry:
    stage: CycleStage
    detail: str


@dataclass(frozen=True)
class CognitiveCycleResult:
    decision: CognitiveDecision
    keys: Tuple[KeyState, ...]
    trace: Tuple[CycleTraceEntry, ...]
    rested: bool = True
    authority: str = "none"

    @property
    def ready(self) -> bool:
        return all(state.satisfied for state in self.keys)

    def to_dict(self) -> Mapping[str, object]:
        return {
            "outcome": self.decision.outcome.value,
            "reason": self.decision.reason,
            "confidence": self.decision.confidence,
            "interrupt": self.decision.interrupt,
            "question": self.decision.question,
            "keys": tuple(
                {"key": state.key.value, "satisfied": state.satisfied, "reason": state.reason}
                for state in self.keys
            ),
            "trace": tuple(
                {"stage": entry.stage.value, "detail": entry.detail} for entry in self.trace
            ),
            "rested": self.rested,
            "authority": self.authority,
        }


class CognitiveCycle:
    """Run one bounded model-free Native Brain cycle."""

    def __init__(self, baseline_identity, presence_gate: PresenceGate | None = None) -> None:
        self._integrity_gate = NoDriftIntegrityGate(baseline_identity)
        self._presence_gate = presence_gate or PresenceGate()

    def run(
        self,
        orientation: SelfOrientation,
        observation: ObservationEnvelope | None,
        presence: PresenceContext,
    ) -> CognitiveCycleResult:
        trace = [CycleTraceEntry(CycleStage.ORIENT_SELF, "self orientation loaded")]
        integrity = self._integrity_gate.evaluate(orientation)
        keys = (
            KeyState(CognitiveKey.IDENTITY, orientation.identity.name == "Velvet", "constitutional identity is Velvet"),
            KeyState(CognitiveKey.CONTINUITY, orientation.continuity_verified, "Riven continuity verified" if orientation.continuity_verified else "Riven continuity missing"),
            KeyState(CognitiveKey.CONTEXT, orientation.runtime_context_verified, "Runtime context verified" if orientation.runtime_context_verified else "Runtime context missing"),
            KeyState(CognitiveKey.OBSERVATION, observation is not None, "bounded observation available" if observation is not None else "no observation available"),
            KeyState(CognitiveKey.INTEGRITY, integrity.aligned, "No Drift gate aligned" if integrity.aligned else "No Drift gate blocked"),
        )
        trace.append(CycleTraceEntry(CycleStage.CHECK_KEYS, "cognitive keys evaluated"))

        failed = tuple(state for state in keys if not state.satisfied)
        if failed:
            missing = ", ".join(state.key.value for state in failed)
            outcome = CognitiveOutcome.WAIT if observation is None else CognitiveOutcome.SILENCE
            decision = CognitiveDecision(
                outcome=outcome,
                reason=f"cognitive cycle held because required keys are unavailable: {missing}",
                confidence=1.0,
            )
            trace.append(CycleTraceEntry(CycleStage.CHOOSE, decision.reason))
            trace.append(CycleTraceEntry(CycleStage.REST, "cycle ended without forcing progress"))
            return CognitiveCycleResult(decision=decision, keys=keys, trace=tuple(trace))

        assert observation is not None
        trace.append(CycleTraceEntry(CycleStage.OBSERVE, f"accepted {observation.event_type}"))
        decision = self._presence_gate.decide(observation, presence)
        trace.append(CycleTraceEntry(CycleStage.PRESENCE, decision.reason))
        trace.append(CycleTraceEntry(CycleStage.CHOOSE, decision.outcome.value))
        trace.append(CycleTraceEntry(CycleStage.REST, "cycle completed and returned to baseline"))
        return CognitiveCycleResult(decision=decision, keys=keys, trace=tuple(trace))

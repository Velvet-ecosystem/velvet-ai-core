# SPDX-License-Identifier: GPL-3.0-only
"""Integrated deterministic heartbeat for the Velvet Native Brain.

The integrated cycle joins bounded cognitive layers without turning any result
into speech, memory, placement, authorization, execution, or actuation. Every
run is finite, traceable, and returns to rest.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Mapping, Optional, Tuple

from .attention import AttentionAssessment, AttentionContext, AttentionEngine
from .cognition import CognitiveDecision, CognitiveOutcome, ObservationEnvelope
from .curiosity import (
    CuriosityAssessment,
    CuriosityContext,
    CuriosityDisposition,
    CuriosityEngine,
)
from .cycle import CognitiveKey, KeyState
from .expectations import (
    ExpectationAssessment,
    ExpectationContext,
    ExpectationDisposition,
    ExpectationEngine,
)
from .intents import (
    IntentAssessment,
    IntentContext,
    IntentDisposition,
    IntentEngine,
)
from .judgment import (
    JudgmentAssessment,
    JudgmentContext,
    JudgmentDisposition,
    JudgmentEngine,
)
from .patterns import (
    PatternAssessment,
    PatternContext,
    PatternDisposition,
    PatternEngine,
)
from .presence import PresenceContext, PresenceGate
from .self_orientation import NoDriftIntegrityGate, SelfOrientation


class IntegratedCycleStage(str, Enum):
    ORIENT_SELF = "orient-self"
    CHECK_KEYS = "check-keys"
    OBSERVE = "observe"
    PRESENCE = "presence"
    ATTENTION = "attention"
    CURIOSITY = "curiosity"
    JUDGMENT = "judgment"
    PATTERN = "pattern"
    EXPECTATION = "expectation"
    INTENT = "intent"
    SAFETY = "safety"
    CHOOSE = "choose"
    REST = "rest"


class IntegratedCycleOutcome(str, Enum):
    HELD = "held"
    SAFETY_DEFERRED = "safety_deferred"
    QUIET_OBSERVATION = "quiet_observation"
    QUESTION_CANDIDATE = "question_candidate"
    JUDGMENT_READY = "judgment_ready"
    PATTERN_CANDIDATE = "pattern_candidate"
    EXPECTATION_CANDIDATE = "expectation_candidate"
    INTENT_CANDIDATE = "intent_candidate"


@dataclass(frozen=True)
class IntegratedCycleTraceEntry:
    stage: IntegratedCycleStage
    detail: str


@dataclass(frozen=True)
class IntegratedCycleContext:
    """All bounded domain context needed for one integrated heartbeat."""

    presence: PresenceContext = field(default_factory=PresenceContext)
    attention: AttentionContext = field(default_factory=AttentionContext)
    curiosity: CuriosityContext = field(default_factory=CuriosityContext)
    judgment: JudgmentContext = field(default_factory=JudgmentContext)
    pattern: PatternContext = field(default_factory=PatternContext)
    expectation: ExpectationContext = field(default_factory=ExpectationContext)
    intent: IntentContext = field(default_factory=IntentContext)


@dataclass(frozen=True)
class IntegratedCycleResult:
    outcome: IntegratedCycleOutcome
    reason: str
    keys: Tuple[KeyState, ...]
    trace: Tuple[IntegratedCycleTraceEntry, ...]
    presence_decision: Optional[CognitiveDecision] = None
    attention: Optional[AttentionAssessment] = None
    curiosity: Optional[CuriosityAssessment] = None
    judgment: Optional[JudgmentAssessment] = None
    pattern: Optional[PatternAssessment] = None
    expectation: Optional[ExpectationAssessment] = None
    intent: Optional[IntentAssessment] = None
    stopped_at: IntegratedCycleStage = IntegratedCycleStage.REST
    rested: bool = True
    safety_deferred: bool = False
    canonical: bool = False
    speaking_authorized: bool = False
    memory_write_authorized: bool = False
    runtime_placement_authorized: bool = False
    court_authorized: bool = False
    execution_authorized: bool = False
    actuation_authorized: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("integrated cycle reason is required")
        if not self.trace or self.trace[-1].stage is not IntegratedCycleStage.REST:
            raise ValueError("integrated cycles must end in rest")
        if not self.rested:
            raise ValueError("integrated cycles must return to rest")
        if self.safety_deferred != (
            self.outcome is IntegratedCycleOutcome.SAFETY_DEFERRED
        ):
            raise ValueError("safety_deferred must match the cycle outcome")
        if self.canonical:
            raise ValueError("integrated cycle results must remain non-canonical")
        if (
            self.speaking_authorized
            or self.memory_write_authorized
            or self.runtime_placement_authorized
            or self.court_authorized
            or self.execution_authorized
            or self.actuation_authorized
        ):
            raise ValueError("integrated cycles cannot authorize downstream effects")
        if self.authority != "none":
            raise ValueError("integrated cycles cannot carry authority")

    @property
    def ready(self) -> bool:
        return all(state.satisfied for state in self.keys)

    def to_dict(self) -> Mapping[str, object]:
        return {
            "outcome": self.outcome.value,
            "reason": self.reason,
            "keys": tuple(
                {
                    "key": state.key.value,
                    "satisfied": state.satisfied,
                    "reason": state.reason,
                }
                for state in self.keys
            ),
            "trace": tuple(
                {"stage": entry.stage.value, "detail": entry.detail}
                for entry in self.trace
            ),
            "presence_outcome": (
                None
                if self.presence_decision is None
                else self.presence_decision.outcome.value
            ),
            "attention_priority": (
                None if self.attention is None else self.attention.priority
            ),
            "curiosity_disposition": (
                None if self.curiosity is None else self.curiosity.disposition.value
            ),
            "judgment_disposition": (
                None if self.judgment is None else self.judgment.disposition.value
            ),
            "pattern_state": None if self.pattern is None else self.pattern.state.value,
            "expectation_state": (
                None if self.expectation is None else self.expectation.state.value
            ),
            "intent_state": None if self.intent is None else self.intent.state.value,
            "stopped_at": self.stopped_at.value,
            "rested": self.rested,
            "safety_deferred": self.safety_deferred,
            "canonical": self.canonical,
            "authority": self.authority,
        }


class IntegratedCognitiveCycle:
    """Run one complete, finite Native Brain cognitive heartbeat."""

    def __init__(
        self,
        baseline_identity,
        presence_gate: Optional[PresenceGate] = None,
        attention_engine: Optional[AttentionEngine] = None,
        curiosity_engine: Optional[CuriosityEngine] = None,
        judgment_engine: Optional[JudgmentEngine] = None,
        pattern_engine: Optional[PatternEngine] = None,
        expectation_engine: Optional[ExpectationEngine] = None,
        intent_engine: Optional[IntentEngine] = None,
    ) -> None:
        self._integrity_gate = NoDriftIntegrityGate(baseline_identity)
        self._presence_gate = presence_gate or PresenceGate()
        self._attention_engine = attention_engine or AttentionEngine()
        self._curiosity_engine = curiosity_engine or CuriosityEngine()
        self._judgment_engine = judgment_engine or JudgmentEngine()
        self._pattern_engine = pattern_engine or PatternEngine()
        self._expectation_engine = expectation_engine or ExpectationEngine()
        self._intent_engine = intent_engine or IntentEngine()

    def run(
        self,
        orientation: SelfOrientation,
        observation: Optional[ObservationEnvelope],
        context: IntegratedCycleContext,
    ) -> IntegratedCycleResult:
        trace = [
            IntegratedCycleTraceEntry(
                IntegratedCycleStage.ORIENT_SELF,
                "self orientation loaded",
            )
        ]
        integrity = self._integrity_gate.evaluate(orientation)
        keys = self._keys(orientation, observation, integrity.aligned)
        trace.append(
            IntegratedCycleTraceEntry(
                IntegratedCycleStage.CHECK_KEYS,
                "cognitive keys evaluated",
            )
        )

        failed = tuple(state for state in keys if not state.satisfied)
        if failed:
            missing = ", ".join(state.key.value for state in failed)
            return self._finish(
                outcome=IntegratedCycleOutcome.HELD,
                reason=f"required cognitive keys are unavailable: {missing}",
                keys=keys,
                trace=trace,
                stopped_at=IntegratedCycleStage.CHECK_KEYS,
            )

        assert observation is not None
        trace.append(
            IntegratedCycleTraceEntry(
                IntegratedCycleStage.OBSERVE,
                f"accepted {observation.event_type}",
            )
        )

        presence_decision = self._presence_gate.decide(observation, context.presence)
        trace.append(
            IntegratedCycleTraceEntry(
                IntegratedCycleStage.PRESENCE,
                presence_decision.reason,
            )
        )

        attention = self._attention_engine.assess(observation, context.attention)
        trace.append(
            IntegratedCycleTraceEntry(
                IntegratedCycleStage.ATTENTION,
                f"{attention.priority}:{attention.maturity.value}:{attention.score:.4f}",
            )
        )

        if (
            presence_decision.outcome is CognitiveOutcome.ESCALATE
            or attention.priority == "critical"
            or "safety-relevant" in attention.reasons
        ):
            return self._finish(
                outcome=IntegratedCycleOutcome.SAFETY_DEFERRED,
                reason="safety path owns the next decision",
                keys=keys,
                trace=trace,
                stopped_at=IntegratedCycleStage.SAFETY,
                presence_decision=presence_decision,
                attention=attention,
                safety_deferred=True,
            )

        curiosity_context = replace(
            context.curiosity,
            addressed=context.presence.addressed,
        )
        curiosity = self._curiosity_engine.assess(
            observation,
            attention,
            curiosity_context,
        )
        trace.append(
            IntegratedCycleTraceEntry(
                IntegratedCycleStage.CURIOSITY,
                curiosity.disposition.value,
            )
        )
        if curiosity.disposition is CuriosityDisposition.DEFER_TO_SAFETY:
            return self._finish(
                outcome=IntegratedCycleOutcome.SAFETY_DEFERRED,
                reason="curiosity deferred to the safety path",
                keys=keys,
                trace=trace,
                stopped_at=IntegratedCycleStage.SAFETY,
                presence_decision=presence_decision,
                attention=attention,
                curiosity=curiosity,
                safety_deferred=True,
            )

        judgment_context = replace(
            context.judgment,
            integrity_aligned=context.judgment.integrity_aligned and integrity.aligned,
            continuity_verified=(
                context.judgment.continuity_verified
                and orientation.continuity_verified
            ),
            runtime_context_verified=(
                context.judgment.runtime_context_verified
                and orientation.runtime_context_verified
            ),
        )
        judgment = self._judgment_engine.assess(
            observation,
            attention,
            curiosity,
            judgment_context,
        )
        trace.append(
            IntegratedCycleTraceEntry(
                IntegratedCycleStage.JUDGMENT,
                f"{judgment.disposition.value}:{judgment.band.value}:{judgment.confidence:.4f}",
            )
        )
        if judgment.disposition is JudgmentDisposition.DEFER_TO_SAFETY:
            return self._finish(
                outcome=IntegratedCycleOutcome.SAFETY_DEFERRED,
                reason="judgment deferred to the safety path",
                keys=keys,
                trace=trace,
                stopped_at=IntegratedCycleStage.SAFETY,
                presence_decision=presence_decision,
                attention=attention,
                curiosity=curiosity,
                judgment=judgment,
                safety_deferred=True,
            )
        if judgment.disposition is JudgmentDisposition.BLOCKED:
            return self._finish(
                outcome=IntegratedCycleOutcome.HELD,
                reason="judgment stopped at a verified boundary",
                keys=keys,
                trace=trace,
                stopped_at=IntegratedCycleStage.JUDGMENT,
                presence_decision=presence_decision,
                attention=attention,
                curiosity=curiosity,
                judgment=judgment,
            )

        pattern_context = replace(
            context.pattern,
            integrity_aligned=context.pattern.integrity_aligned and integrity.aligned,
            continuity_verified=(
                context.pattern.continuity_verified
                and orientation.continuity_verified
            ),
            runtime_context_verified=(
                context.pattern.runtime_context_verified
                and orientation.runtime_context_verified
            ),
        )
        pattern = self._pattern_engine.assess(
            observation,
            attention,
            judgment,
            pattern_context,
        )
        trace.append(
            IntegratedCycleTraceEntry(
                IntegratedCycleStage.PATTERN,
                f"{pattern.disposition.value}:{pattern.state.value}",
            )
        )
        if pattern.disposition is PatternDisposition.DEFER_TO_SAFETY:
            return self._finish(
                outcome=IntegratedCycleOutcome.SAFETY_DEFERRED,
                reason="pattern review deferred to the safety path",
                keys=keys,
                trace=trace,
                stopped_at=IntegratedCycleStage.SAFETY,
                presence_decision=presence_decision,
                attention=attention,
                curiosity=curiosity,
                judgment=judgment,
                pattern=pattern,
                safety_deferred=True,
            )
        if pattern.disposition is PatternDisposition.BLOCKED:
            return self._finish(
                outcome=IntegratedCycleOutcome.HELD,
                reason="pattern review stopped at a verified boundary",
                keys=keys,
                trace=trace,
                stopped_at=IntegratedCycleStage.PATTERN,
                presence_decision=presence_decision,
                attention=attention,
                curiosity=curiosity,
                judgment=judgment,
                pattern=pattern,
            )

        expectation_context = replace(
            context.expectation,
            integrity_aligned=(
                context.expectation.integrity_aligned and integrity.aligned
            ),
            continuity_verified=(
                context.expectation.continuity_verified
                and orientation.continuity_verified
            ),
            runtime_context_verified=(
                context.expectation.runtime_context_verified
                and orientation.runtime_context_verified
            ),
        )
        expectation = self._expectation_engine.assess(pattern, expectation_context)
        trace.append(
            IntegratedCycleTraceEntry(
                IntegratedCycleStage.EXPECTATION,
                f"{expectation.disposition.value}:{expectation.state.value}",
            )
        )
        if expectation.disposition is ExpectationDisposition.DEFER_TO_SAFETY:
            return self._finish(
                outcome=IntegratedCycleOutcome.SAFETY_DEFERRED,
                reason="expectation review deferred to the safety path",
                keys=keys,
                trace=trace,
                stopped_at=IntegratedCycleStage.SAFETY,
                presence_decision=presence_decision,
                attention=attention,
                curiosity=curiosity,
                judgment=judgment,
                pattern=pattern,
                expectation=expectation,
                safety_deferred=True,
            )
        if expectation.disposition is ExpectationDisposition.BLOCKED:
            return self._finish(
                outcome=IntegratedCycleOutcome.HELD,
                reason="expectation review stopped at a verified boundary",
                keys=keys,
                trace=trace,
                stopped_at=IntegratedCycleStage.EXPECTATION,
                presence_decision=presence_decision,
                attention=attention,
                curiosity=curiosity,
                judgment=judgment,
                pattern=pattern,
                expectation=expectation,
            )

        speech_allowed = presence_decision.outcome in {
            CognitiveOutcome.SPEAK,
            CognitiveOutcome.QUESTION,
        }
        intent_context = replace(
            context.intent,
            integrity_aligned=context.intent.integrity_aligned and integrity.aligned,
            continuity_verified=(
                context.intent.continuity_verified and orientation.continuity_verified
            ),
            runtime_context_verified=(
                context.intent.runtime_context_verified
                and orientation.runtime_context_verified
            ),
            presence_allows_speech=speech_allowed,
        )
        intent = self._intent_engine.assess(
            judgment,
            expectation,
            intent_context,
        )
        trace.append(
            IntegratedCycleTraceEntry(
                IntegratedCycleStage.INTENT,
                f"{intent.disposition.value}:{intent.state.value}",
            )
        )
        if intent.disposition is IntentDisposition.DEFER_TO_SAFETY:
            return self._finish(
                outcome=IntegratedCycleOutcome.SAFETY_DEFERRED,
                reason="intent review deferred to the safety path",
                keys=keys,
                trace=trace,
                stopped_at=IntegratedCycleStage.SAFETY,
                presence_decision=presence_decision,
                attention=attention,
                curiosity=curiosity,
                judgment=judgment,
                pattern=pattern,
                expectation=expectation,
                intent=intent,
                safety_deferred=True,
            )
        if intent.disposition is IntentDisposition.BLOCKED:
            return self._finish(
                outcome=IntegratedCycleOutcome.HELD,
                reason="intent review stopped at a verified boundary",
                keys=keys,
                trace=trace,
                stopped_at=IntegratedCycleStage.INTENT,
                presence_decision=presence_decision,
                attention=attention,
                curiosity=curiosity,
                judgment=judgment,
                pattern=pattern,
                expectation=expectation,
                intent=intent,
            )

        outcome, reason = self._choose_outcome(
            curiosity,
            judgment,
            pattern,
            expectation,
            intent,
        )
        return self._finish(
            outcome=outcome,
            reason=reason,
            keys=keys,
            trace=trace,
            stopped_at=IntegratedCycleStage.INTENT,
            presence_decision=presence_decision,
            attention=attention,
            curiosity=curiosity,
            judgment=judgment,
            pattern=pattern,
            expectation=expectation,
            intent=intent,
        )

    @staticmethod
    def _keys(
        orientation: SelfOrientation,
        observation: Optional[ObservationEnvelope],
        integrity_aligned: bool,
    ) -> Tuple[KeyState, ...]:
        return (
            KeyState(
                CognitiveKey.IDENTITY,
                orientation.identity.name == "Velvet",
                "constitutional identity is Velvet",
            ),
            KeyState(
                CognitiveKey.CONTINUITY,
                orientation.continuity_verified,
                (
                    "Riven continuity verified"
                    if orientation.continuity_verified
                    else "Riven continuity missing"
                ),
            ),
            KeyState(
                CognitiveKey.CONTEXT,
                orientation.runtime_context_verified,
                (
                    "Runtime context verified"
                    if orientation.runtime_context_verified
                    else "Runtime context missing"
                ),
            ),
            KeyState(
                CognitiveKey.OBSERVATION,
                observation is not None,
                (
                    "bounded observation available"
                    if observation is not None
                    else "no observation available"
                ),
            ),
            KeyState(
                CognitiveKey.INTEGRITY,
                integrity_aligned,
                (
                    "No Drift gate aligned"
                    if integrity_aligned
                    else "No Drift gate blocked"
                ),
            ),
        )

    @staticmethod
    def _choose_outcome(
        curiosity: CuriosityAssessment,
        judgment: JudgmentAssessment,
        pattern: PatternAssessment,
        expectation: ExpectationAssessment,
        intent: IntentAssessment,
    ) -> Tuple[IntegratedCycleOutcome, str]:
        if intent.candidate is not None:
            return (
                IntegratedCycleOutcome.INTENT_CANDIDATE,
                "the heartbeat produced a bounded proposal-only intent candidate",
            )
        if expectation.candidate is not None:
            return (
                IntegratedCycleOutcome.EXPECTATION_CANDIDATE,
                "the heartbeat retained a finite expectation candidate",
            )
        if pattern.candidate is not None:
            return (
                IntegratedCycleOutcome.PATTERN_CANDIDATE,
                "the heartbeat retained a non-canonical pattern candidate",
            )
        if judgment.presentation_candidate:
            return (
                IntegratedCycleOutcome.JUDGMENT_READY,
                "supported judgment is ready for downstream presentation review",
            )
        if curiosity.disposition is CuriosityDisposition.QUESTION_CANDIDATE:
            return (
                IntegratedCycleOutcome.QUESTION_CANDIDATE,
                "curiosity produced a question candidate without speaking",
            )
        return (
            IntegratedCycleOutcome.QUIET_OBSERVATION,
            "the heartbeat completed quietly without forcing a conclusion",
        )

    @staticmethod
    def _finish(
        *,
        outcome: IntegratedCycleOutcome,
        reason: str,
        keys: Tuple[KeyState, ...],
        trace: list[IntegratedCycleTraceEntry],
        stopped_at: IntegratedCycleStage,
        presence_decision: Optional[CognitiveDecision] = None,
        attention: Optional[AttentionAssessment] = None,
        curiosity: Optional[CuriosityAssessment] = None,
        judgment: Optional[JudgmentAssessment] = None,
        pattern: Optional[PatternAssessment] = None,
        expectation: Optional[ExpectationAssessment] = None,
        intent: Optional[IntentAssessment] = None,
        safety_deferred: bool = False,
    ) -> IntegratedCycleResult:
        if stopped_at is IntegratedCycleStage.SAFETY:
            trace.append(
                IntegratedCycleTraceEntry(
                    IntegratedCycleStage.SAFETY,
                    reason,
                )
            )
        trace.append(
            IntegratedCycleTraceEntry(
                IntegratedCycleStage.CHOOSE,
                outcome.value,
            )
        )
        trace.append(
            IntegratedCycleTraceEntry(
                IntegratedCycleStage.REST,
                "heartbeat completed and returned to baseline",
            )
        )
        return IntegratedCycleResult(
            outcome=outcome,
            reason=reason,
            keys=keys,
            trace=tuple(trace),
            presence_decision=presence_decision,
            attention=attention,
            curiosity=curiosity,
            judgment=judgment,
            pattern=pattern,
            expectation=expectation,
            intent=intent,
            stopped_at=stopped_at,
            safety_deferred=safety_deferred,
        )

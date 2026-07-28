# SPDX-License-Identifier: GPL-3.0-only
"""Presence-before-speech judgment for Native Brain."""

from __future__ import annotations

from dataclasses import dataclass

from .cognition import CognitiveDecision, CognitiveOutcome, ObservationEnvelope


@dataclass(frozen=True)
class PresenceContext:
    addressed: bool = False
    another_person_speaking: bool = False
    owner_concentrating: bool = False
    urgent: bool = False
    safety_relevant: bool = False
    useful_now: bool = False
    uncertainty: float = 0.0


class PresenceGate:
    """Choose whether Velvet should enter the moment without using a model."""

    def decide(self, observation: ObservationEnvelope, context: PresenceContext) -> CognitiveDecision:
        if context.urgent or context.safety_relevant:
            return CognitiveDecision(
                CognitiveOutcome.ESCALATE,
                reason="time-sensitive safety value exceeds silence",
                confidence=max(observation.confidence, 0.8),
                interrupt=True,
            )

        if context.another_person_speaking or context.owner_concentrating:
            return CognitiveDecision(
                CognitiveOutcome.WAIT,
                reason="the moment belongs to someone else or requires concentration",
                confidence=0.9,
            )

        if context.uncertainty >= 0.6 and context.addressed:
            return CognitiveDecision(
                CognitiveOutcome.QUESTION,
                reason="a question reduces uncertainty better than a weak answer",
                confidence=1.0 - min(context.uncertainty, 1.0),
                question="I am missing enough context to answer well. Could you clarify?",
            )

        if context.addressed:
            return CognitiveDecision(
                CognitiveOutcome.SPEAK,
                reason="Velvet was addressed and speaking is appropriate",
                confidence=observation.confidence,
            )

        if context.useful_now:
            return CognitiveDecision(
                CognitiveOutcome.SPEAK,
                reason="the observation improves understanding now without requiring interruption",
                confidence=observation.confidence,
            )

        return CognitiveDecision(
            CognitiveOutcome.SILENCE,
            reason="remaining present adds more value than speaking",
            confidence=0.95,
        )

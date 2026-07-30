"""Deterministic significance evaluation for Native Brain understandings."""

from __future__ import annotations

from .models import (
    Consequence,
    ErrorCost,
    Evaluation,
    EvaluationProfile,
    Importance,
    Understanding,
    Urgency,
)


_IMPORTANCE_RANK = {
    Importance.ROUTINE: 0,
    Importance.INTERESTING: 1,
    Importance.IMPORTANT: 2,
    Importance.CRITICAL: 3,
}

_CONSEQUENCE_IMPORTANCE = {
    Consequence.NEGLIGIBLE: Importance.ROUTINE,
    Consequence.LIMITED: Importance.INTERESTING,
    Consequence.SERIOUS: Importance.IMPORTANT,
    Consequence.SEVERE: Importance.CRITICAL,
}

_URGENCY_IMPORTANCE = {
    Urgency.ROUTINE: Importance.ROUTINE,
    Urgency.ELEVATED: Importance.INTERESTING,
    Urgency.URGENT: Importance.IMPORTANT,
    Urgency.IMMEDIATE: Importance.CRITICAL,
}


class Evaluator:
    """Apply an explicit profile without trusting an event to grade itself."""

    def evaluate(
        self,
        understanding: Understanding,
        profile: EvaluationProfile | None = None,
    ) -> Evaluation:
        active = profile or EvaluationProfile()
        if not 0.0 <= active.confidence <= 1.0:
            raise ValueError("evaluation profile confidence must be between 0 and 1")

        consequence_importance = _CONSEQUENCE_IMPORTANCE[
            active.potential_consequence
        ]
        urgency_importance = _URGENCY_IMPORTANCE[active.urgency]
        importance = max(
            (consequence_importance, urgency_importance),
            key=lambda item: _IMPORTANCE_RANK[item],
        )

        reasons = active.reasons or (
            "Explicit profile supplied no evidence reasons",
        )
        return Evaluation(
            understanding=understanding,
            importance=importance,
            confidence=active.confidence,
            reasons=reasons,
            urgency=active.urgency,
            potential_consequence=active.potential_consequence,
            cost_of_dismissal=active.cost_of_dismissal,
            cost_of_escalation=active.cost_of_escalation,
        )

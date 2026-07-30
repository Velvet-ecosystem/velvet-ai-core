"""Recommendation-only judgment stage for the Native Brain."""

from .models import (
    Consequence,
    ErrorCost,
    Evaluation,
    Judgment,
    Recommendation,
    Urgency,
)


_COST_RANK = {
    ErrorCost.LOW: 0,
    ErrorCost.MODERATE: 1,
    ErrorCost.HIGH: 2,
    ErrorCost.EXTREME: 3,
}

_CONSEQUENCE_RANK = {
    Consequence.NEGLIGIBLE: 0,
    Consequence.LIMITED: 1,
    Consequence.SERIOUS: 2,
    Consequence.SEVERE: 3,
}

_URGENCY_RANK = {
    Urgency.ROUTINE: 0,
    Urgency.ELEVATED: 1,
    Urgency.URGENT: 2,
    Urgency.IMMEDIATE: 3,
}


class Judge:
    """Raise recommendation severity without authorizing or executing anything."""

    def judge(self, evaluation: Evaluation) -> Judgment:
        dismissal_cost = _COST_RANK[evaluation.cost_of_dismissal]
        escalation_cost = _COST_RANK[evaluation.cost_of_escalation]
        consequence = _CONSEQUENCE_RANK[evaluation.potential_consequence]
        urgency = _URGENCY_RANK[evaluation.urgency]

        if urgency == _URGENCY_RANK[Urgency.IMMEDIATE] and consequence >= _CONSEQUENCE_RANK[Consequence.SERIOUS]:
            return Judgment(
                evaluation=evaluation,
                recommendation=Recommendation.ESCALATE,
                rationale=(
                    "Immediate urgency and serious potential consequence justify "
                    "governed escalation review, not execution."
                ),
            )

        if (
            evaluation.cost_of_dismissal is ErrorCost.EXTREME
            and dismissal_cost > escalation_cost
        ):
            return Judgment(
                evaluation=evaluation,
                recommendation=Recommendation.ESCALATE,
                rationale=(
                    "The cost of dismissing a true condition is extreme and exceeds "
                    "the cost of escalation; recommend governed escalation only."
                ),
            )

        if dismissal_cost > escalation_cost and (
            evaluation.cost_of_dismissal is ErrorCost.HIGH
            or (
                urgency >= _URGENCY_RANK[Urgency.URGENT]
                and consequence >= _CONSEQUENCE_RANK[Consequence.SERIOUS]
            )
        ):
            return Judgment(
                evaluation=evaluation,
                recommendation=Recommendation.NOTIFY,
                rationale=(
                    "The cost of dismissal outweighs the cost of a false alarm; "
                    "recommend notification without granting authority."
                ),
            )

        if (
            evaluation.potential_consequence is Consequence.SEVERE
            and evaluation.cost_of_escalation is not ErrorCost.EXTREME
        ):
            return Judgment(
                evaluation=evaluation,
                recommendation=Recommendation.NOTIFY,
                rationale=(
                    "Severe potential consequence deserves human-visible attention; "
                    "notification remains non-authoritative."
                ),
            )

        if evaluation.confidence < 0.5 and consequence >= _CONSEQUENCE_RANK[Consequence.SERIOUS]:
            return Judgment(
                evaluation=evaluation,
                recommendation=Recommendation.NOTIFY,
                rationale=(
                    "Low confidence combined with serious potential consequence "
                    "requires cautious notification, not silent dismissal."
                ),
            )

        return Judgment(
            evaluation=evaluation,
            recommendation=Recommendation.OBSERVE,
            rationale="Sprint 1 defaults to observation without action.",
        )

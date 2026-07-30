"""Recommendation-only judgment stage for the Native Brain."""

from .models import Evaluation, Judgment, Recommendation


class Judge:
    """Produce a recommendation without executing or authorizing it."""

    def judge(self, evaluation: Evaluation) -> Judgment:
        return Judgment(
            evaluation=evaluation,
            recommendation=Recommendation.OBSERVE,
            rationale="Sprint 1 defaults to observation without action.",
        )

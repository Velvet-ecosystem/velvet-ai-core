"""Deterministic significance evaluation for Native Brain understandings."""

from .models import Evaluation, Importance, Understanding


class Evaluator:
    """Assign a conservative initial importance and confidence."""

    def evaluate(self, understanding: Understanding) -> Evaluation:
        return Evaluation(
            understanding=understanding,
            importance=Importance.ROUTINE,
            confidence=1.0,
            reasons=("Sprint 1 deterministic default",),
        )

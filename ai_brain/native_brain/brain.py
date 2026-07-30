"""Public orchestration entry point for Velvet's Native Brain."""

from __future__ import annotations

from typing import Any, Mapping

from .context import ContextBuilder
from .evaluation import Evaluator
from .judgment import Judge
from .models import DecisionReceipt
from .observation import Observer
from .receipts import ReceiptWriter
from .understanding import Understander


class NativeBrain:
    """Run the deterministic Sprint 1 decision spine.

    The returned receipt is a recommendation record only. This class does not
    authorize or execute physical actions.
    """

    def __init__(self) -> None:
        self._observer = Observer()
        self._context_builder = ContextBuilder()
        self._understander = Understander()
        self._evaluator = Evaluator()
        self._judge = Judge()
        self._receipt_writer = ReceiptWriter()

    def process(
        self,
        event: Mapping[str, Any],
        state: Mapping[str, Any] | None = None,
    ) -> DecisionReceipt:
        observation = self._observer.observe(event)
        context = self._context_builder.build(state)
        understanding = self._understander.understand(observation, context)
        evaluation = self._evaluator.evaluate(understanding)
        judgment = self._judge.judge(evaluation)
        return self._receipt_writer.write(judgment)

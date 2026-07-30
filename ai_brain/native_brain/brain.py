"""Public orchestration entry point for Velvet's Native Brain."""

from __future__ import annotations

from typing import Any, Mapping

from .context import ContextBuilder
from .evaluation import Evaluator
from .event_protocol import EventProtocolAdapter
from .judgment import Judge
from .models import DecisionReceipt, ReflectionReview
from .observation import Observer
from .receipts import ReceiptWriter
from .reflection import ReceiptReviewer
from .understanding import Understander


class NativeBrain:
    """Run the deterministic Native Brain decision spine.

    Returned receipts and reviews are evidence records only. This class does not
    authorize, publish, rewrite history, or execute physical actions.
    """

    def __init__(self) -> None:
        self._observer = Observer()
        self._context_builder = ContextBuilder()
        self._understander = Understander()
        self._evaluator = Evaluator()
        self._judge = Judge()
        self._receipt_writer = ReceiptWriter()
        self._event_protocol = EventProtocolAdapter()
        self._receipt_reviewer = ReceiptReviewer()

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

    def process_protocol_event(
        self,
        record: Mapping[str, Any],
        state: Mapping[str, Any] | None = None,
    ) -> DecisionReceipt:
        """Normalize a bus record and run it through the same decision spine.

        Transport acceptance is not action approval. The adapter rejects
        authority-bearing fields in observation payloads and never publishes
        a response back to the bus.
        """

        return self.process(self._event_protocol.normalize(record), state)

    def reflect(self, receipt: DecisionReceipt) -> ReflectionReview:
        """Create an append-only review without mutating the original receipt."""

        return self._receipt_reviewer.review(receipt)

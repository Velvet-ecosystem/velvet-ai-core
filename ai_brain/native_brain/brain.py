"""Public orchestration entry point for Velvet's Native Brain."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .context import ContextBuilder
from .distributed import DistributedReasoningCoordinator
from .evaluation import Evaluator
from .event_protocol import EventProtocolAdapter
from .fusion import EvidenceFusionEngine
from .judgment import Judge
from .learning import LearningProposalBuilder
from .models import (
    CapabilityAdvertisement,
    DecisionReceipt,
    EvidenceContribution,
    EvidenceFusion,
    LearningProposal,
    ReasoningHandoff,
    ReasoningTask,
    ReflectionReview,
)
from .observation import Observer
from .receipts import ReceiptWriter
from .reflection import ReceiptReviewer
from .understanding import Understander


class NativeBrain:
    """Run Velvet's deterministic, recommendation-only reasoning spine."""

    def __init__(self) -> None:
        self._observer = Observer()
        self._context_builder = ContextBuilder()
        self._understander = Understander()
        self._evaluator = Evaluator()
        self._judge = Judge()
        self._receipt_writer = ReceiptWriter()
        self._event_protocol = EventProtocolAdapter()
        self._receipt_reviewer = ReceiptReviewer()
        self._learning_proposals = LearningProposalBuilder()
        self._distributed = DistributedReasoningCoordinator()
        self._fusion = EvidenceFusionEngine()

    def process(self, event: Mapping[str, Any], state: Mapping[str, Any] | None = None) -> DecisionReceipt:
        observation = self._observer.observe(event)
        context = self._context_builder.build(state)
        understanding = self._understander.understand(observation, context)
        evaluation = self._evaluator.evaluate(understanding)
        judgment = self._judge.judge(evaluation)
        return self._receipt_writer.write(judgment)

    def process_protocol_event(self, record: Mapping[str, Any], state: Mapping[str, Any] | None = None) -> DecisionReceipt:
        return self.process(self._event_protocol.normalize(record), state)

    def reflect(self, receipt: DecisionReceipt) -> ReflectionReview:
        return self._receipt_reviewer.review(receipt)

    def propose_learning(self, reviews: Iterable[ReflectionReview], subject: str) -> LearningProposal:
        return self._learning_proposals.propose(reviews, subject)

    def offer_reasoning_task(
        self,
        task: ReasoningTask,
        advertisements: Iterable[CapabilityAdvertisement],
    ) -> ReasoningHandoff:
        return self._distributed.offer(task, advertisements)

    def fuse_evidence(
        self,
        subject: str,
        contributions: Iterable[EvidenceContribution],
    ) -> EvidenceFusion:
        """Create an evidence record only; consensus grants no authority."""

        return self._fusion.fuse(subject, contributions)

"""Public orchestration entry point for Velvet's Native Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

from .attention import AttentionArbiter
from .context import ContextBuilder
from .distributed import DistributedReasoningCoordinator
from .evaluation import Evaluator
from .event_protocol import EventProtocolAdapter
from .freshness import EvidenceFreshnessEvaluator
from .fusion import EvidenceFusionEngine
from .judgment import Judge
from .learning import LearningProposalBuilder
from .models import (
    AttentionDecision,
    AttentionProfile,
    CapabilityAdvertisement,
    DecisionReceipt,
    EvidenceContribution,
    EvidenceFreshness,
    EvidenceFusion,
    EvaluationProfile,
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
        self._attention = AttentionArbiter()
        self._event_protocol = EventProtocolAdapter()
        self._receipt_reviewer = ReceiptReviewer()
        self._learning_proposals = LearningProposalBuilder()
        self._distributed = DistributedReasoningCoordinator()
        self._freshness = EvidenceFreshnessEvaluator()
        self._fusion = EvidenceFusionEngine(freshness=self._freshness)

    def process(
        self,
        event: Mapping[str, Any],
        state: Mapping[str, Any] | None = None,
        evaluation_profile: EvaluationProfile | None = None,
    ) -> DecisionReceipt:
        observation = self._observer.observe(event)
        context = self._context_builder.build(state)
        understanding = self._understander.understand(observation, context)
        evaluation = self._evaluator.evaluate(understanding, evaluation_profile)
        judgment = self._judge.judge(evaluation)
        return self._receipt_writer.write(judgment)

    def process_protocol_event(
        self,
        record: Mapping[str, Any],
        state: Mapping[str, Any] | None = None,
        evaluation_profile: EvaluationProfile | None = None,
    ) -> DecisionReceipt:
        """Normalize transport data while keeping risk grading out-of-band."""

        return self.process(
            self._event_protocol.normalize(record),
            state,
            evaluation_profile,
        )

    def arbitrate_attention(
        self,
        receipt: DecisionReceipt,
        profile: AttentionProfile | None = None,
    ) -> AttentionDecision:
        """Apply the Doctrine of Silence without delivering or authorizing."""

        return self._attention.decide(receipt, profile)

    def reflect(self, receipt: DecisionReceipt) -> ReflectionReview:
        return self._receipt_reviewer.review(receipt)

    def propose_learning(
        self,
        reviews: Iterable[ReflectionReview],
        subject: str,
    ) -> LearningProposal:
        return self._learning_proposals.propose(reviews, subject)

    def offer_reasoning_task(
        self,
        task: ReasoningTask,
        advertisements: Iterable[CapabilityAdvertisement],
    ) -> ReasoningHandoff:
        return self._distributed.offer(task, advertisements)

    def evaluate_evidence_freshness(
        self,
        contributions: Iterable[EvidenceContribution],
        now: datetime | None = None,
    ) -> tuple[EvidenceFreshness, ...]:
        """Review evidence age without mutating or authorizing anything."""

        return self._freshness.evaluate_many(contributions, now)

    def fuse_evidence(
        self,
        subject: str,
        contributions: Iterable[EvidenceContribution],
        now: datetime | None = None,
    ) -> EvidenceFusion:
        """Fuse current evidence only; confidence never grants authority."""

        return self._fusion.fuse(subject, contributions, now)

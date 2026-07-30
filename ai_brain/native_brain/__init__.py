"""Velvet Native Brain package."""

from .brain import NativeBrain
from .distributed import DistributedReasoningCoordinator
from .event_protocol import EventProtocolAdapter, EventProtocolError
from .fusion import EvidenceFusionEngine
from .learning import LearningProposalBuilder
from .models import (
    BrainContext,
    CapabilityAdvertisement,
    DecisionReceipt,
    EvidenceContribution,
    EvidenceFusion,
    Evaluation,
    FusionDisposition,
    HandoffDisposition,
    Importance,
    Judgment,
    LearningDisposition,
    LearningProposal,
    Observation,
    ReasoningHandoff,
    ReasoningTask,
    Recommendation,
    ReflectionReview,
    ReviewDisposition,
    Understanding,
)
from .reflection import ReceiptReviewer

__all__ = [
    "BrainContext", "CapabilityAdvertisement", "DecisionReceipt",
    "DistributedReasoningCoordinator", "EvidenceContribution", "EvidenceFusion",
    "EvidenceFusionEngine", "Evaluation", "EventProtocolAdapter",
    "EventProtocolError", "FusionDisposition", "HandoffDisposition",
    "Importance", "Judgment", "LearningDisposition", "LearningProposal",
    "LearningProposalBuilder", "NativeBrain", "Observation", "ReasoningHandoff",
    "ReasoningTask", "ReceiptReviewer", "Recommendation", "ReflectionReview",
    "ReviewDisposition", "Understanding",
]

"""Velvet Native Brain package.

The Native Brain turns events into explainable recommendations. It does not
own physical authority and must not bypass Runtime or Court.
"""

from .brain import NativeBrain
from .event_protocol import EventProtocolAdapter, EventProtocolError
from .models import (
    BrainContext,
    DecisionReceipt,
    Evaluation,
    Importance,
    Judgment,
    Observation,
    Recommendation,
    ReflectionReview,
    ReviewDisposition,
    Understanding,
)
from .reflection import ReceiptReviewer

__all__ = [
    "BrainContext",
    "DecisionReceipt",
    "Evaluation",
    "EventProtocolAdapter",
    "EventProtocolError",
    "Importance",
    "Judgment",
    "NativeBrain",
    "Observation",
    "ReceiptReviewer",
    "Recommendation",
    "ReflectionReview",
    "ReviewDisposition",
    "Understanding",
]

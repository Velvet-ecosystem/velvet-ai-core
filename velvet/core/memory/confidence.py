# SPDX-License-Identifier: GPL-3.0-only
"""Confidence classification and revision rules for Velvet memory."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceAssessment:
    value: float
    band: str
    wording: str


class MemoryConfidencePolicy:
    """Classify confidence without changing memory kind or authority."""

    @staticmethod
    def assess(value: float) -> ConfidenceAssessment:
        MemoryConfidencePolicy._validate(value)
        numeric = float(value)
        if numeric >= 0.85:
            return ConfidenceAssessment(numeric, "high", "remembered with high confidence")
        if numeric >= 0.60:
            return ConfidenceAssessment(numeric, "moderate", "remembered with some confidence")
        if numeric >= 0.30:
            return ConfidenceAssessment(numeric, "low", "remembered uncertainly")
        return ConfidenceAssessment(numeric, "very_low", "only weakly remembered")

    @staticmethod
    def revise(current: float, proposed: float, max_step: float = 0.25) -> float:
        MemoryConfidencePolicy._validate(current)
        MemoryConfidencePolicy._validate(proposed)
        if not isinstance(max_step, (int, float)) or not 0.0 < float(max_step) <= 1.0:
            raise ValueError("max_step must be greater than 0.0 and at most 1.0")
        delta = float(proposed) - float(current)
        limited = max(-float(max_step), min(float(max_step), delta))
        return round(float(current) + limited, 6)

    @staticmethod
    def allows_fact_promotion(kind: str, authority_status: str, confidence: float) -> bool:
        MemoryConfidencePolicy._validate(confidence)
        del kind, authority_status
        return False

    @staticmethod
    def _validate(value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("confidence must be numeric")
        if not 0.0 <= float(value) <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

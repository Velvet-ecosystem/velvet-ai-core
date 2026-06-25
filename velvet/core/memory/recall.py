# SPDX-License-Identifier: GPL-3.0-only
"""Transparent recall ranking for Velvet memory candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class RecallCandidate:
    event_id: str
    association: float
    confidence: float
    salience: float
    authority_status: str


@dataclass(frozen=True)
class RecallScore:
    event_id: str
    score: float
    association: float
    confidence: float
    salience: float
    authority_weight: float


class MemoryRecallRanker:
    AUTHORITY_WEIGHTS = {
        "accepted": 1.0,
        "observed": 0.9,
        "historical": 0.8,
        "candidate": 0.6,
        "superseded": 0.3,
        "rejected": 0.1,
    }

    @classmethod
    def score(cls, candidate: RecallCandidate) -> RecallScore:
        cls._text(candidate.event_id, "event_id")
        cls._unit(candidate.association, "association")
        cls._unit(candidate.confidence, "confidence")
        cls._unit(candidate.salience, "salience")
        authority_weight = cls.AUTHORITY_WEIGHTS.get(candidate.authority_status, 0.5)
        score = (
            candidate.association * 0.45
            + candidate.salience * 0.30
            + candidate.confidence * 0.20
            + authority_weight * 0.05
        )
        return RecallScore(
            candidate.event_id,
            round(score, 6),
            candidate.association,
            candidate.confidence,
            candidate.salience,
            authority_weight,
        )

    @classmethod
    def rank(cls, candidates: Iterable[RecallCandidate]) -> List[RecallScore]:
        scored = [cls.score(candidate) for candidate in candidates]
        return sorted(scored, key=lambda item: (-item.score, item.event_id))

    @staticmethod
    def _unit(value: float, name: str) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("{} must be numeric".format(name))
        if not 0.0 <= float(value) <= 1.0:
            raise ValueError("{} must be between 0.0 and 1.0".format(name))

    @staticmethod
    def _text(value: str, name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("{} must be a non-empty string".format(name))

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class DecayAssessment:
    salience: float
    protected: bool


class MemoryDecayPolicy:
    PROTECTED_TAGS = {"pinned", "safety", "continuity", "identity"}

    @classmethod
    def assess(
        cls,
        age_seconds: float,
        base_salience: float = 1.0,
        half_life_seconds: float = 2592000.0,
        tags: Optional[Iterable[str]] = None,
        authority_status: Optional[str] = None,
    ) -> DecayAssessment:
        cls._non_negative(age_seconds, "age_seconds")
        cls._unit(base_salience, "base_salience")
        if not isinstance(half_life_seconds, (int, float)) or half_life_seconds <= 0:
            raise ValueError("half_life_seconds must be positive")

        protected = bool(set(tags or []) & cls.PROTECTED_TAGS)
        protected = protected or authority_status == "accepted"
        if protected:
            return DecayAssessment(float(base_salience), True)

        factor = math.pow(0.5, float(age_seconds) / float(half_life_seconds))
        return DecayAssessment(round(float(base_salience) * factor, 6), False)

    @classmethod
    def reinforce(cls, current_salience: float, amount: float) -> float:
        cls._unit(current_salience, "current_salience")
        cls._unit(amount, "amount")
        value = current_salience + (1.0 - current_salience) * amount
        return round(min(1.0, value), 6)

    @staticmethod
    def _non_negative(value: float, name: str) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("{} must be numeric".format(name))
        if value < 0:
            raise ValueError("{} must be non-negative".format(name))

    @staticmethod
    def _unit(value: float, name: str) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("{} must be numeric".format(name))
        if not 0.0 <= value <= 1.0:
            raise ValueError("{} must be between 0.0 and 1.0".format(name))

# SPDX-License-Identifier: GPL-3.0-only
"""Optional LLM adapter boundary for Native Brain v0."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .safety import NativeBrainSafetyError


FORBIDDEN_LLM_CLAIMS = (
    "authority granted",
    "hardware touched",
    "can frame sent",
    "relay activated",
    "vehicle started",
    "medical takeover",
)


@dataclass(frozen=True)
class LLMPolishRequest:
    """A factual response skeleton that a model may polish."""

    skeleton: str
    instruction: str = "Polish wording only. Do not add authority, action, or hardware claims."


class OptionalLLMAdapter:
    """Keeps a model as optional language help, not Velvet's identity."""

    def polish(
        self,
        request: LLMPolishRequest,
        polish_fn: Optional[Callable[[str], str]] = None,
    ) -> str:
        if polish_fn is None:
            return request.skeleton

        candidate = polish_fn(request.skeleton)
        if not isinstance(candidate, str) or not candidate.strip():
            raise NativeBrainSafetyError("LLM polish must return non-empty text")

        lowered = candidate.lower()
        for phrase in FORBIDDEN_LLM_CLAIMS:
            if phrase in lowered:
                raise NativeBrainSafetyError(
                    "LLM polish crossed Native Brain authority boundary: %s" % phrase
                )

        return candidate

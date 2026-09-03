# SPDX-License-Identifier: GPL-3.0-only
"""Compose bounded conversation resolvers without collapsing their ownership."""

from __future__ import annotations

from typing import Callable, Iterable, Tuple

from .conversation_ingress import (
    ConversationMeaningKind,
    ConversationWorkRequest,
    GroundedConversationMeaning,
)

Resolver = Callable[[ConversationWorkRequest], GroundedConversationMeaning]


class ConversationResolverChain:
    """Try resolvers in a deterministic order until one has grounded meaning.

    ``UNAVAILABLE`` means "this resolver has no applicable grounded answer" and
    allows the next bounded organ to try. Any other response, including an
    authority fence, stops the chain immediately.
    """

    def __init__(self, resolvers: Iterable[Resolver]) -> None:
        resolved = tuple(resolvers)
        if not resolved:
            raise ValueError("at least one conversation resolver is required")
        if any(not callable(item) for item in resolved):
            raise TypeError("all conversation resolvers must be callable")
        self._resolvers = resolved  # type: Tuple[Resolver, ...]

    def __call__(self, request: ConversationWorkRequest) -> GroundedConversationMeaning:
        if not isinstance(request, ConversationWorkRequest):
            raise TypeError("request must be ConversationWorkRequest")

        unavailable_qualifiers = []
        for resolver in self._resolvers:
            meaning = resolver(request)
            if not isinstance(meaning, GroundedConversationMeaning):
                raise TypeError("conversation resolver must return GroundedConversationMeaning")
            if meaning.response_kind is not ConversationMeaningKind.UNAVAILABLE:
                return meaning
            unavailable_qualifiers.extend(meaning.qualifiers)

        qualifiers = tuple(dict.fromkeys(unavailable_qualifiers))[:16]
        return GroundedConversationMeaning(
            response_kind=ConversationMeaningKind.UNAVAILABLE,
            confidence=0.0,
            qualifiers=qualifiers or ("no-grounded-answer",),
        )

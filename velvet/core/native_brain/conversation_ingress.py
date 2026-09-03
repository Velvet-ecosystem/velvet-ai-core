# SPDX-License-Identifier: GPL-3.0-only
"""Grounded conversation ingress for Velvet Native Brain.

This module accepts the normalized turn event emitted by ``velvet-language``
and converts it into a read-only Core work request. Core may attach verified
meaning through a resolver, but this boundary never grants Runtime authority,
executes an action, or owns human-facing wording.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

from .cognition import ObservationEnvelope

LANGUAGE_CONVERSATION_TURN_EVENT = "velvet.language.conversation.turn"
LANGUAGE_CONVERSATION_SCHEMA_VERSION = "0.1"
CORE_CONVERSATION_MEANING_EVENT = "velvet.core.conversation.meaning"
CORE_CONVERSATION_SCHEMA_VERSION = "0.1"
MAX_TURN_CHARACTERS = 4096

_ALLOWED_MODALITIES = frozenset({"text", "speech_transcript"})


class ConversationMeaningKind(str, Enum):
    """Structured meaning Core may return to the Language organ."""

    FACT = "fact"
    EVIDENCE = "evidence"
    UNAVAILABLE = "unavailable"
    ACKNOWLEDGE = "acknowledge"
    AUTHORITY_REQUIRED = "authority_required"


@dataclass(frozen=True)
class ConversationWorkRequest:
    """One normalized, read-only human turn presented to Native Brain."""

    conversation_id: str
    turn_id: str
    turn_number: int
    text: str
    modality: str
    audience: str
    act: str
    strategy: str
    requires_authority_check: bool
    may_speak: bool
    authority_granted: bool = False

    def __post_init__(self) -> None:
        _require_text("conversation_id", self.conversation_id)
        _require_text("turn_id", self.turn_id)
        _require_text("text", self.text)
        _require_text("audience", self.audience)
        _require_text("act", self.act)
        _require_text("strategy", self.strategy)
        if len(self.text) > MAX_TURN_CHARACTERS:
            raise ValueError("conversation text exceeds maximum length")
        if isinstance(self.turn_number, bool) or not isinstance(self.turn_number, int):
            raise ValueError("turn_number must be an integer")
        if self.turn_number < 1:
            raise ValueError("turn_number must be positive")
        if self.modality not in _ALLOWED_MODALITIES:
            raise ValueError("unsupported conversation modality")
        if not isinstance(self.requires_authority_check, bool):
            raise ValueError("requires_authority_check must be boolean")
        if not isinstance(self.may_speak, bool):
            raise ValueError("may_speak must be boolean")
        if self.authority_granted:
            raise ValueError("conversation work request cannot grant authority")

    def to_observation(self) -> ObservationEnvelope:
        """Project the turn into the existing read-only cognition contract."""

        return ObservationEnvelope(
            event_type=LANGUAGE_CONVERSATION_TURN_EVENT,
            source="velvet-language",
            payload={
                "conversation_id": self.conversation_id,
                "turn_id": self.turn_id,
                "turn_number": self.turn_number,
                "text": self.text,
                "modality": self.modality,
                "audience": self.audience,
                "act": self.act,
                "strategy": self.strategy,
                "requires_authority_check": self.requires_authority_check,
                "may_speak": self.may_speak,
                "authority_granted": False,
            },
            confidence=1.0,
            read_only=True,
        )


@dataclass(frozen=True)
class GroundedConversationMeaning:
    """Verified structured meaning returned to Language for realization.

    ``FACT`` carries a verified scalar fact. ``EVIDENCE`` carries one bounded,
    reference-only passage selected from an external evidence provider. The
    latter is deliberately distinct so retrieval can never masquerade as body
    truth or canonical memory. Language remains responsible for final wording.
    """

    response_kind: ConversationMeaningKind
    confidence: float
    fact_id: Optional[str] = None
    value: Any = None
    unit: Optional[str] = None
    source_label: Optional[str] = None
    qualifiers: Tuple[str, ...] = ()
    source_refs: Tuple[str, ...] = ()
    authority: str = "none"
    grants_authority: bool = False
    grants_execution: bool = False
    grants_actuation: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.response_kind, ConversationMeaningKind):
            raise ValueError("response_kind must be ConversationMeaningKind")
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
            raise ValueError("confidence must be numeric")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.fact_id is not None:
            _require_text("fact_id", self.fact_id)
        if self.unit is not None:
            _require_text("unit", self.unit)
        if self.source_label is not None:
            _require_text("source_label", self.source_label)
        _require_text_tuple("qualifiers", self.qualifiers)
        _require_text_tuple("source_refs", self.source_refs)
        if self.authority != "none":
            raise ValueError("conversation meaning cannot carry authority")
        if self.grants_authority or self.grants_execution or self.grants_actuation:
            raise ValueError("conversation meaning cannot grant authority or execution")

        if self.response_kind is ConversationMeaningKind.FACT:
            if self.fact_id is None:
                raise ValueError("fact response requires fact_id")
            _require_scalar("value", self.value)
        elif self.response_kind is ConversationMeaningKind.EVIDENCE:
            if self.fact_id is None:
                raise ValueError("evidence response requires fact_id")
            if self.source_label is None:
                raise ValueError("evidence response requires source_label")
            if not self.source_refs:
                raise ValueError("evidence response requires source_refs")
            _require_scalar("value", self.value)
            if not isinstance(self.value, str) or not self.value.strip():
                raise ValueError("evidence response value must be non-empty text")
        elif self.value is not None:
            raise ValueError("non-fact conversation meaning cannot carry a value")

    def to_event(self, request: ConversationWorkRequest) -> Dict[str, Any]:
        """Serialize meaning for the Language organ without creating authority."""

        return {
            "event": CORE_CONVERSATION_MEANING_EVENT,
            "schema_version": CORE_CONVERSATION_SCHEMA_VERSION,
            "conversation_id": request.conversation_id,
            "turn_id": request.turn_id,
            "turn_number": request.turn_number,
            "response_kind": self.response_kind.value,
            "fact_id": self.fact_id,
            "value": self.value,
            "unit": self.unit,
            "source_label": self.source_label,
            "confidence": float(self.confidence),
            "qualifiers": list(self.qualifiers),
            "source_refs": list(self.source_refs),
            "requires_authority_check": request.requires_authority_check,
            "authority": "none",
            "grants_authority": False,
            "grants_execution": False,
            "grants_actuation": False,
        }


GroundedResolver = Callable[[ConversationWorkRequest], GroundedConversationMeaning]


def conversation_work_request_from_event(event: Mapping[str, Any]) -> ConversationWorkRequest:
    """Validate a Language turn event and return Core's read-only request."""

    if not isinstance(event, Mapping):
        raise TypeError("conversation event must be a mapping")
    if event.get("event") != LANGUAGE_CONVERSATION_TURN_EVENT:
        raise ValueError("unexpected conversation event type")
    if event.get("schema_version") != LANGUAGE_CONVERSATION_SCHEMA_VERSION:
        raise ValueError("unsupported conversation schema version")
    if event.get("authority_granted") is not False:
        raise ValueError("conversation ingress requires authority_granted=false")

    return ConversationWorkRequest(
        conversation_id=_text_value(event, "conversation_id"),
        turn_id=_text_value(event, "turn_id"),
        turn_number=event.get("turn_number"),
        text=_text_value(event, "text"),
        modality=_text_value(event, "modality"),
        audience=_text_value(event, "audience"),
        act=_text_value(event, "act"),
        strategy=_text_value(event, "strategy"),
        requires_authority_check=event.get("requires_authority_check"),
        may_speak=event.get("may_speak"),
        authority_granted=False,
    )


def handle_conversation_turn(
    event: Mapping[str, Any],
    resolver: Optional[GroundedResolver] = None,
) -> Dict[str, Any]:
    """Run the conversation ingress boundary and return structured meaning.

    A resolver may consult verified Core/body/memory/evidence context. Its result
    is validated by ``GroundedConversationMeaning`` before serialization. When
    no resolver is bound, Core says only that grounded meaning is unavailable.
    """

    request = conversation_work_request_from_event(event)
    _ = request.to_observation()

    if resolver is None:
        meaning = GroundedConversationMeaning(
            response_kind=ConversationMeaningKind.UNAVAILABLE,
            confidence=0.0,
            qualifiers=("no-grounded-resolver",),
        )
    else:
        meaning = resolver(request)
        if not isinstance(meaning, GroundedConversationMeaning):
            raise TypeError("grounded resolver must return GroundedConversationMeaning")

    return meaning.to_event(request)


def _text_value(event: Mapping[str, Any], key: str) -> str:
    value = event.get(key)
    _require_text(key, value)
    return str(value).strip()


def _require_text(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be non-empty text" % name)


def _require_text_tuple(name: str, value: Tuple[str, ...]) -> None:
    if not isinstance(value, tuple):
        raise ValueError("%s must be a tuple" % name)
    for item in value:
        _require_text(name, item)


def _require_scalar(name: str, value: Any) -> None:
    if isinstance(value, (dict, list, tuple, set)):
        raise ValueError("%s must be a scalar" % name)
    if isinstance(value, str) and len(value) > 512:
        raise ValueError("%s text must be <= 512 characters" % name)

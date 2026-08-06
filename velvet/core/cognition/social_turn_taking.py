# SPDX-License-Identifier: GPL-3.0-only
"""Embodied, proposal-only social turn-taking for Velvet."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

from .workspace_context import CognitiveWorkspaceContext


class TurnPosture(str, Enum):
    LISTEN = "LISTEN"
    HOLD_SILENCE = "HOLD_SILENCE"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    RESPOND = "RESPOND"
    YIELD = "YIELD"
    INTERRUPT_FOR_SAFETY = "INTERRUPT_FOR_SAFETY"
    RECOVER_TURN = "RECOVER_TURN"


@dataclass(frozen=True)
class TurnSignals:
    signal_id: str
    body_id: str
    node_id: str
    cognitive_event_id: str
    source_refs: Tuple[str, ...]
    correlation_ids: Tuple[str, ...] = ()
    owner_present: bool = True
    owner_speech_active: bool = False
    likely_incomplete_utterance: float = 0.0
    elapsed_silence_seconds: float = 0.0
    velvet_speaking: bool = False
    response_ready: bool = False
    explicit_question_pending: bool = False
    requested_silence: bool = False
    driving_demand: float = 0.0
    safety_severity: float = 0.0
    accepted_interrupt_ref: Optional[str] = None
    previous_posture: TurnPosture = TurnPosture.LISTEN
    replay_state: str = "live"

    def __post_init__(self) -> None:
        for name, value in (
            ("signal_id", self.signal_id),
            ("body_id", self.body_id),
            ("node_id", self.node_id),
            ("cognitive_event_id", self.cognitive_event_id),
        ):
            _text(name, value)
        _sequence("source_refs", self.source_refs, True)
        _sequence("correlation_ids", self.correlation_ids)
        _ratio("likely_incomplete_utterance", self.likely_incomplete_utterance)
        _non_negative("elapsed_silence_seconds", self.elapsed_silence_seconds)
        _ratio("driving_demand", self.driving_demand)
        _ratio("safety_severity", self.safety_severity)
        for name, value in (
            ("owner_present", self.owner_present),
            ("owner_speech_active", self.owner_speech_active),
            ("velvet_speaking", self.velvet_speaking),
            ("response_ready", self.response_ready),
            ("explicit_question_pending", self.explicit_question_pending),
            ("requested_silence", self.requested_silence),
        ):
            if not isinstance(value, bool):
                raise ValueError("%s must be boolean" % name)
        if self.accepted_interrupt_ref is not None:
            _text("accepted_interrupt_ref", self.accepted_interrupt_ref)
        if not isinstance(self.previous_posture, TurnPosture):
            raise ValueError("previous_posture must be TurnPosture")
        if self.replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid replay_state")


@dataclass(frozen=True)
class TurnDecision:
    posture: TurnPosture
    reason: str
    confidence: float
    speak_allowed: bool
    interrupting: bool
    source_refs: Tuple[str, ...]
    accepted_interrupt_ref: Optional[str] = None
    maximum_response_seconds: Optional[float] = None
    proposal_only: bool = True
    authority_granted: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.posture, TurnPosture):
            raise ValueError("posture must be TurnPosture")
        _text("reason", self.reason)
        _ratio("confidence", self.confidence)
        _sequence("source_refs", self.source_refs, True)
        if self.interrupting and self.posture is not TurnPosture.INTERRUPT_FOR_SAFETY:
            raise ValueError("only safety posture may be interrupting")
        if self.posture is TurnPosture.INTERRUPT_FOR_SAFETY:
            if not self.accepted_interrupt_ref:
                raise ValueError(
                    "safety interruption requires accepted interrupt reference"
                )
        elif self.accepted_interrupt_ref is not None:
            raise ValueError("accepted interrupt reference requires safety posture")
        if self.maximum_response_seconds is not None:
            _non_negative("maximum_response_seconds", self.maximum_response_seconds)
        if self.proposal_only is not True or self.authority_granted is not False:
            raise ValueError("turn decision must remain proposal-only")

    def read_only_view(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "posture": self.posture.value,
                "reason": self.reason,
                "confidence": self.confidence,
                "speak_allowed": self.speak_allowed,
                "interrupting": self.interrupting,
                "source_refs": self.source_refs,
                "accepted_interrupt_ref": self.accepted_interrupt_ref,
                "maximum_response_seconds": self.maximum_response_seconds,
                "proposal_only": True,
                "authority_granted": False,
            }
        )


class SocialTurnCoordinator:
    def decide(
        self,
        signals: TurnSignals,
        *,
        workspace_view: Mapping[str, Any],
        modulator_values: Mapping[str, float],
    ) -> TurnDecision:
        context = CognitiveWorkspaceContext.from_view(workspace_view)
        context.assert_matches(body_id=signals.body_id, node_id=signals.node_id)
        if context.cognitive_event_id != signals.cognitive_event_id:
            raise ValueError("turn signals belong to another cognitive event")
        if context.replay_state != signals.replay_state:
            raise ValueError("workspace and turn signals replay_state differ")
        if context.correlation_ids and signals.correlation_ids:
            if not set(context.correlation_ids).intersection(signals.correlation_ids):
                raise ValueError("turn signals lack workspace correlation")
        modulators = _validate_modulators(modulator_values)
        refs = _merge(context.source_refs, signals.source_refs)

        if signals.accepted_interrupt_ref is not None:
            refs = _merge(refs, (signals.accepted_interrupt_ref,))
            return TurnDecision(
                posture=TurnPosture.INTERRUPT_FOR_SAFETY,
                reason="accepted safety interruption outranks conversational turn",
                confidence=max(0.8, signals.safety_severity),
                speak_allowed=True,
                interrupting=True,
                source_refs=refs,
                accepted_interrupt_ref=signals.accepted_interrupt_ref,
                maximum_response_seconds=2.0,
            )

        if signals.velvet_speaking and signals.owner_speech_active:
            return _decision(
                TurnPosture.YIELD,
                "owner speech began while Velvet was speaking",
                0.98,
                False,
                refs,
            )
        if signals.requested_silence:
            return _decision(
                TurnPosture.HOLD_SILENCE,
                "explicit silence request remains active",
                1.0,
                False,
                refs,
            )
        if not signals.owner_present:
            return _decision(
                TurnPosture.HOLD_SILENCE,
                "no present conversation partner is established",
                0.95,
                False,
                refs,
            )
        if signals.owner_speech_active:
            return _decision(
                TurnPosture.LISTEN,
                "owner speech is active",
                0.98,
                False,
                refs,
            )

        hold_window = 0.45 + modulators.get("uncertainty", 0.0) * 0.8
        hold_window -= modulators.get("social_engagement", 0.0) * 0.15
        hold_window = max(0.25, min(1.5, hold_window))
        if signals.likely_incomplete_utterance >= 0.55:
            return _decision(
                TurnPosture.HOLD_SILENCE,
                "utterance appears incomplete",
                signals.likely_incomplete_utterance,
                False,
                refs,
            )
        if signals.elapsed_silence_seconds < hold_window:
            return _decision(
                TurnPosture.HOLD_SILENCE,
                "silence remains inside the bounded turn-hold window",
                0.85,
                False,
                refs,
            )
        if (
            signals.previous_posture is TurnPosture.INTERRUPT_FOR_SAFETY
            and signals.safety_severity < 0.35
        ):
            return _decision(
                TurnPosture.RECOVER_TURN,
                "safety interruption cleared and conversational turn may recover",
                0.85,
                True,
                refs,
                maximum_response_seconds=2.0,
            )
        if signals.driving_demand >= 0.8:
            if signals.response_ready and signals.explicit_question_pending:
                return _decision(
                    TurnPosture.ACKNOWLEDGE,
                    "high driving demand permits only a brief acknowledgement",
                    0.92,
                    True,
                    refs,
                    maximum_response_seconds=1.5,
                )
            return _decision(
                TurnPosture.HOLD_SILENCE,
                "driving demand suppresses nonessential speech",
                0.92,
                False,
                refs,
            )
        if signals.response_ready:
            urgency = modulators.get("urgency", 0.0)
            maximum = max(
                2.0,
                8.0 - signals.driving_demand * 5.0 - urgency * 2.0,
            )
            return _decision(
                TurnPosture.RESPOND,
                "a bounded response is ready and the turn is open",
                0.9,
                True,
                refs,
                maximum_response_seconds=round(maximum, 2),
            )
        if signals.explicit_question_pending:
            return _decision(
                TurnPosture.ACKNOWLEDGE,
                "question is pending but a complete response is not ready",
                0.82,
                True,
                refs,
                maximum_response_seconds=1.5,
            )
        return _decision(
            TurnPosture.LISTEN,
            "no response or interruption is currently required",
            0.75,
            False,
            refs,
        )


def _decision(
    posture: TurnPosture,
    reason: str,
    confidence: float,
    speak_allowed: bool,
    source_refs: Tuple[str, ...],
    maximum_response_seconds: Optional[float] = None,
) -> TurnDecision:
    return TurnDecision(
        posture=posture,
        reason=reason,
        confidence=float(confidence),
        speak_allowed=speak_allowed,
        interrupting=False,
        source_refs=source_refs,
        maximum_response_seconds=maximum_response_seconds,
    )


def _validate_modulators(values: Mapping[str, float]) -> dict:
    if not isinstance(values, Mapping):
        raise ValueError("modulator_values must be a mapping")
    allowed = {
        "arousal",
        "novelty",
        "uncertainty",
        "urgency",
        "social_engagement",
        "prediction_stability",
    }
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(
            "turn-taking received forbidden modulators: %s" % sorted(unknown)
        )
    result = {}
    for name, value in values.items():
        _ratio(name, value)
        result[name] = float(value)
    return result


def _sequence(name: str, values: Any, required: bool = False) -> Tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise ValueError("%s must be a list or tuple" % name)
    result = []
    for value in values:
        _text(name, value)
        if value.strip() not in result:
            result.append(value.strip())
    if required and not result:
        raise ValueError("%s must not be empty" % name)
    return tuple(result)


def _merge(*groups: Tuple[str, ...]) -> Tuple[str, ...]:
    result = []
    for group in groups:
        for value in group:
            if value not in result:
                result.append(value)
    return tuple(result)


def _text(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


def _ratio(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % name)
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError("%s must be between 0 and 1" % name)


def _non_negative(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % name)
    if float(value) < 0.0:
        raise ValueError("%s must be non-negative" % name)


__all__ = [
    "TurnPosture",
    "TurnSignals",
    "TurnDecision",
    "SocialTurnCoordinator",
]

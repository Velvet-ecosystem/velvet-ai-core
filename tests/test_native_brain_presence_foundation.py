from datetime import datetime, timedelta, timezone

import pytest

from velvet.core.native_brain import (
    CognitiveOutcome,
    DeferredThought,
    ObservationEnvelope,
    OpenThread,
    PresenceContext,
    PresenceGate,
    ThreadStatus,
)


def observation() -> ObservationEnvelope:
    return ObservationEnvelope(
        event_type="vehicle.temperature.observed",
        source="ruby.sensor",
        payload={"celsius": 91.0},
        confidence=0.8,
    )


def test_observation_rejects_write_capability() -> None:
    with pytest.raises(ValueError):
        ObservationEnvelope("x", "y", {}, read_only=False)


def test_silence_is_a_complete_outcome() -> None:
    decision = PresenceGate().decide(observation(), PresenceContext())
    assert decision.outcome is CognitiveOutcome.SILENCE
    assert decision.interrupt is False


def test_owner_concentration_causes_wait() -> None:
    decision = PresenceGate().decide(
        observation(), PresenceContext(addressed=True, owner_concentrating=True)
    )
    assert decision.outcome is CognitiveOutcome.WAIT


def test_uncertainty_can_choose_question_over_answer() -> None:
    decision = PresenceGate().decide(
        observation(), PresenceContext(addressed=True, uncertainty=0.8)
    )
    assert decision.outcome is CognitiveOutcome.QUESTION
    assert decision.question


def test_only_safety_value_interrupts_without_prompt() -> None:
    decision = PresenceGate().decide(
        observation(), PresenceContext(safety_relevant=True)
    )
    assert decision.outcome is CognitiveOutcome.ESCALATE
    assert decision.interrupt is True


def test_open_threads_are_noncanonical_and_expire() -> None:
    opened = datetime.now(timezone.utc) - timedelta(minutes=10)
    thread = OpenThread(
        "coolant trend", "waiting for another observation", timedelta(minutes=5), opened_at=opened
    )
    assert thread.canonical is False
    assert thread.expire_if_stale() is True
    assert thread.status is ThreadStatus.EXPIRED


def test_deferred_thoughts_are_noncanonical_and_stale() -> None:
    created = datetime.now(timezone.utc) - timedelta(minutes=20)
    thought = DeferredThought(
        "washer fluid is low", "owner concentrating", timedelta(minutes=15), created_at=created
    )
    assert thought.canonical is False
    assert thought.is_stale() is True

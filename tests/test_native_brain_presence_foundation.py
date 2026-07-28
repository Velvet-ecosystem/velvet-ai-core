from datetime import datetime, timedelta, timezone
import unittest

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


class NativeBrainPresenceFoundationTests(unittest.TestCase):
    def test_observation_rejects_write_capability(self) -> None:
        with self.assertRaises(ValueError):
            ObservationEnvelope("x", "y", {}, read_only=False)

    def test_silence_is_a_complete_outcome(self) -> None:
        decision = PresenceGate().decide(observation(), PresenceContext())
        self.assertIs(decision.outcome, CognitiveOutcome.SILENCE)
        self.assertFalse(decision.interrupt)

    def test_owner_concentration_causes_wait(self) -> None:
        decision = PresenceGate().decide(
            observation(), PresenceContext(addressed=True, owner_concentrating=True)
        )
        self.assertIs(decision.outcome, CognitiveOutcome.WAIT)

    def test_uncertainty_can_choose_question_over_answer(self) -> None:
        decision = PresenceGate().decide(
            observation(), PresenceContext(addressed=True, uncertainty=0.8)
        )
        self.assertIs(decision.outcome, CognitiveOutcome.QUESTION)
        self.assertTrue(decision.question)

    def test_only_safety_value_interrupts_without_prompt(self) -> None:
        decision = PresenceGate().decide(
            observation(), PresenceContext(safety_relevant=True)
        )
        self.assertIs(decision.outcome, CognitiveOutcome.ESCALATE)
        self.assertTrue(decision.interrupt)

    def test_open_threads_are_noncanonical_and_expire(self) -> None:
        opened = datetime.now(timezone.utc) - timedelta(minutes=10)
        thread = OpenThread(
            "coolant trend",
            "waiting for another observation",
            timedelta(minutes=5),
            opened_at=opened,
        )
        self.assertFalse(thread.canonical)
        self.assertTrue(thread.expire_if_stale())
        self.assertIs(thread.status, ThreadStatus.EXPIRED)

    def test_deferred_thoughts_are_noncanonical_and_stale(self) -> None:
        created = datetime.now(timezone.utc) - timedelta(minutes=20)
        thought = DeferredThought(
            "washer fluid is low",
            "owner concentrating",
            timedelta(minutes=15),
            created_at=created,
        )
        self.assertFalse(thought.canonical)
        self.assertTrue(thought.is_stale())


if __name__ == "__main__":
    unittest.main()

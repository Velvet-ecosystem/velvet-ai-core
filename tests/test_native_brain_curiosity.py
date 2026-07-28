# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.native_brain import (
    AttentionAssessment,
    CuriosityContext,
    CuriosityDisposition,
    CuriosityEngine,
    ObservationEnvelope,
    ObservationMaturity,
)


class NativeBrainCuriosityTests(unittest.TestCase):
    def observation(self):
        return ObservationEnvelope(
            event_type="vehicle.coolant.observed",
            source="ruby.sensor",
            payload={"celsius": 92.0},
            confidence=0.8,
        )

    def attention(self, maturity=ObservationMaturity.NEW, priority="low", reasons=None):
        return AttentionAssessment(
            maturity=maturity,
            score=0.2,
            priority=priority,
            reasons=tuple(reasons or (f"maturity:{maturity.value}",)),
        )

    def test_low_new_observation_does_not_create_unfinished_thought(self):
        result = CuriosityEngine().assess(
            self.observation(),
            self.attention(),
            CuriosityContext(),
        )

        self.assertIs(result.disposition, CuriosityDisposition.NONE)
        self.assertIsNone(result.thread_candidate)
        self.assertEqual(result.authority, "none")
        self.assertFalse(result.canonical)

    def test_repeated_unexplained_observation_creates_quiet_watch_candidate(self):
        result = CuriosityEngine().assess(
            self.observation(),
            self.attention(ObservationMaturity.REPEATED, "normal"),
            CuriosityContext(missing_evidence=1),
        )

        self.assertIs(result.disposition, CuriosityDisposition.WATCH)
        self.assertIsNotNone(result.thread_candidate)
        self.assertFalse(result.thread_candidate.canonical)
        self.assertEqual(result.thread_candidate.authority, "none")
        self.assertFalse(result.speak_now)
        self.assertFalse(result.interrupt)

    def test_conflict_may_form_question_candidate_but_never_speaks_directly(self):
        result = CuriosityEngine().assess(
            self.observation(),
            self.attention(ObservationMaturity.CONFIRMED, "high"),
            CuriosityContext(
                contradiction=0.8,
                addressed=True,
                owner_available=True,
            ),
        )

        self.assertIs(result.disposition, CuriosityDisposition.QUESTION_CANDIDATE)
        self.assertIn("conflicting evidence", result.question_candidate)
        self.assertFalse(result.speak_now)
        self.assertFalse(result.interrupt)

    def test_existing_thread_prevents_duplicate_thread_candidate(self):
        result = CuriosityEngine().assess(
            self.observation(),
            self.attention(ObservationMaturity.REPEATED, "normal"),
            CuriosityContext(missing_evidence=1, existing_thread=True),
        )

        self.assertIs(result.disposition, CuriosityDisposition.WATCH)
        self.assertIsNone(result.thread_candidate)

    def test_safety_attention_outranks_curiosity(self):
        result = CuriosityEngine().assess(
            self.observation(),
            self.attention(
                ObservationMaturity.NEW,
                "critical",
                reasons=("maturity:new", "safety-relevant"),
            ),
            CuriosityContext(contradiction=1.0),
        )

        self.assertIs(result.disposition, CuriosityDisposition.DEFER_TO_SAFETY)
        self.assertIsNone(result.thread_candidate)
        self.assertIsNone(result.question_candidate)

    def test_mature_explained_observation_resolves_without_thread(self):
        result = CuriosityEngine().assess(
            self.observation(),
            self.attention(ObservationMaturity.EXPECTATION, "normal"),
            CuriosityContext(explanation_available=True),
        )

        self.assertIs(result.disposition, CuriosityDisposition.RESOLVED)
        self.assertIsNone(result.thread_candidate)

    def test_identical_inputs_produce_identical_assessments(self):
        observation = self.observation()
        attention = self.attention(ObservationMaturity.CONFIRMED, "high")
        context = CuriosityContext(unexplained_change=0.7, missing_evidence=2)
        engine = CuriosityEngine()

        first = engine.assess(observation, attention, context)
        second = engine.assess(observation, attention, context)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

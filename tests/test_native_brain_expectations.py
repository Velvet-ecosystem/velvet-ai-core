# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.native_brain import (
    ExpectationContext,
    ExpectationDisposition,
    ExpectationEngine,
    ExpectationState,
    PatternAssessment,
    PatternCandidate,
    PatternDisposition,
    PatternState,
)


class NativeBrainExpectationTests(unittest.TestCase):
    def pattern(self, confidence=0.86, state=PatternState.STABLE, eligible=True):
        candidate = None
        if state is not PatternState.NONE and state is not PatternState.BLOCKED:
            candidate = PatternCandidate(
                statement="battery voltage tends to fall during prolonged parked audio load",
                observation_key="vehicle.power.parked-audio-voltage",
                scope="founder-vehicle",
                state=state,
                confidence=confidence,
                support_count=5,
                independent_contexts=3,
                corroborating_sources=2,
                contradiction_count=0,
            )
        return PatternAssessment(
            state=state,
            disposition=(
                PatternDisposition.FORM_CANDIDATE
                if candidate is not None
                else PatternDisposition.OBSERVE
            ),
            reasons=(f"state:{state.value}",),
            candidate=candidate,
            eligible_for_expectation_review=eligible,
        )

    def context(self, **overrides):
        values = {
            "expected_statement": (
                "if the parked audio load continues, battery voltage may fall again"
            ),
            "triggering_conditions": (
                "vehicle parked",
                "audio amplifiers remain active",
            ),
            "evidence_references": (
                "pattern:vehicle.power.parked-audio-voltage",
                "receipt:power-observation-series-17",
            ),
            "evaluated_at": 100.0,
            "horizon_seconds": 300.0,
            "review_after_seconds": 120.0,
        }
        values.update(overrides)
        return ExpectationContext(**values)

    def test_stable_pattern_forms_active_finite_expectation(self):
        result = ExpectationEngine().assess(self.pattern(), self.context())

        self.assertIs(result.state, ExpectationState.ACTIVE)
        self.assertIs(result.disposition, ExpectationDisposition.FORM_CANDIDATE)
        self.assertTrue(result.eligible_for_intent_review)
        self.assertIsNotNone(result.candidate)
        self.assertEqual(result.candidate.formed_at, 100.0)
        self.assertEqual(result.candidate.review_at, 220.0)
        self.assertEqual(result.candidate.expires_at, 400.0)

    def test_expectation_remains_candidate_not_fact_or_authority(self):
        candidate = ExpectationEngine().assess(
            self.pattern(), self.context()
        ).candidate

        self.assertIsNotNone(candidate)
        self.assertTrue(candidate.candidate)
        self.assertTrue(candidate.expectation)
        self.assertFalse(candidate.fact)
        self.assertFalse(candidate.prediction)
        self.assertFalse(candidate.canonical)
        self.assertFalse(candidate.speaking_authorized)
        self.assertFalse(candidate.memory_write_authorized)
        self.assertFalse(candidate.execution_authorized)
        self.assertEqual(candidate.authority, "none")

    def test_non_stable_pattern_cannot_form_expectation(self):
        result = ExpectationEngine().assess(
            self.pattern(state=PatternState.TESTABLE, eligible=False),
            self.context(),
        )

        self.assertIs(result.state, ExpectationState.NONE)
        self.assertIs(result.disposition, ExpectationDisposition.OBSERVE)
        self.assertIsNone(result.candidate)
        self.assertIn("stable-pattern-required", result.reasons)

    def test_missing_trigger_conditions_keeps_observing(self):
        result = ExpectationEngine().assess(
            self.pattern(), self.context(triggering_conditions=())
        )

        self.assertIs(result.state, ExpectationState.NONE)
        self.assertIn("no-bounded-triggering-conditions", result.reasons)

    def test_missing_evidence_references_keeps_observing(self):
        result = ExpectationEngine().assess(
            self.pattern(), self.context(evidence_references=())
        )

        self.assertIs(result.state, ExpectationState.NONE)
        self.assertIn("no-evidence-references", result.reasons)

    def test_lower_confidence_stable_pattern_forms_provisional_candidate(self):
        result = ExpectationEngine().assess(
            self.pattern(confidence=0.60), self.context()
        )

        self.assertIs(result.state, ExpectationState.PROVISIONAL)
        self.assertFalse(result.eligible_for_intent_review)
        self.assertIsNotNone(result.candidate)

    def test_existing_expectation_is_retained_without_auto_renewal(self):
        result = ExpectationEngine().assess(
            self.pattern(),
            self.context(
                evaluated_at=220.0,
                existing_candidate=True,
                existing_formed_at=100.0,
                existing_expires_at=400.0,
            ),
        )

        self.assertIs(result.state, ExpectationState.ACTIVE)
        self.assertIs(result.disposition, ExpectationDisposition.RETAIN_CANDIDATE)
        self.assertEqual(result.candidate.expires_at, 400.0)
        self.assertIn("review-due-no-auto-renewal", result.reasons)

    def test_single_contradiction_weakens_expectation(self):
        result = ExpectationEngine().assess(
            self.pattern(), self.context(contradiction_count=1)
        )

        self.assertIs(result.state, ExpectationState.WEAKENED)
        self.assertIs(result.disposition, ExpectationDisposition.WEAKEN_CANDIDATE)
        self.assertFalse(result.eligible_for_intent_review)

    def test_repeated_contradiction_retires_expectation(self):
        result = ExpectationEngine().assess(
            self.pattern(), self.context(contradiction_count=2)
        )

        self.assertIs(result.state, ExpectationState.RETIRED)
        self.assertIs(result.disposition, ExpectationDisposition.RETIRE_CANDIDATE)
        self.assertIn("evidence-no-longer-supports-expectation", result.reasons)

    def test_repeated_missed_occurrence_retires_expectation(self):
        result = ExpectationEngine().assess(
            self.pattern(), self.context(missed_occurrences=2)
        )

        self.assertIs(result.state, ExpectationState.RETIRED)
        self.assertIs(result.disposition, ExpectationDisposition.RETIRE_CANDIDATE)

    def test_existing_candidate_expires_at_original_boundary(self):
        result = ExpectationEngine().assess(
            self.pattern(),
            self.context(
                evaluated_at=401.0,
                existing_candidate=True,
                existing_formed_at=100.0,
                existing_expires_at=400.0,
            ),
        )

        self.assertIs(result.state, ExpectationState.EXPIRED)
        self.assertIs(result.disposition, ExpectationDisposition.EXPIRE_CANDIDATE)
        self.assertEqual(result.candidate.expires_at, 400.0)
        self.assertIn("finite-expectation-expired", result.reasons)

    def test_integrity_gate_blocks_expectation_formation(self):
        result = ExpectationEngine().assess(
            self.pattern(), self.context(integrity_aligned=False)
        )

        self.assertIs(result.state, ExpectationState.BLOCKED)
        self.assertIs(result.disposition, ExpectationDisposition.BLOCKED)
        self.assertEqual(result.authority, "none")

    def test_safety_priority_outranks_expectation_formation(self):
        result = ExpectationEngine().assess(
            self.pattern(), self.context(safety_priority=True)
        )

        self.assertIs(result.state, ExpectationState.BLOCKED)
        self.assertIs(result.disposition, ExpectationDisposition.DEFER_TO_SAFETY)
        self.assertIsNone(result.candidate)

    def test_identical_inputs_produce_identical_expectations(self):
        pattern = self.pattern()
        context = self.context()
        engine = ExpectationEngine()

        first = engine.assess(pattern, context)
        second = engine.assess(pattern, context)

        self.assertEqual(first, second)

    def test_existing_candidate_requires_finite_original_times(self):
        with self.assertRaisesRegex(ValueError, "formed and expiry"):
            self.context(existing_candidate=True)

    def test_review_must_fit_inside_horizon(self):
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            self.context(horizon_seconds=60.0, review_after_seconds=61.0)


if __name__ == "__main__":
    unittest.main()

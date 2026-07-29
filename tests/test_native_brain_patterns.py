# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.native_brain import (
    AttentionAssessment,
    ConfidenceBand,
    JudgmentAssessment,
    JudgmentDisposition,
    ObservationEnvelope,
    ObservationMaturity,
    PatternContext,
    PatternDisposition,
    PatternEngine,
    PatternState,
)


class NativeBrainPatternTests(unittest.TestCase):
    def observation(self, simulated=False):
        return ObservationEnvelope(
            event_type="vehicle.coolant.observed",
            source="ruby.sensor",
            payload={"celsius": 94.0},
            confidence=0.9,
            simulated=simulated,
        )

    def attention(
        self,
        maturity=ObservationMaturity.REPEATED,
        score=0.7,
        priority="high",
        reasons=None,
    ):
        return AttentionAssessment(
            maturity=maturity,
            score=score,
            priority=priority,
            reasons=tuple(reasons or (f"maturity:{maturity.value}",)),
        )

    def judgment(
        self,
        band=ConfidenceBand.SUPPORTED,
        confidence=0.75,
        disposition=JudgmentDisposition.READY,
    ):
        return JudgmentAssessment(
            confidence=confidence,
            band=band,
            disposition=disposition,
            reasons=("evidence-calibrated",),
            claim="coolant rises after extended idle",
            presentation_candidate=disposition is JudgmentDisposition.READY,
        )

    def context(self, **overrides):
        values = {
            "candidate_statement": "coolant tends to rise after extended idle",
            "observation_key": "vehicle.coolant.after-idle",
            "support_count": 2,
            "independent_contexts": 1,
            "corroborating_sources": 0,
            "contradiction_count": 0,
        }
        values.update(overrides)
        return PatternContext(**values)

    def test_single_occurrence_does_not_form_pattern(self):
        result = PatternEngine().assess(
            self.observation(),
            self.attention(ObservationMaturity.NEW),
            self.judgment(),
            self.context(support_count=1),
        )

        self.assertIs(result.state, PatternState.NONE)
        self.assertIs(result.disposition, PatternDisposition.OBSERVE)
        self.assertIsNone(result.candidate)

    def test_repeated_supported_evidence_forms_emerging_candidate(self):
        result = PatternEngine().assess(
            self.observation(),
            self.attention(),
            self.judgment(),
            self.context(),
        )

        self.assertIs(result.state, PatternState.EMERGING)
        self.assertIs(result.disposition, PatternDisposition.FORM_CANDIDATE)
        self.assertIsNotNone(result.candidate)
        self.assertFalse(result.candidate.fact)
        self.assertFalse(result.candidate.expectation)
        self.assertFalse(result.candidate.canonical)
        self.assertEqual(result.candidate.authority, "none")

    def test_independent_corroboration_forms_testable_candidate(self):
        result = PatternEngine().assess(
            self.observation(),
            self.attention(ObservationMaturity.PATTERN),
            self.judgment(),
            self.context(
                support_count=3,
                independent_contexts=2,
                corroborating_sources=1,
            ),
        )

        self.assertIs(result.state, PatternState.TESTABLE)
        self.assertFalse(result.eligible_for_expectation_review)

    def test_strong_broad_support_forms_stable_candidate_only(self):
        result = PatternEngine().assess(
            self.observation(),
            self.attention(ObservationMaturity.EXPECTATION, score=0.9),
            self.judgment(ConfidenceBand.STRONG, 0.9),
            self.context(
                support_count=5,
                independent_contexts=3,
                corroborating_sources=2,
            ),
        )

        self.assertIs(result.state, PatternState.STABLE)
        self.assertTrue(result.eligible_for_expectation_review)
        self.assertFalse(result.candidate.expectation)
        self.assertFalse(result.candidate.fact)

    def test_heavy_contradiction_rejects_candidate(self):
        result = PatternEngine().assess(
            self.observation(),
            self.attention(ObservationMaturity.PATTERN),
            self.judgment(),
            self.context(
                support_count=2,
                independent_contexts=2,
                corroborating_sources=1,
                contradiction_count=3,
                existing_candidate=True,
            ),
        )

        self.assertIs(result.state, PatternState.REJECTED)
        self.assertIs(result.disposition, PatternDisposition.REJECT_CANDIDATE)
        self.assertIsNotNone(result.candidate)

    def test_simulation_cannot_form_real_pattern(self):
        result = PatternEngine().assess(
            self.observation(simulated=True),
            self.attention(ObservationMaturity.PATTERN),
            self.judgment(ConfidenceBand.STRONG, 0.9),
            self.context(
                support_count=6,
                independent_contexts=4,
                corroborating_sources=3,
            ),
        )

        self.assertIs(result.state, PatternState.NONE)
        self.assertIn("simulated-evidence", result.reasons[0])
        self.assertIsNone(result.candidate)

    def test_integrity_gate_blocks_pattern_formation(self):
        result = PatternEngine().assess(
            self.observation(),
            self.attention(),
            self.judgment(),
            self.context(integrity_aligned=False),
        )

        self.assertIs(result.state, PatternState.BLOCKED)
        self.assertIs(result.disposition, PatternDisposition.BLOCKED)
        self.assertEqual(result.authority, "none")

    def test_safety_path_outranks_pattern_formation(self):
        result = PatternEngine().assess(
            self.observation(),
            self.attention(
                ObservationMaturity.REPEATED,
                priority="critical",
                reasons=("maturity:repeated", "safety-relevant"),
            ),
            JudgmentAssessment(
                confidence=0.0,
                band=ConfidenceBand.BLOCKED,
                disposition=JudgmentDisposition.DEFER_TO_SAFETY,
                reasons=("safety-path-owns-next-judgment",),
            ),
            self.context(),
        )

        self.assertIs(result.state, PatternState.BLOCKED)
        self.assertIs(result.disposition, PatternDisposition.DEFER_TO_SAFETY)
        self.assertIsNone(result.candidate)

    def test_identical_inputs_produce_identical_pattern_assessments(self):
        observation = self.observation()
        attention = self.attention(ObservationMaturity.PATTERN)
        judgment = self.judgment()
        context = self.context(
            support_count=3,
            independent_contexts=2,
            corroborating_sources=1,
        )
        engine = PatternEngine()

        first = engine.assess(observation, attention, judgment, context)
        second = engine.assess(observation, attention, judgment, context)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

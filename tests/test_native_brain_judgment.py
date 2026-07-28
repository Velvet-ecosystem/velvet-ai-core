# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.native_brain import (
    AttentionAssessment,
    ConfidenceBand,
    CuriosityAssessment,
    CuriosityDisposition,
    JudgmentContext,
    JudgmentDisposition,
    JudgmentEngine,
    ObservationEnvelope,
    ObservationMaturity,
)


class NativeBrainJudgmentTests(unittest.TestCase):
    def observation(self, confidence=0.8, simulated=False):
        return ObservationEnvelope(
            event_type="vehicle.coolant.observed",
            source="ruby.sensor",
            payload={"celsius": 92.0},
            confidence=confidence,
            simulated=simulated,
        )

    def attention(
        self,
        maturity=ObservationMaturity.CONFIRMED,
        score=0.7,
        priority="normal",
        reasons=None,
    ):
        return AttentionAssessment(
            maturity=maturity,
            score=score,
            priority=priority,
            reasons=tuple(reasons or (f"maturity:{maturity.value}",)),
        )

    def curiosity(self, disposition=CuriosityDisposition.NONE):
        question = None
        if disposition is CuriosityDisposition.QUESTION_CANDIDATE:
            question = "Which verified observation resolves the conflict?"
        return CuriosityAssessment(
            disposition=disposition,
            reason="bounded curiosity state",
            question_candidate=question,
        )

    def test_unaligned_integrity_blocks_judgment(self):
        result = JudgmentEngine().assess(
            self.observation(),
            self.attention(),
            self.curiosity(),
            JudgmentContext(
                candidate_claim="Coolant temperature is stable.",
                integrity_aligned=False,
            ),
        )

        self.assertIs(result.band, ConfidenceBand.BLOCKED)
        self.assertIs(result.disposition, JudgmentDisposition.BLOCKED)
        self.assertEqual(result.confidence, 0.0)
        self.assertFalse(result.presentation_candidate)

    def test_missing_required_evidence_stays_insufficient_and_asks(self):
        result = JudgmentEngine().assess(
            self.observation(),
            self.attention(),
            self.curiosity(CuriosityDisposition.QUESTION_CANDIDATE),
            JudgmentContext(
                candidate_claim="Coolant temperature is stable.",
                source_reliability=0.8,
                evidence_completeness=0.7,
                missing_evidence=("second temperature sample",),
            ),
        )

        self.assertIs(result.band, ConfidenceBand.INSUFFICIENT)
        self.assertIs(result.disposition, JudgmentDisposition.QUESTION)
        self.assertIn("required-evidence-missing", result.reasons)
        self.assertFalse(result.presentation_candidate)

    def test_contradiction_lowers_confidence_and_keeps_question_open(self):
        engine = JudgmentEngine()
        baseline = engine.assess(
            self.observation(),
            self.attention(),
            self.curiosity(),
            JudgmentContext(
                candidate_claim="Coolant temperature is stable.",
                source_reliability=0.8,
                evidence_completeness=0.8,
            ),
        )
        conflicted = engine.assess(
            self.observation(),
            self.attention(),
            self.curiosity(CuriosityDisposition.QUESTION_CANDIDATE),
            JudgmentContext(
                candidate_claim="Coolant temperature is stable.",
                source_reliability=0.8,
                evidence_completeness=0.8,
                contradiction=0.8,
            ),
        )

        self.assertLess(conflicted.confidence, baseline.confidence)
        self.assertIs(conflicted.disposition, JudgmentDisposition.QUESTION)
        self.assertIn("contradictory-evidence", conflicted.reasons)

    def test_mature_corroborated_evidence_becomes_strong_presentation_candidate(self):
        result = JudgmentEngine().assess(
            self.observation(confidence=0.95),
            self.attention(
                maturity=ObservationMaturity.EXPECTATION,
                score=0.85,
                priority="high",
            ),
            self.curiosity(CuriosityDisposition.RESOLVED),
            JudgmentContext(
                candidate_claim="Coolant temperature remains within its established range.",
                source_reliability=0.95,
                evidence_completeness=0.95,
                freshness=0.95,
                corroborating_sources=3,
            ),
        )

        self.assertIs(result.band, ConfidenceBand.STRONG)
        self.assertIs(result.disposition, JudgmentDisposition.READY)
        self.assertTrue(result.presentation_candidate)
        self.assertEqual(result.authority, "none")
        self.assertFalse(result.canonical)

    def test_simulated_evidence_cannot_independently_support_a_claim(self):
        result = JudgmentEngine().assess(
            self.observation(confidence=1.0, simulated=True),
            self.attention(
                maturity=ObservationMaturity.EXPECTATION,
                score=1.0,
                priority="high",
            ),
            self.curiosity(CuriosityDisposition.RESOLVED),
            JudgmentContext(
                candidate_claim="Coolant temperature remains within its established range.",
                source_reliability=1.0,
                evidence_completeness=1.0,
                corroborating_sources=3,
            ),
        )

        self.assertLessEqual(result.confidence, 0.49)
        self.assertIs(result.band, ConfidenceBand.TENTATIVE)
        self.assertIs(result.disposition, JudgmentDisposition.CORRELATE)
        self.assertIn("simulated-evidence-cap", result.reasons)
        self.assertFalse(result.presentation_candidate)

    def test_safety_priority_bypasses_normal_judgment(self):
        result = JudgmentEngine().assess(
            self.observation(),
            self.attention(
                priority="critical",
                reasons=("maturity:new", "safety-relevant"),
            ),
            self.curiosity(CuriosityDisposition.DEFER_TO_SAFETY),
            JudgmentContext(candidate_claim="A safety event may be developing."),
        )

        self.assertIs(result.disposition, JudgmentDisposition.DEFER_TO_SAFETY)
        self.assertIs(result.band, ConfidenceBand.BLOCKED)
        self.assertFalse(result.presentation_candidate)

    def test_evidence_without_a_candidate_claim_remains_observation(self):
        result = JudgmentEngine().assess(
            self.observation(confidence=0.95),
            self.attention(
                maturity=ObservationMaturity.EXPECTATION,
                score=0.9,
                priority="high",
            ),
            self.curiosity(CuriosityDisposition.RESOLVED),
            JudgmentContext(
                source_reliability=0.95,
                evidence_completeness=0.95,
                corroborating_sources=3,
            ),
        )

        self.assertIs(result.disposition, JudgmentDisposition.OBSERVE)
        self.assertIsNone(result.claim)
        self.assertFalse(result.presentation_candidate)

    def test_identical_inputs_produce_identical_judgments(self):
        observation = self.observation()
        attention = self.attention()
        curiosity = self.curiosity(CuriosityDisposition.WATCH)
        context = JudgmentContext(
            candidate_claim="Coolant temperature may be changing.",
            source_reliability=0.7,
            evidence_completeness=0.5,
            corroborating_sources=1,
        )
        engine = JudgmentEngine()

        first = engine.assess(observation, attention, curiosity, context)
        second = engine.assess(observation, attention, curiosity, context)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

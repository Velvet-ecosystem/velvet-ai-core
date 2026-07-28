# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.native_brain.attention import (
    AttentionContext,
    AttentionEngine,
    ObservationMaturity,
)
from velvet.core.native_brain.cognition import ObservationEnvelope


class NativeBrainAttentionTests(unittest.TestCase):
    def observation(self, confidence=0.8):
        return ObservationEnvelope(
            event_type="vehicle.temperature.observed",
            source="ruby.sensor",
            payload={"celsius": 91.0},
            confidence=confidence,
        )

    def test_single_observation_starts_new_and_low(self):
        result = AttentionEngine().assess(self.observation(), AttentionContext())
        self.assertEqual(result.maturity, ObservationMaturity.NEW)
        self.assertEqual(result.priority, "low")
        self.assertEqual(result.authority, "none")

    def test_repetition_advances_maturity(self):
        result = AttentionEngine().assess(
            self.observation(), AttentionContext(repetition_count=2)
        )
        self.assertEqual(result.maturity, ObservationMaturity.REPEATED)

    def test_corroboration_confirms_observation(self):
        result = AttentionEngine().assess(
            self.observation(),
            AttentionContext(repetition_count=2, corroborating_sources=1),
        )
        self.assertEqual(result.maturity, ObservationMaturity.CONFIRMED)
        self.assertIn("corroborated", result.reasons)

    def test_history_and_repetition_form_pattern_and_expectation(self):
        engine = AttentionEngine()
        pattern = engine.assess(
            self.observation(),
            AttentionContext(repetition_count=4, historical_matches=1),
        )
        expectation = engine.assess(
            self.observation(),
            AttentionContext(repetition_count=5, historical_matches=3),
        )
        self.assertEqual(pattern.maturity, ObservationMaturity.PATTERN)
        self.assertEqual(expectation.maturity, ObservationMaturity.EXPECTATION)

    def test_safety_relevance_has_priority_without_authority(self):
        result = AttentionEngine().assess(
            self.observation(), AttentionContext(safety_relevance=0.9)
        )
        self.assertEqual(result.priority, "critical")
        self.assertEqual(result.authority, "none")

    def test_identical_inputs_are_deterministic(self):
        context = AttentionContext(
            repetition_count=3,
            corroborating_sources=1,
            owner_relevance=0.7,
            novelty=0.6,
        )
        engine = AttentionEngine()
        first = engine.assess(self.observation(), context)
        second = engine.assess(self.observation(), context)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

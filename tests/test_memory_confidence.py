# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.memory.confidence import MemoryConfidencePolicy


class MemoryConfidencePolicyTests(unittest.TestCase):
    def test_confidence_bands_are_explicit(self):
        self.assertEqual(MemoryConfidencePolicy.assess(0.9).band, "high")
        self.assertEqual(MemoryConfidencePolicy.assess(0.7).band, "moderate")
        self.assertEqual(MemoryConfidencePolicy.assess(0.4).band, "low")
        self.assertEqual(MemoryConfidencePolicy.assess(0.1).band, "very_low")

    def test_revision_step_is_limited(self):
        self.assertEqual(MemoryConfidencePolicy.revise(0.4, 0.9), 0.65)
        self.assertEqual(MemoryConfidencePolicy.revise(0.8, 0.1), 0.55)

    def test_custom_revision_step_is_supported(self):
        self.assertEqual(MemoryConfidencePolicy.revise(0.4, 0.9, max_step=0.1), 0.5)

    def test_confidence_never_promotes_memory_to_fact(self):
        self.assertFalse(
            MemoryConfidencePolicy.allows_fact_promotion("inference", "candidate", 1.0)
        )
        self.assertFalse(
            MemoryConfidencePolicy.allows_fact_promotion("candidate", "accepted", 1.0)
        )

    def test_invalid_values_are_rejected(self):
        with self.assertRaises(ValueError):
            MemoryConfidencePolicy.assess(1.1)
        with self.assertRaises(TypeError):
            MemoryConfidencePolicy.assess("high")
        with self.assertRaises(ValueError):
            MemoryConfidencePolicy.revise(0.5, 0.6, max_step=0.0)


if __name__ == "__main__":
    unittest.main()

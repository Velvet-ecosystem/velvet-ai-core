# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.memory.decay import MemoryDecayPolicy


class MemoryDecayPolicyTests(unittest.TestCase):
    def test_unprotected_memory_loses_salience_by_half_life(self):
        result = MemoryDecayPolicy.assess(
            age_seconds=100.0,
            base_salience=1.0,
            half_life_seconds=100.0,
        )

        self.assertFalse(result.protected)
        self.assertEqual(result.salience, 0.5)

    def test_protected_tags_preserve_salience(self):
        for tag in ("pinned", "safety", "continuity", "identity"):
            result = MemoryDecayPolicy.assess(
                age_seconds=1000000.0,
                base_salience=0.8,
                tags=[tag],
            )
            self.assertTrue(result.protected)
            self.assertEqual(result.salience, 0.8)

    def test_accepted_memory_is_protected(self):
        result = MemoryDecayPolicy.assess(
            age_seconds=1000000.0,
            base_salience=0.9,
            authority_status="accepted",
        )

        self.assertTrue(result.protected)
        self.assertEqual(result.salience, 0.9)

    def test_reinforcement_is_reversible_and_bounded(self):
        self.assertEqual(MemoryDecayPolicy.reinforce(0.5, 0.5), 0.75)
        self.assertEqual(MemoryDecayPolicy.reinforce(1.0, 0.8), 1.0)

    def test_invalid_values_are_rejected(self):
        with self.assertRaises(ValueError):
            MemoryDecayPolicy.assess(age_seconds=-1.0)
        with self.assertRaises(ValueError):
            MemoryDecayPolicy.assess(age_seconds=1.0, half_life_seconds=0.0)
        with self.assertRaises(ValueError):
            MemoryDecayPolicy.reinforce(0.5, 1.1)


if __name__ == "__main__":
    unittest.main()

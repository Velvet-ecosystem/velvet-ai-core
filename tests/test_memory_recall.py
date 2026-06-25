# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.memory.recall import MemoryRecallRanker, RecallCandidate


class MemoryRecallRankerTests(unittest.TestCase):
    def test_ranking_is_deterministic(self):
        candidates = [
            RecallCandidate("b", 0.8, 0.9, 0.7, "accepted"),
            RecallCandidate("a", 0.8, 0.9, 0.7, "accepted"),
        ]

        ranked = MemoryRecallRanker.rank(candidates)

        self.assertEqual([item.event_id for item in ranked], ["a", "b"])

    def test_association_is_strongest_component(self):
        strong_link = RecallCandidate("linked", 1.0, 0.4, 0.4, "candidate")
        weak_link = RecallCandidate("weak", 0.1, 1.0, 1.0, "accepted")

        ranked = MemoryRecallRanker.rank([weak_link, strong_link])

        self.assertEqual(ranked[0].event_id, "linked")

    def test_authority_affects_rank_but_does_not_dominate(self):
        accepted = RecallCandidate("accepted", 0.5, 0.5, 0.5, "accepted")
        candidate = RecallCandidate("candidate", 0.5, 0.5, 0.5, "candidate")

        ranked = MemoryRecallRanker.rank([candidate, accepted])

        self.assertEqual(ranked[0].event_id, "accepted")
        self.assertLess(ranked[0].authority_weight, 1.01)

    def test_score_exposes_component_values(self):
        result = MemoryRecallRanker.score(
            RecallCandidate("event-1", 0.7, 0.6, 0.5, "historical")
        )

        self.assertEqual(result.association, 0.7)
        self.assertEqual(result.confidence, 0.6)
        self.assertEqual(result.salience, 0.5)
        self.assertEqual(result.authority_weight, 0.8)

    def test_invalid_values_are_rejected(self):
        with self.assertRaises(ValueError):
            MemoryRecallRanker.score(
                RecallCandidate("", 0.5, 0.5, 0.5, "accepted")
            )
        with self.assertRaises(ValueError):
            MemoryRecallRanker.score(
                RecallCandidate("event", 1.1, 0.5, 0.5, "accepted")
            )


if __name__ == "__main__":
    unittest.main()

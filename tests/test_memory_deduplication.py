# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.memory.deduplication import MemoryDuplicateDetector


class MemoryDuplicateDetectorTests(unittest.TestCase):
    def setUp(self):
        self.detector = MemoryDuplicateDetector()

    def test_exact_duplicate_ignores_event_identity_and_timestamp(self):
        left = {
            "event_id": "a",
            "ts": 1.0,
            "kind": "fact",
            "payload": {"claim": "route A"},
            "source": "conversation",
            "tags": ["route", "preference"],
        }
        right = {
            "event_id": "b",
            "ts": 2.0,
            "kind": "fact",
            "payload": {"claim": "route A"},
            "source": "conversation",
            "tags": ["preference", "route"],
        }

        self.assertTrue(self.detector.is_exact_duplicate(left, right))

    def test_semantically_similar_but_different_payload_is_not_duplicate(self):
        left = {
            "event_id": "a",
            "kind": "fact",
            "payload": {"claim": "route A"},
        }
        right = {
            "event_id": "b",
            "kind": "fact",
            "payload": {"claim": "prefers route A"},
        }

        self.assertFalse(self.detector.is_exact_duplicate(left, right))

    def test_duplicate_groups_are_deterministic(self):
        records = [
            {"event_id": "c", "kind": "fact", "payload": {"x": 1}},
            {"event_id": "a", "kind": "fact", "payload": {"x": 1}},
            {"event_id": "b", "kind": "fact", "payload": {"x": 2}},
        ]

        groups = self.detector.duplicate_groups(records)

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].event_ids, ("a", "c"))

    def test_authority_or_receipt_difference_prevents_duplicate_match(self):
        left = {
            "event_id": "a",
            "kind": "fact",
            "payload": {"x": 1},
            "authority_status": "candidate",
        }
        right = {
            "event_id": "b",
            "kind": "fact",
            "payload": {"x": 1},
            "authority_status": "accepted",
        }

        self.assertFalse(self.detector.is_exact_duplicate(left, right))

    def test_invalid_records_are_rejected(self):
        with self.assertRaises(ValueError):
            self.detector.fingerprint({"kind": "fact", "payload": {}})
        with self.assertRaises(TypeError):
            self.detector.fingerprint(
                {"event_id": "a", "kind": "fact", "payload": "not-a-dict"}
            )


if __name__ == "__main__":
    unittest.main()

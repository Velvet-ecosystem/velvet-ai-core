import unittest

from velvet.cli.memory import explain, neighbours, recall, verify


class MemoryCliTests(unittest.TestCase):
    def records(self):
        return [
            {"event_id": "query-1", "ts": 100.0, "related_event_ids": ["memory-1"]},
            {"event_id": "memory-1", "ts": 100.0, "related_event_ids": ["query-1"], "confidence": 0.9, "authority_status": "accepted"},
        ]

    def test_recall_and_explain_are_read_only(self):
        records = self.records()
        recalled = recall(records, "query-1", 1)
        detail = explain(records, "query-1", 1)
        self.assertEqual(recalled[0]["event_id"], "memory-1")
        self.assertFalse(detail["truth_claimed"])
        self.assertFalse(detail["authority_granted"])
        self.assertEqual(records, self.records())

    def test_neighbours_and_verify(self):
        linked = neighbours(self.records(), "query-1")
        checked = verify(self.records())
        self.assertEqual(linked["neighbours"], ["memory-1"])
        self.assertEqual(checked, {"valid": True, "record_count": 2, "mode": "read-only"})


if __name__ == "__main__":
    unittest.main()

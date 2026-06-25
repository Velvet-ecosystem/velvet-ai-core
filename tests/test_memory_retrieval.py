# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.memory.retrieval import MemoryRetrievalService


class MemoryRetrievalServiceTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            {
                "event_id": "query",
                "ts": 100.0,
                "kind": "conversation",
                "payload": {"text": "route"},
                "related_event_ids": ["fact-a", "candidate-b"],
            },
            {
                "event_id": "fact-a",
                "ts": 50.0,
                "kind": "fact",
                "payload": {"claim": "route A"},
                "confidence": 0.9,
                "authority_status": "accepted",
            },
            {
                "event_id": "candidate-b",
                "ts": 50.0,
                "kind": "candidate",
                "payload": {"claim": "route B"},
                "confidence": 0.4,
                "authority_status": "candidate",
            },
            {
                "event_id": "unrelated",
                "ts": 100.0,
                "kind": "fact",
                "payload": {"claim": "unrelated"},
                "confidence": 1.0,
                "authority_status": "accepted",
            },
        ]

    def test_retrieves_only_exact_neighbours(self):
        service = MemoryRetrievalService(self.records)

        results = service.retrieve("query", now=100.0)

        self.assertEqual(
            [result.record["event_id"] for result in results],
            ["fact-a", "candidate-b"],
        )
        self.assertNotIn("unrelated", [result.record["event_id"] for result in results])

    def test_result_exposes_score_components(self):
        service = MemoryRetrievalService(self.records)

        result = service.retrieve("query", limit=1, now=100.0)[0]

        self.assertEqual(result.score.event_id, "fact-a")
        self.assertEqual(result.score.association, 1.0)
        self.assertEqual(result.score.confidence, 0.9)
        self.assertEqual(result.score.authority_weight, 1.0)

    def test_limit_and_unknown_query_are_safe(self):
        service = MemoryRetrievalService(self.records)

        self.assertEqual(len(service.retrieve("query", limit=1, now=100.0)), 1)
        self.assertEqual(service.retrieve("missing", now=100.0), [])

    def test_input_and_returned_records_do_not_mutate_service_snapshot(self):
        source = list(self.records)
        service = MemoryRetrievalService(source)
        source[1]["payload"]["claim"] = "changed outside"

        first = service.retrieve("query", limit=1, now=100.0)[0]
        first.record["payload"] = {"claim": "changed result"}
        second = service.retrieve("query", limit=1, now=100.0)[0]

        self.assertEqual(second.record["payload"], {"claim": "route A"})

    def test_records_without_timestamp_are_not_ranked(self):
        records = list(self.records)
        records[1] = dict(records[1])
        records[1].pop("ts")
        service = MemoryRetrievalService(records)

        results = service.retrieve("query", now=100.0)

        self.assertEqual([result.record["event_id"] for result in results], ["candidate-b"])

    def test_duplicate_event_ids_and_bad_limits_are_rejected(self):
        with self.assertRaises(ValueError):
            MemoryRetrievalService([self.records[0], self.records[0]])

        service = MemoryRetrievalService(self.records)
        with self.assertRaises(ValueError):
            service.retrieve("query", limit=0, now=100.0)


if __name__ == "__main__":
    unittest.main()

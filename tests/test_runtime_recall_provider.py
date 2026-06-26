# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.memory.retrieval import MemoryRetrievalService
from velvet.core.memory.runtime_provider import RuntimeRecallProvider


class RuntimeRecallProviderTests(unittest.TestCase):
    def test_returns_real_retrieval_results(self):
        records = [
            {
                "event_id": "query-1",
                "ts": 100.0,
                "kind": "observation",
                "related_event_ids": ["memory-1"],
                "confidence": 1.0,
                "authority_status": "observed",
            },
            {
                "event_id": "memory-1",
                "ts": 100.0,
                "kind": "fact",
                "related_event_ids": ["query-1"],
                "confidence": 0.9,
                "authority_status": "accepted",
            },
        ]
        service = MemoryRetrievalService(records)
        provider = RuntimeRecallProvider(service)

        results = provider("query-1", 10)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score.event_id, "memory-1")
        self.assertEqual(results[0].record["event_id"], "memory-1")
        self.assertEqual(results[0].score.authority_weight, 1.0)

    def test_rejects_wrong_service_type(self):
        with self.assertRaises(TypeError):
            RuntimeRecallProvider(object())


if __name__ == "__main__":
    unittest.main()

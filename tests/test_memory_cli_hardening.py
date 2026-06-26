import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from velvet.cli.memory import load_records, main, recall
from velvet.core.memory.retrieval import MemoryRetrievalService


class MemoryCliHardeningTests(unittest.TestCase):
    def test_duplicate_event_ids_are_rejected(self):
        records = [
            {"event_id": "same", "ts": 1.0},
            {"event_id": "same", "ts": 2.0},
        ]
        with self.assertRaises(ValueError):
            MemoryRetrievalService(records)

    def test_limits_are_bounded_and_bool_is_rejected(self):
        service = MemoryRetrievalService([{"event_id": "query", "ts": 1.0}])
        for invalid in (True, 0, 51):
            with self.assertRaises(ValueError):
                service.retrieve("query", invalid)

    def test_malformed_source_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.json"
            path.write_text(json.dumps([{"event_id": "one"}, "bad"]), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_records(str(path))

    def test_main_emits_machine_readable_error(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(["memory", "--source", "/missing/records.json", "verify"])
        document = json.loads(stderr.getvalue())
        self.assertEqual(code, 2)
        self.assertFalse(document["ok"])
        self.assertIn("type", document["error"])
        self.assertIn("message", document["error"])

    def test_recall_respects_upper_bound(self):
        with self.assertRaises(ValueError):
            recall([{"event_id": "query", "ts": 1.0}], "query", 51)


if __name__ == "__main__":
    unittest.main()

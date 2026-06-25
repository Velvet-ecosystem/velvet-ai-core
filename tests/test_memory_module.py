# SPDX-License-Identifier: GPL-3.0-only

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from velvet.core.modules.memory import MemoryModule
from velvet.core.schemas.memory import MemoryRecord


class MemoryModuleTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "nested" / "memory.jsonl"
        self.registry_patch = patch(
            "velvet.core.modules.memory.get_registry", return_value=None
        )
        self.bus_patch = patch(
            "velvet.core.modules.memory.get_event_bus", return_value=None
        )
        self.registry_patch.start()
        self.bus_patch.start()

    def tearDown(self):
        self.bus_patch.stop()
        self.registry_patch.stop()
        self.tempdir.cleanup()

    def test_start_and_stop_write_lifecycle_records(self):
        module = MemoryModule(str(self.path))
        module.start()
        module.stop()

        records = [json.loads(line) for line in self.path.read_text().splitlines()]
        self.assertEqual([record["kind"] for record in records], ["system", "system"])
        self.assertEqual(
            [record["payload"]["event"] for record in records],
            ["boot", "shutdown"],
        )
        for record in records:
            self.assertEqual(record["schema_version"], 1)
            self.assertTrue(record["event_id"])
            self.assertIsInstance(record["ts"], float)
            self.assertEqual(record["source"], "velvet-ai-core")
            self.assertIn("lifecycle", record["tags"])

    def test_write_returns_stable_record_and_filtered_read_streams(self):
        module = MemoryModule(str(self.path))
        module.start()
        written = module.write_event(
            "observation",
            {"seat": "driver"},
            source="seat-monitor",
            confidence=0.92,
            authority_status="observed",
            receipt_id="receipt-123",
            related_event_ids=["prior-event"],
            tags=["vehicle", "seat"],
        )
        module.write_event("conversation", {"text": "hello"})

        observations = list(module.adapter.read("observation"))
        module.stop()

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]["event_id"], written["event_id"])
        self.assertEqual(observations[0]["payload"], {"seat": "driver"})
        self.assertEqual(observations[0]["confidence"], 0.92)
        self.assertEqual(observations[0]["receipt_id"], "receipt-123")
        self.assertEqual(observations[0]["related_event_ids"], ["prior-event"])

    def test_reader_skips_malformed_lines_without_losing_valid_history(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text(
            '{"kind":"observation","payload":{"ok":true}}\n'
            'not-json\n'
            '["not", "an", "object"]\n'
            '{"kind":"decision","payload":{"approved":true}}\n',
            encoding="utf-8",
        )
        module = MemoryModule(str(self.path))

        records = list(module.adapter.read())

        self.assertEqual([record["kind"] for record in records], ["observation", "decision"])

    def test_write_rejects_invalid_records_and_inactive_module(self):
        module = MemoryModule(str(self.path))
        with self.assertRaises(RuntimeError):
            module.write_event("observation", {})

        module.start()
        with self.assertRaises(ValueError):
            module.write_event("", {})
        with self.assertRaises(TypeError):
            module.write_event("observation", [])
        with self.assertRaises(ValueError):
            module.write_event("observation", {}, confidence=1.1)
        module.stop()

    def test_memory_record_round_trip_preserves_links_without_private_expansion(self):
        original = MemoryRecord(
            kind="candidate",
            payload={"claim": "driver prefers route A"},
            source="conversation",
            confidence=0.6,
            authority_status="candidate",
            related_event_ids=["conversation-1"],
            tags=["preference"],
        )

        restored = MemoryRecord.from_dict(original.to_dict())

        self.assertEqual(restored.to_dict(), original.to_dict())
        self.assertNotIn("receipt_id", original.to_dict())


if __name__ == "__main__":
    unittest.main()

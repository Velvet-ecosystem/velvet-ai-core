# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.memory import (
    MemoryLifecycle,
    MemoryTransitionBridge,
)


class RecordingWriter:
    def __init__(self):
        self.calls = []

    def write_event(self, **kwargs):
        self.calls.append(kwargs)
        return {"event_id": "written-1", **kwargs}


class MemoryTransitionBridgeTests(unittest.TestCase):
    def test_approved_transition_is_appended_once(self):
        writer = RecordingWriter()
        bridge = MemoryTransitionBridge(writer)
        transition = MemoryLifecycle.reviewed_fact(
            "candidate-1",
            {"claim": "route A is preferred"},
            reviewed_by="Mister",
            receipt_id="receipt-1",
            confidence=0.9,
        )

        result = bridge.append(transition, approved=True)

        self.assertEqual(len(writer.calls), 1)
        self.assertEqual(result["kind"], "fact")
        self.assertEqual(result["receipt_id"], "receipt-1")
        self.assertEqual(result["related_event_ids"], ["candidate-1"])

    def test_unapproved_transition_is_not_written(self):
        writer = RecordingWriter()
        bridge = MemoryTransitionBridge(writer)
        transition = MemoryLifecycle.candidate(
            {"claim": "route A is preferred"},
            source="conversation",
            confidence=0.5,
        )

        with self.assertRaises(PermissionError):
            bridge.append(transition, approved=False)

        self.assertEqual(writer.calls, [])

    def test_wrong_object_type_is_rejected(self):
        writer = RecordingWriter()
        bridge = MemoryTransitionBridge(writer)

        with self.assertRaises(TypeError):
            bridge.append({}, approved=True)

        self.assertEqual(writer.calls, [])


if __name__ == "__main__":
    unittest.main()

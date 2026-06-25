# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.memory import MemoryLifecycle


class MemoryLifecycleTests(unittest.TestCase):
    def test_candidate_is_described_without_being_written(self):
        transition = MemoryLifecycle.candidate(
            {"claim": "route A is preferred"},
            source="conversation",
            confidence=0.6,
        )

        self.assertEqual(transition.kind, "candidate")
        self.assertEqual(transition.authority_status, "candidate")
        self.assertEqual(transition.source, "conversation")
        self.assertEqual(transition.confidence, 0.6)

    def test_reviewed_fact_links_back_to_candidate(self):
        transition = MemoryLifecycle.reviewed_fact(
            "candidate-1",
            {"claim": "route A is preferred"},
            reviewed_by="Mister",
            receipt_id="receipt-1",
            confidence=0.95,
        )

        args = transition.to_write_args()
        self.assertEqual(args["kind"], "fact")
        self.assertEqual(args["authority_status"], "accepted")
        self.assertEqual(args["related_event_ids"], ["candidate-1"])
        self.assertEqual(args["receipt_id"], "receipt-1")
        self.assertEqual(args["payload"]["reviewed_by"], "Mister")

    def test_confidence_revision_preserves_target_history(self):
        transition = MemoryLifecycle.confidence_revision(
            "fact-1", 0.4, "new evidence conflicts"
        )

        self.assertEqual(transition.kind, "inference")
        self.assertEqual(transition.related_event_ids, ["fact-1"])
        self.assertEqual(transition.tags, ["confidence-revision"])
        self.assertEqual(transition.confidence, 0.4)

    def test_supersession_points_to_original_record(self):
        transition = MemoryLifecycle.supersession(
            "fact-old",
            "fact",
            {"claim": "route B is preferred"},
            reviewed_by="Mister",
            reason="preference changed",
            receipt_id="receipt-2",
            confidence=1.0,
        )

        args = transition.to_write_args()
        self.assertEqual(args["authority_status"], "superseded")
        self.assertEqual(args["related_event_ids"], ["fact-old"])
        self.assertEqual(args["payload"]["supersedes"], "fact-old")
        self.assertEqual(args["payload"]["reviewed_by"], "Mister")

    def test_required_link_fields_reject_blank_values(self):
        with self.assertRaises(ValueError):
            MemoryLifecycle.reviewed_fact("", {}, reviewed_by="Mister")
        with self.assertRaises(ValueError):
            MemoryLifecycle.confidence_revision("fact-1", 0.5, "")


if __name__ == "__main__":
    unittest.main()

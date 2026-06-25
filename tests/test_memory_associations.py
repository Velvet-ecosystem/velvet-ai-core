# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.memory.associations import MemoryAssociationIndex


class MemoryAssociationIndexTests(unittest.TestCase):
    def test_forward_links_and_backlinks_are_built(self):
        index = MemoryAssociationIndex()
        index.add_records(
            [
                {"event_id": "a", "related_event_ids": []},
                {"event_id": "b", "related_event_ids": ["a"]},
                {"event_id": "c", "related_event_ids": ["a", "b"]},
            ]
        )

        self.assertEqual(index.forward_links("c"), ["a", "b"])
        self.assertEqual(index.backlinks("a"), ["b", "c"])
        self.assertEqual(index.neighbours("b"), ["a", "c"])
        self.assertTrue(index.has_link("c", "b"))

    def test_duplicate_links_collapse_deterministically(self):
        index = MemoryAssociationIndex()
        index.add_record(
            {"event_id": "b", "related_event_ids": ["a", "a", "a"]}
        )

        self.assertEqual(index.forward_links("b"), ["a"])
        self.assertEqual(index.backlinks("a"), ["b"])

    def test_self_links_are_ignored(self):
        index = MemoryAssociationIndex()
        index.add_record({"event_id": "a", "related_event_ids": ["a"]})

        self.assertEqual(index.forward_links("a"), [])
        self.assertEqual(index.backlinks("a"), [])

    def test_invalid_records_are_rejected(self):
        index = MemoryAssociationIndex()

        with self.assertRaises(ValueError):
            index.add_record({"related_event_ids": []})
        with self.assertRaises(TypeError):
            index.add_record({"event_id": "a", "related_event_ids": "b"})
        with self.assertRaises(ValueError):
            index.add_record({"event_id": "a", "related_event_ids": [""]})


if __name__ == "__main__":
    unittest.main()

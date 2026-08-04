"""Tests for the guarded descriptive world-state container."""

import unittest

from velvet.core.schemas import (
    EntityIdentity,
    EntityLifecycle,
    IdentityStatus,
    TemporalState,
    WorldEntity,
)
from velvet.core.world_state import (
    WorldStateStore,
    WorldUpdateDisposition,
)


class WorldStateStoreTests(unittest.TestCase):
    def identity(self, name="Tiburon"):
        return EntityIdentity(
            entity_id="vehicle:tiburon",
            entity_type="vehicle",
            canonical_name=name,
            status=IdentityStatus.KNOWN,
            confidence=1.0,
        )

    def entity(
        self,
        sequence,
        monotonic_time,
        state=None,
        identity=None,
        receipts=("receipt-1",),
    ):
        return WorldEntity(
            identity=identity or self.identity(),
            temporal=TemporalState(
                observed_at=monotonic_time,
                received_at=monotonic_time,
                monotonic_time=monotonic_time,
                valid_from=monotonic_time,
                valid_until=None,
                stale_after_ms=1000,
                sequence=sequence,
            ),
            lifecycle=EntityLifecycle.ACTIVE,
            state=state or {"vehicle": {"speed_kph": 0}},
            source_receipt_ids=receipts,
        )

    def test_first_snapshot_becomes_current(self):
        store = WorldStateStore()
        entity = self.entity(1, 10.0)

        record = store.apply(entity)

        self.assertEqual(record.disposition, WorldUpdateDisposition.ACCEPTED)
        self.assertIs(store.current(entity.entity_id), entity)
        self.assertEqual(store.revision, 1)

    def test_newer_sequence_replaces_current_and_preserves_history(self):
        store = WorldStateStore()
        first = self.entity(1, 10.0)
        second = self.entity(
            2,
            11.0,
            state={"vehicle": {"speed_kph": 12}},
            receipts=("receipt-1", "receipt-2"),
        )

        store.apply(first)
        record = store.apply(second)

        self.assertEqual(record.disposition, WorldUpdateDisposition.ACCEPTED)
        self.assertIs(store.current(second.entity_id), second)
        self.assertEqual(store.revision, 2)
        self.assertEqual(len(store.history(second.entity_id)), 2)

    def test_equal_or_older_sequence_is_rejected(self):
        store = WorldStateStore()
        current = self.entity(3, 30.0)
        store.apply(current)

        record = store.apply(self.entity(3, 31.0))

        self.assertEqual(
            record.disposition,
            WorldUpdateDisposition.REJECTED_OLDER_SEQUENCE,
        )
        self.assertIs(store.current(current.entity_id), current)
        self.assertEqual(store.revision, 1)

    def test_newer_sequence_with_older_monotonic_time_is_rejected(self):
        store = WorldStateStore()
        current = self.entity(3, 30.0)
        store.apply(current)

        record = store.apply(self.entity(4, 29.0))

        self.assertEqual(
            record.disposition,
            WorldUpdateDisposition.REJECTED_OLDER_TIME,
        )
        self.assertIs(store.current(current.entity_id), current)

    def test_unsequenced_updates_require_increasing_monotonic_time(self):
        store = WorldStateStore()
        current = self.entity(None, 10.0)
        store.apply(current)

        record = store.apply(self.entity(None, 10.0))

        self.assertEqual(
            record.disposition,
            WorldUpdateDisposition.REJECTED_OLDER_TIME,
        )

    def test_identity_cannot_be_silently_renamed(self):
        store = WorldStateStore()
        current = self.entity(1, 10.0)
        store.apply(current)

        renamed = self.entity(
            2,
            11.0,
            identity=self.identity(name="Not Tiburon"),
        )
        record = store.apply(renamed)

        self.assertEqual(
            record.disposition,
            WorldUpdateDisposition.REJECTED_IDENTITY_CHANGE,
        )
        self.assertIs(store.current(current.entity_id), current)

    def test_view_is_a_copy_of_current_mapping(self):
        store = WorldStateStore()
        entity = self.entity(1, 10.0)
        store.apply(entity)

        view = store.view()
        copied = dict(view.entities)
        copied.clear()

        self.assertIs(store.current(entity.entity_id), entity)
        self.assertEqual(view.revision, 1)
        self.assertFalse(view.authority_granted)
        self.assertFalse(view.execution_performed)

    def test_rejected_update_is_still_recorded(self):
        store = WorldStateStore()
        store.apply(self.entity(2, 20.0))
        rejected = store.apply(self.entity(1, 19.0, receipts=("old",)))

        history = store.history("vehicle:tiburon")

        self.assertEqual(len(history), 2)
        self.assertIs(history[-1], rejected)
        self.assertEqual(history[-1].source_receipt_ids, ("old",))
        self.assertFalse(history[-1].authority_granted)
        self.assertFalse(history[-1].execution_performed)


if __name__ == "__main__":
    unittest.main()

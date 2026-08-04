"""Tests for explicit temporal transitions in the descriptive world model."""

import unittest

from velvet.core.schemas import (
    EntityIdentity,
    IdentityStatus,
    TemporalState,
    WorldEntity,
)
from velvet.core.temporal_transitions import (
    TemporalTransitionManager,
    TemporalTransitionType,
)


class TemporalTransitionTests(unittest.TestCase):
    def setUp(self):
        self.manager = TemporalTransitionManager()
        self.identity = EntityIdentity(
            entity_id="vehicle:tiburon",
            entity_type="vehicle",
            canonical_name="Tiburon",
            status=IdentityStatus.KNOWN,
            confidence=1.0,
        )
        self.current = WorldEntity(
            identity=self.identity,
            temporal=TemporalState(
                observed_at=100.0,
                received_at=101.0,
                monotonic_time=10.0,
                valid_from=100.0,
                valid_until=None,
                stale_after_ms=1000,
                sequence=4,
            ),
            source_receipt_ids=("receipt-4",),
        )

    def temporal(self, **changes):
        values = {
            "observed_at": 102.0,
            "received_at": 103.0,
            "monotonic_time": 12.0,
            "valid_from": 102.0,
            "valid_until": None,
            "stale_after_ms": 1000,
            "sequence": 5,
        }
        values.update(changes)
        return TemporalState(**values)

    def test_newer_temporal_state_advances(self):
        result = self.manager.advance(
            self.current,
            self.temporal(),
            ("receipt-5",),
        )
        self.assertEqual(result.record.transition_type, TemporalTransitionType.ADVANCE)
        self.assertEqual(result.entity.temporal.sequence, 5)
        self.assertIn("receipt-5", result.entity.source_receipt_ids)
        self.assertFalse(result.record.authority_granted)
        self.assertFalse(result.record.execution_performed)

    def test_older_sequence_is_rejected(self):
        result = self.manager.advance(
            self.current,
            self.temporal(sequence=4),
            ("receipt-old",),
        )
        self.assertEqual(
            result.record.transition_type,
            TemporalTransitionType.REJECTED_OLDER_SEQUENCE,
        )
        self.assertIs(result.entity, self.current)

    def test_equal_or_older_monotonic_time_is_rejected(self):
        result = self.manager.advance(
            self.current,
            self.temporal(sequence=5, monotonic_time=10.0),
            ("receipt-old-time",),
        )
        self.assertEqual(
            result.record.transition_type,
            TemporalTransitionType.REJECTED_OLDER_TIME,
        )

    def test_estimated_time_remains_explicit(self):
        result = self.manager.advance(
            self.current,
            self.temporal(estimated=True),
            ("receipt-estimate",),
        )
        self.assertEqual(
            result.record.transition_type,
            TemporalTransitionType.ESTIMATED,
        )
        self.assertTrue(result.entity.temporal.estimated)

    def test_disputed_order_remains_explicit(self):
        result = self.manager.advance(
            self.current,
            self.temporal(disputed=True),
            ("receipt-dispute",),
        )
        self.assertEqual(
            result.record.transition_type,
            TemporalTransitionType.DISPUTED,
        )
        self.assertTrue(result.entity.temporal.disputed)

    def test_gap_open_and_recovery_preserve_gap_history(self):
        opened = self.manager.open_gap(
            self.current,
            started_at=104.0,
            started_monotonic=14.0,
            reason="sensor stream interrupted",
            receipt_id="receipt-gap",
        )
        self.assertEqual(
            opened.record.transition_type,
            TemporalTransitionType.GAP_OPENED,
        )
        self.assertTrue(opened.entity.temporal.disputed)
        self.assertEqual(len(opened.gaps), 1)
        self.assertTrue(opened.gaps[0].open)

        recovered = self.manager.close_gap(
            opened.entity,
            ended_at=110.0,
            ended_monotonic=20.0,
            recovery_receipt_id="receipt-recovery",
            existing_gaps=opened.gaps,
            recovered_state=self.temporal(
                observed_at=110.0,
                received_at=110.5,
                monotonic_time=20.0,
                valid_from=110.0,
                sequence=6,
                disputed=False,
            ),
        )
        self.assertEqual(
            recovered.record.transition_type,
            TemporalTransitionType.GAP_CLOSED,
        )
        self.assertFalse(recovered.gaps[0].open)
        self.assertEqual(recovered.gaps[0].duration_seconds(), 6.0)
        self.assertFalse(recovered.entity.temporal.disputed)
        self.assertEqual(recovered.entity.temporal.sequence, 6)

    def test_recovery_cannot_revive_stale_history(self):
        opened = self.manager.open_gap(
            self.current,
            started_at=104.0,
            started_monotonic=14.0,
            reason="missing observations",
            receipt_id="receipt-gap",
        )
        recovered = self.manager.close_gap(
            opened.entity,
            ended_at=110.0,
            ended_monotonic=20.0,
            recovery_receipt_id="receipt-recovery",
            existing_gaps=opened.gaps,
            recovered_state=self.temporal(
                observed_at=99.0,
                received_at=110.0,
                monotonic_time=9.0,
                valid_from=99.0,
                sequence=3,
            ),
        )
        self.assertIn(
            recovered.record.transition_type,
            {
                TemporalTransitionType.REJECTED_OLDER_SEQUENCE,
                TemporalTransitionType.REJECTED_OLDER_TIME,
            },
        )
        self.assertTrue(recovered.gaps[0].open)

    def test_second_open_gap_is_rejected(self):
        opened = self.manager.open_gap(
            self.current,
            started_at=104.0,
            started_monotonic=14.0,
            reason="first gap",
            receipt_id="receipt-gap-1",
        )
        repeated = self.manager.open_gap(
            opened.entity,
            started_at=105.0,
            started_monotonic=15.0,
            reason="second gap",
            receipt_id="receipt-gap-2",
            existing_gaps=opened.gaps,
        )
        self.assertEqual(
            repeated.record.transition_type,
            TemporalTransitionType.REJECTED_INVALID_GAP,
        )
        self.assertEqual(repeated.gaps, opened.gaps)

    def test_duration_uses_valid_interval(self):
        self.assertEqual(self.manager.duration_seconds(self.current, 115.0), 15.0)
        ended = WorldEntity(
            identity=self.identity,
            temporal=self.temporal(valid_from=102.0, valid_until=108.0),
        )
        self.assertEqual(self.manager.duration_seconds(ended, 200.0), 6.0)


if __name__ == "__main__":
    unittest.main()

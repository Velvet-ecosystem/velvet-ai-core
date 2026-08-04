"""Tests for descriptive spatial relationship transitions."""

import unittest

from velvet.core.schemas import (
    EntityIdentity,
    EntityLifecycle,
    IdentityStatus,
    SpatialRelation,
    SpatialRelationType,
    TemporalState,
    WorldEntity,
)
from velvet.core.spatial_transitions import (
    SpatialTransitionDisposition,
    SpatialTransitionEngine,
)


class SpatialTransitionTests(unittest.TestCase):
    def setUp(self):
        self.engine = SpatialTransitionEngine()
        self.identity = EntityIdentity(
            entity_id="vehicle-tiburon",
            entity_type="vehicle",
            canonical_name="Tiburon",
            status=IdentityStatus.KNOWN,
            confidence=1.0,
        )
        self.entity = WorldEntity(
            identity=self.identity,
            temporal=TemporalState(
                observed_at=100.0,
                received_at=100.1,
                monotonic_time=50.0,
                valid_from=100.0,
                valid_until=None,
                stale_after_ms=1000,
                sequence=1,
            ),
            lifecycle=EntityLifecycle.ACTIVE,
            source_receipt_ids=("receipt-world-1",),
        )

    def relation(
        self,
        relation_id="rel-1",
        relation_type=SpatialRelationType.LOCATED_IN,
        object_entity_id="garage",
        observed_at=101.0,
        receipt_id="receipt-space-1",
    ):
        return SpatialRelation(
            relation_id=relation_id,
            subject_entity_id=self.entity.entity_id,
            relation_type=relation_type,
            object_entity_id=object_entity_id,
            frame_id="property-frame",
            confidence=0.9,
            observed_at=observed_at,
            receipt_id=receipt_id,
        )

    def test_adds_new_relation_without_authority(self):
        result = self.engine.add_or_replace(self.entity, self.relation())

        self.assertEqual(result.record.disposition, SpatialTransitionDisposition.ADDED)
        self.assertEqual(len(result.entity.spatial_relations), 1)
        self.assertFalse(result.record.authority_granted)
        self.assertFalse(result.record.execution_performed)
        self.assertFalse(result.entity.authority_granted)
        self.assertFalse(result.entity.execution_performed)

    def test_replaces_named_relation_with_newer_evidence(self):
        first = self.engine.add_or_replace(self.entity, self.relation()).entity
        replacement = self.relation(
            relation_id="rel-2",
            object_entity_id="driveway",
            observed_at=102.0,
            receipt_id="receipt-space-2",
        )

        result = self.engine.add_or_replace(
            first,
            replacement,
            replace_relation_id="rel-1",
        )

        self.assertEqual(
            result.record.disposition,
            SpatialTransitionDisposition.REPLACED,
        )
        self.assertEqual(result.record.previous_relation_id, "rel-1")
        self.assertEqual(
            tuple(item.relation_id for item in result.entity.spatial_relations),
            ("rel-2",),
        )

    def test_older_replacement_is_rejected(self):
        first = self.engine.add_or_replace(self.entity, self.relation()).entity
        older = self.relation(
            relation_id="rel-old",
            observed_at=99.0,
            receipt_id="receipt-old",
        )

        result = self.engine.add_or_replace(
            first,
            older,
            replace_relation_id="rel-1",
        )

        self.assertEqual(
            result.record.disposition,
            SpatialTransitionDisposition.REJECTED_OLDER_EVIDENCE,
        )
        self.assertIs(result.entity, first)

    def test_expiry_removes_current_relation_but_preserves_receipts(self):
        first = self.engine.add_or_replace(self.entity, self.relation()).entity
        result = self.engine.expire(first, "rel-1", "receipt-expire-1")

        self.assertEqual(
            result.record.disposition,
            SpatialTransitionDisposition.EXPIRED,
        )
        self.assertEqual(result.entity.spatial_relations, ())
        self.assertIn("receipt-space-1", result.record.receipt_ids)
        self.assertIn("receipt-expire-1", result.record.receipt_ids)
        self.assertIn("receipt-expire-1", result.entity.source_receipt_ids)

    def test_dispute_marks_relation_without_erasing_it(self):
        first = self.engine.add_or_replace(self.entity, self.relation()).entity
        result = self.engine.dispute(
            first,
            "rel-1",
            "receipt-dispute-1",
            "camera and GNSS disagree",
        )

        self.assertEqual(
            result.record.disposition,
            SpatialTransitionDisposition.DISPUTED,
        )
        relation = result.entity.spatial_relations[0]
        self.assertTrue(relation.attributes["disputed"])
        self.assertEqual(
            relation.attributes["dispute_reason"],
            "camera and GNSS disagree",
        )
        self.assertEqual(relation.receipt_id, "receipt-space-1")

    def test_relation_subject_must_match_entity(self):
        wrong = SpatialRelation(
            relation_id="rel-wrong",
            subject_entity_id="different-entity",
            relation_type=SpatialRelationType.NEAR,
            object_entity_id="garage",
            frame_id="property-frame",
            confidence=0.5,
            observed_at=101.0,
            receipt_id="receipt-wrong",
        )
        result = self.engine.add_or_replace(self.entity, wrong)

        self.assertEqual(
            result.record.disposition,
            SpatialTransitionDisposition.REJECTED_ENTITY_MISMATCH,
        )
        self.assertEqual(result.entity.spatial_relations, ())

    def test_near_and_visible_relations_do_not_imply_reachability_or_permission(self):
        near = self.engine.add_or_replace(
            self.entity,
            self.relation(
                relation_id="rel-near",
                relation_type=SpatialRelationType.NEAR,
            ),
        ).entity
        visible = self.engine.add_or_replace(
            near,
            self.relation(
                relation_id="rel-visible",
                relation_type=SpatialRelationType.VISIBLE_FROM,
                receipt_id="receipt-visible",
            ),
        ).entity

        types = {item.relation_type for item in visible.spatial_relations}
        self.assertIn(SpatialRelationType.NEAR, types)
        self.assertIn(SpatialRelationType.VISIBLE_FROM, types)
        self.assertNotIn(SpatialRelationType.REACHABLE_FROM, types)
        self.assertFalse(visible.authority_granted)

    def test_unknown_relation_cannot_be_expired_or_disputed(self):
        expired = self.engine.expire(
            self.entity,
            "missing-relation",
            "receipt-expire",
        )
        disputed = self.engine.dispute(
            self.entity,
            "missing-relation",
            "receipt-dispute",
            "not found",
        )

        self.assertEqual(
            expired.record.disposition,
            SpatialTransitionDisposition.REJECTED_UNKNOWN_RELATION,
        )
        self.assertEqual(
            disputed.record.disposition,
            SpatialTransitionDisposition.REJECTED_UNKNOWN_RELATION,
        )


if __name__ == "__main__":
    unittest.main()

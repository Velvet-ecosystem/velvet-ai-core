"""Tests for the descriptive shared world-model foundation."""

import unittest

from velvet.core.schemas import (
    EntityIdentity,
    EntityLifecycle,
    IdentityEvidence,
    IdentityStatus,
    SpatialRelation,
    SpatialRelationType,
    TemporalState,
    WorldEntity,
)


class WorldModelFoundationTests(unittest.TestCase):
    def identity(self):
        return EntityIdentity(
            entity_id="vehicle:tiburon",
            entity_type="vehicle",
            canonical_name="Tiburon",
            status=IdentityStatus.KNOWN,
            confidence=0.99,
            aliases=("2008 Hyundai Tiburon",),
            evidence=(
                IdentityEvidence(
                    evidence_id="identity-1",
                    evidence_type="body-registry",
                    source="runtime",
                    observed_at=100.0,
                    confidence=1.0,
                    receipt_id="receipt-identity-1",
                ),
            ),
        )

    def temporal(self):
        return TemporalState(
            observed_at=100.0,
            received_at=100.1,
            monotonic_time=50.0,
            valid_from=100.0,
            valid_until=None,
            stale_after_ms=1000,
            sequence=4,
        )

    def test_world_entity_keeps_identity_role_and_authority_separate(self):
        entity = WorldEntity(
            identity=self.identity(),
            temporal=self.temporal(),
            lifecycle=EntityLifecycle.ACTIVE,
            roles=("current_body", "vehicle"),
            state={"ignition": "off"},
            source_receipt_ids=("receipt-state-1",),
        )

        self.assertEqual(entity.entity_id, "vehicle:tiburon")
        self.assertEqual(entity.identity.canonical_name, "Tiburon")
        self.assertIn("current_body", entity.roles)
        self.assertFalse(entity.authority_granted)
        self.assertFalse(entity.execution_performed)

    def test_temporal_state_uses_monotonic_freshness(self):
        temporal = self.temporal()
        self.assertFalse(temporal.is_stale(51.0))
        self.assertTrue(temporal.is_stale(51.001))

    def test_spatial_relation_requires_matching_subject(self):
        relation = SpatialRelation(
            relation_id="spatial-1",
            subject_entity_id="person:mister",
            relation_type=SpatialRelationType.LOCATED_IN,
            object_entity_id="vehicle:tiburon",
            frame_id="frame:tiburon-cabin",
            confidence=0.95,
            observed_at=100.0,
            receipt_id="receipt-spatial-1",
        )

        with self.assertRaises(ValueError):
            WorldEntity(
                identity=self.identity(),
                temporal=self.temporal(),
                spatial_relations=(relation,),
            )

    def test_identity_cannot_name_itself_as_lineage_parent(self):
        with self.assertRaises(ValueError):
            EntityIdentity(
                entity_id="node:velour",
                entity_type="node",
                canonical_name="Velour",
                status=IdentityStatus.KNOWN,
                confidence=1.0,
                lineage_parent_id="node:velour",
            )

    def test_world_entity_rejects_authority_claims(self):
        with self.assertRaises(ValueError):
            WorldEntity(
                identity=self.identity(),
                temporal=self.temporal(),
                authority_granted=True,
            )

    def test_serialization_preserves_uncertainty_and_provenance(self):
        identity = EntityIdentity(
            entity_id="person:unknown-1",
            entity_type="person",
            canonical_name="Unknown Person 1",
            status=IdentityStatus.POSSIBLE,
            confidence=0.35,
        )
        entity = WorldEntity(
            identity=identity,
            temporal=TemporalState(
                observed_at=200.0,
                received_at=203.0,
                monotonic_time=80.0,
                valid_from=200.0,
                valid_until=None,
                stale_after_ms=500,
                estimated=True,
                disputed=True,
            ),
            lifecycle=EntityLifecycle.UNKNOWN,
        )

        record = entity.to_dict()
        self.assertEqual(record["identity"]["status"], "POSSIBLE")
        self.assertTrue(record["temporal"]["estimated"])
        self.assertTrue(record["temporal"]["disputed"])
        self.assertFalse(record["authority_granted"])


if __name__ == "__main__":
    unittest.main()

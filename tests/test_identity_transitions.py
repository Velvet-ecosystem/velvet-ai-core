"""Tests for evidence-backed, non-authoritative identity transitions."""

import unittest

from velvet.core.identity_transitions import (
    IdentityTransitionDisposition,
    IdentityTransitionEngine,
)
from velvet.core.schemas.world_model import (
    EntityIdentity,
    IdentityEvidence,
    IdentityStatus,
)


class IdentityTransitionTests(unittest.TestCase):
    def setUp(self):
        self.engine = IdentityTransitionEngine()
        self.identity = EntityIdentity(
            entity_id="person-mister",
            entity_type="person",
            canonical_name="Mister",
            status=IdentityStatus.UNKNOWN,
            confidence=0.0,
        )

    def evidence(self, evidence_id, source, confidence, receipt_id=None):
        return IdentityEvidence(
            evidence_id=evidence_id,
            evidence_type="corroboration",
            source=source,
            observed_at=100.0,
            confidence=confidence,
            receipt_id=receipt_id or "receipt-%s" % evidence_id,
            details={},
        )

    def test_single_strong_source_cannot_make_identity_known(self):
        result = self.engine.add_evidence(
            self.identity,
            self.evidence("face-1", "camera", 0.99),
        )
        self.assertEqual(result.identity.status, IdentityStatus.LIKELY)
        self.assertFalse(result.record.authority_granted)
        self.assertFalse(result.record.execution_performed)

    def test_distinct_strong_sources_can_promote_to_known(self):
        first = self.engine.add_evidence(
            self.identity,
            self.evidence("face-1", "camera", 0.90),
        )
        second = self.engine.add_evidence(
            first.identity,
            self.evidence("nfc-1", "nfc-reader", 0.90),
        )
        self.assertEqual(second.identity.status, IdentityStatus.KNOWN)
        self.assertEqual(len(second.identity.evidence), 2)

    def test_duplicate_evidence_is_rejected_without_mutation(self):
        first = self.engine.add_evidence(
            self.identity,
            self.evidence("same", "camera", 0.8),
        )
        duplicate = self.engine.add_evidence(
            first.identity,
            self.evidence("same", "camera", 1.0),
        )
        self.assertEqual(
            duplicate.record.disposition,
            IdentityTransitionDisposition.REJECTED_DUPLICATE_EVIDENCE,
        )
        self.assertEqual(duplicate.identity, first.identity)

    def test_alias_does_not_create_new_identity(self):
        result = self.engine.add_alias(
            self.identity,
            "Founder",
            "receipt-alias",
        )
        self.assertEqual(result.identity.entity_id, self.identity.entity_id)
        self.assertIn("Founder", result.identity.aliases)
        self.assertEqual(result.identity.status, IdentityStatus.UNKNOWN)

    def test_dispute_preserves_prior_evidence(self):
        first = self.engine.add_evidence(
            self.identity,
            self.evidence("face-1", "camera", 0.8),
        )
        dispute = self.engine.dispute(
            first.identity,
            self.evidence("conflict-1", "manual-review", 0.4),
            related_entity_id="person-other",
        )
        self.assertEqual(dispute.identity.status, IdentityStatus.DISPUTED)
        self.assertEqual(len(dispute.identity.evidence), 2)
        self.assertEqual(dispute.record.related_entity_id, "person-other")

    def test_possible_duplicate_is_flagged_not_merged(self):
        result = self.engine.flag_duplicate(
            self.identity,
            "person-copy",
            "receipt-duplicate",
        )
        self.assertEqual(result.identity.status, IdentityStatus.DISPUTED)
        self.assertEqual(result.identity.entity_id, "person-mister")
        self.assertEqual(result.record.related_entity_id, "person-copy")

    def test_successor_has_explicit_lineage_and_distinct_identity(self):
        result = self.engine.create_successor(
            self.identity,
            "velvet-body-2",
            "Velvet Successor",
            self.evidence("lineage-1", "riven", 0.95),
        )
        self.assertIsNotNone(result.successor)
        self.assertEqual(result.successor.lineage_parent_id, self.identity.entity_id)
        self.assertNotEqual(result.successor.entity_id, self.identity.entity_id)
        self.assertEqual(
            result.record.disposition,
            IdentityTransitionDisposition.SUCCESSOR_CREATED,
        )

    def test_successor_does_not_inherit_known_status_from_predecessor(self):
        known = EntityIdentity(
            entity_id="velvet-body-1",
            entity_type="system_body",
            canonical_name="Velvet",
            status=IdentityStatus.KNOWN,
            confidence=0.99,
        )
        result = self.engine.create_successor(
            known,
            "velvet-body-2",
            "Velvet Successor",
            self.evidence("lineage-1", "riven", 0.95),
        )
        self.assertEqual(result.successor.status, IdentityStatus.LIKELY)

    def test_retirement_preserves_evidence_and_history(self):
        first = self.engine.add_evidence(
            self.identity,
            self.evidence("face-1", "camera", 0.8),
        )
        retired = self.engine.retire(first.identity, "receipt-retire")
        self.assertEqual(retired.identity.status, IdentityStatus.REJECTED)
        self.assertEqual(retired.identity.evidence, first.identity.evidence)
        self.assertIn("receipt-retire", retired.record.receipt_ids)

    def test_identity_transition_record_never_grants_authority(self):
        result = self.engine.add_alias(
            self.identity,
            "Owner",
            "receipt-owner-alias",
        )
        self.assertFalse(result.record.authority_granted)
        self.assertFalse(result.record.execution_performed)


if __name__ == "__main__":
    unittest.main()

import unittest

from velvet.core.identity_transitions import (
    IdentityTransitionDisposition,
    IdentityTransitionRecord,
)
from velvet.core.recognition_evidence import (
    RecognitionDisposition,
    RecognitionFusion,
)
from velvet.core.schemas.world_model import IdentityStatus
from velvet.core.spatial_transitions import (
    SpatialTransitionDisposition,
    SpatialTransitionRecord,
)
from velvet.core.temporal_transitions import (
    TemporalTransitionRecord,
    TemporalTransitionType,
)
from velvet.core.world_event_bridge import (
    WorldEventBridge,
    WorldEventEnvelope,
    WorldEventType,
)
from velvet.core.world_state import (
    WorldUpdateDisposition,
    WorldUpdateRecord,
)


class WorldEventBridgeTests(unittest.TestCase):
    def setUp(self):
        self.bridge = WorldEventBridge(
            source="ai-core.world",
            node_id="up2-founder",
            organ_name="native-brain",
        )

    def test_world_update_uses_standard_event_protocol_shape(self):
        record = WorldUpdateRecord(
            update_id="update-1",
            entity_id="person-mister",
            disposition=WorldUpdateDisposition.ACCEPTED,
            incoming_sequence=2,
            current_sequence=1,
            incoming_monotonic_time=12.0,
            current_monotonic_time=11.0,
            source_receipt_ids=("receipt-1",),
            reason="newer compatible snapshot accepted",
        )

        event = self.bridge.from_world_update(record, timestamp=100.0)
        payload = event.to_event_protocol()

        self.assertEqual(payload["event_id"], "update-1")
        self.assertEqual(payload["event_type"], "WORLD_ENTITY_UPDATED")
        self.assertEqual(payload["family"], "world")
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["node_id"], "up2-founder")
        self.assertEqual(payload["organ_name"], "native-brain")
        self.assertEqual(payload["entity_id"], "person-mister")
        self.assertEqual(payload["receipt_ids"], ["receipt-1"])
        self.assertFalse(payload["authority_granted"])
        self.assertFalse(payload["execution_performed"])

    def test_rejected_world_update_remains_observable(self):
        record = WorldUpdateRecord(
            update_id="update-2",
            entity_id="vehicle-tibby",
            disposition=WorldUpdateDisposition.REJECTED_OLDER_TIME,
            incoming_sequence=None,
            current_sequence=None,
            incoming_monotonic_time=4.0,
            current_monotonic_time=5.0,
            source_receipt_ids=("receipt-old",),
            reason="incoming monotonic time precedes current state",
        )

        event = self.bridge.from_world_update(record, timestamp=101.0)

        self.assertEqual(
            event.event_type,
            WorldEventType.WORLD_ENTITY_UPDATE_REJECTED,
        )
        self.assertEqual(
            event.payload["disposition"],
            "REJECTED_OLDER_TIME",
        )

    def test_spatial_transition_does_not_publish_permission(self):
        record = SpatialTransitionRecord(
            transition_id="spatial-1",
            entity_id="person-mister",
            relation_id="relation-seat",
            disposition=SpatialTransitionDisposition.ADDED,
            previous_relation_id=None,
            receipt_ids=("receipt-space",),
            reason="relationship added",
        )

        event = self.bridge.from_spatial_transition(record, timestamp=102.0)
        payload = event.to_event_protocol()

        self.assertEqual(payload["event_type"], "SPATIAL_RELATION_CHANGED")
        self.assertNotIn("permission", payload["payload"])
        self.assertNotIn("authorized", payload["payload"])
        self.assertFalse(payload["authority_granted"])

    def test_temporal_rejection_maps_to_rejected_event(self):
        record = TemporalTransitionRecord(
            transition_id="temporal-1",
            entity_id="person-mister",
            transition_type=TemporalTransitionType.REJECTED_OLDER_SEQUENCE,
            previous_sequence=4,
            incoming_sequence=3,
            previous_monotonic_time=20.0,
            incoming_monotonic_time=19.0,
            source_receipt_ids=("receipt-time",),
            reason="incoming temporal state is not newer",
        )

        event = self.bridge.from_temporal_transition(record, timestamp=103.0)

        self.assertEqual(
            event.event_type,
            WorldEventType.TEMPORAL_STATE_REJECTED,
        )

    def test_identity_event_separates_status_from_authority(self):
        record = IdentityTransitionRecord(
            transition_id="identity-1",
            entity_id="person-mister",
            disposition=IdentityTransitionDisposition.EVIDENCE_ACCEPTED,
            previous_status=IdentityStatus.LIKELY,
            new_status=IdentityStatus.KNOWN,
            evidence_ids=("face-1", "voice-1"),
            receipt_ids=("receipt-face", "receipt-voice"),
            reason="identity evidence accepted and status recalculated",
        )

        event = self.bridge.from_identity_transition(record, timestamp=104.0)
        payload = event.to_event_protocol()

        self.assertEqual(payload["payload"]["new_status"], "KNOWN")
        self.assertFalse(payload["authority_granted"])
        self.assertNotIn("role", payload["payload"])
        self.assertNotIn("ownership", payload["payload"])

    def test_disputed_recognition_gets_explicit_event_type(self):
        fusion = RecognitionFusion(
            fusion_id="fusion-1",
            candidate_entity_id="person-mister",
            disposition=RecognitionDisposition.DISPUTED,
            confidence=0.72,
            modality_count=2,
            source_count=2,
            observation_ids=("face-1", "voice-1"),
            receipt_ids=("receipt-face", "receipt-voice"),
            conflicting_candidate_ids=("person-unknown",),
            rationale="supporting observations disagree on location",
            identity_evidence=(),
        )

        event = self.bridge.from_recognition_fusion(fusion, timestamp=105.0)

        self.assertEqual(
            event.event_type,
            WorldEventType.RECOGNITION_EVIDENCE_DISPUTED,
        )
        self.assertEqual(
            event.payload["conflicting_candidate_ids"],
            ["person-unknown"],
        )

    def test_event_envelope_rejects_authority_claim(self):
        with self.assertRaises(ValueError):
            WorldEventEnvelope(
                event_id="bad-event",
                event_type=WorldEventType.WORLD_ENTITY_UPDATED,
                source="ai-core.world",
                timestamp=1.0,
                node_id="node",
                organ_name="brain",
                entity_id="entity",
                payload={},
                authority_granted=True,
            )

    def test_receipts_are_deduplicated_without_reordering(self):
        event = WorldEventEnvelope(
            event_id="event-1",
            event_type=WorldEventType.WORLD_ENTITY_UPDATED,
            source="ai-core.world",
            timestamp=1.0,
            node_id="node",
            organ_name="brain",
            entity_id="entity",
            payload={},
            receipt_ids=("r1", "r2", "r1"),
        )

        self.assertEqual(event.receipt_ids, ("r1", "r2"))


if __name__ == "__main__":
    unittest.main()

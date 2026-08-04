import unittest

from ai_brain.native_brain.world_context import (
    ContextFactDisposition,
    NativeBrainWorldContextProjector,
    WorldContextPolicy,
)
from velvet.core.world_event_bridge import WorldEventEnvelope, WorldEventType


class NativeBrainWorldContextTests(unittest.TestCase):
    def event(
        self,
        event_id="event-1",
        event_type=WorldEventType.WORLD_ENTITY_UPDATED,
        timestamp=10.0,
        entity_id="person:mister",
        payload=None,
        authority_granted=False,
        execution_performed=False,
    ):
        return WorldEventEnvelope(
            event_id=event_id,
            event_type=event_type,
            source="velvet-ai-core.world-model",
            timestamp=timestamp,
            node_id="founder",
            organ_name="native-brain",
            entity_id=entity_id,
            receipt_ids=("receipt-1",),
            payload=payload or {"disposition": "ACCEPTED"},
            authority_granted=authority_granted,
            execution_performed=execution_performed,
        )

    def test_ingests_current_descriptive_fact(self):
        projector = NativeBrainWorldContextProjector()
        fact = projector.ingest(self.event(), now=12.0)

        self.assertIsNotNone(fact)
        self.assertEqual(fact.disposition, ContextFactDisposition.CURRENT)
        self.assertFalse(fact.authority_granted)
        self.assertFalse(fact.execution_performed)

    def test_duplicate_event_is_ignored(self):
        projector = NativeBrainWorldContextProjector()
        event = self.event()

        self.assertIsNotNone(projector.ingest(event))
        self.assertIsNone(projector.ingest(event))
        self.assertEqual(len(projector.snapshot(12.0).facts_for("person:mister")), 1)

    def test_recognition_dispute_remains_disputed_as_it_ages(self):
        projector = NativeBrainWorldContextProjector()
        event = self.event(
            event_type=WorldEventType.RECOGNITION_EVIDENCE_DISPUTED,
            payload={
                "disposition": "DISPUTED",
                "confidence": 0.81,
                "rationale": "voice and image disagree",
            },
        )
        projector.ingest(event, now=10.0)

        fact = projector.snapshot(1000.0).latest("person:mister")
        self.assertEqual(fact.disposition, ContextFactDisposition.DISPUTED)
        self.assertEqual(fact.confidence, 0.81)

    def test_rejected_transition_is_context_not_truth(self):
        projector = NativeBrainWorldContextProjector()
        event = self.event(
            event_type=WorldEventType.IDENTITY_STATE_REJECTED,
            payload={
                "disposition": "REJECTED_INVALID_PROMOTION",
                "reason": "insufficient independent evidence",
            },
        )
        projector.ingest(event)

        fact = projector.snapshot(11.0).latest("person:mister")
        self.assertEqual(fact.disposition, ContextFactDisposition.REJECTED)
        self.assertIn("REJECTED_INVALID_PROMOTION", fact.summary)

    def test_freshness_transitions_current_aging_stale(self):
        projector = NativeBrainWorldContextProjector(
            WorldContextPolicy(current_for_seconds=5.0, stale_after_seconds=20.0)
        )
        projector.ingest(self.event(timestamp=10.0), now=10.0)

        self.assertEqual(
            projector.snapshot(14.0).latest("person:mister").disposition,
            ContextFactDisposition.CURRENT,
        )
        self.assertEqual(
            projector.snapshot(20.0).latest("person:mister").disposition,
            ContextFactDisposition.AGING,
        )
        self.assertEqual(
            projector.snapshot(31.0).latest("person:mister").disposition,
            ContextFactDisposition.STALE,
        )

    def test_future_timestamp_is_treated_as_current_not_negative_age(self):
        projector = NativeBrainWorldContextProjector()
        projector.ingest(self.event(timestamp=20.0), now=10.0)

        fact = projector.snapshot(10.0).latest("person:mister")
        self.assertEqual(fact.disposition, ContextFactDisposition.CURRENT)

    def test_context_is_bounded_per_entity(self):
        projector = NativeBrainWorldContextProjector(
            WorldContextPolicy(max_facts_per_entity=2)
        )
        for index in range(3):
            projector.ingest(
                self.event(event_id="event-%d" % index, timestamp=float(index))
            )

        facts = projector.snapshot(3.0).facts_for("person:mister")
        self.assertEqual([fact.event_id for fact in facts], ["event-1", "event-2"])

    def test_entities_keep_separate_context_buckets(self):
        projector = NativeBrainWorldContextProjector()
        projector.ingest(self.event(entity_id="person:mister"))
        projector.ingest(
            self.event(event_id="event-2", entity_id="vehicle:tibby")
        )

        context = projector.snapshot(12.0)
        self.assertEqual(len(context.facts_for("person:mister")), 1)
        self.assertEqual(len(context.facts_for("vehicle:tibby")), 1)

    def test_context_and_facts_cannot_claim_authority(self):
        projector = NativeBrainWorldContextProjector()
        projector.ingest(self.event())
        context = projector.snapshot(12.0)

        self.assertFalse(context.authority_granted)
        self.assertFalse(context.execution_performed)
        self.assertFalse(context.latest("person:mister").authority_granted)

    def test_event_envelope_rejects_authority_before_context_intake(self):
        with self.assertRaises(ValueError):
            self.event(authority_granted=True)

    def test_confidence_must_remain_bounded(self):
        projector = NativeBrainWorldContextProjector()
        with self.assertRaises(ValueError):
            projector.ingest(
                self.event(
                    event_type=WorldEventType.RECOGNITION_EVIDENCE_FUSED,
                    payload={"disposition": "LIKELY", "confidence": 1.2},
                )
            )


if __name__ == "__main__":
    unittest.main()

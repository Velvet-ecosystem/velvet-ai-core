import unittest
from types import MappingProxyType

from velvet.core.cognition.episode_consolidation import (
    EPISODE_PROPOSED,
    ClosedEventContext,
    EpisodeConsolidator,
    RetentionClass,
    RetentionPolicy,
)


FLAGS = {
    "interpretation_only": True,
    "transport_only": True,
    "canonical_evidence": False,
    "authority": "none",
    "grants_authority": False,
    "grants_execution": False,
    "grants_actuation": False,
    "replay_safe": True,
}


class Ids:
    def __init__(self):
        self.value = 0

    def __call__(self, prefix):
        self.value += 1
        return "%s-%02d" % (prefix, self.value)


def event_document(event_type, event_id, **overrides):
    payload = {
        "schema_version": "1.0",
        "cognitive_event_id": "cog-entry",
        "node_id": "up2-founder",
        "body_id": "tiburon",
        "source_refs": ["obs-presence", "obs-auth"],
        "correlation_ids": ["entry-1"],
        "monotonic_time": 100.0 if event_type.endswith("opened") else 101.0,
        "replay_state": "fixture",
        "health_state": "healthy",
        "degraded_reasons": [],
        **FLAGS,
        "mode": "OBSERVE",
        "lifecycle_state": "OPEN" if event_type.endswith("opened") else "COMPLETED",
        "event_kind": "vehicle_entry",
        "confidence": 0.98,
        "freshness_state": "fresh",
        "observation_refs": ["obs-presence", "obs-auth"],
        "proposal_refs": ["proposal-unlock"],
        "authorization_refs": ["court-decision-1"],
        "execution_refs": ["execution-contract-1"],
        "receipt_refs": ["receipt-unlock"],
        "prediction_refs": ["prediction-unlock"],
        "interruption_refs": [],
        "contradiction_refs": [],
        "boundary_ids": ["boundary-complete"],
    }
    if event_type.endswith("closed"):
        payload.update(
            completion_reason="lock-state-confirmed",
            closing_boundary_id="boundary-complete",
        )
    payload.update(overrides)
    return {
        "event_id": event_id,
        "timestamp": 1000.0,
        "source": "velvet-ai-core.workspace",
        "event_type": event_type,
        "intent": None,
        "payload": payload,
        "metadata": {
            "contract": "velvet.cognitive-events.v1",
            "schema_version": "1.0",
            "family": "cognitive-event",
            "authority": "none",
            "interpretation_only": True,
        },
        "parent_event_id": None,
        "receipt_id": None,
    }


def opened(**overrides):
    return event_document("cognitive.event.opened", "opened-1", **overrides)


def closed(**overrides):
    return event_document("cognitive.event.closed", "closed-1", **overrides)


def prediction_view(**overrides):
    values = {
        "prediction_id": "prediction-unlock",
        "prediction_error_id": None,
        "cognitive_event_id": "cog-entry",
        "body_id": "tiburon",
        "node_id": "up2-founder",
        "status": "confirmed",
        "source_refs": ("obs-auth", "obs-lock"),
        "receipt_refs": ("receipt-unlock",),
        "replay_state": "fixture",
        "authority_granted": False,
        "automatic_retry_requested": False,
    }
    values.update(overrides)
    return values


def action_view(**overrides):
    values = {
        "tracking_id": "tracking-unlock",
        "cognitive_event_id": "cog-entry",
        "body_id": "tiburon",
        "node_id": "up2-founder",
        "state": "completed",
        "authorization_ref": "court-decision-1",
        "execution_ref": "execution-contract-1",
        "source_refs": ("execution-contract-1", "obs-lock"),
        "receipt_refs": ("receipt-unlock",),
        "outstanding_effect_refs": (),
        "replay_state": "fixture",
        "authority_granted": False,
        "execution_performed": False,
        "automatic_retry_requested": False,
    }
    values.update(overrides)
    return values


def interrupt_view(**overrides):
    values = {
        "interrupt_id": "interrupt-impact",
        "cognitive_event_id": "cog-entry",
        "body_id": "tiburon",
        "node_id": "up2-founder",
        "accepted": True,
        "source_refs": ("obs-impact",),
        "outstanding_effect_refs": ("door-motor-state-unknown",),
        "replay_state": "fixture",
        "authority_granted": False,
        "safeing_authorized": False,
        "safeing_performed": False,
    }
    values.update(overrides)
    return values


class ClosedEventContextTests(unittest.TestCase):
    def test_opened_and_closed_documents_form_context(self):
        context = ClosedEventContext.from_event_documents(opened(), closed())
        self.assertEqual(context.cognitive_event_id, "cog-entry")
        self.assertEqual(context.started_at, 100.0)
        self.assertEqual(context.ended_at, 101.0)
        self.assertFalse(context.identity_proof)
        self.assertIn("closed-1", context.source_refs)

    def test_nonterminal_closed_event_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "terminal"):
            ClosedEventContext.from_event_documents(
                opened(), closed(lifecycle_state="DEVELOPING")
            )

    def test_mismatched_documents_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "body_id"):
            ClosedEventContext.from_event_documents(opened(), closed(body_id="house"))
        with self.assertRaisesRegex(ValueError, "end before"):
            ClosedEventContext.from_event_documents(
                opened(monotonic_time=102.0), closed(monotonic_time=101.0)
            )

    def test_authority_smuggling_in_source_event_is_rejected(self):
        bad = closed()
        bad["payload"]["nested"] = {"capability_token": "bad"}
        with self.assertRaisesRegex(ValueError, "forbidden authority"):
            ClosedEventContext.from_event_documents(opened(), bad)


class EpisodeConsolidatorTests(unittest.TestCase):
    def setUp(self):
        self.ids = Ids()
        self.consolidator = EpisodeConsolidator(
            body_id="tiburon",
            node_id="up2-founder",
            id_factory=self.ids,
            replay_state="fixture",
        )

    def consolidate(self, **overrides):
        values = {
            "opened_event": opened(),
            "closed_event": closed(),
            "summary": "Mister entered the vehicle and the driver door unlocked.",
            "confidence": 0.98,
            "actors": ("Mister",),
            "locations": ("tiburon.driver-door",),
            "what_changed": ("driver door lock changed to unlocked",),
            "prediction_views": (prediction_view(),),
            "action_views": (action_view(),),
            "receipt_refs": ("receipt-unlock",),
        }
        values.update(overrides)
        return self.consolidator.consolidate(**values)

    def test_episode_links_evidence_without_replacing_it(self):
        episode = self.consolidate()
        payload = episode.emission.payload
        self.assertEqual(payload["memory_navigation_only"], True)
        self.assertEqual(payload["canonical_memory"], False)
        self.assertEqual(payload["identity_proof"], False)
        self.assertIn("obs-presence", payload["source_refs"])
        self.assertIn("receipt-unlock", payload["receipt_refs"])
        self.assertIn("prediction-unlock", payload["prediction_refs"])
        self.assertIn("tracking-unlock", payload["action_tracking_refs"])

    def test_episode_event_document_uses_cognitive_protocol(self):
        episode = self.consolidate()
        document = episode.emission.to_event_document(
            source="velvet-ai-core.episodes", timestamp=2000.0
        )
        self.assertEqual(document["event_type"], EPISODE_PROPOSED)
        self.assertEqual(
            document["metadata"]["contract"], "velvet.cognitive-events.v1"
        )
        self.assertEqual(document["parent_event_id"], "closed-1")
        self.assertIsNone(document["receipt_id"])

    def test_pending_prediction_cannot_enter_closed_episode(self):
        with self.assertRaisesRegex(ValueError, "pending prediction"):
            self.consolidate(prediction_views=(prediction_view(status="pending"),))

    def test_active_action_cannot_enter_closed_episode(self):
        with self.assertRaisesRegex(ValueError, "active action"):
            self.consolidate(action_views=(action_view(state="started"),))

    def test_unaccepted_interrupt_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "accepted interrupts"):
            self.consolidate(interrupt_views=(interrupt_view(accepted=False),))

    def test_interrupted_episode_preserves_outstanding_effects(self):
        episode = self.consolidate(
            closed_event=closed(
                lifecycle_state="INTERRUPTED",
                completion_reason="impact-interrupt",
                interruption_refs=["interrupt-impact"],
            ),
            interrupt_views=(interrupt_view(),),
        )
        self.assertIn("interrupt-impact", episode.interruption_refs)
        self.assertIn("door-motor-state-unknown", episode.outstanding_effect_refs)
        self.assertEqual(
            episode.emission.payload["completion_state"], "INTERRUPTED"
        )

    def test_significant_retention_requires_policy_and_receipts(self):
        with self.assertRaisesRegex(ValueError, "policy_ref"):
            self.consolidate(
                retention=RetentionPolicy(RetentionClass.SIGNIFICANT),
                receipt_refs=(),
                prediction_views=(),
                action_views=(),
                closed_event=closed(receipt_refs=[]),
            )
        with self.assertRaisesRegex(ValueError, "requires receipts"):
            self.consolidate(
                retention=RetentionPolicy(
                    RetentionClass.SIGNIFICANT,
                    policy_ref="memory.significant.v1",
                ),
                receipt_refs=(),
                prediction_views=(),
                action_views=(),
                closed_event=closed(receipt_refs=[]),
            )

    def test_protected_retention_requires_reason(self):
        with self.assertRaisesRegex(ValueError, "protected_reason"):
            self.consolidate(
                retention=RetentionPolicy(
                    RetentionClass.PROTECTED,
                    policy_ref="memory.protected.v1",
                )
            )
        episode = self.consolidate(
            retention=RetentionPolicy(
                RetentionClass.PROTECTED,
                policy_ref="memory.protected.v1",
                continuity_anchor_ref="riven-anchor-1",
                protected_reason="medical emergency evidence",
            )
        )
        self.assertEqual(episode.retention_class, RetentionClass.PROTECTED)
        self.assertEqual(
            episode.emission.payload["continuity_anchor_ref"],
            "riven-anchor-1",
        )

    def test_transient_episode_cannot_claim_continuity_anchor(self):
        with self.assertRaisesRegex(ValueError, "continuity anchor"):
            self.consolidate(
                retention=RetentionPolicy(
                    RetentionClass.TRANSIENT,
                    continuity_anchor_ref="riven-anchor-1",
                )
            )

    def test_related_views_must_match_event_body_and_replay(self):
        with self.assertRaisesRegex(ValueError, "another body"):
            self.consolidate(
                prediction_views=(prediction_view(body_id="house"),)
            )
        with self.assertRaisesRegex(ValueError, "replay_state"):
            self.consolidate(action_views=(action_view(replay_state="live"),))

    def test_related_view_authority_smuggling_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "forbidden authority"):
            self.consolidate(
                prediction_views=(prediction_view(nested={"executor": "bad"}),)
            )

    def test_read_only_episode_view_is_immutable(self):
        episode = self.consolidate()
        view = episode.read_only_view()
        self.assertIsInstance(view, MappingProxyType)
        with self.assertRaises(TypeError):
            view["identity_proof"] = True
        self.assertFalse(episode.identity_proof)

    def test_duplicate_episode_id_and_capacity_fail_closed(self):
        self.consolidate(episode_id="episode-fixed")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.consolidate(episode_id="episode-fixed")
        limited = EpisodeConsolidator(
            body_id="tiburon",
            node_id="up2-founder",
            max_episodes=1,
            replay_state="fixture",
        )
        limited.consolidate(
            opened_event=opened(),
            closed_event=closed(),
            summary="one",
            confidence=1.0,
        )
        with self.assertRaisesRegex(RuntimeError, "capacity"):
            limited.consolidate(
                opened_event=opened(),
                closed_event=closed(),
                summary="two",
                confidence=1.0,
            )


if __name__ == "__main__":
    unittest.main()

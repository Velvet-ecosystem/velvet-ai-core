# SPDX-License-Identifier: GPL-3.0-only

import unittest
from types import MappingProxyType

from velvet.core.cognition import (
    BOUNDARY_PROPOSED,
    EVENT_CLOSED,
    EVENT_OPENED,
    EVENT_UPDATED,
    AssociationDisposition,
    BoundaryType,
    CognitiveMode,
    CurrentEventWorkspace,
    LifecycleState,
    ObservationRole,
    WorkspaceObservation,
)


class IdFactory:
    def __init__(self):
        self.count = 0

    def __call__(self, prefix):
        self.count += 1
        return "%s-%03d" % (prefix, self.count)


class CognitiveEventWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.ids = IdFactory()
        self.workspace = CurrentEventWorkspace(
            body_id="tiburon-01",
            node_id="queen-01",
            max_observations=3,
            id_factory=self.ids,
            replay_state="fixture",
        )

    def observation(self, event_id="obs-001", **overrides):
        values = {
            "event_id": event_id,
            "event_type": "presence.observed",
            "source": "presence-fusion",
            "body_id": "tiburon-01",
            "observed_at": 100.0,
            "monotonic_time": 50.0,
            "confidence": 0.8,
            "payload": {"zone": "driver-door"},
            "correlation_ids": ("trace-entry-001",),
            "source_refs": ("sensor-packet-001",),
            "receipt_id": "receipt-" + event_id,
            "stale_after_ms": 5000,
        }
        values.update(overrides)
        return WorkspaceObservation(**values)

    def open(self):
        return self.workspace.open(
            event_kind="vehicle_entry",
            observation=self.observation(),
            now=101.0,
            cognitive_event_id="cog-entry-001",
        )

    def test_open_emits_protocol_compatible_non_authoritative_snapshot(self):
        emission = self.open()
        self.assertEqual(emission.event_type, EVENT_OPENED)
        payload = emission.payload
        self.assertTrue(payload["interpretation_only"])
        self.assertFalse(payload["canonical_evidence"])
        self.assertFalse(payload["grants_authority"])
        self.assertFalse(payload["grants_execution"])
        self.assertFalse(payload["grants_actuation"])
        self.assertEqual(payload["replay_state"], "fixture")
        self.assertEqual(payload["mode"], "OBSERVE")
        self.assertEqual(payload["lifecycle_state"], "OPEN")

    def test_read_only_view_rejects_mutation(self):
        self.open()
        view = self.workspace.read_only_view()
        self.assertIsInstance(view, MappingProxyType)
        with self.assertRaises(TypeError):
            view["mode"] = "TRACK_ACTION"

    def test_read_only_view_is_deeply_immutable(self):
        self.open()
        view = self.workspace.read_only_view()
        with self.assertRaises(AttributeError):
            view["observation_refs"].append("obs-bad")

    def test_observation_rejects_direct_authority_claims(self):
        with self.assertRaisesRegex(ValueError, "forbidden authority fields"):
            self.observation(payload={"authority_granted": True})

    def test_related_observation_is_deterministically_associated(self):
        self.open()
        result = self.workspace.observe(
            self.observation("obs-002", confidence=0.9, monotonic_time=51.0),
            now=101.1,
        )
        self.assertEqual(result.disposition, AssociationDisposition.ACCEPTED)
        self.assertEqual(result.emission.event_type, EVENT_UPDATED)
        self.assertEqual(result.snapshot.observation_refs, ("obs-001", "obs-002"))
        self.assertEqual(result.snapshot.lifecycle_state, LifecycleState.DEVELOPING)

    def test_unrelated_observation_is_not_sucked_into_event(self):
        self.open()
        result = self.workspace.observe(
            self.observation("obs-other", correlation_ids=("trace-other",)),
            now=101.0,
        )
        self.assertEqual(result.disposition, AssociationDisposition.UNRELATED)
        self.assertNotIn("obs-other", result.snapshot.observation_refs)

    def test_explicit_event_link_can_associate_without_correlation(self):
        self.open()
        result = self.workspace.observe(
            self.observation(
                "obs-linked",
                correlation_ids=(),
                related_cognitive_event_id="cog-entry-001",
            ),
            now=101.0,
        )
        self.assertEqual(result.disposition, AssociationDisposition.ACCEPTED)

    def test_stale_observation_is_rejected_without_mutation(self):
        self.open()
        before = self.workspace.snapshot()
        result = self.workspace.observe(
            self.observation("obs-stale", observed_at=90.0, stale_after_ms=1000),
            now=101.0,
        )
        self.assertEqual(result.disposition, AssociationDisposition.STALE)
        self.assertEqual(result.snapshot, before)

    def test_wrong_body_is_rejected(self):
        self.open()
        result = self.workspace.observe(
            self.observation("obs-house", body_id="house-01"),
            now=101.0,
        )
        self.assertEqual(result.disposition, AssociationDisposition.WRONG_BODY)

    def test_duplicate_observation_is_idempotent(self):
        self.open()
        result = self.workspace.observe(self.observation(), now=101.0)
        self.assertEqual(result.disposition, AssociationDisposition.DUPLICATE)
        self.assertEqual(result.snapshot.observation_refs, ("obs-001",))

    def test_nested_authority_fields_are_rejected_at_input(self):
        with self.assertRaisesRegex(ValueError, "forbidden authority fields"):
            self.observation(payload={"nested": {"executor_name": "lock-writer"}})

    def test_contradiction_is_preserved_and_reduces_confidence(self):
        self.open()
        result = self.workspace.observe(
            self.observation("obs-contradiction", confidence=0.8),
            now=101.0,
            role=ObservationRole.CONTRADICTING,
        )
        self.assertIn("obs-contradiction", result.snapshot.contradiction_refs)
        self.assertLess(result.snapshot.confidence, 0.8)

    def test_interrupt_is_recorded_but_does_not_authorize_safeing(self):
        self.open()
        result = self.workspace.observe(
            self.observation("obs-impact", confidence=0.99),
            now=101.0,
            role=ObservationRole.INTERRUPTING,
        )
        self.assertIn("obs-impact", result.snapshot.interruption_refs)
        self.assertFalse(result.emission.authority_granted)
        self.assertNotIn("safeing_authorized", result.emission.payload)

    def test_mode_transition_separates_proposal_and_tracking(self):
        self.open()
        proposed = self.workspace.set_mode(
            CognitiveMode.PROPOSE_ACTION,
            proposal_ref="intent-unlock-001",
            monotonic_time=51.0,
        )
        self.assertEqual(proposed.payload["mode"], "PROPOSE_ACTION")
        self.assertEqual(proposed.payload["proposal_refs"], ("intent-unlock-001",))
        with self.assertRaisesRegex(ValueError, "authorization_ref"):
            self.workspace.set_mode(CognitiveMode.TRACK_ACTION, execution_ref="exec-001")
        tracked = self.workspace.set_mode(
            CognitiveMode.TRACK_ACTION,
            authorization_ref="court-decision-001",
            execution_ref="execution-contract-001",
            monotonic_time=52.0,
        )
        self.assertEqual(tracked.payload["mode"], "TRACK_ACTION")
        self.assertFalse(tracked.payload["grants_execution"])

    def test_boundary_requires_known_evidence(self):
        self.open()
        with self.assertRaisesRegex(ValueError, "already belong"):
            self.workspace.propose_boundary(
                boundary_type=BoundaryType.COMPLETION,
                recommended_terminal_state=LifecycleState.COMPLETED,
                evidence_refs=("made-up-evidence",),
                confidence=0.9,
                monotonic_time=52.0,
            )

    def test_close_requires_recorded_boundary(self):
        self.open()
        with self.assertRaisesRegex(ValueError, "unknown boundary_id"):
            self.workspace.close(
                boundary_id="boundary-fake",
                completion_reason="not enough",
                monotonic_time=53.0,
            )

    def test_boundary_then_close_preserves_chain(self):
        opened = self.open()
        boundary = self.workspace.propose_boundary(
            boundary_type=BoundaryType.COMPLETION,
            recommended_terminal_state=LifecycleState.COMPLETED,
            evidence_refs=("obs-001",),
            confidence=0.95,
            monotonic_time=52.0,
        )
        self.assertEqual(boundary.emission.event_type, BOUNDARY_PROPOSED)
        closed = self.workspace.close(
            boundary_id=boundary.boundary_id,
            completion_reason="entry observation handled",
            monotonic_time=53.0,
        )
        self.assertEqual(closed.event_type, EVENT_CLOSED)
        self.assertEqual(closed.payload["lifecycle_state"], "COMPLETED")
        self.assertEqual(closed.parent_emission_id, boundary.emission.emission_id)
        document = closed.to_event_document(source="velvet-ai-core", timestamp=1000.0)
        self.assertEqual(document["metadata"]["authority"], "none")
        self.assertEqual(document["parent_event_id"], boundary.emission.emission_id)
        self.assertIsInstance(document["payload"]["source_refs"], list)
        self.assertNotEqual(opened.emission_id, closed.emission_id)

    def test_closed_event_rejects_new_observations_and_mode_changes(self):
        self.open()
        boundary = self.workspace.propose_boundary(
            boundary_type=BoundaryType.COMPLETION,
            recommended_terminal_state=LifecycleState.COMPLETED,
            evidence_refs=("obs-001",),
            confidence=0.95,
            monotonic_time=52.0,
        )
        self.workspace.close(
            boundary_id=boundary.boundary_id,
            completion_reason="done",
            monotonic_time=53.0,
        )
        result = self.workspace.observe(self.observation("obs-late"), now=101.0)
        self.assertEqual(result.disposition, AssociationDisposition.CLOSED)
        with self.assertRaisesRegex(RuntimeError, "closed"):
            self.workspace.set_mode(CognitiveMode.OBSERVE)

    def test_capacity_limit_reports_degradation_without_eviction(self):
        self.open()
        self.workspace.observe(self.observation("obs-002"), now=101.0)
        self.workspace.observe(self.observation("obs-003"), now=101.0)
        result = self.workspace.observe(self.observation("obs-004"), now=101.0)
        self.assertEqual(result.disposition, AssociationDisposition.CAPACITY_REACHED)
        self.assertEqual(result.snapshot.observation_refs, ("obs-001", "obs-002", "obs-003"))
        self.assertIn("observation-capacity-reached", result.snapshot.degraded_reasons)
        self.assertIsNotNone(result.emission)
        self.assertEqual(result.emission.payload["health_state"], "degraded")

    def test_reset_only_after_close(self):
        self.open()
        with self.assertRaisesRegex(RuntimeError, "open"):
            self.workspace.reset_closed()
        boundary = self.workspace.propose_boundary(
            boundary_type=BoundaryType.COMPLETION,
            recommended_terminal_state=LifecycleState.COMPLETED,
            evidence_refs=("obs-001",),
            confidence=0.9,
            monotonic_time=52.0,
        )
        self.workspace.close(
            boundary_id=boundary.boundary_id,
            completion_reason="done",
            monotonic_time=53.0,
        )
        self.workspace.reset_closed()
        self.assertFalse(self.workspace.is_open)
        with self.assertRaisesRegex(RuntimeError, "no current event"):
            self.workspace.snapshot()


if __name__ == "__main__":
    unittest.main()

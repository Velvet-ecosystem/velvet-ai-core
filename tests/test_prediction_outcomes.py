import unittest

from velvet.core.cognition.prediction_outcomes import (
    ACTION_TRACKING_FINISHED,
    ACTION_TRACKING_STARTED,
    PREDICTION_CREATED,
    PREDICTION_ERROR,
    PREDICTION_RESOLVED,
    ActionOutcomeTracker,
    ActionTrackingState,
    PredictionErrorClass,
    PredictionStatus,
    PredictionTracker,
)
from velvet.core.cognition.workspace_context import CognitiveWorkspaceContext


class Ids:
    def __init__(self):
        self.value = 0

    def __call__(self, prefix):
        self.value += 1
        return "%s-%02d" % (prefix, self.value)


def workspace_view(**overrides):
    values = {
        "schema_version": "1.0",
        "cognitive_event_id": "cog-entry",
        "node_id": "up2-founder",
        "body_id": "tiburon",
        "source_refs": ("obs-presence", "obs-auth"),
        "correlation_ids": ("entry-1",),
        "monotonic_time": 100.0,
        "replay_state": "fixture",
        "health_state": "healthy",
        "degraded_reasons": (),
        "interpretation_only": True,
        "transport_only": True,
        "canonical_evidence": False,
        "authority": "none",
        "grants_authority": False,
        "grants_execution": False,
        "grants_actuation": False,
        "replay_safe": True,
        "mode": "TRACK_ACTION",
        "lifecycle_state": "ACTION_TRACKING",
        "event_kind": "vehicle_entry",
        "confidence": 0.98,
        "freshness_state": "fresh",
        "observation_refs": ("obs-presence", "obs-auth"),
        "proposal_refs": ("proposal-unlock",),
        "authorization_refs": ("court-decision-1",),
        "execution_refs": ("execution-contract-1",),
        "receipt_refs": (),
        "prediction_refs": (),
        "interruption_refs": (),
        "nested_event_ids": (),
    }
    values.update(overrides)
    return values


class PredictionTests(unittest.TestCase):
    def setUp(self):
        self.ids = Ids()
        self.tracker = PredictionTracker(
            body_id="tiburon",
            node_id="up2-founder",
            id_factory=self.ids,
            replay_state="fixture",
        )

    def create(self, **overrides):
        values = {
            "cognitive_event_id": "cog-entry",
            "subject": "driver_door_lock",
            "expected_state": {"locked": False},
            "expected_by": 101.0,
            "confidence": 0.9,
            "source_model": "door-state-model",
            "source_version": "1.0",
            "source_refs": ("obs-request",),
            "observation_refs": ("obs-request",),
            "correlation_ids": ("entry-1",),
            "monotonic_time": 100.0,
        }
        values.update(overrides)
        return self.tracker.create(**values)

    def test_create_is_pending_transport_only(self):
        record, emission = self.create()
        self.assertEqual(record.status, PredictionStatus.PENDING)
        self.assertEqual(emission.event_type, PREDICTION_CREATED)
        self.assertEqual(emission.payload["authority"], "none")
        self.assertFalse(emission.payload["grants_execution"])
        self.assertEqual(emission.payload["replay_state"], "fixture")

    def test_deadline_cannot_precede_creation(self):
        with self.assertRaisesRegex(ValueError, "expected_by"):
            self.create(expected_by=99.0)

    def test_expected_state_rejects_nested_authority(self):
        with self.assertRaisesRegex(ValueError, "forbidden authority"):
            self.create(expected_state={"locked": False, "x": {"executor": "lock"}})

    def test_numeric_tolerance_confirms(self):
        record, _ = self.create(
            expected_state={"voltage": 12.0},
            tolerance={"voltage": 0.25},
        )
        outcome = self.tracker.resolve(
            record.prediction_id,
            observed_state={"voltage": 12.2},
            observation_refs=("obs-voltage",),
            confidence=0.95,
            monotonic_time=100.5,
        )
        self.assertEqual(outcome.record.status, PredictionStatus.CONFIRMED)
        self.assertIsNone(outcome.error)
        self.assertEqual(outcome.resolution.event_type, PREDICTION_RESOLVED)

    def test_mismatch_emits_error_without_retry(self):
        record, _ = self.create()
        outcome = self.tracker.resolve(
            record.prediction_id,
            observed_state={"locked": True},
            observation_refs=("obs-lock",),
            confidence=0.99,
            monotonic_time=100.7,
        )
        self.assertEqual(outcome.record.status, PredictionStatus.CONTRADICTED)
        self.assertEqual(outcome.record.error_class, PredictionErrorClass.MISMATCH)
        self.assertEqual(outcome.error.event_type, PREDICTION_ERROR)
        self.assertFalse(outcome.error.payload["automatic_retry_requested"])

    def test_partial_outcome_is_distinct(self):
        record, _ = self.create(expected_state={"locked": False, "ajar": False})
        outcome = self.tracker.resolve(
            record.prediction_id,
            observed_state={"locked": False},
            observation_refs=("obs-lock",),
            confidence=0.8,
            monotonic_time=100.7,
        )
        self.assertEqual(outcome.record.error_class, PredictionErrorClass.PARTIAL)

    def test_empty_observation_is_unknown_unobservable(self):
        record, _ = self.create()
        outcome = self.tracker.resolve(
            record.prediction_id,
            observed_state={},
            observation_refs=("obs-sensor-unavailable",),
            confidence=0.8,
            monotonic_time=100.7,
        )
        self.assertEqual(outcome.record.status, PredictionStatus.UNKNOWN)
        self.assertEqual(outcome.record.error_class, PredictionErrorClass.UNOBSERVABLE)

    def test_resolution_requires_evidence(self):
        record, _ = self.create()
        with self.assertRaisesRegex(ValueError, "requires evidence"):
            self.tracker.resolve(
                record.prediction_id,
                observed_state={"locked": False},
                observation_refs=(),
                confidence=0.9,
                monotonic_time=100.5,
            )

    def test_expiry_is_timeout_and_cannot_happen_early(self):
        record, _ = self.create()
        with self.assertRaisesRegex(ValueError, "before expected_by"):
            self.tracker.expire(record.prediction_id, monotonic_time=100.9)
        outcome = self.tracker.expire(record.prediction_id, monotonic_time=101.1)
        self.assertEqual(outcome.record.status, PredictionStatus.EXPIRED)
        self.assertEqual(outcome.record.error_class, PredictionErrorClass.TIMEOUT)
        self.assertFalse(outcome.error.payload["automatic_retry_requested"])

    def test_unknown_impossible_is_explicit(self):
        record, _ = self.create()
        outcome = self.tracker.mark_unknown(
            record.prediction_id,
            monotonic_time=100.5,
            reason_class=PredictionErrorClass.IMPOSSIBLE,
            observed_state={"sensor_state": "invalid"},
        )
        self.assertEqual(outcome.record.status, PredictionStatus.UNKNOWN)
        self.assertEqual(outcome.record.error_class, PredictionErrorClass.IMPOSSIBLE)

    def test_cannot_resolve_twice(self):
        record, _ = self.create()
        self.tracker.resolve(
            record.prediction_id,
            observed_state={"locked": False},
            observation_refs=("obs-lock",),
            confidence=1.0,
            monotonic_time=100.5,
        )
        with self.assertRaisesRegex(RuntimeError, "already resolved"):
            self.tracker.resolve(
                record.prediction_id,
                observed_state={"locked": True},
                observation_refs=("obs-lock-2",),
                confidence=1.0,
                monotonic_time=100.6,
            )

    def test_error_chain_follows_resolution(self):
        record, created = self.create()
        outcome = self.tracker.resolve(
            record.prediction_id,
            observed_state={"locked": True},
            observation_refs=("obs-lock",),
            confidence=1.0,
            monotonic_time=100.5,
        )
        self.assertEqual(outcome.resolution.parent_emission_id, created.emission_id)
        self.assertEqual(outcome.error.parent_emission_id, outcome.resolution.emission_id)

    def test_read_only_view_is_deeply_immutable(self):
        record, _ = self.create(expected_state={"nested": {"value": 1}})
        view = self.tracker.read_only_view(record.prediction_id)
        with self.assertRaises(TypeError):
            view["status"] = "confirmed"
        with self.assertRaises(TypeError):
            view["expected_state"]["nested"]["value"] = 2

    def test_stability_reports_confirmed_ratio(self):
        first, _ = self.create(prediction_id="prediction-a")
        second, _ = self.create(prediction_id="prediction-b", subject="passenger-door")
        self.tracker.resolve(
            first.prediction_id,
            observed_state={"locked": False},
            observation_refs=("obs-a",),
            confidence=1.0,
            monotonic_time=100.5,
        )
        self.tracker.resolve(
            second.prediction_id,
            observed_state={"locked": True},
            observation_refs=("obs-b",),
            confidence=1.0,
            monotonic_time=100.5,
        )
        self.assertEqual(self.tracker.prediction_stability(), 0.5)

    def test_event_document_matches_protocol_envelope(self):
        _, emission = self.create()
        document = emission.to_event_document(source="velvet-ai-core.prediction", timestamp=1000.0)
        self.assertEqual(document["metadata"]["contract"], "velvet.cognitive-events.v1")
        self.assertEqual(document["metadata"]["authority"], "none")
        self.assertIsNone(document["receipt_id"])


class ActionOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.ids = Ids()
        self.tracker = ActionOutcomeTracker(
            body_id="tiburon",
            node_id="up2-founder",
            id_factory=self.ids,
            replay_state="fixture",
        )

    def start(self, **overrides):
        values = {
            "cognitive_event_id": "cog-entry",
            "authorization_ref": "court-decision-1",
            "execution_ref": "execution-contract-1",
            "source_refs": ("proposal-1",),
            "prediction_refs": ("prediction-1",),
            "correlation_ids": ("entry-1",),
            "monotonic_time": 100.0,
        }
        values.update(overrides)
        return self.tracker.start(**values)

    def test_start_requires_external_refs(self):
        with self.assertRaisesRegex(ValueError, "authorization_ref"):
            self.start(authorization_ref="")
        with self.assertRaisesRegex(ValueError, "execution_ref"):
            self.start(execution_ref="")

    def test_start_is_tracking_only(self):
        record, emission = self.start()
        self.assertEqual(record.state, ActionTrackingState.STARTED)
        self.assertEqual(emission.event_type, ACTION_TRACKING_STARTED)
        self.assertTrue(emission.payload["tracking_only"])
        self.assertFalse(emission.payload["execution_performed"])
        self.assertFalse(emission.payload["automatic_retry_requested"])

    def test_completed_requires_evidence_and_tracks_outcome(self):
        record, started = self.start()
        with self.assertRaisesRegex(ValueError, "requires outcome evidence"):
            self.tracker.finish(
                record.tracking_id,
                state=ActionTrackingState.COMPLETED,
                monotonic_time=100.4,
            )
        finished, emission = self.tracker.finish(
            record.tracking_id,
            state=ActionTrackingState.COMPLETED,
            monotonic_time=100.5,
            observation_refs=("obs-lock-unlocked",),
            receipt_refs=("receipt-execution",),
            observed_state={"locked": False},
            outcome_confidence=0.99,
        )
        self.assertEqual(finished.state, ActionTrackingState.COMPLETED)
        self.assertEqual(emission.event_type, ACTION_TRACKING_FINISHED)
        self.assertEqual(emission.parent_emission_id, started.emission_id)
        self.assertEqual(emission.payload["observed_state"], {"locked": False})

    def test_failed_does_not_retry(self):
        record, _ = self.start()
        _, emission = self.tracker.finish(
            record.tracking_id,
            state=ActionTrackingState.FAILED,
            monotonic_time=100.5,
            receipt_refs=("receipt-failure",),
            observed_state={"fault": "jammed"},
        )
        self.assertFalse(emission.payload["automatic_retry_requested"])
        self.assertFalse(emission.payload["grants_authority"])

    def test_interrupted_preserves_outstanding_effects(self):
        record, _ = self.start()
        with self.assertRaisesRegex(ValueError, "outstanding effect"):
            self.tracker.finish(
                record.tracking_id,
                state=ActionTrackingState.INTERRUPTED,
                monotonic_time=100.4,
            )
        finished, emission = self.tracker.finish(
            record.tracking_id,
            state=ActionTrackingState.INTERRUPTED,
            monotonic_time=100.5,
            outstanding_effect_refs=("door-motor-state-unknown",),
            observed_state={"locked": "unknown"},
        )
        self.assertEqual(finished.state, ActionTrackingState.INTERRUPTED)
        self.assertEqual(
            emission.payload["outstanding_effect_refs"],
            ("door-motor-state-unknown",),
        )

    def test_unknown_outcome_is_explicit(self):
        record, _ = self.start()
        finished, emission = self.tracker.finish(
            record.tracking_id,
            state=ActionTrackingState.UNKNOWN,
            monotonic_time=100.5,
            observed_state={"locked": "unobservable"},
            outcome_confidence=0.4,
        )
        self.assertEqual(finished.state, ActionTrackingState.UNKNOWN)
        self.assertEqual(emission.payload["outcome_confidence"], 0.4)

    def test_observed_state_rejects_authority_smuggling(self):
        record, _ = self.start()
        with self.assertRaisesRegex(ValueError, "forbidden authority"):
            self.tracker.finish(
                record.tracking_id,
                state=ActionTrackingState.UNKNOWN,
                monotonic_time=100.5,
                observed_state={"nested": {"capability_token": "bad"}},
            )

    def test_cannot_finish_twice(self):
        record, _ = self.start()
        self.tracker.finish(
            record.tracking_id,
            state=ActionTrackingState.UNKNOWN,
            monotonic_time=100.5,
        )
        with self.assertRaisesRegex(RuntimeError, "already finished"):
            self.tracker.finish(
                record.tracking_id,
                state=ActionTrackingState.UNKNOWN,
                monotonic_time=100.6,
            )


class WorkspaceIntegrationTests(unittest.TestCase):
    def test_context_rejects_closed_or_forged_workspace(self):
        with self.assertRaisesRegex(ValueError, "closed"):
            CognitiveWorkspaceContext.from_view(
                workspace_view(lifecycle_state="COMPLETED", mode="OBSERVE")
            )
        forged = workspace_view()
        forged["nested"] = {"capability_token": "bad"}
        with self.assertRaisesRegex(ValueError, "forbidden authority"):
            CognitiveWorkspaceContext.from_view(forged)

    def test_prediction_attaches_to_workspace_body_and_correlations(self):
        tracker = PredictionTracker(
            body_id="tiburon",
            node_id="up2-founder",
            replay_state="fixture",
        )
        record, emission = tracker.create_from_workspace(
            workspace_view=workspace_view(mode="PROPOSE_ACTION", lifecycle_state="PROPOSAL_PENDING"),
            subject="driver_door_lock",
            expected_state={"locked": False},
            expected_by=101.0,
            confidence=0.9,
            source_model="door-state",
            source_version="1",
            monotonic_time=100.1,
            observation_refs=("obs-auth",),
        )
        self.assertEqual(record.cognitive_event_id, "cog-entry")
        self.assertEqual(emission.payload["correlation_ids"], ("entry-1",))
        self.assertIn("obs-presence", emission.payload["source_refs"])

    def test_action_tracking_requires_track_mode_and_existing_refs(self):
        tracker = ActionOutcomeTracker(
            body_id="tiburon",
            node_id="up2-founder",
            replay_state="fixture",
        )
        with self.assertRaisesRegex(ValueError, "TRACK_ACTION"):
            tracker.start_from_workspace(
                workspace_view=workspace_view(mode="PROPOSE_ACTION", lifecycle_state="PROPOSAL_PENDING"),
                authorization_ref="court-decision-1",
                execution_ref="execution-contract-1",
                monotonic_time=100.2,
            )
        with self.assertRaisesRegex(ValueError, "authorization_ref"):
            tracker.start_from_workspace(
                workspace_view=workspace_view(),
                authorization_ref="court-other",
                execution_ref="execution-contract-1",
                monotonic_time=100.2,
            )

    def test_full_explicit_prediction_outcome_loop(self):
        predictions = PredictionTracker(
            body_id="tiburon", node_id="up2-founder", replay_state="fixture"
        )
        prediction, _ = predictions.create_from_workspace(
            workspace_view=workspace_view(mode="PROPOSE_ACTION", lifecycle_state="PROPOSAL_PENDING"),
            subject="driver_door_lock",
            expected_state={"locked": False},
            expected_by=101.0,
            confidence=0.95,
            source_model="door-state",
            source_version="1",
            monotonic_time=100.1,
            observation_refs=("obs-auth",),
            prediction_id="prediction-unlock",
        )
        actions = ActionOutcomeTracker(
            body_id="tiburon", node_id="up2-founder", replay_state="fixture"
        )
        action, _ = actions.start_from_workspace(
            workspace_view=workspace_view(),
            authorization_ref="court-decision-1",
            execution_ref="execution-contract-1",
            prediction_refs=(prediction.prediction_id,),
            monotonic_time=100.2,
        )
        finished, _ = actions.finish(
            action.tracking_id,
            state=ActionTrackingState.COMPLETED,
            monotonic_time=100.5,
            observation_refs=("obs-lock-unlocked",),
            receipt_refs=("receipt-unlock",),
            observed_state={"locked": False},
            outcome_confidence=0.99,
        )
        outcome = predictions.resolve(
            prediction.prediction_id,
            observed_state=finished.observed_state,
            observation_refs=finished.observation_refs,
            receipt_refs=finished.receipt_refs,
            confidence=finished.outcome_confidence,
            monotonic_time=finished.finished_at,
        )
        self.assertEqual(outcome.record.status, PredictionStatus.CONFIRMED)
        self.assertIsNone(outcome.error)
        self.assertFalse(outcome.record.automatic_retry_requested)


if __name__ == "__main__":
    unittest.main()

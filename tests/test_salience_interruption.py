import unittest
from types import MappingProxyType, SimpleNamespace

from velvet.core.cognition.salience_interruption import (
    INTERRUPT_ACCEPTED,
    INTERRUPT_CANDIDATE,
    SalienceAccumulator,
    SalienceDisposition,
    SalienceSignal,
    apply_accepted_interrupt,
)


class Ids:
    def __init__(self):
        self.value = 0

    def __call__(self, prefix):
        self.value += 1
        return "%s-%02d" % (prefix, self.value)


def workspace_view(**overrides):
    values = {
        "cognitive_event_id": "cog-driving",
        "body_id": "tiburon",
        "node_id": "up2-founder",
        "lifecycle_state": "DEVELOPING",
        "mode": "OBSERVE",
        "source_refs": ("obs-road",),
        "correlation_ids": ("drive-1",),
        "proposal_refs": (),
        "authorization_refs": (),
        "execution_refs": (),
        "prediction_refs": (),
        "replay_state": "fixture",
        "interpretation_only": True,
        "canonical_evidence": False,
        "authority": "none",
        "grants_authority": False,
        "grants_execution": False,
        "grants_actuation": False,
    }
    values.update(overrides)
    return values


def signal(signal_id="sig-1", interrupt_key="impact", **overrides):
    values = {
        "signal_id": signal_id,
        "interrupt_key": interrupt_key,
        "cognitive_event_id": "cog-driving",
        "event_type": "vehicle.impact.candidate",
        "source": "imu",
        "body_id": "tiburon",
        "node_id": "up2-founder",
        "reason": "unexpected acceleration",
        "observed_at": 100.0,
        "monotonic_time": 100.0,
        "severity": 0.2,
        "rate_of_change": 0.2,
        "novelty": 0.2,
        "confidence": 0.7,
        "source_trust": 0.9,
        "persistence": 0.1,
        "cross_sensor_agreement": 0.0,
        "source_refs": ("obs-imu",),
        "correlation_ids": ("drive-1",),
        "replay_state": "fixture",
    }
    values.update(overrides)
    return SalienceSignal(**values)


class SalienceAccumulatorTests(unittest.TestCase):
    def setUp(self):
        self.ids = Ids()
        self.accumulator = SalienceAccumulator(
            body_id="tiburon",
            node_id="up2-founder",
            id_factory=self.ids,
            replay_state="fixture",
        )

    def test_low_priority_novelty_does_not_interrupt(self):
        result = self.accumulator.evaluate(
            signal(), workspace_view=workspace_view(), now=100.1
        )
        self.assertEqual(result.disposition, SalienceDisposition.ACCUMULATING)
        self.assertEqual(result.candidate.event_type, INTERRUPT_CANDIDATE)
        self.assertIsNone(result.accepted)
        self.assertLess(result.record.accumulated_score, result.record.threshold)

    def test_persistent_moderate_risk_crosses_threshold(self):
        common = {
            "severity": 0.55,
            "rate_of_change": 0.5,
            "novelty": 0.4,
            "confidence": 0.9,
            "source_trust": 0.9,
            "persistence": 0.6,
            "cross_sensor_agreement": 0.5,
        }
        first = self.accumulator.evaluate(
            signal("sig-a", **common), workspace_view=workspace_view(), now=100.1
        )
        second = self.accumulator.evaluate(
            signal("sig-b", observed_at=100.1, monotonic_time=100.1, **common),
            workspace_view=workspace_view(),
            now=100.2,
        )
        self.assertEqual(first.disposition, SalienceDisposition.ACCUMULATING)
        self.assertEqual(second.disposition, SalienceDisposition.ACCEPTED)
        self.assertEqual(second.accepted.event_type, INTERRUPT_ACCEPTED)
        self.assertGreaterEqual(
            second.record.accumulated_score, second.record.threshold
        )

    def test_critical_signal_interrupts_immediately_without_safeing_authority(self):
        result = self.accumulator.evaluate(
            signal(
                severity=0.95,
                rate_of_change=0.9,
                novelty=0.6,
                confidence=0.99,
                source_trust=0.99,
                persistence=0.8,
                cross_sensor_agreement=0.8,
                safety_critical=True,
                requires_immediate_safeing=True,
                outstanding_effect_refs=("steering-state-unknown",),
            ),
            workspace_view=workspace_view(),
            now=100.1,
        )
        self.assertEqual(result.disposition, SalienceDisposition.ACCEPTED)
        self.assertTrue(result.accepted.payload["requires_immediate_safeing"])
        self.assertFalse(result.accepted.payload["safeing_authorized"])
        self.assertFalse(result.accepted.payload["safeing_performed"])
        self.assertEqual(result.accepted.payload["safe_state_reached"], "unknown")

    def test_duplicate_signal_is_idempotent(self):
        first = self.accumulator.evaluate(
            signal(), workspace_view=workspace_view(), now=100.1
        )
        duplicate = self.accumulator.evaluate(
            signal(), workspace_view=workspace_view(), now=100.2
        )
        self.assertEqual(first.disposition, SalienceDisposition.ACCUMULATING)
        self.assertEqual(duplicate.disposition, SalienceDisposition.DUPLICATE)
        self.assertEqual(len(duplicate.record.signal_refs), 1)

    def test_stale_and_unrelated_signals_are_rejected(self):
        stale = self.accumulator.evaluate(
            signal(stale_after_ms=100), workspace_view=workspace_view(), now=101.0
        )
        unrelated = self.accumulator.evaluate(
            signal("sig-2", cognitive_event_id="cog-other"),
            workspace_view=workspace_view(),
            now=100.1,
        )
        self.assertEqual(stale.disposition, SalienceDisposition.STALE)
        self.assertEqual(unrelated.disposition, SalienceDisposition.UNRELATED)

    def test_wrong_body_and_node_are_distinct(self):
        body = self.accumulator.evaluate(
            signal(body_id="house"), workspace_view=workspace_view(), now=100.1
        )
        node = self.accumulator.evaluate(
            signal("sig-2", node_id="velour"),
            workspace_view=workspace_view(),
            now=100.1,
        )
        self.assertEqual(body.disposition, SalienceDisposition.WRONG_BODY)
        self.assertEqual(node.disposition, SalienceDisposition.WRONG_NODE)

    def test_replay_posture_must_match(self):
        with self.assertRaisesRegex(ValueError, "replay_state"):
            self.accumulator.evaluate(
                signal(replay_state="live"),
                workspace_view=workspace_view(),
                now=100.1,
            )

    def test_payload_rejects_authority_and_safeing_smuggling(self):
        with self.assertRaisesRegex(ValueError, "forbidden authority"):
            signal(payload={"nested": {"capability_token": "bad"}})
        with self.assertRaisesRegex(ValueError, "forbidden authority"):
            signal(payload={"safeing_authorized": True})

    def test_source_flood_is_rate_limited(self):
        accumulator = SalienceAccumulator(
            body_id="tiburon",
            node_id="up2-founder",
            max_signals_per_source=1,
            replay_state="fixture",
        )
        first = accumulator.evaluate(
            signal("sig-a"), workspace_view=workspace_view(), now=100.1
        )
        second = accumulator.evaluate(
            signal("sig-b", observed_at=100.1, monotonic_time=100.1),
            workspace_view=workspace_view(),
            now=100.2,
        )
        self.assertEqual(first.disposition, SalienceDisposition.ACCUMULATING)
        self.assertEqual(second.disposition, SalienceDisposition.RATE_LIMITED)

    def test_accepted_interrupt_is_not_accepted_twice(self):
        critical = dict(
            severity=1.0,
            rate_of_change=1.0,
            novelty=1.0,
            confidence=1.0,
            source_trust=1.0,
            persistence=1.0,
            cross_sensor_agreement=1.0,
            safety_critical=True,
        )
        first = self.accumulator.evaluate(
            signal("sig-a", **critical), workspace_view=workspace_view(), now=100.1
        )
        second = self.accumulator.evaluate(
            signal("sig-b", observed_at=100.1, monotonic_time=100.1, **critical),
            workspace_view=workspace_view(),
            now=100.2,
        )
        self.assertEqual(first.disposition, SalienceDisposition.ACCEPTED)
        self.assertEqual(second.disposition, SalienceDisposition.ALREADY_ACCEPTED)

    def test_candidate_and_acceptance_emission_chain(self):
        result = self.accumulator.evaluate(
            signal(
                severity=1.0,
                rate_of_change=1.0,
                novelty=1.0,
                confidence=1.0,
                source_trust=1.0,
                persistence=1.0,
                cross_sensor_agreement=1.0,
                safety_critical=True,
            ),
            workspace_view=workspace_view(),
            now=100.1,
        )
        self.assertEqual(
            result.accepted.parent_emission_id, result.candidate.emission_id
        )
        document = result.accepted.to_event_document(
            source="velvet-ai-core.salience", timestamp=1000.0
        )
        self.assertEqual(
            document["metadata"]["contract"], "velvet.cognitive-events.v1"
        )
        self.assertEqual(document["metadata"]["authority"], "none")

    def test_read_only_view_is_immutable(self):
        result = self.accumulator.evaluate(
            signal(), workspace_view=workspace_view(), now=100.1
        )
        view = self.accumulator.read_only_view("impact")
        self.assertIsInstance(view, MappingProxyType)
        with self.assertRaises(TypeError):
            view["accepted"] = True
        self.assertFalse(result.record.authority_granted)


class FakeWorkspace:
    def __init__(self):
        self.view = workspace_view()
        self.observed = None
        self.boundary_kwargs = None

    def read_only_view(self):
        return self.view

    def observe(self, observation, **kwargs):
        self.observed = observation
        return SimpleNamespace(disposition=SimpleNamespace(value="accepted"))

    def propose_boundary(self, **kwargs):
        self.boundary_kwargs = kwargs
        return SimpleNamespace(boundary_id="boundary-1", **kwargs)


class WorkspaceApplicationTests(unittest.TestCase):
    def test_accepted_interrupt_becomes_workspace_evidence_and_boundary(self):
        accumulator = SalienceAccumulator(
            body_id="tiburon", node_id="up2-founder", replay_state="fixture"
        )
        result = accumulator.evaluate(
            signal(
                severity=1.0,
                rate_of_change=1.0,
                novelty=1.0,
                confidence=1.0,
                source_trust=1.0,
                persistence=1.0,
                cross_sensor_agreement=1.0,
                safety_critical=True,
            ),
            workspace_view=workspace_view(),
            now=100.1,
        )
        workspace = FakeWorkspace()
        application = apply_accepted_interrupt(workspace, result, now=100.1)
        self.assertEqual(workspace.observed.event_type, INTERRUPT_ACCEPTED)
        self.assertFalse(workspace.observed.payload["safeing_authorized"])
        self.assertEqual(
            getattr(application.boundary.recommended_terminal_state, "value", None),
            "INTERRUPTED",
        )
        self.assertEqual(
            application.boundary.evidence_refs,
            (result.accepted.emission_id,),
        )

    def test_nonaccepted_candidate_cannot_interrupt_workspace(self):
        accumulator = SalienceAccumulator(
            body_id="tiburon", node_id="up2-founder", replay_state="fixture"
        )
        result = accumulator.evaluate(
            signal(), workspace_view=workspace_view(), now=100.1
        )
        with self.assertRaisesRegex(ValueError, "accepted interrupt"):
            apply_accepted_interrupt(FakeWorkspace(), result, now=100.1)


if __name__ == "__main__":
    unittest.main()

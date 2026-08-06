import unittest
from types import MappingProxyType

from velvet.core.cognition.operational_modulators import (
    MODULATORS_SNAPSHOTTED,
    ModulatorUpdate,
    OperationalModulatorRegistry,
)
from velvet.core.cognition.social_turn_taking import (
    SocialTurnCoordinator,
    TurnPosture,
    TurnSignals,
)


class Ids:
    def __init__(self):
        self.value = 0

    def __call__(self, prefix):
        self.value += 1
        return "%s-%02d" % (prefix, self.value)


def workspace_view(**overrides):
    values = {
        "cognitive_event_id": "cog-cabin",
        "body_id": "tiburon",
        "node_id": "up2-founder",
        "lifecycle_state": "DEVELOPING",
        "mode": "OBSERVE",
        "source_refs": ("obs-presence",),
        "correlation_ids": ("cabin-1",),
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


def update(update_id="update-1", source="prediction", values=None, **overrides):
    data = {
        "update_id": update_id,
        "source": source,
        "body_id": "tiburon",
        "node_id": "up2-founder",
        "cognitive_event_id": "cog-cabin",
        "values": values or {"uncertainty": 0.8},
        "source_refs": ("obs-update",),
        "correlation_ids": ("cabin-1",),
        "monotonic_time": 100.0,
        "replay_state": "fixture",
    }
    data.update(overrides)
    return ModulatorUpdate(**data)


def signals(**overrides):
    data = {
        "signal_id": "turn-1",
        "body_id": "tiburon",
        "node_id": "up2-founder",
        "cognitive_event_id": "cog-cabin",
        "source_refs": ("obs-turn",),
        "correlation_ids": ("cabin-1",),
        "owner_present": True,
        "elapsed_silence_seconds": 1.0,
        "replay_state": "fixture",
    }
    data.update(overrides)
    return TurnSignals(**data)


class OperationalModulatorTests(unittest.TestCase):
    def setUp(self):
        self.registry = OperationalModulatorRegistry(
            body_id="tiburon",
            node_id="up2-founder",
            replay_state="fixture",
            id_factory=Ids(),
        )

    def test_allowed_source_updates_modulator(self):
        changed = self.registry.apply(update(), workspace_view=workspace_view())
        self.assertTrue(changed)
        self.assertEqual(self.registry.value("uncertainty"), 0.8)

    def test_source_allowlist_is_enforced(self):
        with self.assertRaisesRegex(ValueError, "cannot update"):
            update(source="presence", values={"urgency": 0.9})

    def test_duplicate_update_is_idempotent(self):
        item = update()
        self.assertTrue(self.registry.apply(item, workspace_view=workspace_view()))
        self.assertFalse(self.registry.apply(item, workspace_view=workspace_view()))

    def test_rate_limit_bounds_later_change(self):
        self.registry.apply(
            update(values={"uncertainty": 0.0}),
            workspace_view=workspace_view(),
        )
        self.registry.apply(
            update(
                "update-2",
                values={"uncertainty": 1.0},
                monotonic_time=100.1,
            ),
            workspace_view=workspace_view(),
        )
        self.assertLessEqual(self.registry.value("uncertainty"), 0.061)

    def test_decay_moves_toward_baseline(self):
        self.registry.apply(
            update(values={"uncertainty": 1.0}),
            workspace_view=workspace_view(),
        )
        self.registry.advance(105.0)
        self.assertLess(self.registry.value("uncertainty"), 1.0)
        self.assertGreaterEqual(self.registry.value("prediction_stability"), 0.0)

    def test_wrong_event_and_replay_fail(self):
        with self.assertRaisesRegex(ValueError, "another cognitive event"):
            self.registry.apply(
                update(cognitive_event_id="cog-other"),
                workspace_view=workspace_view(),
            )
        with self.assertRaisesRegex(ValueError, "replay_state"):
            self.registry.apply(
                update("update-2", replay_state="live"),
                workspace_view=workspace_view(),
            )

    def test_trust_context_must_come_from_runtime(self):
        with self.assertRaisesRegex(ValueError, "velvet-runtime"):
            self.registry.set_trust_context(
                "owner_verified", source="language", source_ref="ctx-1"
            )
        self.registry.set_trust_context(
            "owner_verified", source="velvet-runtime", source_ref="ctx-1"
        )
        snapshot = self.registry.snapshot_for_consumer(
            "turn-taking", workspace_view=workspace_view(), monotonic_time=100.0
        )
        self.assertEqual(snapshot.trust_context, "owner_verified")

    def test_forbidden_consumer_cannot_read_modulators(self):
        for consumer in ("court", "authentication", "executor", "safety-gate"):
            with self.assertRaisesRegex(ValueError, "forbidden"):
                self.registry.snapshot_for_consumer(
                    consumer,
                    workspace_view=workspace_view(),
                    monotonic_time=100.0,
                )

    def test_consumer_receives_only_allowlisted_values(self):
        snapshot = self.registry.snapshot_for_consumer(
            "turn-taking", workspace_view=workspace_view(), monotonic_time=100.0
        )
        self.assertNotIn("resource_pressure", snapshot.values)
        self.assertIn("urgency", snapshot.values)
        self.assertFalse(snapshot.authority_granted)

    def test_snapshot_event_matches_protocol_shape(self):
        snapshot = self.registry.snapshot_for_consumer(
            "interface", workspace_view=workspace_view(), monotonic_time=100.0
        )
        document = snapshot.to_event_document(
            source="velvet-ai-core.modulators", timestamp=1000.0
        )
        self.assertEqual(document["event_type"], MODULATORS_SNAPSHOTTED)
        self.assertTrue(document["payload"]["cannot_change_authority"])
        self.assertEqual(document["metadata"]["authority"], "none")

    def test_snapshot_view_is_immutable(self):
        snapshot = self.registry.snapshot_for_consumer(
            "logging", workspace_view=workspace_view(), monotonic_time=100.0
        )
        view = snapshot.read_only_view()
        self.assertIsInstance(view, MappingProxyType)
        with self.assertRaises(TypeError):
            view["authority_granted"] = True


class SocialTurnTests(unittest.TestCase):
    def setUp(self):
        self.coordinator = SocialTurnCoordinator()
        self.modulators = {
            "uncertainty": 0.2,
            "urgency": 0.1,
            "social_engagement": 0.7,
        }

    def decide(self, signal=None, modulators=None):
        return self.coordinator.decide(
            signal or signals(),
            workspace_view=workspace_view(),
            modulator_values=(
                self.modulators if modulators is None else modulators
            ),
        )

    def test_owner_speech_is_listened_to(self):
        decision = self.decide(signals(owner_speech_active=True))
        self.assertEqual(decision.posture, TurnPosture.LISTEN)
        self.assertFalse(decision.speak_allowed)

    def test_velvet_yields_when_owner_starts_speaking(self):
        decision = self.decide(
            signals(owner_speech_active=True, velvet_speaking=True)
        )
        self.assertEqual(decision.posture, TurnPosture.YIELD)

    def test_incomplete_utterance_holds_silence(self):
        decision = self.decide(
            signals(
                likely_incomplete_utterance=0.8,
                elapsed_silence_seconds=2.0,
            )
        )
        self.assertEqual(decision.posture, TurnPosture.HOLD_SILENCE)

    def test_short_silence_respects_hold_window(self):
        decision = self.decide(signals(elapsed_silence_seconds=0.2))
        self.assertEqual(decision.posture, TurnPosture.HOLD_SILENCE)

    def test_explicit_silence_wins(self):
        decision = self.decide(
            signals(requested_silence=True, response_ready=True)
        )
        self.assertEqual(decision.posture, TurnPosture.HOLD_SILENCE)

    def test_high_driving_demand_suppresses_nonessential_response(self):
        decision = self.decide(
            signals(driving_demand=0.9, response_ready=True)
        )
        self.assertEqual(decision.posture, TurnPosture.HOLD_SILENCE)

    def test_high_demand_question_gets_brief_acknowledgement(self):
        decision = self.decide(
            signals(
                driving_demand=0.9,
                response_ready=True,
                explicit_question_pending=True,
            )
        )
        self.assertEqual(decision.posture, TurnPosture.ACKNOWLEDGE)
        self.assertLessEqual(decision.maximum_response_seconds, 1.5)

    def test_ready_response_is_bounded(self):
        decision = self.decide(signals(response_ready=True))
        self.assertEqual(decision.posture, TurnPosture.RESPOND)
        self.assertTrue(decision.speak_allowed)
        self.assertGreater(decision.maximum_response_seconds, 0.0)

    def test_urgency_modulator_alone_cannot_trigger_safety_interrupt(self):
        decision = self.decide(
            signals(response_ready=True, safety_severity=1.0),
            modulators={"urgency": 1.0},
        )
        self.assertNotEqual(
            decision.posture, TurnPosture.INTERRUPT_FOR_SAFETY
        )
        self.assertFalse(decision.interrupting)

    def test_accepted_interrupt_is_required_for_safety_posture(self):
        decision = self.decide(
            signals(
                accepted_interrupt_ref="interrupt-1",
                safety_severity=0.9,
            )
        )
        self.assertEqual(
            decision.posture, TurnPosture.INTERRUPT_FOR_SAFETY
        )
        self.assertTrue(decision.interrupting)
        self.assertEqual(decision.accepted_interrupt_ref, "interrupt-1")
        self.assertFalse(decision.authority_granted)

    def test_turn_recovers_after_safety_clears(self):
        decision = self.decide(
            signals(
                previous_posture=TurnPosture.INTERRUPT_FOR_SAFETY,
                safety_severity=0.1,
                elapsed_silence_seconds=2.0,
            )
        )
        self.assertEqual(decision.posture, TurnPosture.RECOVER_TURN)

    def test_absent_partner_holds_silence(self):
        decision = self.decide(
            signals(owner_present=False, response_ready=True)
        )
        self.assertEqual(decision.posture, TurnPosture.HOLD_SILENCE)

    def test_wrong_workspace_or_forbidden_modulator_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "another cognitive event"):
            self.coordinator.decide(
                signals(cognitive_event_id="cog-other"),
                workspace_view=workspace_view(),
                modulator_values={},
            )
        with self.assertRaisesRegex(ValueError, "forbidden modulators"):
            self.decide(modulators={"resource_pressure": 0.8})

    def test_decision_view_is_immutable_and_proposal_only(self):
        decision = self.decide(signals(response_ready=True))
        view = decision.read_only_view()
        self.assertIsInstance(view, MappingProxyType)
        with self.assertRaises(TypeError):
            view["authority_granted"] = True
        self.assertTrue(decision.proposal_only)
        self.assertFalse(decision.authority_granted)


if __name__ == "__main__":
    unittest.main()

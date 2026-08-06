import unittest
from types import MappingProxyType

from velvet.core.cognition.governed_plasticity import (
    ChangeDelta,
    GovernedPlasticityRegistry,
    LearningComponentContract,
    LearningEvidence,
    PlasticityDisposition,
    PlasticityPosture,
    PlasticityProposal,
)


class Ids:
    def __init__(self):
        self.value = 0

    def __call__(self, prefix):
        self.value += 1
        return "%s-%02d" % (prefix, self.value)


def contract(**overrides):
    values = {
        "component_id": "turn-timing",
        "learning_domain": "conversation.timing",
        "mutable_fields": ("silence_hold_seconds",),
        "posture": PlasticityPosture.APPROVED,
        "maximum_change": 0.1,
        "evidence_threshold": 2,
        "minimum_samples": 20,
        "validation_method": "deterministic-replay",
        "rollback_checkpoint": "checkpoint-turn-v1",
        "owner_presence_required": True,
        "promotion_required": True,
        "receipt_policy": "plasticity.promotion.v1",
    }
    values.update(overrides)
    return LearningComponentContract(**values)


def evidence(evidence_id="evidence-1", **overrides):
    values = {
        "evidence_id": evidence_id,
        "component_id": "turn-timing",
        "body_id": "tiburon",
        "node_id": "up2-founder",
        "source": "turn-taking",
        "metric_name": "interruption_rate",
        "sample_count": 10,
        "confidence": 0.9,
        "source_refs": ("episode-1",),
        "receipt_refs": ("receipt-1",),
        "simulated": False,
        "replay_state": "live",
    }
    values.update(overrides)
    return LearningEvidence(**values)


def proposal(**overrides):
    values = {
        "proposal_id": "proposal-1",
        "component_id": "turn-timing",
        "body_id": "tiburon",
        "node_id": "up2-founder",
        "deltas": (
            ChangeDelta(
                field_name="silence_hold_seconds",
                before=0.45,
                after=0.49,
                normalized_magnitude=0.04,
            ),
        ),
        "evidence": (evidence("evidence-1"), evidence("evidence-2")),
        "checkpoint_ref": "checkpoint-turn-v1",
        "validation_ref": "validation-turn-v2",
        "source_refs": ("episode-1", "episode-2"),
        "created_at": 100.0,
        "expires_at": 200.0,
        "replay_state": "live",
        "owner_presence_ref": "presence-owner-1",
        "owner_presence_verified_by": "velvet-runtime",
        "owner_presence_simulated": False,
        "approval_ref": "owner-approval-1",
        "promotion_receipt_ref": "promotion-receipt-1",
    }
    values.update(overrides)
    return PlasticityProposal(**values)


class ContractTests(unittest.TestCase):
    def test_protected_learning_domains_are_rejected(self):
        for domain in (
            "court.policy",
            "identity.recognition",
            "vehicle.brake",
            "medical.emergency",
            "receipt.rewrite",
        ):
            with self.assertRaisesRegex(ValueError, "protected domains"):
                contract(learning_domain=domain)

    def test_protected_mutable_field_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "protected domains"):
            contract(mutable_fields=("safety_threshold",))

    def test_enabled_contract_requires_bounded_change_and_promotion(self):
        with self.assertRaisesRegex(ValueError, "maximum_change"):
            contract(maximum_change=0.0)
        with self.assertRaisesRegex(ValueError, "externally required"):
            contract(promotion_required=False)

    def test_change_delta_rejects_authority_smuggling(self):
        with self.assertRaisesRegex(ValueError, "forbidden authority"):
            ChangeDelta(
                "silence_hold_seconds",
                0.45,
                {"capability_token": "bad"},
                0.1,
            )


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = GovernedPlasticityRegistry(
            body_id="tiburon",
            node_id="up2-founder",
            replay_state="live",
            id_factory=Ids(),
        )
        self.registry.register(contract())

    def test_approved_contract_can_only_become_externally_eligible(self):
        decision = self.registry.evaluate(proposal(), now=120.0)
        self.assertEqual(
            decision.disposition,
            PlasticityDisposition.ELIGIBLE_FOR_EXTERNAL_PROMOTION,
        )
        self.assertTrue(decision.promotion_eligible)
        self.assertFalse(decision.change_applied)
        self.assertFalse(decision.authority_granted)
        self.assertTrue(decision.requires_external_promotion)

    def test_disabled_contract_rejects(self):
        registry = GovernedPlasticityRegistry(
            body_id="tiburon", node_id="up2-founder", replay_state="live"
        )
        registry.register(
            contract(
                posture=PlasticityPosture.DISABLED,
                maximum_change=0.0,
            )
        )
        decision = registry.evaluate(proposal(), now=120.0)
        self.assertEqual(decision.disposition, PlasticityDisposition.REJECTED)
        self.assertIn("disabled", " ".join(decision.reasons))

    def test_observe_only_never_promotes(self):
        registry = GovernedPlasticityRegistry(
            body_id="tiburon", node_id="up2-founder", replay_state="live"
        )
        registry.register(contract(posture=PlasticityPosture.OBSERVE_ONLY))
        decision = registry.evaluate(proposal(), now=120.0)
        self.assertEqual(
            decision.disposition, PlasticityDisposition.OBSERVED_ONLY
        )
        self.assertFalse(decision.promotion_eligible)

    def test_proposed_posture_requires_external_approval_even_with_refs(self):
        registry = GovernedPlasticityRegistry(
            body_id="tiburon", node_id="up2-founder", replay_state="live"
        )
        registry.register(contract(posture=PlasticityPosture.PROPOSED))
        decision = registry.evaluate(proposal(), now=120.0)
        self.assertEqual(
            decision.disposition,
            PlasticityDisposition.EXTERNAL_APPROVAL_REQUIRED,
        )
        self.assertIn("not approved", " ".join(decision.reasons))

    def test_missing_presence_approval_or_receipt_stays_external(self):
        decision = self.registry.evaluate(
            proposal(
                owner_presence_ref=None,
                owner_presence_verified_by=None,
                approval_ref=None,
                promotion_receipt_ref=None,
            ),
            now=120.0,
        )
        self.assertEqual(
            decision.disposition,
            PlasticityDisposition.EXTERNAL_APPROVAL_REQUIRED,
        )
        text = " ".join(decision.reasons)
        self.assertIn("owner presence", text)
        self.assertIn("approval", text)
        self.assertIn("promotion receipt", text)

    def test_simulated_presence_cannot_approve(self):
        decision = self.registry.evaluate(
            proposal(owner_presence_simulated=True), now=120.0
        )
        self.assertEqual(
            decision.disposition,
            PlasticityDisposition.EXTERNAL_APPROVAL_REQUIRED,
        )
        self.assertIn("simulated owner presence", " ".join(decision.reasons))

    def test_simulated_or_replay_evidence_cannot_promote(self):
        fixture_registry = GovernedPlasticityRegistry(
            body_id="tiburon",
            node_id="up2-founder",
            replay_state="fixture",
        )
        fixture_registry.register(contract())
        fixture_evidence = (
            evidence("evidence-1", simulated=True, replay_state="fixture"),
            evidence("evidence-2", simulated=True, replay_state="fixture"),
        )
        decision = fixture_registry.evaluate(
            proposal(
                replay_state="fixture",
                evidence=fixture_evidence,
            ),
            now=120.0,
        )
        self.assertEqual(
            decision.disposition,
            PlasticityDisposition.EXTERNAL_APPROVAL_REQUIRED,
        )
        self.assertIn("cannot be promoted", " ".join(decision.reasons))

    def test_insufficient_evidence_or_samples_rejects(self):
        decision = self.registry.evaluate(
            proposal(evidence=(evidence("evidence-1", sample_count=1),)),
            now=120.0,
        )
        self.assertEqual(decision.disposition, PlasticityDisposition.REJECTED)
        text = " ".join(decision.reasons)
        self.assertIn("evidence records", text)
        self.assertIn("evidence samples", text)

    def test_wrong_body_node_replay_and_expiry_reject(self):
        for kwargs, phrase in (
            ({"body_id": "house"}, "another body"),
            ({"node_id": "velour"}, "another node"),
            ({"replay_state": "fixture"}, "replay_state"),
        ):
            item = proposal(
                proposal_id="proposal-%s" % phrase.replace(" ", "-"),
                **kwargs
            )
            decision = self.registry.evaluate(item, now=120.0)
            self.assertEqual(
                decision.disposition, PlasticityDisposition.REJECTED
            )
            self.assertIn(phrase, " ".join(decision.reasons))
        expired = self.registry.evaluate(
            proposal(proposal_id="proposal-expired", expires_at=110.0),
            now=120.0,
        )
        self.assertIn("expired", " ".join(expired.reasons))

    def test_checkpoint_change_limit_and_mutable_fields_are_enforced(self):
        bad_checkpoint = self.registry.evaluate(
            proposal(
                proposal_id="proposal-checkpoint",
                checkpoint_ref="wrong",
            ),
            now=120.0,
        )
        self.assertIn("checkpoint", " ".join(bad_checkpoint.reasons))

        too_large = self.registry.evaluate(
            proposal(
                proposal_id="proposal-large",
                deltas=(
                    ChangeDelta(
                        "silence_hold_seconds", 0.45, 0.8, 0.35
                    ),
                ),
            ),
            now=120.0,
        )
        self.assertIn("maximum_change", " ".join(too_large.reasons))

        unknown_field = self.registry.evaluate(
            proposal(
                proposal_id="proposal-field",
                deltas=(ChangeDelta("voice_speed", 1.0, 0.95, 0.05),),
            ),
            now=120.0,
        )
        self.assertIn("non-mutable", " ".join(unknown_field.reasons))

    def test_proposal_idempotence_and_reuse_detection(self):
        first = self.registry.evaluate(proposal(), now=120.0)
        duplicate = self.registry.evaluate(proposal(), now=130.0)
        self.assertEqual(first.decision_id, duplicate.decision_id)
        with self.assertRaisesRegex(ValueError, "reused"):
            self.registry.evaluate(
                proposal(
                    deltas=(
                        ChangeDelta(
                            "silence_hold_seconds", 0.45, 0.5, 0.05
                        ),
                    )
                ),
                now=130.0,
            )

    def test_decision_view_is_immutable_and_nonapplying(self):
        decision = self.registry.evaluate(proposal(), now=120.0)
        view = decision.read_only_view()
        self.assertIsInstance(view, MappingProxyType)
        with self.assertRaises(TypeError):
            view["change_applied"] = True
        self.assertFalse(decision.change_applied)
        self.assertFalse(decision.authority_granted)

    def test_unregistered_component_rejects(self):
        registry = GovernedPlasticityRegistry(
            body_id="tiburon", node_id="up2-founder", replay_state="live"
        )
        decision = registry.evaluate(proposal(), now=120.0)
        self.assertEqual(decision.disposition, PlasticityDisposition.REJECTED)
        self.assertIn("no registered", " ".join(decision.reasons))


if __name__ == "__main__":
    unittest.main()
